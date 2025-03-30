/**
 * getTopicJsonFilePath()
 * -----------------
 * Determines the JSON file path for the current topic.
 * Example: If the URL is /content/software.html, fetch from /datasets/content/software.json.
 */
function getTopicJsonFilePath() {
  let pathParts = window.location.pathname.split('/').filter(Boolean);
  if (pathParts.length < 2) {
    console.error('Invalid URL structure for topic page.');
    return null;
  }
  let fileName = pathParts[pathParts.length - 1];
  let topic = fileName.replace('.html', '').toLowerCase();
  return `/datasets/content/${topic}.json`;
}

/**
 * getCategoriesJsonFilePath()
 * -----------------
 * Determines the JSON file path for the current topic's category list.
 * Example: If the URL is /content/software.html, the JSON file is expected at /datasets/content/software/software-categories.json.
 */
function getCategoriesJsonFilePath() {
  let pathParts = window.location.pathname.split('/').filter(Boolean);
  if (pathParts.length < 2) {
    console.error('Invalid URL structure for topic page.');
    return null;
  }
  let fileName = pathParts[pathParts.length - 1];
  let topic = fileName.replace('.html', '').toLowerCase();
  return `/datasets/content/${topic}/${topic}-categories.json`;
}

/**
 * setupSearch()
 * -------------
 * Attaches events to the search input (id "topicSearch"), the search icon,
 * and the clear icon. The search is lazy-loaded on the first keystroke.
 * Additionally, when the input is empty and the user either clicks the search
 * icon or presses Enter, it displays all entries. The clear icon clears the input
 * and removes all displayed cards.
 */
  function setupSearch(jsonUrl) {
    const searchInput = document.getElementById("topicSearch");
    const container = document.querySelector(".topic-search");
    const searchIcon = document.getElementById("search-icon");
    const clearIcon = document.getElementById("clear-icon");

    if (!searchInput || !container) return;

    // New focus handler
    searchInput.addEventListener("focus", () => {
      if (!dataLoaded) {
        performSearch(true); // Load data on first interaction
      }
    });

    let dataLoaded = false;
    let allData = [];

  // Function that performs the search.
  // If force is true, a search is triggered even if the input is empty (showing all results).
  function performSearch(force = false) {
    let searchTerm = searchInput.value.toLowerCase();

    // If the input is empty and not forced, clear the container and return.
    if (searchTerm === "" && !force) {
      container.innerHTML = "";
      return;
    }

    // Lazy-load the JSON data upon first search.
    if (!dataLoaded) {
      fetch(jsonUrl)
        .then(response => {
          if (!response.ok) {
            throw new Error(`Unable to fetch data: ${response.statusText}`);
          }
          return response.json();
        })
        .then(data => {
          if (!Array.isArray(data)) {
            throw new Error("Invalid data format: Expected an array of entries.");
          }
          allData = data;
          dataLoaded = true;
          filterAndDisplayCards(searchTerm, allData, container);
        })
        .catch(error => {
          console.error("Error loading topic data:", error);
          container.innerHTML = `<div class="alert alert-danger" role="alert">${error.message}</div>`;
        });
    } else {
      filterAndDisplayCards(searchTerm, allData, container);
    }
  }

  // When the user types in the search bar...
  searchInput.addEventListener("input", function () {
    let searchTerm = searchInput.value.toLowerCase();
    if (searchTerm === "") {
      // When the input is cleared by typing, remove all cards.
      container.innerHTML = "";
    } else {
      performSearch(); // Show filtered results.
    }
  });

  // When the user presses Enter in the search bar, force a search (even if empty) to show all results.
  searchInput.addEventListener("keydown", function (e) {
    if (e.key === "Enter") {
      e.preventDefault(); 
      performSearch(true);
    }
  });

  // Clicking the search icon will force a search.
  if (searchIcon) {
    searchIcon.addEventListener("click", function () {
      performSearch(true);
    });
  }

  // The clear icon clears the input field and removes the displayed results.
  if (clearIcon) {
    clearIcon.addEventListener("click", function () {
      searchInput.value = "";
      container.innerHTML = "";
    });
  }
}

/**
 * filterAndDisplayCards()
 * ------------------------
 * Filters the loaded data based on the search term and appends matching cards into the container.
 */
function filterAndDisplayCards(searchTerm, allData, container) {
  // The filter returns all entries when searchTerm is an empty string.
  const filteredData = allData.filter(entry => entry.name.toLowerCase().includes(searchTerm));
  container.innerHTML = ""; // Clear container before adding new cards.
  filteredData.forEach(entry => container.appendChild(createTopicCard(entry)));
}

