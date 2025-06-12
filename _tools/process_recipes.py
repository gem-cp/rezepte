import re
import os
import sys
import yaml # For parsing front matter

# Helper to extract front matter and content
def extract_front_matter(text_content):
    front_matter = {}
    main_content = text_content

    if text_content.startswith("---"):
        try:
            end_fm = text_content.find("---", 3)
            if end_fm != -1:
                fm_text = text_content[3:end_fm]
                front_matter = yaml.safe_load(fm_text) or {} # Ensure it's a dict
                main_content = text_content[end_fm + 3:].lstrip()
        except yaml.YAMLError as e:
            print(f"Warning: Could not parse existing YAML front matter: {e}")
        except Exception as e:
            print(f"Warning: Error processing front matter: {e}")

    return front_matter, main_content

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


    existing_fm, main_markdown_content = extract_front_matter(content)

    # Initialize variables, prioritizing existing front matter for image
    image_path = existing_fm.get("image", "") # Get existing image path or default to empty

    # Most parsing will now happen on main_markdown_content, not the full 'content'

    # Extract Title (from the first H1 heading in main_markdown_content)
    title_match = re.search(r"^#\s*(.*)", main_markdown_content, re.MULTILINE)
    if title_match:
        title = title_match.group(1).strip()
    elif "title" in existing_fm: # Fallback to title in existing front matter
        title = existing_fm["title"]
    else:
        print(f"Warning: Title not found in H1 or front matter for {filepath}")
        title = "Untitled Recipe" # Default title

    # Extract Prep Time from main_markdown_content
    prep_time_match = re.search(r"Vorbereitungszeit:\s*(.*)", main_markdown_content, re.IGNORECASE)
    if prep_time_match:
        prep_time = prep_time_match.group(1).replace("**", "").strip()
    elif "prep_time" in existing_fm:
        prep_time = existing_fm["prep_time"]
    else:
        prep_time = "" # Handle missing field

    # Extract Cook Time from main_markdown_content
    cook_time_match = re.search(r"Kochzeit:\s*(.*)", main_markdown_content, re.IGNORECASE)
    if cook_time_match:
        cook_time = cook_time_match.group(1).replace("**", "").strip()
    elif "cook_time" in existing_fm:
        cook_time = existing_fm["cook_time"]
    else:
        cook_time = "" # Handle missing field

    # Extract Portions from main_markdown_content
    portions_match = re.search(r"Portionen:\s*(.*)", main_markdown_content, re.IGNORECASE)
    if portions_match:
        portions = portions_match.group(1).replace("**", "").strip()
    elif "portions" in existing_fm:
        portions = existing_fm["portions"]
    else:
        portions = "" # Handle missing field

    # Extract Ingredients from main_markdown_content
    ingredients_list = []
    ingredients_section_match = re.search(r"## Zutaten\n\n(.*?)(?=\n## |\Z)", main_markdown_content, re.DOTALL | re.IGNORECASE)
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
    elif "ingredients" in existing_fm and isinstance(existing_fm["ingredients"], list):
        ingredients_list = existing_fm["ingredients"]
    else:
        print(f"Warning: Ingredients not found in content or front matter for {filepath}")

    # Extract Instructions (Zubereitung) from main_markdown_content
    # If "Zubereitung" section exists, it's the primary source for instructions.
    # Otherwise, the whole main_markdown_content (after FM) is considered instructions.
    instructions_content = main_markdown_content # Default to all content after FM
    instructions_match = re.search(r"## Zubereitung\n\n(.*?)(?=\n## Hilfreiche Tipps|\Z)", main_markdown_content, re.DOTALL | re.IGNORECASE)
    if instructions_match:
        instructions_content = instructions_match.group(1).strip()
        # Check if there's any meaningful content before "Zubereitung" that's not part of other extractions
        # This part might need refinement if descriptions/intros are common before "Zutaten" or "Zubereitung"
        # For now, if "Zubereitung" is found, we prioritize that.
        # If an intro section exists before "Zutaten" or "Zubereitung", it might be lost with current logic
        # unless it's part of the content before the first H1 that becomes the title.

    else:
        # If no "Zubereitung" heading, check if there's an "instructions" field in existing FM
        if "instructions" in existing_fm:
             instructions_content = existing_fm["instructions"]
        else:
            # If still no "Zubereitung" heading, we use main_markdown_content,
            # but need to be careful if it contains the H1 title, metadata lines etc.
            # The current logic for title/metadata extraction should ideally remove those parts already.
            # This part is tricky: what if main_markdown_content *is* just the H1 title and metadata lines because there's no other body?
            # For now, if "Zubereitung" is not found, the whole main_markdown_content is used.
            # This might be okay if the file is purely a recipe instruction set without the specific heading.
            # If the content was already "Instructions could not be reliably extracted." from a previous run, keep it.
            if not main_markdown_content.strip() or main_markdown_content.strip() == "Instructions could not be reliably extracted.":
                 instructions_content = "Instructions could not be reliably extracted."
            # else, instructions_content is already main_markdown_content (this variable is no longer used for the main body)
            print(f"Warning: '## Zubereitung' section not found in {filepath}. The full original content (after any original FM) will be used as the body.")

    # The variable 'instructions_content' is no longer the definitive body for the output file.
    # The body of the new file will be 'main_markdown_content'.
    # The parsing logic above for title, ingredients, etc., is still valuable for the new front matter.
    # Manual escaping of title, prep_time etc. for YAML is not strictly needed here if yaml.dump is robust,
    # but it's kept for the new_front_matter_dict construction as a direct value.
    # yaml.dump itself should handle quoting and escaping correctly for the final YAML string.

    # Values for new_front_matter_dict should be the raw extracted ones.
    new_front_matter_dict = {
        "layout": "recipe",
        "title": title,
        "prep_time": prep_time,
        "cook_time": cook_time,
        "portions": portions,
        "ingredients": ingredients_list,
        "image": image_path # Use the preserved or default empty image_path
    }

    # Remove keys with empty string values, but keep image even if empty for Unsplash logic
    # Also keep ingredients even if empty list.
    # Note: The title, prep_time etc. going into new_front_matter_dict are already stripped and potentially modified.
    final_fm_dict = {k: v for k, v in new_front_matter_dict.items() if v or k == "image" or k == "ingredients"}


    try:
        # Use yaml.dump to generate the front matter string for better handling of special characters
        # and correct list formatting.
        fm_yaml_string = yaml.dump(final_fm_dict, allow_unicode=True, default_flow_style=False, sort_keys=False)
    except Exception as e:
        print(f"Error dumping YAML for {filepath}: {e}")
        # Fallback to basic string formatting if yaml.dump fails
        # For this fallback, we DO need to ensure the strings are properly escaped for manual YAML construction.
        escaped_title_fallback = str(final_fm_dict.get("title","")).replace('"', '\\"')
        escaped_prep_fallback = str(final_fm_dict.get("prep_time","")).replace('"', '\\"')
        escaped_cook_fallback = str(final_fm_dict.get("cook_time","")).replace('"', '\\"')
        escaped_portions_fallback = str(final_fm_dict.get("portions","")).replace('"', '\\"')
        escaped_image_fallback = str(final_fm_dict.get("image","")).replace('"', '\\"')

        fm_yaml_string = "layout: recipe\n"
        fm_yaml_string += f'title: "{escaped_title_fallback}"\n'
        if final_fm_dict.get("prep_time"): fm_yaml_string += f'prep_time: "{escaped_prep_fallback}"\n'
        if final_fm_dict.get("cook_time"): fm_yaml_string += f'cook_time: "{escaped_cook_fallback}"\n'
        if final_fm_dict.get("portions"): fm_yaml_string += f'portions: "{escaped_portions_fallback}"\n'
        fm_yaml_string += f'image: "{escaped_image_fallback}"\n' # Always include image
        fm_yaml_string += "ingredients:\n" # Always include ingredients key
        for ing in final_fm_dict.get("ingredients", []):
            escaped_ing = str(ing).replace('"', '\\"')
            fm_yaml_string += f'  - "{escaped_ing}"\n'

    # The main change: use main_markdown_content as the body of the new file
    new_content = f"---\n{fm_yaml_string}---\n\n{main_markdown_content}"

    # The 'title' returned is the one extracted for front matter.
    return new_content, final_fm_dict.get("title", "Untitled Recipe")

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
