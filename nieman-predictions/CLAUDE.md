# Claude Context - Nieman Lab Predictions Project

## Project Goal
Download all Nieman Lab predictions articles with metadata (author, date, URL, tags, content) and prepare them for LLM analysis.

## Technical Findings

### RSS Feed Structure
- **Main feed**: https://feeds.feedburner.com/NiemanJournalismLab
  - Only shows ~16 most recent articles
  - Contains: title, link, author (dc:creator), pubDate, category, description, content:encoded (full HTML)
  - Category field shows "Regular post" for all items (not useful for filtering predictions)

- **Tag feed**: https://www.niemanlab.org/tag/predictions/feed/
  - Only had 15 items from 2010-2020 (incomplete)
  - RSS feeds are limited in scope

### Collection Pages
- URL pattern: `https://www.niemanlab.org/collection/predictions-YYYY/`
- Available years: 2017, 2018, 2020, 2021, 2022, 2023, 2024, 2025, 2026
- **Issue**: Direct WebFetch attempts returned 403 Forbidden
- **Solution**: Use requests library with browser-like headers in the Python script

### Prediction Identification
Since there's no dedicated "prediction" category in the feed, the script uses multiple heuristics:
1. URL contains `/collection/predictions-`
2. Tags include "prediction"
3. Title contains prediction keywords
4. Content mentions prediction phrases in first 500 characters

### Article Metadata Available
From RSS and scraping:
- url (canonical link)
- title (h1 tag)
- author (meta tags, byline, rel="author")
- published (article:published_time meta tag, time datetime attribute)
- tags (rel="tag" links, .tags/.categories classes)
- description (meta description, og:description)
- content_html (article .entry-content or similar)
- content_text (plain text extraction)

### Rate Limiting
- Script includes 2-second delay between requests
- Uses browser-like User-Agent to avoid blocks
- Respectful to Nieman Lab servers

## File Structure

```
nieman-predictions/
├── download_predictions.py      # Main downloader script
├── analyze_predictions.py       # Analysis and LLM export tool
├── requirements.txt             # Python dependencies
├── GETTING_STARTED.md          # Quick start guide
├── README_PREDICTIONS.md       # Full documentation
├── CLAUDE.md                   # This file - technical context
└── predictions_data/           # Output directory
    ├── *.json                  # Individual article files
    └── example_prediction.json # Example structure
```

## Potential Issues to Watch

1. **Website structure changes**: If Nieman Lab redesigns, the HTML selectors in `fetch_article_content()` may need updating
2. **Rate limiting**: If downloading fails, may need to increase delays or add retry logic
3. **New collection years**: Add new years to `COLLECTION_URLS` list as they're published
4. **RSS feed changes**: FeedBurner could change or be deprecated

## Future Enhancements

If needed later:
- Add retry logic with exponential backoff
- Implement incremental updates (only download new articles)
- Add vector database integration for semantic search
- Create a simple web UI for browsing predictions
- Add direct LLM integration (Claude API, OpenAI API)
- Extract and analyze prediction accuracy (compare old predictions to reality)

## Dependencies
- feedparser: RSS/Atom feed parsing
- requests: HTTP requests with custom headers
- beautifulsoup4: HTML parsing and content extraction
- lxml: Fast XML/HTML parser (backend for beautifulsoup4)

## Testing Status
- RSS feed parsing: ✓ Verified working
- Collection page structure: ✓ Analyzed (2026 collection)
- Article download: Not tested (requires dependency installation)
- Metadata extraction: Not tested (requires dependency installation)

## Next Steps When Resuming
1. Install dependencies: `pip install -r requirements.txt`
2. Run downloader: `python3 download_predictions.py`
3. Verify output in predictions_data/
4. Run analyzer: `python3 analyze_predictions.py`
5. Use exported text files with Claude or other LLM
