import os # Provides functions for interacting with the operating system (e.g., file and directory operations)
import json # Allows for easy encoding and decoding of JSON data
import re # Offers regular expression support for advanced string searching and manipulation
import hashlib # Contains algorithms for secure hashing (e.g., SHA, MD5) for data integrity and verification
import shutil # Enables high-level file operations such as copying and removing files/directories 

# Utility Functions
def slugify(text):
    """
    Convert a string into a file-friendly slug.
    Handles potential None input. (Using robust version)
    """
    if text is None:
        return "unknown"
    text = str(text).lower().replace(" ", "-").replace("_", "-")
    # Allow alphanumeric, hyphen, and period. Remove others.
    text = re.sub(r'[^a-z0-9\-.]', '', text)
    # Avoid leading/trailing hyphens/periods
    text = text.strip(".-")
    # Handle empty string after sanitization
    return text if text else "unknown"

def normalize_value(value):
    """
    Ensure all values are strings; if missing, default to "unknown".
    """
    # Return string version if not None or empty, otherwise return "unknown"
    # Handles numbers, booleans etc. by converting to string first.
    return str(value).strip() if value is not None and str(value).strip() != "" else "unknown"

def write_file(file_path, content_str):
    """
    Write content_str to file_path only if the content hash differs.
    Ensures the directory exists before writing.
    Returns True if written, False otherwise (for potential conditional logging).
    """
    # Check if content_str is None before trying to encode
    if content_str is None:
        print(f"Error: Attempted to write None to {file_path}. Skipping write.")
        return False

    new_hash = hashlib.sha256(content_str.encode('utf-8')).hexdigest()
    wrote_file = False
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                existing_content = f.read()
            existing_hash = hashlib.sha256(existing_content.encode('utf-8')).hexdigest()
            if existing_hash == new_hash:
                # print(f"Skipping write for {file_path} (content hash unchanged)")
                return False # Signal no write needed
        except Exception as e:
            print(f"Warning: Error reading file {file_path} for comparison: {e}")

    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content_str)
        print(f"Written/Updated file: {file_path}")
        wrote_file = True
    except Exception as e:
        print(f"Error writing file {file_path}: {e}")
        wrote_file = False
    return wrote_file

# Cleanup Functions
def cleanup_html_content_files(expected_files_by_dir):
    """
    Iterate through the expected files dictionary and clean up orphaned HTML files.
    """
    print("Starting HTML File Cleanup")
    for directory, expected_filenames_set in expected_files_by_dir.items():
        cleanup_orphan_html_files(directory, expected_filenames_set)
    print("HTML File Cleanup Finished")

def cleanup_orphan_html_files(directory, expected_files):
    """
    Delete any .html file in the specified directory that is not in expected_files.
    (Original cleanup_directory function renamed for clarity).
    """
    if not os.path.isdir(directory):
        return

    try:
        for filename in os.listdir(directory):
            if filename.endswith(".html") and filename not in expected_files:
                file_path = os.path.join(directory, filename)
                try:
                    os.remove(file_path)
                    print(f"Deleted orphaned .html file: {file_path}")
                except Exception as e:
                    print(f"Error deleting file {file_path}: {e}")
    except FileNotFoundError:
        print(f"Cleanup Warning: Directory '{directory}' disappeared during HTML file cleanup scan.")
    except Exception as e:
        print(f"Error scanning directory {directory} for HTML file cleanup: {e}")

