import os
import json
import re
import hashlib
import sqlite3
import shutil # Use shutil for removing non-empty directories

# Utility Functions

def slugify(text):
    """
    Convert a string into a file-friendly slug.
    Handles potential None input.
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
    Convert empty strings or Python None to None for consistency.
    """
    return value if value not in ("", None) else None

def write_file_if_different(file_path, content_str):
    """
    Write content_str to file_path only if the file doesn't exist or if its content has changed.
    Creates directories if they don't exist.
    Returns True if the file was written, False otherwise.
    """
    # Ensure content_str is not None before encoding
    if content_str is None:
        print(f"Error: Attempted to write None to {file_path}. Skipping write.")
        return False

    new_hash = hashlib.sha256(content_str.encode('utf-8')).hexdigest()
    # Check if file exists
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                existing_content = f.read()
            existing_hash = hashlib.sha256(existing_content.encode('utf-8')).hexdigest()
            # Compare hashes
            if existing_hash == new_hash:
                # print(f"Skipping write for {file_path} (content hash unchanged)") # Keep this commented for cleaner logs
                return False # Content is the same, signal no write occurred
        except FileNotFoundError:
             pass # If file disappears between os.path.exists and open, proceed to write
        except Exception as e:
            print(f"Warning: Error reading existing file {file_path} for comparison: {e}. Proceeding to write.")

    # If file doesn't exist or content is different, write the new content
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content_str)
        print(f"Written file: {file_path}")
        return True # Signal that write occurred
    except Exception as e:
        print(f"Error writing file {file_path}: {e}")
        return False # Signal that write failed

