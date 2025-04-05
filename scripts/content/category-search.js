// Find "media-pieces" and render a list of content related to a category
// Search engine only functions with the name of "media-pieces"

/**
 * getJsonFilePath()
 * -----------------
 * Extracts the topic and category from the current URL to build the path
 * to the JSON file for that category.
 * Expected URL structure: /content/{topic}/{category}.html
 */
function getJsonFilePath() {
  let pathParts = window.location.pathname.split('/').filter(Boolean);
  if (pathParts.length < 3) {
    console.error('Invalid URL structure for category page.');
    return null;
  }
  // Example: if URL is /content/documents/books.html:
  // topic = "documents", category = "books"
  let topic = pathParts[1].toLowerCase();
  let category = pathParts[2].replace('.html', '').toLowerCase();
  return `/datasets/content/${topic}/${category}.json`;
}

/**
 * capitalizeWords(str)
 * ---------------------
 * Capitalizes each word in a string.
 */
function capitalizeWords(str) {
  return str
    .split(' ')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join(' ');
}

/**
 * createCategoryCard(entry)
 * --------------------------
 * Creates a Bootstrap card for an entry with the following layout:
 *
 * TOP ROW:
 *   - Left (text-start): Entry name as a link (using media_piece_path) with class "no-underline"
 *   - Right (text-end): File size (file_size concatenated with data_metric) or "N/A"
 *
 * BOTTOM ROW:
 *   - Left (text-start): Entry type
 *   - Right (text-end): Entry year
 *
 * Returns the card element.
 */
function createCategoryCard(entry) {
  // Create the main card container.
  const card = document.createElement('div');
  card.className = 'card mt-3 mb-3';

  const cardBody = document.createElement('div');
  cardBody.className = 'card-body';  // CSS rule for .content-paragraph will apply to children.
  cardBody.style.padding = '8px';
  

  // --- Top Row: Name Link ---
  const topRow = document.createElement('div');
  topRow.className = 'row';

  const nameCol = document.createElement('div');
  nameCol.className = 'col-12 text-start';
  const nameLink = document.createElement('a');
  nameCol.style.padding = '3px 18px 3px 18px';
  nameLink.href = entry.media_piece_path;
  // Use the "card-title", "no-underline", and "content-paragraph" classes.
  nameLink.className = 'card-title no-underline content-paragraph';
  // Create a <strong> element for the entry name.
  const strongEl = document.createElement('strong');
  strongEl.textContent = entry.name;
  nameLink.appendChild(strongEl);

  nameCol.appendChild(nameLink);
  topRow.appendChild(nameCol);
  cardBody.appendChild(topRow);


  // --- Bottom Row: Type, File Size, and Year ---
  const bottomRow = document.createElement('div');
  bottomRow.className = 'row mt-0';

  const typeCol = document.createElement('div');
  typeCol.className = 'col-6 text-start content-paragraph';
  typeCol.textContent = entry.type;
  typeCol.style.padding = '0 0 3px 18px';
  bottomRow.appendChild(typeCol);

  const sizeCol = document.createElement('div');
  sizeCol.className = 'col-3 text-center content-paragraph';
  sizeCol.style.padding = '0 0 3px 0';
  let fileSizeText = "N/A";
  if (entry.file_size && entry.data_metric) {
    fileSizeText = entry.file_size + " " + entry.data_metric;
  } else if (entry.data_metric) {
    fileSizeText = "N/A" + " " + entry.data_metric;
  }
  sizeCol.textContent = fileSizeText;
  bottomRow.appendChild(sizeCol);

  const yearCol = document.createElement('div');
  yearCol.className = 'col-3 text-end content-paragraph';
  yearCol.style.padding = '0 18px 3px 0';
  yearCol.textContent = entry.year;
  bottomRow.appendChild(yearCol);

  cardBody.appendChild(bottomRow);


  cardBody.appendChild(bottomRow);
  card.appendChild(cardBody);

  return card;
}


/**
 * setupSearch()
 * -------------
 * Attaches an event listener to the search input (id "categorySearch")
 * to continuously filter the displayed cards by entry name.
 */
function setupSearch() {
  const searchInput = document.getElementById("categorySearch");
  if (!searchInput) return;
  
  searchInput.addEventListener("input", function () {
    const searchTerm = searchInput.value.toLowerCase();
    // Get all cards within the container.
    const cardContainer = document.querySelector('.category-search');
    const cards = cardContainer.querySelectorAll('.card');
    cards.forEach(card => {
      // Find the card title.
      const titleLink = card.querySelector('.card-title');
      if (titleLink) {
        const cardName = titleLink.textContent.toLowerCase();
        if (cardName.includes(searchTerm)) {
          card.style.display = "";
        } else {
          card.style.display = "none";
        }
      }
    });
  });
}

/**
 * showLoadingScreen()
 * ---------------------
 * Displays a loading screen (with an animated GIF) inside the container
 * with class "category-search" while JSON data is being fetched.
 */
function showLoadingScreen() {
  const loadingScreen = document.getElementById("loading-screen");
  if (loadingScreen) {
    loadingScreen.innerHTML = ``;
  }
}


/**
 * loadCategoryData()
 * ------------------
 * Loads the JSON dataset for the current category, creates a card for each entry,
 * and appends the cards to the container. Also sets up live search functionality.
 */
function loadCategoryData() {
  showLoadingScreen();
  const jsonUrl = getJsonFilePath();
  if (!jsonUrl) {
    console.error('Failed to determine JSON file path for category.');
    return;
  }
  
  fetch(jsonUrl)
    .then(response => {
      if (!response.ok) {
        throw new Error(`Unable to fetch data: ${response.statusText}`);
      }
      return response.json();
    })
    .then(data => {
      const container = document.querySelector('.category-search');
      if (container) {
        container.innerHTML = ''; // Clear loading screen.
        // Assume data is an array of entry objects.
        data.forEach(entry => {
          const card = createCategoryCard(entry);
          container.appendChild(card);
        });
        setupSearch(); // Enable live search filtering.
      } else {
        console.error('No container found with class "category-search"');
      }
    })
    .catch(error => {
      console.error('Error loading category data:', error);
      const container = document.querySelector('.category-search');
      if (container) {
        container.innerHTML = `<div class="alert alert-danger" role="alert">
          ${error.message}
        </div>`;
      }
    });
}

document.addEventListener('DOMContentLoaded', loadCategoryData);