def cleanup_orphan_content_folders(output_base_path, active_topic_slugs, active_categories_by_topic_slug):
    """
    Cleans up orphaned topic and category folders in the HTML content directory
    based on active slugs derived from the dataset (content.json).

    Args:
        output_base_path (str): The base path where topic folders are located (e.g., './content').
        active_topic_slugs (set): A set of all topic slugs derived from content.json.
        active_categories_by_topic_slug (dict): A dictionary mapping active topic slugs to sets of active category slugs for that topic.
    """
    print(f"\nStarting Orphan Folder Cleanup")

    if not os.path.isdir(output_base_path):
        print(f"Error: Output base path '{output_base_path}' does not exist.")
        return

    # 1. Cleanup Orphan Topic Folders
    topic_items_to_check = []
    try:
        for item_name in os.listdir(output_base_path):
            item_path = os.path.join(output_base_path, item_name)
            known_files_or_dirs = ['templates', 'media', 'content.py']
            if os.path.isdir(item_path) and item_name not in known_files_or_dirs:
                 topic_items_to_check.append((item_name, item_path))
            elif os.path.isfile(item_path) and item_name.endswith(".html"):
                 if item_name not in ['index.html', 'content.html']:
                     expected_topic_slug = item_name[:-5]
                     if expected_topic_slug not in active_topic_slugs:
                         print(f"Identified orphaned topic HTML file: {item_path}")
                         try:
                             os.remove(item_path)
                             print(f"Deleted orphaned topic HTML file: {item_path}")
                         except OSError as e:
                             print(f"Error deleting topic HTML file {item_path}: {e}")
    except Exception as e:
        print(f"Error scanning topic folders/files in {output_base_path}: {e}")
        return

    for topic_slug, item_path in topic_items_to_check:
        if topic_slug not in active_topic_slugs:
            print(f"Identified orphaned topic folder: {item_path}")
            try:
                shutil.rmtree(item_path)
                print(f"Deleted orphaned topic folder: {item_path}")
            except OSError as e:
                print(f"Error deleting topic folder {item_path}: {e}")

    # 2. Cleanup Orphan Category Folders (within remaining active topic folders)
    for topic_slug in active_topic_slugs:
        topic_folder_path = os.path.join(output_base_path, topic_slug)
        if not os.path.isdir(topic_folder_path):
            continue

        active_category_slugs_for_topic = active_categories_by_topic_slug.get(topic_slug, set())
        category_items_to_check = []
        try:
            for item_name in os.listdir(topic_folder_path):
                item_path = os.path.join(topic_folder_path, item_name)
                if os.path.isdir(item_path):
                    category_items_to_check.append((item_name, item_path))
                elif os.path.isfile(item_path) and item_name.endswith(".html"):
                    expected_category_slug = item_name[:-5]
                    if expected_category_slug not in active_category_slugs_for_topic:
                         print(f"Identified orphaned category HTML file: {item_path}")
                         try:
                             os.remove(item_path)
                             print(f"Deleted orphaned category HTML file: {item_path}")
                         except OSError as e:
                             print(f"Error deleting category HTML file {item_path}: {e}")
        except Exception as e:
            print(f"Error scanning category folders/files in {topic_folder_path}: {e}")
            continue

        for category_slug, item_path in category_items_to_check:
            if category_slug not in active_category_slugs_for_topic:
                print(f"Identified orphaned category folder: {item_path}")
                try:
                    shutil.rmtree(item_path)
                    print(f"Deleted orphaned category folder: {item_path}")
                except OSError as e:
                    print(f"Error deleting category folder {item_path}: {e}")

    print(f"Orphan Folder Cleanup Finished")

