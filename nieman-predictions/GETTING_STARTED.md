# Getting Started - Nieman Lab Predictions Downloader

## Quick Start

This project downloads all Nieman Lab predictions articles (2017-2026) with full metadata and prepares them for LLM analysis.

## Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

Or manually:
```bash
pip install feedparser requests beautifulsoup4 lxml
```

## Step 2: Download All Predictions

```bash
python3 download_predictions.py
```

This will:
- Fetch articles from RSS feeds
- Scrape collection pages for years 2017-2026
- Download each article with full content
- Save to `predictions_data/` as individual JSON files
- Takes ~5-10 minutes depending on number of articles

## Step 3: Analyze and Export for LLM

```bash
python3 analyze_predictions.py
```

This will:
- Load all downloaded predictions
- Print statistics (totals, by year, by author, top tags)
- Export text files formatted for LLM analysis:
  - `all_predictions_for_llm.txt` - All predictions in one file
  - `predictions_2025_for_llm.txt` - By year
  - `predictions_2024_for_llm.txt` - By year
  - etc.

## Step 4: Use with an LLM

Upload the exported text files to Claude, ChatGPT, or your preferred LLM and ask:
- "What are the main themes in these predictions?"
- "How have predictions about AI changed over the years?"
- "Which predictions from 2020 came true?"
- "Summarize the key trends predicted for 2025"

## Files Created

- **download_predictions.py** - Downloads all articles from Nieman Lab
- **analyze_predictions.py** - Analyzes and exports for LLM use
- **requirements.txt** - Python dependencies
- **README_PREDICTIONS.md** - Full documentation
- **predictions_data/** - Directory where articles are saved

## Metadata Captured for Each Article

- url - Original article URL
- title - Article headline
- author - Author name
- published - Publication date
- tags - Categories/tags
- description - Meta description
- content_html - Full HTML content
- content_text - Plain text version
- is_prediction - Boolean flag identifying predictions

## RSS Feed Used

https://feeds.feedburner.com/NiemanJournalismLab

## Resources

- [Nieman Lab Predictions 2026](https://www.niemanlab.org/collection/predictions-2026/)
- [Nieman Lab Predictions 2025](https://www.niemanlab.org/collection/predictions-2025/)
- Collection pages exist for: 2026, 2025, 2024, 2023, 2022, 2021, 2020, 2018, 2017

## Next Session

When you come back:
1. Check if dependencies are installed: `python3 -c "import feedparser, requests, bs4"`
2. Run the download script if you haven't: `python3 download_predictions.py`
3. Analyze and use with LLM: `python3 analyze_predictions.py`
