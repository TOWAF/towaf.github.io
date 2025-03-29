import os # Used for encoding and decoding JSON data
import json # File path manipulation and directory operations.
import re # Pattern matching and text manipulation.
import hashlib # Hash algorithms to compare new dataset fragments

def slugify(text):
    """
    Convert many values into a file-friendly-slug:
    - Lowercase the text.
    - Replace spaces and underscores with dashes.
    - Remove characters that are not alphanumeric, dashes, or dots.
    - Remove leading and trailing dots.
    """
    text = str(text).lower().replace(" ", "-").replace("_", "-")
    return re.sub(r'[^a-z0-9\-.]', '', text).strip(".")

def normalize_value(value):
    """
    Ensure all values are strings; if missing, default to "unknown".
    """
    return str(value).strip() if value not in ("", None) else "unknown"

def write_file(file_path, content_str):
    """
    Write content_str to file_path only if the content hash differs.
    Ensures the directory exists before writing.
    """
    new_hash = hashlib.sha256(content_str.encode('utf-8')).hexdigest()

    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                existing_content = f.read()
            existing_hash = hashlib.sha256(existing_content.encode('utf-8')).hexdigest()
            if existing_hash == new_hash:
                print(f"Skipping write for {file_path} (content hash unchanged)")
                return
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")

    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content_str)
        print(f"Updated file: {file_path}")
    except Exception as e:
        print(f"Error writing file {file_path}: {e}")

def cleanup_directory(directory, expected_files):
    """
    Delete any .html file in the specified directory that is not in expected_files.
    """
    if os.path.exists(directory):
        for filename in os.listdir(directory):
            if filename.endswith(".html") and filename not in expected_files:
                file_path = os.path.join(directory, filename)
                try:
                    os.remove(file_path)
                    print(f"Deleted orphaned file: {file_path}")
                except Exception as e:
                    print(f"Error deleting file {file_path}: {e}")

def load_database(db_path):
    """
    Load the JSON dataset from the given path.
    """
    if not os.path.exists(db_path):
        print(f"Error: Database file {db_path} not found.")
        return None
    with open(db_path, "r", encoding="utf-8") as f:
        return json.load(f)

def load_template(template_path):
    """
    Load the HTML template file from the given path.
    """
    if not os.path.exists(template_path):
        print(f"Error: Template file {template_path} not found.")
        return None
    with open(template_path, "r", encoding="utf-8") as f:
        return f.read()

def generate_media_html(entry, template):
    """
    Replace placeholders in the media-piece template with entry data.
    Expected placeholders:
      - NAME_ENTRY, TOPIC_ENTRY, CATEGORY_ENTRY (display originals)
      - TOPIC-SLUGIFIED, CATEGORY-SLUGIFIED, NAME-SLUGIFIED (for URLs)
    """
    return (template
            .replace("NAME_ENTRY", entry.get("name", "Unknown"))
            .replace("TOPIC_ENTRY", entry.get("topic", "Unknown"))
            .replace("CATEGORY_ENTRY", entry.get("category", "Unknown"))
            .replace("TOPIC-SLUGIFIED", slugify(entry.get("topic", "unknown")))
            .replace("CATEGORY-SLUGIFIED", slugify(entry.get("category", "unknown")))
            .replace("NAME-SLUGIFIED", slugify(entry.get("name", "unknown")))
           )

def generate_category_html(topic_original, category_original, entries, category_template):
    """
    Generate the HTML for a category summary page.
    The category template should have placeholders:
      - TOPIC_ENTRY, CATEGORY_ENTRY (original names)
      - TOPIC-SLUGIFIED, CATEGORY-SLUGIFIED (for URLs)
    """
    html = category_template
    html = html.replace("TOPIC_ENTRY", topic_original)
    html = html.replace("CATEGORY_ENTRY", category_original)
    html = html.replace("TOPIC-SLUGIFIED", slugify(topic_original))
    html = html.replace("CATEGORY-SLUGIFIED", slugify(category_original))
    return html

def generate_topic_html(topic_original, categories, topic_template):
    """
    Generate the HTML for a topic page using the topic template.
    The template should contain:
      - TOPIC_ENTRY: original topic name.
      - TOPIC-SLUGIFIED: slugified topic name.
    """
    topic_slug = slugify(topic_original)
    html = topic_template
    html = html.replace("TOPIC_ENTRY", topic_original)
    html = html.replace("TOPIC-SLUGIFIED", topic_slug)
    return html