# Data Processing Functions
def load_database(db_path):
    """
    Load the JSON dataset from the given path (content.json).
    """
    if not os.path.exists(db_path):
        print(f"Error: Database file {db_path} not found.")
        return None
    try:
        with open(db_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from {db_path}: {e}")
        return None
    except Exception as e:
        print(f"Error loading database file {db_path}: {e}")
        return None

def load_template(template_path):
    """
    Load the HTML template file from the given path.
    """
    if not os.path.exists(template_path):
        print(f"Error: Template file {template_path} not found.")
        return None
    try:
        with open(template_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"Error loading template file {template_path}: {e}")
        return None


# Generation Functions
def generate_media_html(entry, template):
    """
    Replace placeholders in the media-piece template with entry data.
    Uses placeholder format like NAME_ENTRY (no braces).
    Ensures replacement values are strings.
    """
    # Ensure defaults are strings
    name_display = entry.get("name", "Unknown Name") or "Unknown Name"
    topic_display = entry.get("topic", "Unknown Topic") or "Unknown Topic"
    category_display = entry.get("category", "Unknown Category") or "Unknown Category"

    # Use slugs for URLs/paths (slugify handles None)
    topic_slug_val = slugify(entry.get("topic"))
    category_slug_val = slugify(entry.get("category"))
    name_slug_val = slugify(entry.get("name"))

    # Perform replacements, ensuring all replacement values are strings
    content = template # Start with the original template string
    try:
        content = content.replace("NAME_ENTRY", str(name_display))
        content = content.replace("TOPIC_ENTRY", str(topic_display))
        content = content.replace("CATEGORY_ENTRY", str(category_display))
        
        content = content.replace("TOPIC-SLUGIFIED", str(topic_slug_val))
        content = content.replace("CATEGORY-SLUGIFIED", str(category_slug_val))
        content = content.replace("NAME-SLUGIFIED", str(name_slug_val))
    except Exception as e:
        print(f"Error during placeholder replacement for entry '{name_display}': {e}")
        # Decide how to handle: return None, return partially replaced content, or raise error?
        # Returning None might cause issues downstream, maybe return template or partial content?
        return template # Return original template on error to avoid None propagation

    return content

def generate_category_html(topic_original, category_original, entries, category_template):
    """
    Generate the HTML for a category summary page.
    Uses placeholder format like TOPIC_ENTRY (no braces).
    """
    # Ensure display values are strings
    topic_display = str(topic_original) if topic_original else "Unknown Topic"
    category_display = str(category_original) if category_original else "Unknown Category"
    # slugify handles None
    topic_slug_val = slugify(topic_original)
    category_slug_val = slugify(category_original)

    html = category_template
    try:
        html = html.replace("TOPIC_ENTRY", topic_display)
        html = html.replace("CATEGORY_ENTRY", category_display)
        html = html.replace("TOPIC-SLUGIFIED", topic_slug_val)
        html = html.replace("CATEGORY-SLUGIFIED", category_slug_val)
        # Add logic here to insert links to individual media pieces if template requires
    except Exception as e:
        print(f"Error during placeholder replacement for category '{category_display}' in topic '{topic_display}': {e}")
        return category_template # Return original template on error

    return html

def generate_topic_html(topic_original, categories, topic_template):
    """
    Generate the HTML for a topic page using the topic template.
    Uses placeholder format like TOPIC_ENTRY (no braces).
    """
    # Ensure display value is string
    topic_display = str(topic_original) if topic_original else "Unknown Topic"
    # slugify handles None
    topic_slug_val = slugify(topic_original)

    html = topic_template
    try:
        html = html.replace("TOPIC_ENTRY", topic_display)
        html = html.replace("TOPIC-SLUGIFIED", topic_slug_val)
        # Add logic here to insert links to category pages if template requires
    except Exception as e:
        print(f"Error during placeholder replacement for topic '{topic_display}': {e}")
        return topic_template # Return original template on error

    return html

def collect_entries(db_data):
    """
    Process the raw dataset from content.json and return a list of entry dictionaries.
    Uses normalize_value for consistency.
    """
    global_entries = []
    if not isinstance(db_data, list):
        print("Error: Expected a list of entries from content.json")
        return []

    for entry in db_data:
        if not isinstance(entry, dict):
            print(f"Warning: Skipping non-dictionary item in content.json: {entry}")
            continue
        # Normalize essential fields used for path generation and grouping
        processed_entry = {
            "name": normalize_value(entry.get("name")),
            "topic": normalize_value(entry.get("topic")),
            "category": normalize_value(entry.get("category")),
            # Include other fields as needed, potentially normalizing them too
            **entry # Include all original fields
        }
        # Ensure essential fields have a default if normalization resulted in None/"unknown"
        if processed_entry["name"] == "unknown": processed_entry["name"] = "unknown-name"
        if processed_entry["topic"] == "unknown": processed_entry["topic"] = "unknown-topic"
        if processed_entry["category"] == "unknown": processed_entry["category"] = "unknown-category"

        global_entries.append(processed_entry)

    global_entries.sort(key=lambda e: e.get("name", "unknown-name").lower())
    return global_entries

def generate_pages(entries, media_template, category_template, topic_template, base_output):
    """
    Generate website pages based on entries data and templates.
    Returns a dictionary mapping directories to sets of expected HTML file names.
    """
    expected_files = {} # Maps directory path -> set of expected .html filenames within it
    topics_data = {}    # Maps original topic name -> {original category name -> [entries]}

    for entry in entries:
        topic_original = entry.get("topic")
        category_original = entry.get("category")
        topics_data.setdefault(topic_original, {}).setdefault(category_original, []).append(entry)

    for topic_original, categories_data in topics_data.items():
        topic_slug = slugify(topic_original)
        topic_dir = os.path.join(base_output, topic_slug)
        os.makedirs(topic_dir, exist_ok=True)

        topic_page_filename = f"{topic_slug}.html"
        topic_page_path = os.path.join(base_output, topic_page_filename)
        category_names = list(categories_data.keys())
        topic_html = generate_topic_html(topic_original, category_names, topic_template)
        write_file(topic_page_path, topic_html)
        expected_files.setdefault(base_output, set()).add(topic_page_filename)

        for category_original, cat_entries in categories_data.items():
            category_slug = slugify(category_original)
            category_dir = os.path.join(topic_dir, category_slug)
            os.makedirs(category_dir, exist_ok=True)

            category_summary_filename = f"{category_slug}.html"
            category_summary_path = os.path.join(topic_dir, category_summary_filename)
            category_html = generate_category_html(topic_original, category_original, cat_entries, category_template)
            write_file(category_summary_path, category_html)
            expected_files.setdefault(topic_dir, set()).add(category_summary_filename)

            for entry in cat_entries:
                name_slug = slugify(entry.get("name", "unknown-name"))
                media_filename = f"{name_slug}.html"
                media_filepath = os.path.join(category_dir, media_filename)
                media_html = generate_media_html(entry, media_template)
                write_file(media_filepath, media_html)
                expected_files.setdefault(category_dir, set()).add(media_filename)

    return expected_files




def main():
    """
    Main function to generate website HTML fragments from content.json.
    """
    script_dir = os.path.dirname(os.path.realpath(__file__))
    db_path = os.path.normpath(os.path.join(script_dir, "../datasets/content.json"))
    media_template_path = os.path.join(script_dir, "templates/slugified-media-piece.html")
    category_template_path = os.path.join(script_dir, "templates/slugified-category.html")
    topic_template_path = os.path.join(script_dir, "templates/slugified-topic.html")
    base_output = script_dir

    db_data = load_database(db_path)
    if db_data is None: return

    media_template = load_template(media_template_path)
    if media_template is None: return
    category_template = load_template(category_template_path)
    if category_template is None: return
    topic_template = load_template(topic_template_path)
    if topic_template is None: return

    entries = collect_entries(db_data)
    print(f"\nTotal entries processed from content.json: {len(entries)}\n")
    if not entries:
        print("No entries to process. Exiting.")
        return

    expected_files_by_dir = generate_pages(entries, media_template, category_template, topic_template, base_output)

    cleanup_html_content_files(expected_files_by_dir)

    active_topic_slugs = set()
    active_categories_by_topic_slug = {}
    for entry in entries:
        topic_slug = slugify(entry.get("topic", "unknown-topic"))
        category_slug = slugify(entry.get("category", "unknown-category"))
        active_topic_slugs.add(topic_slug)
        active_categories_by_topic_slug.setdefault(topic_slug, set()).add(category_slug)

    cleanup_orphan_content_folders(base_output, active_topic_slugs, active_categories_by_topic_slug)

    print("\nWebsite HTML generation complete!\n")

if __name__ == "__main__":
    main()
