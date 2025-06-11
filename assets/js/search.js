(function() {
  function displaySearchResults(results, store) {
    var searchResults = document.getElementById('search-results');
    searchResults.innerHTML = ''; // Clear previous results

    if (results.length) {
      var ul = document.createElement('ul');
      results.forEach(function(result) {
        var item = store[result.ref]; // Get the full item from the store
        var listItem = document.createElement('li');
        // Ensure item and item.url are defined before creating the link
        var linkHTML = item && item.url ? '<a href="' + item.url + '">' + (item.title || 'Untitled') + '</a>' : (item.title || 'Untitled');
        var excerptHTML = item && item.excerpt ? '<br><small>' + item.excerpt.substring(0,150) + '...</small>' : '';
        listItem.innerHTML = linkHTML + excerptHTML;
        ul.appendChild(listItem);
      });
      searchResults.appendChild(ul);
    } else {
      searchResults.innerHTML = '<li>No results found.</li>';
    }
  }

  // Get the path from the global variable set in default.html
  var searchDataURL = window.searchDataPath || '/assets/js/search-data.json'; // Fallback just in case

  fetch(searchDataURL)
    .then(response => {
      if (!response.ok) {
        throw new Error('Network response was not ok ' + response.statusText);
      }
      return response.json();
    })
    .then(documents => {
      // Create a store for easy access to document details by URL
      var store = {};
      documents.forEach(function(doc) {
        // Ensure doc.url is present before adding to store to prevent 'undefined' keys
        if (doc.url) {
          store[doc.url] = doc;
        } else {
          console.warn("Document without URL found:", doc);
        }
      });

      var idx = lunr(function () {
        this.ref('url');
        this.field('title', { boost: 10 });
        this.field('content');
        this.field('excerpt');

        documents.forEach(function (doc) {
          // Ensure doc has a URL before adding to Lunr, as it's the ref
          if (doc.url) {
            this.add(doc);
          }
        }, this);
      });

      var searchInput = document.getElementById('search-input');
      var searchResultsContainer = document.getElementById('search-results');

      if (searchInput) {
        searchInput.addEventListener('keyup', function () {
          var query = this.value.trim();
          if (query.length < 2 && query.length !== 0) {
            searchResultsContainer.innerHTML = ''; // Clear results for short queries
            searchResultsContainer.style.display = 'none';
            return;
          }
          if (query === "") {
            searchResultsContainer.innerHTML = ''; // Clear results if query is empty
            searchResultsContainer.style.display = 'none';
            return;
          }
          var results = idx.search(query);
          displaySearchResults(results, store);
          searchResultsContainer.style.display = results.length > 0 ? 'block' : 'none';
        });

        // Hide results when input loses focus, unless clicking on a result
        // This is a common pattern but can be tricky. A simpler approach:
        searchInput.addEventListener('blur', function() {
          // Delay hiding to allow click on results
          setTimeout(function() {
            // searchResultsContainer.innerHTML = '';
            // searchResultsContainer.style.display = 'none';
          }, 200); // 200ms delay
        });

        // Show results when input gains focus and there's text
         searchInput.addEventListener('focus', function () {
            if (this.value.trim().length >=2 && searchResultsContainer.children.length > 0) {
                 searchResultsContainer.style.display = 'block';
            }
        });

      } else {
        console.error("Search input field not found.");
      }
    })
    .catch(error => {
      console.error("Error fetching or processing search data:", error);
      var searchResults = document.getElementById('search-results');
      if (searchResults) {
        searchResults.innerHTML = '<li>Error loading search. Please try again later.</li>';
        searchResults.style.display = 'block';
      }
    });
})();
