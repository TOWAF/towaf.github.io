import os
import json
import re
import hashlib
import sqlite3

def load_blacklist(file_path):
    """
    Load the blacklist (list of keys to exclude) from the specified JSON file.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            blacklist = json.load(f)
        print(f"\nLoaded blacklist from {file_path}: {blacklist}")
        return blacklist
    except Exception as e:
        print(f"\nError loading blacklist from {file_path}: {e}")
        return []

def slugify(text):
    """
    Convert a string into a file-friendly slug.
    """
    text = text.lower().replace(" ", "-").replace("_", "-")
    return re.sub(r'[^a-z0-9\-.]', '', text).strip(".")

def normalize_value(value):
    """
    Convert empty strings to None for consistency.
    """
    return value if value not in ("", None) else None

def write_file_if_different(file_path, content_str):
    """
    Write content_str to file_path only if the file doesn't exist or if its content has changed.
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
        print(f"Written file {file_path}")
    except Exception as e:
        print(f"Error writing file {file_path}: {e}")

def cleanup_directory(directory, expected_files):
    """
    Delete any .json file in the specified directory that is not in expected_files.
    """
    for filename in os.listdir(directory):
        if filename.endswith(".json") and filename not in expected_files:
            file_path = os.path.join(directory, filename)
            try:
                os.remove(file_path)
                print(f"Deleted orphaned .json file {file_path}")
            except Exception as e:
                print(f"Error deleting file {file_path}: {e}")

def filter_entry(entry, keys_to_remove):
    """
    Returns a copy of the entry dictionary with keys in keys_to_remove removed.
    """
    return {k: v for k, v in entry.items() if k not in keys_to_remove}

def process_table_from_sqlite(conn, table_name, output_base, blacklist_keys):
    """
    Process a table from the SQLite database:
      1. Use PRAGMA table_info to get column names and determine primary key columns.
      2. Fetch all rows and convert them to dictionaries.
      3. Normalize values and auto-fill media_piece_path and screenshot_path.
      4. Remove keys found in the external blacklist plus any primary key columns from all outputs.
      5. Group entries by category, sorting entries alphabetically by 'name'.
      6. Write aggregated JSON files for the table and for each category.
    Returns the list of filtered entries.
    """
    cur = conn.cursor()

    # Retrieve column information.
    cur.execute(f"PRAGMA table_info({table_name});")
    columns_info = cur.fetchall()
    columns = [col[1] for col in columns_info]  # Second element is the column name.
    print(f"\nProcessing table '{table_name}' with columns: {columns}")

    # Determine primary key columns (the 6th column in PRAGMA result > 0 indicates PK).
    primary_keys = [col[1] for col in columns_info if col[5] > 0]
    print(f"Primary key columns for table '{table_name}': {primary_keys}")

    # Combine blacklist and detected primary key names.
    keys_to_remove = set(blacklist_keys) | set(primary_keys)

    # Fetch all rows.
    cur.execute(f"SELECT * FROM {table_name};")
    rows = cur.fetchall()

    all_entries_filtered = []      # For aggregated table output.
    data_by_category_filtered = {} # For aggregated category outputs.

    for row in rows:
        # Build the full entry dictionary.
        entry = {col: normalize_value(val) for col, val in zip(columns, row)}
        # Normalize key fields.
        entry["name"] = normalize_value(entry.get("name", "unknown"))
        entry["topic"] = normalize_value(entry.get("topic", "unknown"))
        entry["category"] = normalize_value(entry.get("category", "unknown"))
        if entry.get("file_name"):
            entry["file_name"] = slugify(entry["file_name"])

        topic_slug = slugify(entry["topic"])
        category = entry["category"]
        # If category is missing or "unknown", force it into unknown-categories.
        category_slug = slugify(category) if category and category.lower() != "unknown" else "unknown-categories"
        name_slug = slugify(entry["name"])
        # Auto-fill file paths.
        entry["media_piece_path"] = f"/content/{topic_slug}/{category_slug}/{name_slug}.html"
        if not entry.get("screenshot_path"):
            entry["screenshot_path"] = f"/media/content/{topic_slug}/{category_slug}/{name_slug}.jpg"

        # Create the filtered entry (without keys to remove).
        filtered_entry = filter_entry(entry, keys_to_remove)

        # Save the filtered version.
        all_entries_filtered.append(filtered_entry)

        # Group filtered entries by category.
        cat_key = category if category and category.lower() != "unknown" else "unknown"
        data_by_category_filtered.setdefault(cat_key, []).append(filtered_entry)

    # Sort the filtered entries alphabetically by 'name'.
    all_entries_filtered.sort(key=lambda e: e.get("name", "").lower())

    # Write the aggregated table file (filtered).
    table_output_file = os.path.join(output_base, f"{table_name}.json")
    content_str = json.dumps(all_entries_filtered, indent=4)
    write_file_if_different(table_output_file, content_str)

    # Process each category.
    for cat, entries in data_by_category_filtered.items():
        entries.sort(key=lambda e: e.get("name", "").lower())
        # Use slugified category name (or "unknown-categories").
        cat_slug = slugify(cat) if cat.lower() != "unknown" else "unknown-categories"
        cat_folder = os.path.join(output_base, table_name, cat_slug)
        os.makedirs(cat_folder, exist_ok=True)
        expected_files = set()
        for entry in entries:
            file_name_slug = slugify(entry["name"])
            filename = f"{file_name_slug}.json"
            expected_files.add(filename)
            entry_file = os.path.join(cat_folder, filename)
            entry_str = json.dumps(entry, indent=4)
            write_file_if_different(entry_file, entry_str)
        # Write the aggregated category file (filtered).
        aggregated_cat_file = os.path.join(output_base, table_name, f"{cat_slug}.json")
        cat_content_str = json.dumps(entries, indent=4)
        write_file_if_different(aggregated_cat_file, cat_content_str)
        cleanup_directory(cat_folder, expected_files)

    return all_entries_filtered



