# Wikipedia Date Finder

Find random Wikipedia articles containing specific dates. Available as both a command-line tool and web app.

## Python CLI

Find articles that actually contain the date in their content:

```bash
python wikipedia_date_finder.py "January 15, 2024"
python wikipedia_date_finder.py "11/20/1968"
python wikipedia_date_finder.py "2024-07-04"
```

**Requirements:** `requests`, `beautifulsoup4`

## Web App

Interactive Svelte-based web interface for the same functionality.

```bash
npm install
npm run dev
```

Open the displayed local URL in your browser.

## How It Works

- **Specific dates (with year)**: Searches article content to verify the date appears
- **General dates (month/day only)**: Returns curated "On This Day" events
- Always shows context explaining the date's relevance

## Vibe Code Disclaimer

Created with Claude Code.