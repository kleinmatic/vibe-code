// Wikipedia Date Finder - Client-side JavaScript implementation
// Calls Wikipedia APIs directly from the browser

const WIKIPEDIA_API = "https://en.wikipedia.org/w/api.php";
const FEED_API = "https://api.wikimedia.org/feed/v1/wikipedia/en/onthisday";

// Parse date string into Date object
export function parseDate(dateString) {
  const currentYear = new Date().getFullYear();

  const formats = [
    { regex: /^(\d{4})-(\d{2})-(\d{2})$/, parser: (m) => new Date(m[1], m[2] - 1, m[3]) }, // YYYY-MM-DD
    { regex: /^(\d{1,2})\/(\d{1,2})\/(\d{4})$/, parser: (m) => new Date(m[3], m[1] - 1, m[2]) }, // MM/DD/YYYY
    { regex: /^(\d{1,2})\/(\d{1,2})$/, parser: (m) => new Date(currentYear, m[1] - 1, m[2]) }, // MM/DD (no year)
    { regex: /^(\d{4})$/, parser: (m) => new Date(m[1], 0, 1) }, // YYYY
  ];

  for (const format of formats) {
    const match = dateString.match(format.regex);
    if (match) {
      return format.parser(match);
    }
  }

  // Try parsing as natural language (handles "January 15", "July 4", etc.)
  const date = new Date(dateString);
  if (!isNaN(date.getTime())) {
    return date;
  }

  throw new Error('Invalid date format. Try: MM/DD, YYYY-MM-DD, MM/DD/YYYY, "Month DD", or "Month DD, YYYY"');
}

// Check if date string includes a year
export function hasYearComponent(dateString) {
  return /\b\d{4}\b/.test(dateString);
}

// Get article text content
async function getArticleExtract(articleTitle) {
  const params = new URLSearchParams({
    action: "query",
    format: "json",
    titles: articleTitle,
    prop: "extracts",
    explaintext: "true",
    exlimit: "1",
    origin: "*", // For CORS
  });

  const response = await fetch(`${WIKIPEDIA_API}?${params}`);
  const data = await response.json();

  const pages = data.query?.pages || {};
  for (const pageId in pages) {
    if (pages[pageId].extract) {
      return pages[pageId].extract.substring(0, 3000); // Limit size
    }
  }
  return null;
}

// Find date context in article text
function findDateContext(text, date) {
  if (!text) return { found: false, context: null };

  const year = date.getFullYear();
  const monthNames = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
  ];
  const monthName = monthNames[date.getMonth()];
  const monthAbbr = monthName.substring(0, 3);
  const day = date.getDate();
  const dayPadded = day.toString().padStart(2, '0');

  const patterns = [
    `${monthName} ${day}, ${year}`,
    `${monthAbbr} ${day}, ${year}`,
    `${monthName} ${dayPadded}, ${year}`,
    `${monthAbbr} ${dayPadded}, ${year}`,
    `${day} ${monthName} ${year}`,
    `${year}-${(date.getMonth() + 1).toString().padStart(2, '0')}-${dayPadded}`,
  ];

  for (const pattern of patterns) {
    const index = text.toLowerCase().indexOf(pattern.toLowerCase());
    if (index !== -1) {
      const start = Math.max(0, index - 100);
      const end = Math.min(text.length, index + pattern.length + 100);
      let context = text.substring(start, end).trim();

      if (start > 0) context = "..." + context;
      if (end < text.length) context = context + "...";

      return { found: true, context };
    }
  }

  return { found: false, context: null };
}

// Verify date appears in article
async function verifyDateInArticle(articleTitle, date) {
  const extract = await getArticleExtract(articleTitle);
  if (!extract) return { verified: false, context: null };

  return findDateContext(extract, date);
}

// Try CirrusSearch API
async function tryCirrusSearch(date, maxAttempts = 5) {
  const year = date.getFullYear();
  const monthNames = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
  ];
  const monthName = monthNames[date.getMonth()];
  const monthAbbr = monthName.substring(0, 3);
  const day = date.getDate();
  const dayPadded = day.toString().padStart(2, '0');
  const monthPadded = (date.getMonth() + 1).toString().padStart(2, '0');

  const datePatterns = [
    `${monthName}\\s+${day},?\\s+${year}`,
    `${monthAbbr}\\s+${day},?\\s+${year}`,
    `${day}\\s+${monthName}\\s+${year}`,
    `${year}-${monthPadded}-${dayPadded}`,
  ];

  const regexPattern = datePatterns.join("|");
  const searchQuery = `"${monthName} ${year}" insource:/${regexPattern}/`;

  const params = new URLSearchParams({
    action: "query",
    format: "json",
    list: "search",
    srsearch: searchQuery,
    srnamespace: "0",
    srlimit: "50",
    srsort: "random",
    origin: "*",
  });

  try {
    const response = await fetch(`${WIKIPEDIA_API}?${params}`);
    const data = await response.json();
    const results = data.query?.search || [];

    if (results.length > 0) {
      // Shuffle and try a few
      const shuffled = results.sort(() => Math.random() - 0.5);

      for (let i = 0; i < Math.min(maxAttempts, shuffled.length); i++) {
        const article = shuffled[i];
        const { verified, context } = await verifyDateInArticle(article.title, date);

        if (verified) {
          return {
            success: true,
            article: article.title,
            context,
            method: "CirrusSearch (verified in content)",
          };
        }
      }

      // Return first result even if unverified
      return {
        success: true,
        article: results[0].title,
        context: null,
        method: "CirrusSearch (unverified)",
      };
    }

    return { success: false };
  } catch (error) {
    console.error("CirrusSearch failed:", error);
    return { success: false };
  }
}