def generate_category_lists(global_entries, output_base):
    """
    Group entries by topic and extract unique original category names for each topic.
    Write a JSON file named "{topic_slug}-categories.json" in "/datasets/content/{topic_slug}/".
    """
    topics = {}
    for entry in global_entries:
        topic = entry["topic"]
        topics.setdefault(topic, set()).add(entry["category"])
    
    for topic_original, categories in topics.items():
        topic_slug = slugify(topic_original)
        topic_folder = os.path.join(output_base, topic_slug)
        os.makedirs(topic_folder, exist_ok=True)
        output_file = os.path.join(topic_folder, f"{topic_slug}-categories.json")
        category_list = sorted(list(categories))
        content_str = json.dumps(category_list, indent=4)
        write_file_if_different(output_file, content_str)

def generate_topics_list(global_entries, output_base):
    """
    Extract unique topics from global_entries and write them to a JSON file.
    The output file is located at "{output_base}/topics.json" and is expected
    to contain a sorted list of topics (in title case).
    """
    topics_set = {entry["topic"].title() for entry in global_entries if "topic" in entry}
    topics_list = sorted(list(topics_set))
    output_file = os.path.join(output_base, "topics.json")
    content_str = json.dumps(topics_list, indent=4)
    write_file_if_different(output_file, content_str)

def main():
    """
    Main function:
      1. Connects to the SQLite database.
      2. Processes each table by introspecting its schema and extracting rows.
      3. Aggregates all entries into a universal JSON file.
      4. Generates category lists and a topics list.
    """
    script_dir = os.path.dirname(os.path.realpath(__file__))
    # Database file is TOWAF-database.db.
    db_file = os.path.join(script_dir, "TOWAF-database.db")
    # Output folder for dataset fragments.
    output_base = os.path.join(script_dir, "content")
    os.makedirs(output_base, exist_ok=True)
    
    # Load the blacklist from blacklist.json.
    blacklist_file = os.path.join(script_dir, "blacklist.json")
    blacklist_keys = load_blacklist(blacklist_file)

    conn = sqlite3.connect(f"file:{db_file}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row

    cur = conn.cursor()
    # Retrieve list of user tables; skip internal tables like sqlite_sequence.
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
    tables = [row[0] for row in cur.fetchall()]
    print("\nTables found in database:", tables)

    global_entries = []
    for table in tables:
        entries = process_table_from_sqlite(conn, table, output_base, blacklist_keys)
        if entries:
            global_entries.extend(entries)

    # Sort all global entries alphabetically by 'name'.
    global_entries.sort(key=lambda e: e.get("name", "").lower())
    # Write the universal aggregated file with all entries to content.json in the script's folder.
    universal_file = os.path.join(script_dir, "content.json")
    universal_content = json.dumps(global_entries, indent=4)
    write_file_if_different(universal_file, universal_content)
    print(f"\nCreated universal dataset file {universal_file} with {len(global_entries)} entries.\n")

    # Generate category lists and topics list (topics.json in the output_base folder).
    generate_category_lists(global_entries, output_base)
    generate_topics_list(global_entries, output_base)
    
    conn.close()
    print("\nDataset fragments generation complete!\n")

if __name__ == "__main__":
    main()
