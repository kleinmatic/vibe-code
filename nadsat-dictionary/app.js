/* ==========================================================================
   NADSAT DICTIONARY LOGIC — app.js
   Responsive interaction, fuzzy search, synonym resolution, and widget logic
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {
  // DOM Elements
  const searchInput = document.getElementById('search-input');
  const clearSearchBtn = document.getElementById('clear-search-btn');
  const alphabetFilterNav = document.getElementById('alphabet-filter-nav');
  const dictionaryFeed = document.getElementById('dictionary-feed');
  const noResultsState = document.getElementById('no-results-state');
  const emptyQueryText = document.getElementById('empty-query-text');
  const resetExplorerBtn = document.getElementById('reset-explorer-btn');
  const resultsCount = document.getElementById('results-count');
  const lexiconSize = document.getElementById('lexicon-size');
  
  // Randomizer Widget Elements
  const randomCardContent = document.getElementById('random-card-content');
  const viddyRandomBtn = document.getElementById('viddy-random-btn');

  // Application State
  let processedDictionary = [];
  let activeLetterFilter = 'all';
  let currentSearchQuery = '';

  // 1. Process Raw Embedded Lexicon Data
  // Implements the exact synonyms and parenthetical alternate spellings resolution
  function loadAndProcessDictionary() {
    if (typeof DICTIONARY_DATA === 'undefined') {
      console.error('DICTIONARY_DATA is not defined. Make sure dictionary.js is loaded first.');
      return;
    }

    const words = [];
    DICTIONARY_DATA.forEach(row => {
      const nadsatField = row.Nadsat ? row.Nadsat.trim() : '';
      const english = row.English ? row.English.trim() : '';
      const origin = row['Word origin'] ? row['Word origin'].trim() : '';

      if (!nadsatField) return;

      // Handle comma-separated synonyms (e.g. "guff, guffaw")
      let entriesToCreate = [];
      if (nadsatField.includes(',')) {
        entriesToCreate = nadsatField.split(',').map(s => s.trim()).filter(Boolean);
      } else {
        entriesToCreate = [nadsatField];
      }

      // Handle parenthetical forms (e.g. "horrorshow (xorosho)")
      const allSearchableForms = [];
      entriesToCreate.forEach(entry => {
        allSearchableForms.push(entry);

        // Regex matching for alternate pronunciation within parentheses
        const match = entry.match(/^(.+?)\s*\((.+?)\)\s*$/);
        if (match) {
          const mainWord = match[1].trim();
          const alternate = match[2].trim();
          
          if (!allSearchableForms.includes(mainWord)) allSearchableForms.push(mainWord);
          if (!allSearchableForms.includes(alternate)) allSearchableForms.push(alternate);
        }
      });

      // Create search index entries for all matching forms
      allSearchableForms.forEach(searchableForm => {
        words.push({
          nadsat: searchableForm,
          english: english,
          origin: origin,
          original_nadsat: nadsatField // Retain the full literal for correct UI display
        });
      });
    });

    processedDictionary = words;
    
    // Set total unique items count
    lexiconSize.textContent = DICTIONARY_DATA.length;
  }

  // 2. Generate A-Z Filter Tag Nav
  // Proactively disables letters that have zero matching words in the lexicon
  function generateAlphabetTags() {
    const letters = 'abcdefghijklmnopqrstuvwxyz'.split('');
    
    // Check which letters actually contain words
    const populatedLetters = new Set();
    processedDictionary.forEach(word => {
      const firstChar = word.nadsat.charAt(0).toLowerCase();
      if (/[a-z]/.test(firstChar)) {
        populatedLetters.add(firstChar);
      }
    });

    // Render A-Z letter button tags
    letters.forEach(letter => {
      const button = document.createElement('button');
      button.className = 'letter-tag';
      button.textContent = letter.toUpperCase();
      button.dataset.letter = letter;
      button.id = `letter-btn-${letter}`;
      
      if (!populatedLetters.has(letter)) {
        button.classList.add('disabled');
        button.setAttribute('aria-disabled', 'true');
        button.setAttribute('tabindex', '-1');
      }

      button.addEventListener('click', () => handleLetterFilterClick(letter));
      alphabetFilterNav.appendChild(button);
    });
  }

  // 3. Filter & Render Dictionary Cards
  function renderExplorerFeed() {
    const query = currentSearchQuery.toLowerCase().trim();
    
    // Step 3a: Perform filtering
    let filtered = processedDictionary.filter(word => {
      // Starting letter condition
      if (activeLetterFilter !== 'all') {
        if (word.nadsat.charAt(0).toLowerCase() !== activeLetterFilter) {
          return false;
        }
      }

      // Search match condition (nadsat, english meaning, or etymology origin text)
      if (query !== '') {
        const matchesNadsat = word.nadsat.toLowerCase().includes(query);
        const matchesEnglish = word.english.toLowerCase().includes(query);
        const matchesOrigin = word.origin.toLowerCase().includes(query);
        return matchesNadsat || matchesEnglish || matchesOrigin;
      }

      return true;
    });

    // Step 3b: Deduplicate results by their original_nadsat representation 
    // This aggregates multiple synonym search records (like guff / guffaw) into a single clean UI card
    const uniqueCards = [];
    const seenOriginals = new Set();
    filtered.forEach(word => {
      if (!seenOriginals.has(word.original_nadsat)) {
        seenOriginals.add(word.original_nadsat);
        uniqueCards.push(word);
      }
    });

    // Step 3c: Render UI
    resultsCount.textContent = uniqueCards.length;
    dictionaryFeed.innerHTML = '';

    if (uniqueCards.length === 0) {
      dictionaryFeed.style.display = 'none';
      noResultsState.style.display = 'flex';
      emptyQueryText.textContent = query || activeLetterFilter.toUpperCase();
    } else {
      noResultsState.style.display = 'none';
      dictionaryFeed.style.display = 'grid';

      uniqueCards.forEach((word, index) => {
        const card = document.createElement('article');
        card.className = 'word-card glass-panel';
        // Minor stagger transition delay for smooth aesthetic entrance
        card.style.animationDelay = `${index * 0.02}s`;

        // Highlight synonyms if comma-separated
        let synonymsHTML = '';
        if (word.original_nadsat.includes(',')) {
          const synonymsList = word.original_nadsat.split(',').map(s => s.trim());
          synonymsHTML = `<div class="synonyms-group">
            ${synonymsList.map(s => `<span class="synonym-pill">${s}</span>`).join('')}
          </div>`;
        }

        // Standard origin mapping
        const originDisplay = word.origin && word.origin !== '—' 
          ? `<div class="origin-block">
              <span class="origin-tag">Etymology</span>
              <p class="origin-text">${word.origin}</p>
             </div>`
          : '';

        card.innerHTML = `
          <div class="card-header">
            <h3 class="nadsat-word">${word.original_nadsat}</h3>
          </div>
          <p class="english-def">${word.english}</p>
          ${synonymsHTML}
          ${originDisplay}
        `;
        
        dictionaryFeed.appendChild(card);
      });
    }
  }

  // 4. UI Interaction Handlers
  function handleSearchInput(e) {
    currentSearchQuery = e.target.value;
    
    // Toggle clear button visibility
    if (currentSearchQuery.length > 0) {
      clearSearchBtn.style.display = 'flex';
    } else {
      clearSearchBtn.style.display = 'none';
    }

    renderExplorerFeed();
  }

  function clearSearch() {
    searchInput.value = '';
    currentSearchQuery = '';
    clearSearchBtn.style.display = 'none';
    searchInput.focus();
    renderExplorerFeed();
  }

  function handleLetterFilterClick(letter) {
    // Toggle active state in navigation
    const letterTags = alphabetFilterNav.querySelectorAll('.letter-tag');
    letterTags.forEach(tag => {
      if (tag.dataset.letter === letter) {
        tag.classList.add('active');
      } else {
        tag.classList.remove('active');
      }
    });

    activeLetterFilter = letter;
    renderExplorerFeed();
  }

  function resetExplorer() {
    searchInput.value = '';
    currentSearchQuery = '';
    clearSearchBtn.style.display = 'none';
    activeLetterFilter = 'all';
    
    // Reset A-Z filter UI
    const letterTags = alphabetFilterNav.querySelectorAll('.letter-tag');
    letterTags.forEach(tag => {
      if (tag.dataset.letter === 'all') {
        tag.classList.add('active');
      } else {
        tag.classList.remove('active');
      }
    });

    renderExplorerFeed();
  }

  // 5. Showcase Widget: Random Nadsat Generator
  function displayRandomWord(animate = false) {
    if (typeof DICTIONARY_DATA === 'undefined' || DICTIONARY_DATA.length === 0) return;

    if (animate) {
      randomCardContent.classList.add('shuffling');
      viddyRandomBtn.disabled = true;
    }

    setTimeout(() => {
      // Pick random entry from original un-expanded dataset
      const randomIndex = Math.floor(Math.random() * DICTIONARY_DATA.length);
      const chosen = DICTIONARY_DATA[randomIndex];
      
      const nadsat = chosen.Nadsat.trim();
      const english = chosen.English.trim();
      const origin = chosen['Word origin'].trim();

      const originHTML = origin && origin !== '—'
        ? `<div class="random-origin"><strong>Origin:</strong> ${origin}</div>`
        : `<div class="random-origin"><em>No etymology documented.</em></div>`;

      randomCardContent.innerHTML = `
        <h4 class="random-word-title">${nadsat}</h4>
        <div class="random-english">${english}</div>
        ${originHTML}
      `;

      if (animate) {
        setTimeout(() => {
          randomCardContent.classList.remove('shuffling');
          viddyRandomBtn.disabled = false;
        }, 200); // match fade in duration
      }
    }, animate ? 200 : 0);
  }

  // 6. Bind Event Listeners
  searchInput.addEventListener('input', handleSearchInput);
  clearSearchBtn.addEventListener('click', clearSearch);
  resetExplorerBtn.addEventListener('click', resetExplorer);
  viddyRandomBtn.addEventListener('click', () => displayRandomWord(true));

  // 7. Initial App Initialization Sequence
  loadAndProcessDictionary();
  generateAlphabetTags();
  renderExplorerFeed();
  displayRandomWord(false); // Init showcase without shuffling animation
});