// Try Feed API (On This Day)
async function tryFeedAPI(date) {
  const month = (date.getMonth() + 1).toString().padStart(2, '0');
  const day = date.getDate().toString().padStart(2, '0');
  const year = date.getFullYear();

  try {
    const response = await fetch(`${FEED_API}/all/${month}/${day}`);
    const data = await response.json();

    const allItems = [];
    const eventTypes = ['selected', 'events', 'births', 'deaths', 'holidays'];

    for (const eventType of eventTypes) {
      if (data[eventType]) {
        for (const item of data[eventType]) {
          if (item.pages) {
            const eventText = item.text || 'Event from this date';
            for (const page of item.pages) {
              allItems.push({
                title: page.titles.normalized,
                context: eventText,
                year: item.year || null,
              });
            }
          }
        }
      }
    }

    if (allItems.length > 0) {
      // Filter by year if specific year requested
      const yearFiltered = allItems.filter((item) => item.year === year);

      if (yearFiltered.length > 0) {
        const item = yearFiltered[Math.floor(Math.random() * yearFiltered.length)];
        return {
          success: true,
          article: item.title,
          context: `Event: ${item.context} (${year})`,
          method: "Feed API (On This Day - exact year match)",
        };
      } else {
        const item = allItems[Math.floor(Math.random() * allItems.length)];
        const itemYear = item.year ? ` (${item.year})` : "";
        return {
          success: true,
          article: item.title,
          context: `Event from this day${itemYear}: ${item.context}`,
          method: "Feed API (On This Day - different year)",
        };
      }
    }

    return { success: false };
  } catch (error) {
    console.error("Feed API failed:", error);
    return { success: false };
  }
}

// Try Date Pages API
async function tryDatePagesAPI(date, verify = true) {
  const monthNames = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
  ];
  const monthName = monthNames[date.getMonth()];
  const day = date.getDate();
  const datePage = `${monthName}_${day}`;

  const params = new URLSearchParams({
    action: "query",
    format: "json",
    prop: "links",
    titles: datePage,
    pllimit: "max",
    plnamespace: "0",
    origin: "*",
  });

  try {
    const response = await fetch(`${WIKIPEDIA_API}?${params}`);
    const data = await response.json();

    const pages = data.query?.pages || {};
    let links = [];

    for (const pageId in pages) {
      if (pages[pageId].links) {
        links = pages[pageId].links.map((link) => link.title);
        break;
      }
    }

    if (links.length >= 10) {
      // Shuffle links
      const shuffled = links.sort(() => Math.random() - 0.5);
      const maxAttempts = verify ? 5 : 1;

      for (let i = 0; i < Math.min(maxAttempts, shuffled.length); i++) {
        const article = shuffled[i];

        if (verify) {
          const { verified, context } = await verifyDateInArticle(article, date);
          if (verified) {
            return {
              success: true,
              article,
              context,
              method: "Date Pages API (verified in content)",
            };
          }
        } else {
          return {
            success: true,
            article,
            context: null,
            method: "Date Pages API (unverified)",
          };
        }
      }

      // Return first link with warning
      return {
        success: true,
        article: links[0],
        context: `Linked from '${datePage}' page (date may not appear in article)`,
        method: "Date Pages API (unverified)",
      };
    }

    return { success: false };
  } catch (error) {
    console.error("Date Pages API failed:", error);
    return { success: false };
  }
}

// Main function to find article with date
export async function findArticleWithDate(dateString, onProgress) {
  const date = parseDate(dateString);
  const hasYear = hasYearComponent(dateString);
  const isYearOnly = /^\d{4}$/.test(dateString.trim());

  if (isYearOnly) {
    onProgress?.("Searching for year-only dates is not yet supported in the web version");
    throw new Error("Year-only dates not supported in web version");
  }

  // Strategy: If has year, prioritize content search. Otherwise use curated events.
  if (hasYear) {
    onProgress?.("Searching article content for specific date...");

    // Tier 1: CirrusSearch
    onProgress?.("Trying CirrusSearch...");
    const cirrusResult = await tryCirrusSearch(date);
    if (cirrusResult.success && cirrusResult.context) {
      return cirrusResult;
    }

    // Tier 2: Feed API
    onProgress?.("Trying Feed API...");
    const feedResult = await tryFeedAPI(date);
    if (feedResult.success) {
      return feedResult;
    }

    // Tier 3: Date Pages API with verification
    onProgress?.("Trying Date Pages API...");
    const datePagesResult = await tryDatePagesAPI(date, true);
    if (datePagesResult.success) {
      return datePagesResult;
    }
  } else {
    onProgress?.("Searching for curated events from this day...");

    // Tier 1: Feed API
    onProgress?.("Trying Feed API...");
    const feedResult = await tryFeedAPI(date);
    if (feedResult.success) {
      return feedResult;
    }

    // Tier 2: Date Pages API
    onProgress?.("Trying Date Pages API...");
    const datePagesResult = await tryDatePagesAPI(date, false);
    if (datePagesResult.success) {
      return datePagesResult;
    }
  }

  throw new Error("No article found after trying all methods");
}
