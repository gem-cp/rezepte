import re
import os
import sys

def parse_recipe(filepath):
    """
    Parses a single recipe Markdown file and extracts metadata.
    """
    print(f"Processing {filepath}...")
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: File not found {filepath}")
        return None
    except Exception as e:
        print(f"Error reading file {filepath}: {e}")
        return None

    # Placeholder for parsing logic
    title = "Extracted Title Placeholder"
    prep_time = "Extracted Prep Time Placeholder"
    cook_time = "Extracted Cook Time Placeholder"
    portions = "Extracted Portions Placeholder"
    ingredients = ["Ingredient 1 Placeholder", "Ingredient 2 Placeholder"]
    instructions_content = "## Zubereitung\n\nInstructions placeholder."

    # Extract Title (from the first H1 heading)
    title_match = re.search(r"^#\s*(.*)", content, re.MULTILINE)
    if title_match:
        title = title_match.group(1).strip()
    else:
        print(f"Warning: Title not found in {filepath}")
        title = "Untitled Recipe" # Default title

    # Extract Prep Time
    prep_time_match = re.search(r"Vorbereitungszeit:\s*(.*)", content, re.IGNORECASE)
    if prep_time_match:
        prep_time = prep_time_match.group(1).replace("**", "").strip()
    else:
        prep_time = "" # Handle missing field

    # Extract Cook Time
    cook_time_match = re.search(r"Kochzeit:\s*(.*)", content, re.IGNORECASE)
    if cook_time_match:
        cook_time = cook_time_match.group(1).replace("**", "").strip()
    else:
        cook_time = "" # Handle missing field

    # Extract Portions
    portions_match = re.search(r"Portionen:\s*(.*)", content, re.IGNORECASE)
    if portions_match:
        portions = portions_match.group(1).replace("**", "").strip()
    else:
        portions = "" # Handle missing field

    # Extract Ingredients
    ingredients_list = []
    ingredients_section_match = re.search(r"## Zutaten\n\n(.*?)(?=\n## |\Z)", content, re.DOTALL | re.IGNORECASE)
    if ingredients_section_match:
        ingredients_text = ingredients_section_match.group(1).strip()
        raw_lines = ingredients_text.split('\n')
        for line in raw_lines:
            line = line.strip()
            if not line or line.startswith("**Für") or line.startswith("---") or line.lower().startswith("für "):
                continue
            line = re.sub(r"^\s*-\s*", "", line) # Remove leading dash
            line = re.sub(r"\*\*(.*?)\*\*", r"\1", line) # Remove bold markdown
            line = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", line) # Remove markdown links, keeping text
            if line:
                ingredients_list.append(line.strip())
    else:
        print(f"Warning: Ingredients not found in {filepath}")

    # Extract Instructions (Zubereitung)
    instructions_match = re.search(r"## Zubereitung\n\n(.*?)(?=\n## Hilfreiche Tipps|\Z)", content, re.DOTALL | re.IGNORECASE)
    if instructions_match:
        instructions_content = instructions_match.group(1).strip()
    else:
        # Fallback: if "Zubereitung" is not found, try to get content after last known metadata or ingredients
        print(f"Warning: '## Zubereitung' section not found in {filepath}. Trying to infer content.")
        # This is a basic fallback, might need refinement
        last_known_section_end = 0
        if ingredients_section_match:
            last_known_section_end = ingredients_section_match.end()

        # Try to find content that is not part of a known section
        potential_content_start = content.find("Portionen:") # Example, find end of last metadata
        if potential_content_start != -1:
            potential_content_start = content.find('\n', potential_content_start) # Move to next line
            if potential_content_start != -1:
                 # Look for the next significant heading or end of file
                next_heading_match = re.search(r"\n## ", content[potential_content_start:], re.IGNORECASE)
                if next_heading_match:
                    instructions_content = content[potential_content_start : potential_content_start + next_heading_match.start()].strip()
                else:
                    instructions_content = content[potential_content_start:].strip() # Take rest of the file
            else:
                instructions_content = "Instructions could not be reliably extracted."
        else:
             instructions_content = "Instructions could not be reliably extracted."


    # Construct new file content
    front_matter = f"""---
layout: recipe
title: "{title}"
prep_time: "{prep_time}"
cook_time: "{cook_time}"
portions: "{portions}"
ingredients:
"""
    for ingredient in ingredients_list:
        front_matter += f'  - "{ingredient}"\n'
    front_matter += 'image: "" # Placeholder for now\n---\n\n'

    new_content = front_matter + instructions_content

    return new_content, title

def main():
    if len(sys.argv) < 2:
        print("Usage: python process_recipes.py <input_file_or_directory>")
        sys.exit(1)

    input_path = sys.argv[1]
    output_dir = "_recipes"

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created output directory: {output_dir}")

    if os.path.isfile(input_path):
        if input_path.endswith(".md"):
            new_content, title = parse_recipe(input_path)
            if new_content and title:
                # Generate filename (e.g., palak-paneer.md from Palak Paneer)
                base_filename = os.path.basename(input_path)
                # A more robust way to generate filename would be to slugify the title
                # For now, use original filename
                output_filepath = os.path.join(output_dir, base_filename)

                try:
                    with open(output_filepath, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    print(f"Successfully processed and wrote: {output_filepath}")
                except Exception as e:
                    print(f"Error writing file {output_filepath}: {e}")
        else:
            print(f"Skipping non-markdown file: {input_path}")

    elif os.path.isdir(input_path):
        print(f"Processing all .md files in directory: {input_path}")
        for filename in os.listdir(input_path):
            if filename.endswith(".md"):
                filepath = os.path.join(input_path, filename)
                # Call parse_recipe and write new file (similar to single file logic)
                parsed_data = parse_recipe(filepath)
                if parsed_data:
                    new_content, title = parsed_data
                    # Generate filename
                    base_filename = filename # Use original filename
                    output_filepath = os.path.join(output_dir, base_filename)
                    try:
                        with open(output_filepath, 'w', encoding='utf-8') as f:
                            f.write(new_content)
                        print(f"Successfully processed and wrote: {output_filepath}")
                    except Exception as e:
                        print(f"Error writing file {output_filepath}: {e}")
            else:
                print(f"Skipping non-markdown file in directory: {filename}")
    else:
        print(f"Error: Input path {input_path} is not a valid file or directory.")
        sys.exit(1)

if __name__ == "__main__":
    main()