/**
 * loadTopicData()
 * ----------------
 * Initializes the search functionality by fetching the topic JSON file URL.
 */
function loadTopicData() {
  const jsonUrl = getTopicJsonFilePath();
  if (!jsonUrl) return;
  setupSearch(jsonUrl);
}

/**
 * createTopicCard(entry)
 * ----------------------
 * Creates a Bootstrap card for a topic entry.
 */
function createTopicCard(entry) {
  const card = document.createElement('div');
  card.className = 'card mt-3 mb-3';

  const cardBody = document.createElement('div');
  cardBody.className = 'card-body';
  cardBody.style.padding = '8px';

  // --- Name Link ---
  const topRow = document.createElement('div');
  topRow.className = 'row';

  const nameCol = document.createElement('div');
  nameCol.className = 'col-12 text-start';
  const nameLink = document.createElement('a');
  nameCol.style.padding = '6px 18px 3px 18px';
  nameLink.href = entry.media_piece_path;
  nameLink.className = 'card-title no-underline content-paragraph';

  const strongEl = document.createElement('strong');
  strongEl.textContent = entry.name;
  nameLink.appendChild(strongEl);
  nameCol.appendChild(nameLink);
  topRow.appendChild(nameCol);
  cardBody.appendChild(topRow);

  // --- Category and Year ---
  const bottomRow = document.createElement('div');
  bottomRow.className = 'row mt-0';

  const categoryCol = document.createElement('div');
  categoryCol.className = 'col-9 text-start content-paragraph';
  categoryCol.style.padding = '0 0 3px 18px';
  categoryCol.textContent = entry.category;
  bottomRow.appendChild(categoryCol);

  const yearCol = document.createElement('div');
  yearCol.className = 'col-3 text-end content-paragraph';
  yearCol.style.padding = '0 18px 3px 0';
  yearCol.textContent = entry.year;
  bottomRow.appendChild(yearCol);

  cardBody.appendChild(bottomRow);
  card.appendChild(cardBody);
  return card;
}

/**
 * slugify()
 * ----------
 * Converts a string into a URL-friendly slug.
 */
function slugify(text) {
  return text
    .toString()
    .toLowerCase()
    .trim()
    .replace(/[\s_]+/g, '-')      // Replace spaces/underscores with a dash.
    .replace(/[^a-z0-9\-]/g, '');  // Remove non-alphanumerics except dashes.
}

/**
 * renderCategoryButtons()
 * -------------------------
 * Renders category buttons in the .button-container div based on an array of category names and the current topic.
 */
function renderCategoryButtons(categories, topic) {
  const container = document.querySelector('.button-container');
  if (!container) {
    console.error("No container found for category buttons.");
    return;
  }
  let buttonsHtml = "";
  categories.forEach(category => {
    let catSlug = slugify(category);
    buttonsHtml += `<a href="/content/${topic}/${catSlug}.html" class="btn btn-primary btn-lg"><strong>${category}</strong></a>\n`;
  });
  // Remove the loading screen if present.
  const loadingScreen = document.getElementById("loading-screen");
  if (loadingScreen) {
    loadingScreen.remove();
  }
  container.innerHTML = buttonsHtml;
}

/**
 * loadCategoryData()
 * ------------------
 * Fetches the category JSON file and renders the category buttons.
 */
function loadCategoryData() {
  const jsonUrl = getCategoriesJsonFilePath();
  if (!jsonUrl) return;
  
  fetch(jsonUrl)
    .then(response => {
      if (!response.ok) {
        throw new Error(`Unable to fetch categories: ${response.statusText}`);
      }
      return response.json();
    })
    .then(categories => {
      let pathParts = window.location.pathname.split('/').filter(Boolean);
      let fileName = pathParts[pathParts.length - 1];
      let topic = fileName.replace('.html', '').toLowerCase();
      
      if (!Array.isArray(categories)) {
        throw new Error("Invalid data format: Expected an array of categories.");
      }
      renderCategoryButtons(categories, topic);
    })
    .catch(error => {
      console.error("Error loading category data:", error);
      const container = document.querySelector('.button-container');
      if (container) {
        container.innerHTML = `<div class="alert alert-danger" role="alert">${error.message}</div>`;
      }
    });
}

/* Run both search and category functionalities when the DOM is fully loaded. */
document.addEventListener("DOMContentLoaded", function(){
  loadTopicData();     // Initializes the search functionality.
  loadCategoryData();  // Initializes the category buttons.
});
