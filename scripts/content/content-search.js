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
    .replace(/[\s_]+/g, '-')      // Replace spaces and underscores with dash.
    .replace(/[^a-z0-9\-]/g, '');  // Remove all non-alphanumeric except dashes.
}

/**
 * getTopicsJsonFilePath()
 * -----------------------
 * Returns the JSON file path that contains the list of topics.
 */
function getTopicsJsonFilePath() {
  return `/datasets/content/topics.json`;
}

/**
 * renderTopicButtons()
 * ----------------------
 * Renders topic buttons inside the .button-container div.
 * Each button links to a page based on the topic slug.
 * Example output:
 *   <a href="/content/audio.html" class="btn btn-primary btn-lg">
 *     <strong>Audio</strong>
 *   </a>
 */
function renderTopicButtons(topics) {
  const container = document.querySelector('.button-container');
  if (!container) {
    console.error("No container found with class 'button-container'.");
    return;
  }
  
  let buttonsHtml = "";
  topics.forEach(topic => {
    const topicSlug = slugify(topic);
    buttonsHtml += `<a href="/content/${topicSlug}.html" class="btn btn-primary btn-lg"><strong>${topic}</strong></a>\n`;
  });
  
  // Remove the loading screen if present.
  const loadingScreen = document.getElementById("loading-screen");
  if (loadingScreen) {
    loadingScreen.remove();
  }
  
  container.innerHTML = buttonsHtml;
}

/**
 * loadTopicsData()
 * ----------------
 * Fetches the JSON file containing topics and renders the topic buttons.
 */
function loadTopicsData() {
  const jsonUrl = getTopicsJsonFilePath();

  fetch(jsonUrl)
    .then(response => {
      if (!response.ok) {
        throw new Error(`Unable to fetch data: ${response.statusText}`);
      }
      return response.json();
    })
    .then(topics => {
      if (!Array.isArray(topics)) {
        throw new Error("Invalid data format: Expected an array of topics.");
      }
      renderTopicButtons(topics);
    })
    .catch(error => {
      console.error("Error loading topics data:", error);
      const container = document.querySelector('.button-container');
      if (container) {
        container.innerHTML = `<div class="alert alert-danger" role="alert">${error.message}</div>`;
      }
    });
}

// When the DOM is fully loaded, run the function to load topics.
document.addEventListener('DOMContentLoaded', loadTopicsData);