def collect_entries(db_data):
    """
    Process the raw dataset from content.json and return a list of entry dictionaries.
    Auto-fill missing file paths for media_piece_path and screenshot_path.
    """
    global_entries = []
    for entry in db_data:
        entry["name"] = normalize_value(entry.get("name", "unknown"))
        entry["topic"] = normalize_value(entry.get("topic", "unknown"))
        entry["category"] = normalize_value(entry.get("category", "unknown"))
     
        global_entries.append(entry)
    global_entries.sort(key=lambda e: e["name"].lower())
    return global_entries

def generate_pages(entries, media_template, category_template, topic_template, base_output):
    """
    Generate website pages:
      - Group entries by topic and then by category.
      - For each topic:
          * Create a topic folder.
          * Generate a topic page at /content/{topic_slug}.html using topic_template.
          * For each category in that topic:
              - Generate a category summary page at /content/{topic_slug}/{category_slug}.html using category_template.
              - Generate individual media-piece pages under /content/{topic_slug}/{category_slug}/ using media_template.
    Returns a dictionary mapping directories to sets of expected file names.
    """
    expected_files = {}
    topics = {}

    # Group entries by topic then by category.
    for entry in entries:
        topic = entry["topic"]
        category = entry["category"]
        topics.setdefault(topic, {}).setdefault(category, []).append(entry)

    # For each topic, generate pages.
    for topic_original, categories in topics.items():
        topic_slug = slugify(topic_original)
        topic_dir = os.path.join(base_output, topic_slug)
        os.makedirs(topic_dir, exist_ok=True)

        # Generate topic page at /content/{topic_slug}.html
        topic_page_path = os.path.join(base_output, f"{topic_slug}.html")
        # Get all unique category names for this topic.
        category_names = list(categories.keys())
        topic_html = generate_topic_html(topic_original, category_names, topic_template)
        write_file(topic_page_path, topic_html)
        expected_files.setdefault(base_output, set()).add(f"{topic_slug}.html")

        # For each category in this topic:
        for category_original, cat_entries in categories.items():
            category_slug = slugify(category_original)
            # Generate category summary page at /content/{topic_slug}/{category_slug}.html
            category_summary_path = os.path.join(topic_dir, f"{category_slug}.html")
            category_html = generate_category_html(topic_original, category_original, cat_entries, category_template)
            write_file(category_summary_path, category_html)
            expected_files.setdefault(topic_dir, set()).add(f"{category_slug}.html")

            # Generate individual media-piece pages in /content/{topic_slug}/{category_slug}/.
            cat_folder = os.path.join(topic_dir, category_slug)
            os.makedirs(cat_folder, exist_ok=True)
            for entry in cat_entries:
                file_name = slugify(entry["name"]) + ".html"
                output_file = os.path.join(cat_folder, file_name)
                media_html = generate_media_html(entry, media_template)
                write_file(output_file, media_html)
                expected_files.setdefault(cat_folder, set()).add(file_name)

    return expected_files

def cleanup_pages(expected_files):
    """
    For each directory in expected_files, delete any .html files that are not expected.
    """
    for directory, files_set in expected_files.items():
        cleanup_directory(directory, files_set)

def main():
    """
    Main function to generate website fragments.
    
    Steps:
      1. Set paths for the database and templates.
      2. Load the dataset from content.json.
      3. Load the media-piece, category, and topic templates.
      4. Collect entries from the dataset.
      5. Generate individual media-piece pages, category summary pages, and topic pages.
      6. Cleanup any orphaned pages.
    """
    script_dir = os.path.dirname(os.path.realpath(__file__))
    db_path = os.path.join(script_dir, "../datasets/content.json")
    media_template_path = os.path.join(script_dir, "../content/templates/slugified-media-piece.html")
    category_template_path = os.path.join(script_dir, "../content/templates/slugified-category.html")
    topic_template_path = os.path.join(script_dir, "../content/templates/slugified-topic.html")
    base_output = script_dir  # Pages will be generated under the script's directory (/content)
    
    db_data = load_database(db_path)
    if db_data is None:
        return

    media_template = load_template(media_template_path)
    if media_template is None:
        return

    category_template = load_template(category_template_path)
    if category_template is None:
        return

    topic_template = load_template(topic_template_path)
    if topic_template is None:
        return

    entries = collect_entries(db_data)
    print(f"\nTotal entries found: {len(entries)}\n")

    expected_files = generate_pages(entries, media_template, category_template, topic_template, base_output)
    cleanup_pages(expected_files)

    print("\nWebsite generation complete!\n")

if __name__ == "__main__":
    main()