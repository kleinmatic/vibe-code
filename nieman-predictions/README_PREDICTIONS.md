# Nieman Lab Predictions Downloader

This script downloads all Nieman Lab predictions articles with full metadata and content.

## Setup

1. Install the required dependencies:

```bash
pip install -r requirements.txt
```

Or install individually:
```bash
pip install feedparser requests beautifulsoup4 lxml
```

## Usage

Run the downloader script:

```bash
python3 download_predictions.py
```

The script will:
1. Fetch articles from RSS feeds (main feed and predictions tag feed)
2. Scrape collection pages for article URLs (2017-2026)
3. Download each article with full content and metadata
4. Save each article as a separate JSON file in the `predictions_data/` directory

## Output Format

Each article is saved as a JSON file with the following structure:

```json
{
  "url": "https://www.niemanlab.org/2025/12/article-slug/",
  "fetched_at": "2025-12-27T12:00:00",
  "title": "Article Title",
  "author": "Author Name",
  "published": "2025-12-19",
  "tags": ["predictions", "journalism"],
  "description": "Meta description",
  "content_html": "<div>...</div>",
  "content_text": "Plain text content...",
  "is_prediction": true
}
```

## Metadata Fields

- **url**: Original article URL
- **fetched_at**: Timestamp when the article was downloaded
- **title**: Article title
- **author**: Author name
- **published**: Publication date
- **tags**: Article tags/categories
- **description**: Meta description
- **content_html**: Full article content in HTML format
- **content_text**: Plain text version of the article
- **is_prediction**: Boolean flag identifying prediction articles

## Identifying Predictions

The script uses multiple heuristics to identify prediction articles:
- URL contains `/collection/predictions-`
- Tags include "prediction"
- Title contains prediction-related keywords
- Content mentions prediction phrases in the first 500 characters

## Rate Limiting

The script includes rate limiting (2 seconds between requests) to be respectful to the Nieman Lab servers.

## Analyzing Predictions

After downloading, use the analysis script to explore the predictions:

```bash
python3 analyze_predictions.py
```

This will:
- Load all downloaded predictions
- Print statistics (total, by year, by author, top tags)
- Export predictions to text files formatted for LLM analysis
- Show example searches

### Analysis Features

**Search predictions by keyword:**
```python
from analyze_predictions import PredictionsAnalyzer

analyzer = PredictionsAnalyzer()
ai_predictions = analyzer.search('AI')
print(f"Found {len(ai_predictions)} predictions about AI")
```

**Group by year:**
```python
by_year = analyzer.get_by_year()
for year, predictions in by_year.items():
    print(f"{year}: {len(predictions)} predictions")
```

**Group by author:**
```python
by_author = analyzer.get_by_author()
for author, predictions in by_author.items():
    print(f"{author}: {len(predictions)} predictions")
```

**Export for LLM analysis:**
```python
# Export all predictions
analyzer.export_for_llm("all_predictions_for_llm.txt")

# Export specific year
analyzer.export_for_llm("predictions_2025.txt", year="2025")
```

## Next Steps: Using an LLM

Once you have downloaded and exported the articles, you can:

1. **Summarize all predictions**: Use the exported text files with Claude, GPT-4, or other LLMs
2. **Search predictions**: Create a vector database for semantic search
3. **Analyze trends**: Track themes and topics across years
4. **Compare predictions**: See how predictions evolved year over year
5. **Fact-check predictions**: Compare past predictions with what actually happened

Example workflow with an LLM:
1. Run `python3 download_predictions.py` to download all articles
2. Run `python3 analyze_predictions.py` to export formatted text files
3. Upload `all_predictions_for_llm.txt` to Claude or your preferred LLM
4. Ask questions like:
   - "What are the main themes in these predictions?"
   - "How have predictions about AI changed over the years?"
   - "Which predictions from 2020 came true?"
   - "Summarize the key trends predicted for 2025"