def load_blacklist(file_path):
    """
    Load the blacklist (list of keys to exclude) from the specified JSON file.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            blacklist = json.load(f)
        print(f"\nLoaded blacklist from {file_path}: {blacklist}")
        return blacklist
    except FileNotFoundError:
        print(f"\nWarning: Blacklist file not found at {file_path}. No keys will be blacklisted.")
        return []
    except json.JSONDecodeError as e:
        print(f"\nError decoding JSON from blacklist file {file_path}: {e}")
        return []
    except Exception as e:
        print(f"\nError loading blacklist from {file_path}: {e}")
        return []

def filter_entry(entry, keys_to_remove):
    """
    Returns a copy of the entry dictionary with keys in keys_to_remove removed.
    """
    return {k: v for k, v in entry.items() if k not in keys_to_remove}


# Cleanup Functions

def cleanup_orphan_files(directory, expected_files):
    """
    Delete any .json file in the specified directory that is not in expected_files.
    """
    if not os.path.isdir(directory):
        # print(f"Cleanup Notice: Directory '{directory}' not found, skipping file cleanup.") # Less verbose
        return

    try:
        for filename in os.listdir(directory):
            # Only target .json files for this cleanup
            if filename.endswith(".json") and filename not in expected_files:
                file_path = os.path.join(directory, filename)
                try:
                    os.remove(file_path)
                    print(f"Deleted orphaned entry .json file: {file_path}")
                except Exception as e:
                    print(f"Error deleting file {file_path}: {e}")
    except FileNotFoundError:
         print(f"Cleanup Warning: Directory '{directory}' disappeared during cleanup scan.")
    except Exception as e:
        print(f"Error scanning directory {directory} for file cleanup: {e}")


def cleanup_orphan_folders(output_base_path, active_topic_slugs, active_categories_by_topic_slug):
    """
    Cleans up orphaned topic folders, category folders, and aggregated category JSON files
    based on active slugs from the database. Targets the dataset directory structure.

    Args:
        output_base_path (str): The base path where topic folders are located (e.g., './datasets/content').
        active_topic_slugs (set): A set of all topic slugs currently found in the database.
        active_categories_by_topic_slug (dict): A dictionary where keys are active topic slugs
                                                and values are sets of active category slugs
                                                for that topic.
    """
    print(f"\nStarting Orphan Folder & File Cleanup for base path: {output_base_path}")

    if not os.path.isdir(output_base_path):
        print(f"Error: Output base path '{output_base_path}' does not exist.")
        return

    # 1. Cleanup Orphan Topic Folders
    topic_items_to_check = []
    try:
        for item_name in os.listdir(output_base_path):
            item_path = os.path.join(output_base_path, item_name)
            # Check if it's a directory AND not a special file/folder
            # Also ignore top-level json files like topics.json, content.json
            known_non_topic_items = ['templates', 'topics.json', 'content.json']
            if os.path.isdir(item_path) and item_name not in known_non_topic_items:
                 topic_items_to_check.append((item_name, item_path))
            # Check for orphaned topic aggregate JSON files (e.g., videos.json)
            elif os.path.isfile(item_path) and item_name.endswith(".json"):
                 expected_topic_slug = item_name[:-5] # Remove .json
                 if expected_topic_slug not in active_topic_slugs and item_name not in known_non_topic_items:
                     print(f"Identified orphaned topic aggregate JSON file: {item_path}")
                     try:
                         os.remove(item_path)
                         print(f"Deleted orphaned topic aggregate JSON file: {item_path}")
                     except OSError as e:
                         print(f"Error deleting topic aggregate JSON file {item_path}: {e}")

    except Exception as e:
        print(f"Error scanning topic level items in {output_base_path}: {e}")
        return

    # Check collected directories against active topic slugs
    for topic_slug, item_path in topic_items_to_check:
        if topic_slug not in active_topic_slugs:
            print(f"Identified orphaned topic folder: {item_path}")
            try:
                shutil.rmtree(item_path)
                print(f"Deleted orphaned topic folder: {item_path}")
            except OSError as e:
                print(f"Error deleting topic folder {item_path}: {e}")

    # 2. Cleanup Orphan Category Folders & Aggregated Category JSONs (within active topic folders)
    for topic_slug in active_topic_slugs:
        topic_folder_path = os.path.join(output_base_path, topic_slug)
        if not os.path.isdir(topic_folder_path):
            continue # Skip if the active topic folder doesn't exist

        active_category_slugs_for_topic = active_categories_by_topic_slug.get(topic_slug, set())
        category_folders_to_check = []
        files_in_topic_folder = []
        try:
            for item_name in os.listdir(topic_folder_path):
                item_path = os.path.join(topic_folder_path, item_name)
                if os.path.isdir(item_path): # Check if it's a category sub-folder
                    category_folders_to_check.append((item_name, item_path))
                elif os.path.isfile(item_path) and item_name.endswith(".json"):
                    # Collect JSON files directly in the topic folder
                    files_in_topic_folder.append((item_name, item_path))

        except Exception as e:
            print(f"Error scanning items in {topic_folder_path}: {e}")
            continue # Skip this topic if we can't scan it

        # Check collected directories against active category slugs for this topic
        for category_slug, item_path in category_folders_to_check:
            if category_slug not in active_category_slugs_for_topic:
                print(f"Identified orphaned category folder: {item_path}")
                try:
                    shutil.rmtree(item_path)
                    print(f"Deleted orphaned category folder: {item_path}")
                except OSError as e:
                    print(f"Error deleting category folder {item_path}: {e}")

        # Check collected JSON files against active category slugs for this topic
        category_list_filename = f"{topic_slug}-categories.json"
        for filename, item_path in files_in_topic_folder:
            if filename == category_list_filename:
                continue # Skip the category list file itself

            # Assume other json files are aggregated category files (e.g., comedy.json)
            potential_category_slug = filename[:-5] # Remove .json
            if potential_category_slug not in active_category_slugs_for_topic:
                print(f"Identified orphaned aggregated category JSON file: {item_path}")
                try:
                    os.remove(item_path)
                    print(f"Deleted orphaned aggregated category JSON file: {item_path}")
                except OSError as e:
                    print(f"Error deleting aggregated category JSON file {item_path}: {e}")


    print(f"Orphan Folder & File Cleanup Finished for base path: {output_base_path}")


# Data Processing Functions

def process_table_from_sqlite(conn, table_name, output_base_datasets, blacklist_keys):
    """
    Process a table from the SQLite database:
      1. Gets column names and primary keys.
      2. Fetches rows, converts to dictionaries.
      3. Normalizes values, slugifies names/categories, auto-fills paths.
      4. **Slugifies the 'file_name' field if it exists.**
      5. Filters out blacklisted/primary keys.
      6. Groups filtered entries by original category name.
      7. Writes individual and aggregated JSON files to the datasets path.
      8. Cleans up orphaned JSON files in category directories.
    Returns a list of all processed (full, not filtered) entries
    and a set of active category slugs found in this table.
    """
    cur = conn.cursor()
    try:
        cur.execute(f"PRAGMA table_info({table_name});")
        columns_info = cur.fetchall()
    except sqlite3.Error as e:
        print(f"Error getting table info for {table_name}: {e}")
        return [], set()

    columns = [col[1] for col in columns_info]
    print(f"\nProcessing table '{table_name}' with columns: {columns}")
    primary_keys = [col[1] for col in columns_info if col[5] > 0]
    # print(f"Primary key columns for table '{table_name}': {primary_keys}") # Less verbose
    keys_to_remove = set(blacklist_keys) | set(primary_keys)

    try:
        cur.execute(f"SELECT * FROM {table_name};")
        rows = cur.fetchall()
    except sqlite3.Error as e:
        print(f"Error fetching rows from {table_name}: {e}")
        return [], set()

    all_entries_full = []
    all_entries_filtered = []
    data_by_category_filtered = {}
    active_category_slugs_in_table = set()

    for row in rows:
        entry = {col: normalize_value(row[idx]) for idx, col in enumerate(columns)}

        # Apply slugify to file_name if it exists
        if entry.get("file_name"): # Check if key exists and value is not None
            original_filename = entry["file_name"]
            entry["file_name"] = slugify(original_filename)
            # Optional: Print if filename changed
            # if original_filename != entry["file_name"]:
            #     print(f"Slugified filename: '{original_filename}' -> '{entry['file_name']}'")
        # End of file_name slugification

        entry_name_original = entry.get("name") or "unknown-name"
        entry_topic_original = entry.get("topic") or table_name
        entry_category_original = entry.get("category") or "unknown-category"

        # Store original values before potentially overwriting with slugs if needed elsewhere
        # entry["name_original"] = entry_name_original # Example if needed
        entry["name"] = entry_name_original # Keep original case for display? Or use slug? Depends on need.
        entry["topic"] = entry_topic_original
        entry["category"] = entry_category_original

        topic_slug = slugify(entry_topic_original)
        category_slug = slugify(entry_category_original) if entry_category_original and entry_category_original.lower() != "unknown" else "unknown-categories"
        name_slug = slugify(entry_name_original)

        active_category_slugs_in_table.add(category_slug)

        # Generate relative paths for JSON data structure consistency
        entry["media_piece_path"] = f"/content/{topic_slug}/{category_slug}/{name_slug}.html"
        if not entry.get("screenshot_path"):
             entry["screenshot_path"] = f"/media/content/{topic_slug}/{category_slug}/{name_slug}.jpg"

        all_entries_full.append(entry.copy())
        filtered_entry = filter_entry(entry, keys_to_remove)
        all_entries_filtered.append(filtered_entry)

        cat_key_grouping = entry_category_original if entry_category_original and entry_category_original.lower() != "unknown" else "unknown-category"
        data_by_category_filtered.setdefault(cat_key_grouping, []).append(filtered_entry)

    # Write aggregated JSON for the entire table/topic (filtered)
    all_entries_filtered.sort(key=lambda e: e.get("name", "").lower())
    table_output_file = os.path.join(output_base_datasets, f"{slugify(table_name)}.json")
    content_str = json.dumps(all_entries_filtered, indent=4)
    write_file_if_different(table_output_file, content_str)

    # Process each category for individual and aggregated JSON files
    processed_categories_slugs = set()
    topic_folder_base = os.path.join(output_base_datasets, slugify(table_name)) # Base folder for this topic

    for cat_original_key, entries_filtered in data_by_category_filtered.items():
        entries_filtered.sort(key=lambda e: e.get("name", "").lower())
        cat_slug = slugify(cat_original_key) if cat_original_key.lower() != "unknown-category" else "unknown-categories"
        processed_categories_slugs.add(cat_slug)

        # Folder for individual entry files within this category
        cat_entry_folder = os.path.join(topic_folder_base, cat_slug)
        os.makedirs(cat_entry_folder, exist_ok=True)

        expected_json_files = set() # Files expected within the category sub-folder
        for entry_filtered in entries_filtered:
            # Use the 'name' field from the filtered entry for the filename slug
            entry_name_for_file = entry_filtered.get("name", "unknown-name")
            file_name_slug = slugify(entry_name_for_file)
            filename = f"{file_name_slug}.json"
            expected_json_files.add(filename)

            entry_file = os.path.join(cat_entry_folder, filename)
            entry_str = json.dumps(entry_filtered, indent=4)
            write_file_if_different(entry_file, entry_str)

        # Write the aggregated category file (filtered) directly into the topic folder
        aggregated_cat_file = os.path.join(topic_folder_base, f"{cat_slug}.json")
        cat_content_str = json.dumps(entries_filtered, indent=4)
        write_file_if_different(aggregated_cat_file, cat_content_str)

        # Cleanup orphaned individual entry .json files within this category sub-folder
        cleanup_orphan_files(cat_entry_folder, expected_json_files)

    # Return the list of full entries (for global aggregation) and the active category slugs for this table
    return all_entries_full, active_category_slugs_in_table


def generate_category_lists(global_entries, output_base_datasets):
    """
    Group entries by topic slug and extract unique original category names for each topic.
    Write a JSON file named "{topic_slug}-categories.json" in the datasets path:
    "{output_base_datasets}/{topic_slug}/{topic_slug}-categories.json".
    """
    categories_by_topic_slug = {}
    for entry in global_entries:
        topic_original = entry.get("topic") or "unknown-topic"
        category_original = entry.get("category") or "unknown-category"
        topic_slug = slugify(topic_original)
        categories_by_topic_slug.setdefault(topic_slug, set()).add(category_original)

    for topic_slug, categories_set in categories_by_topic_slug.items():
        topic_folder = os.path.join(output_base_datasets, topic_slug)
        os.makedirs(topic_folder, exist_ok=True)

        output_file = os.path.join(topic_folder, f"{topic_slug}-categories.json")

        valid_categories = {cat for cat in categories_set if cat and cat != 'unknown-category'} # Exclude default/empty
        category_list_sorted = sorted(list(valid_categories))

        content_str = json.dumps(category_list_sorted, indent=4)
        write_file_if_different(output_file, content_str)
        # Only print if the file was actually written (Removed print for cleaner logs)
        # if wrote_file: print(f"Written category list for topic '{topic_slug}': {output_file}")

def generate_topics_list(global_entries, output_base_datasets):
    """
    Extract unique original topic names from global_entries, sort them,
    and write them to "{output_base_datasets}/topics.json".
    """
    # Use original topic names, filter out potential None/empty strings/defaults
    topics_set_original = {entry.get("topic") for entry in global_entries if entry.get("topic") and entry.get("topic") != 'unknown-topic'}
    topics_list_sorted = sorted(list(topics_set_original))

    output_file = os.path.join(output_base_datasets, "topics.json")
    content_str = json.dumps(topics_list_sorted, indent=4)
    write_file_if_different(output_file, content_str)
    # Only print if the file was actually written (Removed print for cleaner logs)
    # if wrote_file: print(f"Written topics list: {output_file}")

# Main Execution Logic

def main():
    """
    Main function:
      1. Connects to the SQLite database.
      2. Processes each table, generating JSON files and collecting active slugs.
      3. Aggregates all entries into a universal JSON file.
      4. Generates category lists and a topics list based on original names.
      5. Performs cleanup of orphaned dataset files and folders (only in datasets path).
    """
    script_dir = os.path.dirname(os.path.realpath(__file__))
    db_file = os.path.join(script_dir, "TOWAF-database.db")

    output_base_datasets = os.path.join(script_dir, "content")
    os.makedirs(output_base_datasets, exist_ok=True)

    blacklist_file = os.path.join(script_dir, "blacklist.json")
    blacklist_keys = load_blacklist(blacklist_file)

    conn = None
    try:
        conn = sqlite3.connect(db_file)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        tables = [row[0] for row in cur.fetchall()]
        print("\nTables found in database:", tables)
    except sqlite3.Error as e:
        print(f"Database error connecting or listing tables: {e}")
        return
    except Exception as e:
        print(f"An error occurred during setup: {e}")
        if conn:
            conn.close()
        return

    global_entries = []
    all_active_topic_slugs = set()
    all_active_categories_by_topic_slug = {} # Maps topic_slug -> set(category_slugs)

    for table_name in tables:
        topic_slug_for_table = slugify(table_name)
        all_active_topic_slugs.add(topic_slug_for_table)

        entries_full, active_cat_slugs = process_table_from_sqlite(conn, table_name, output_base_datasets, blacklist_keys)

        if entries_full:
            global_entries.extend(entries_full)
            all_active_categories_by_topic_slug.setdefault(topic_slug_for_table, set()).update(active_cat_slugs)
        else:
             # Ensure topic slug exists in dict even if table is empty
             all_active_categories_by_topic_slug.setdefault(topic_slug_for_table, set())

    # Aggregation and Global Lists
    if global_entries:
        global_entries.sort(key=lambda e: (e.get("topic", "").lower(), e.get("name", "").lower()))
        universal_file = os.path.join(script_dir, "content.json")
        universal_content = json.dumps(global_entries, indent=4)
        wrote_universal = write_file_if_different(universal_file, universal_content)
        if wrote_universal:
             print(f"\nCreated/Updated universal dataset file {universal_file} with {len(global_entries)} entries.")
        # else: # Less verbose log
        #      print(f"\nUniversal dataset file {universal_file} is up-to-date ({len(global_entries)} entries).")

        generate_category_lists(global_entries, output_base_datasets)
        generate_topics_list(global_entries, output_base_datasets)
    else:
        print("\nNo entries found in the database. Skipping global file generation and cleanup.")

    # Cleanup Phase
    # Only run cleanup if there were active topics identified
    if all_active_topic_slugs:
        # Cleanup dataset folders and aggregated category json files
        cleanup_orphan_folders(output_base_datasets, all_active_topic_slugs, all_active_categories_by_topic_slug)

    # Close the database connection
    if conn:
        conn.close()

    print("\nDataset fragments generation and cleanup complete!\n")


if __name__ == "__main__":
    main()
