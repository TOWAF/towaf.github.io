import os # Provides functions for interacting with the operating system (e.g., file and directory operations)
import shutil # Enables high-level file operations such as copying and removing files/directories 
import json # Allows for easy encoding and decoding of JSON data

def replace_in_file(file_path, old_name, new_name):
    """Replaces occurrences of old_name with new_name in a file, handling case."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            file_content = file.read()
    except UnicodeDecodeError:
        print(f"Skipping binary file: {file_path}")
        return  # Skip the rest of the function for binary files
    except FileNotFoundError:
        print(f"Error: File not found: {file_path}")
        return

    # Replace occurrences with different cases
    file_content = file_content.replace(old_name.upper(), new_name.upper())
    file_content = file_content.replace(old_name.lower(), new_name.lower())
    file_content = file_content.replace(old_name.capitalize(), new_name.capitalize())
    file_content = file_content.replace(old_name, new_name)

    try:
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(file_content)
    except IOError:
        print(f"Error: Could not write to file: {file_path}")

def rename_file_or_dir(old_path, new_path):
    """Renames a file or directory."""
    try:
        shutil.move(old_path, new_path)
    except FileNotFoundError:
        print(f"Error: File or directory not found: {old_path}")
    except OSError as e:
        print(f"Error renaming {old_path} to {new_path}: {e}")

def process_directory(root_dir, old_name, new_name):
    """Recursively processes the directory, renaming and replacing content."""
    for item in os.listdir(root_dir):
        item_path = os.path.join(root_dir, item)
        new_item_name = item.replace(old_name.lower(), new_name.lower()).replace(old_name.upper(), new_name.upper()).replace(old_name.capitalize(), new_name.capitalize()).replace(old_name, new_name)
        new_item_path = os.path.join(root_dir, new_item_name)

        if item != new_item_name:
            rename_file_or_dir(item_path, new_item_path)
            item_path = new_item_path  # Update path after renaming

        if os.path.isfile(item_path) and not item_path.endswith(".db"):  # Check file extension
            replace_in_file(item_path, old_name, new_name)
        elif os.path.isdir(item_path):
            process_directory(item_path, old_name, new_name)

def main():
    # Determine the script's directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = script_dir

    css_file = os.path.join(root_dir, "style.css")  # Directly define the CSS file path
    config_file = os.path.join(root_dir, "quick-setup-data.json")  # Path to the JSON config file

    # Load the configuration from the JSON file
    try:
        with open(config_file, 'r') as f:
            config_data = json.load(f)
            old_codename = config_data.get("CodeName")
            old_main_color = config_data.get("ColorVariables", {}).get("--main-color") #safely get old color
    except FileNotFoundError:
        print(f"Error: {config_file} not found.")
        return
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in {config_file}")
        return

    # Offer to change the main color FIRST
    user_input = input(f"Do you want to change the main color in style.css (currently '{old_main_color}')? (Y/n): ")
    if user_input.lower() == "y":
        print("\nHere's a color picker to help you choose:")
        print("->  https://www.w3schools.com/colors/colors_picker.asp")
        print("\nPlease provide the new main color in either HEX or RGB format.")
        print("For good contrast on a light background, consider darker shades.")
        print("For example: '#408040' or 'rgb(64, 128, 64)'")
        new_color = input("Enter the new main color: ").strip()

        # Update the JSON config
        config_data["ColorVariables"]["--main-color"] = new_color
        try:
            with open(config_file, 'w') as f:
                json.dump(config_data, f, indent=2)  # Save with indentation for readability
            print(f"Successfully updated --main-color in {config_file}")

            #Since we're no longer using change_main_color, we need to update the CSS file too
            replace_in_file(css_file, old_main_color, new_color)
            print(f"Successfully updated --main-color in {css_file}")

        except IOError:
            print(f"Error: Could not write to {config_file}")

    else:
        print("Main color change skipped.")

    # Ask the user if they want to change the codename
    user_input = input(f"Do you want to change the current codename '{old_codename}'? (Y/n): ")
    if user_input.lower() == "y":
        # Prompt the user for the new codename
        new_name = input("Enter the new codename: ").strip()
        if not new_name:
            print("Error: New codename cannot be empty.")
            return

        # Process the directory (if needed - depends on your project structure)
        process_directory(root_dir, old_codename, new_name)

        # Update the JSON config
        config_data["CodeName"] = new_name
        try:
            with open(config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
            print(f"Successfully updated CodeName in {config_file}")
        except IOError:
            print(f"Error: Could not write to {config_file}")
    else:
        print("Codename change skipped.")

    print("Script execution complete.")

if __name__ == "__main__":
    main()