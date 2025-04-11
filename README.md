# The Open Web Archive Framework (TOWAF)

![loading](https://github.com/user-attachments/assets/9496a23e-74ed-4191-8438-194128ee3faf)

Demo version of The Open Web Archive Framework.

Simple Folder-Based Web Framework for Diverse Digital Content!

TLDR: Archive.org but anyone can host the website as a static site.

## Overview

The Open Web Archive Framework (TOWAF) is a customizable archive tool designed for the easy deployment and navigation of digitally archived content. It addresses the challenges of managing and publishing independent digital archives by facilitating the creation and maintenance of simple archives that present links and metadata information.

The framework aims to provide a standardized yet customizable solution for communities to independently create archive websites focused on presenting links and metadata, ensuring valuable information about creative works can be preserved and presented clearly.

## Features

* **Database-Driven:** Uses an SQLite database to manage metadata.
* **Static Site Generation:** Python scripts process the database to generate fragmented JSON datasets and static HTML pages.
* **Client-Side Loading:** JavaScript loads necessary data fragments on the client-side, optimizing bandwidth usage.
* **File-Manager Inspired UI:** Features a graphical user interface for topic/category navigation.
* **Basic Search:** Allows filtering by name within topic and category pages.
* **Customizable:** Offers options for initial customization like project codename and theme color via `quick-setup.py`.
* **Portable:** Suitable for deployment on static hosting platforms (like GitHub Pages) without needing complex backend infrastructure.

## Technology Stack

* **Database:** SQLite (managed via SQLiteStudio)
* **Backend/Processing:** Python 3
    * Libraries: `sqlite3`, `json`, `os`, `re`, `hashlib`, `shutil`, `subprocess`, `sys`
* **Frontend:**
    * HTML5, CSS3
    * JavaScript (for data loading and dynamic display)
    * Bootstrap 5 (for responsive UI)
    * Font Awesome 5 (for icons)
* **Data Format:** JSON (fragmented datasets)

## Workflow / Basic Instructions

The typical workflow for managing a TOWAF archive involves:

1.  **Database Management:** Add, remove, or modify tables and entries (metadata) within the `TOWAF-database.db` file using a tool like SQLiteStudio. Define tables for different content topics (e.g., software, videos).
2.  **Update Script:** Run the `update.py` script. This script executes the following:
    * `datasets.py`: Reads the SQLite database and generates fragmented JSON datasets (`*.json`) for each topic, category, and media piece within the `/datasets` directory. It also handles slugification for URLs.
    * `content.py`: Reads the generated global JSON dataset (`content.json`) and HTML templates (`/content/templates/`) to generate the complete static HTML website structure within the `/content` directory, replacing placeholders with data.
3.  **Deployment:** Deploy the generated static files (primarily the `content`, `datasets`, `media`, and `scripts` folders, along with `index.html` and `style.css`) to a static web host service like cloudflare pages (not github).

**(Optional) Initial Setup:**

* Run `quick-setup.py` to customize the project's codename and main theme color.

## Directory Structure Overview

The project follows a parallel structure for organisation:

* `/content/`: Contains the generated static HTML pages.
* `/datasets/`: Stores the fragmented JSON data files.
* `/media/`: Holds associated media files like images/thumbnails.
* `/scripts/`: Contains the client-side JavaScript files for data loading and search functionality.
* `TOWAF-database.db`: The core SQLite database file.
* `*.py`: Python scripts for processing and generation (`update.py`, `datasets.py`, `content.py`, `quick-setup.py`).
* `index.html`: The main entry point/homepage.
* `style.css`: Main stylesheet.

## Contributing

* Only Visual designs can be submitted

## Alternative link
* https://towaf.github.io/

![favicon-4K](https://github.com/user-attachments/assets/08a04732-9016-4e27-976a-e8113fc2bd21)
