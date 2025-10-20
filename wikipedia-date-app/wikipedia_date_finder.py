#!/usr/bin/env python3
"""
Script to find a random Wikipedia article that includes a specific date.
Uses a smart hybrid approach that prioritizes accuracy:
- For specific dates (with year): Searches content first to guarantee the date appears
- For general dates (month/day): Returns curated events with context
- Always verifies and shows WHERE/WHY the date relates to the article
"""

import requests
import argparse
import random
import re
from datetime import datetime
from urllib.parse import quote
from bs4 import BeautifulSoup


# Wikipedia API configuration
WIKIPEDIA_API = "https://en.wikipedia.org/w/api.php"
FEED_API = "https://api.wikimedia.org/feed/v1/wikipedia/en/onthisday"
USER_AGENT = "WikipediaDateFinder/3.0 (Educational script; github.com/kleinmatic/vibe-code)"

# Headers for all requests
HEADERS = {
    "User-Agent": USER_AGENT
}


def validate_date(date_string):
    """Validate and parse the date string into a datetime object."""
    formats = [
        "%Y-%m-%d",      # 2024-01-15
        "%m/%d/%Y",      # 01/15/2024
        "%d/%m/%Y",      # 15/01/2024
        "%B %d, %Y",     # January 15, 2024
        "%b %d, %Y",     # Jan 15, 2024
        "%Y",            # 2024 (year only)
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_string, fmt)
        except ValueError:
            continue

    raise ValueError(
        f"Invalid date format: {date_string}. "
        f"Try formats like: 2024-01-15, 01/15/2024, 'January 15, 2024', or 2024"
    )


def has_year_component(date_string):
    """Check if the date string includes a year component."""
    # Year-only: exactly 4 digits
    if len(date_string.strip()) == 4 and date_string.strip().isdigit():
        return True

    # Check if any 4-digit year appears in the string
    return bool(re.search(r'\b\d{4}\b', date_string))


def get_article_extract(article_title, max_chars=3000):
    """Get the text content of a Wikipedia article."""
    try:
        params = {
            "action": "query",
            "format": "json",
            "titles": article_title,
            "prop": "extracts",
            "explaintext": True,
            "exlimit": "1",
        }

        response = requests.get(WIKIPEDIA_API, params=params, headers=HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()

        pages = data.get('query', {}).get('pages', {})
        for page_id, page_data in pages.items():
            if 'extract' in page_data:
                extract = page_data['extract']
                # Limit to first max_chars to avoid huge articles
                return extract[:max_chars] if len(extract) > max_chars else extract

        return None
    except Exception as e:
        print(f"  Warning: Could not fetch article content: {e}")
        return None


def find_date_context(text, date_obj):
    """
    Find and extract context around where the date appears in the text.
    Returns (found, context_snippet) tuple.
    """
    if not text:
        return False, None

    # Generate various date formats to search for
    year = date_obj.strftime("%Y")
    month_full = date_obj.strftime("%B")
    month_abbr = date_obj.strftime("%b")
    day = date_obj.strftime("%-d").lstrip("0")
    day_padded = date_obj.strftime("%d")

    date_patterns = [
        f"{month_full} {day}, {year}",
        f"{month_abbr} {day}, {year}",
        f"{month_full} {day_padded}, {year}",
        f"{month_abbr} {day_padded}, {year}",
        f"{day} {month_full} {year}",
        f"{year}-{day_padded}-{day_padded}",
        f"{day_padded}/{day_padded}/{year}",
    ]

    # Search for each pattern
    for pattern in date_patterns:
        # Case-insensitive search
        match = re.search(re.escape(pattern), text, re.IGNORECASE)
        if match:
            # Extract context around the match (100 chars before and after)
            start = max(0, match.start() - 100)
            end = min(len(text), match.end() + 100)
            context = text[start:end]

            # Clean up the context
            context = context.strip()
            if start > 0:
                context = "..." + context
            if end < len(text):
                context = context + "..."

            return True, context

    return False, None


def verify_date_in_article(article_title, date_obj):
    """
    Verify that the date actually appears in the article.
    Returns (verified, context) tuple.
    """
    print(f"  Verifying date appears in article...")

    extract = get_article_extract(article_title)
    if not extract:
        return False, None

    found, context = find_date_context(extract, date_obj)
    return found, context


def try_cirrus_search(date_obj, max_attempts=5):
    """
    Search for articles that actually contain the specific date in their content.
    Returns: (success, article_title, context, method_name) or (False, None, None, None)
    """
    try:
        # Generate search patterns for different date formats
        year = date_obj.strftime("%Y")
        month_full = date_obj.strftime("%B")
        month_abbr = date_obj.strftime("%b")
        month_padded = date_obj.strftime("%m")
        day = date_obj.strftime("%-d")
        day_padded = date_obj.strftime("%d")

        # Build search query - combine indexed term with insource regex
        date_patterns = [
            f"{month_full}\\s+{day},?\\s+{year}",
            f"{month_abbr}\\s+{day},?\\s+{year}",
            f"{day}\\s+{month_full}\\s+{year}",
            f"{year}-{month_padded}-{day_padded}",
        ]
        regex_pattern = "|".join(date_patterns)
        search_query = f'"{month_full} {year}" insource:/{regex_pattern}/'

        params = {
            "action": "query",
            "format": "json",
            "list": "search",
            "srsearch": search_query,
            "srnamespace": "0",
            "srlimit": "50",
            "srsort": "random",
        }

        response = requests.get(WIKIPEDIA_API, params=params, headers=HEADERS, timeout=30)
        response.raise_for_status()
        data = response.json()

        results = data.get('query', {}).get('search', [])

        if results:
            # Try a few random results to find one with good context
            random.shuffle(results)
            for result in results[:max_attempts]:
                article_title = result['title']
                print(f"  Checking: {article_title}")

                verified, context = verify_date_in_article(article_title, date_obj)
                if verified:
                    return True, article_title, context, "CirrusSearch (verified in content)"

            # If none verified, return the first one anyway
            print(f"  Could not verify date in any articles, using first result")
            return True, results[0]['title'], None, "CirrusSearch (unverified)"

        return False, None, None, None

    except Exception as e:
        print(f"CirrusSearch failed: {e}")
        return False, None, None, None


def try_feed_api(date_obj):
    """
    Try Wikipedia's Feed API "On This Day" endpoint.
    Returns: (success, article_title, context, method_name) or (False, None, None, None)
    """
    try:
        month = date_obj.strftime("%m")
        day = date_obj.strftime("%d")
        year = date_obj.strftime("%Y")

        url = f"{FEED_API}/all/{month}/{day}"
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()

        data = response.json()

        # Collect all items with their event descriptions and pages
        all_items = []
        for event_type in ['selected', 'events', 'births', 'deaths', 'holidays']:
            if event_type in data:
                for item in data[event_type]:
                    if 'pages' in item:
                        # Store the event text as context
                        event_text = item.get('text', 'Event from this date')
                        for page in item['pages']:
                            all_items.append({
                                'title': page['titles']['normalized'],
                                'context': event_text,
                                'year': item.get('year', None)
                            })

        if all_items:
            # Filter by year if a specific year was requested
            year_filtered = [item for item in all_items if item['year'] == int(year)]

            if year_filtered:
                item = random.choice(year_filtered)
                context = f"Event: {item['context']} ({year})"
                return True, item['title'], context, "Feed API (On This Day - exact year match)"
            else:
                # No exact year match, return any event from this day
                item = random.choice(all_items)
                item_year = f" ({item['year']})" if item['year'] else ""
                context = f"Event from this day{item_year}: {item['context']}"
                return True, item['title'], context, "Feed API (On This Day - different year)"

        return False, None, None, None

    except Exception as e:
        print(f"Feed API failed: {e}")
        return False, None, None, None


def try_date_pages_api(date_obj, verify=True):
    """
    Try getting links from Wikipedia's date pages.
    Returns: (success, article_title, context, method_name) or (False, None, None, None)
    """
    try:
        date_page = date_obj.strftime("%B_%-d").replace(" ", "_")

        params = {
            "action": "query",
            "format": "json",
            "prop": "links",
            "titles": date_page,
            "pllimit": "max",
            "plnamespace": "0",
        }

        response = requests.get(WIKIPEDIA_API, params=params, headers=HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()

        pages = data.get('query', {}).get('pages', {})
        links = []

        for page_id, page_data in pages.items():
            if 'links' in page_data:
                links = [link['title'] for link in page_data['links']]
                break

        if links and len(links) >= 10:
            # Try multiple random articles if verification is enabled
            random.shuffle(links)
            max_attempts = 5 if verify else 1

            for article in links[:max_attempts]:
                if verify:
                    print(f"  Checking: {article}")
                    verified, context = verify_date_in_article(article, date_obj)
                    if verified:
                        return True, article, context, "Date Pages API (verified in content)"
                else:
                    return True, article, None, "Date Pages API (unverified)"

            # If no verification succeeded, return first article with warning
            context = f"Linked from '{date_page}' page (date may not appear in article)"
            return True, links[0], context, "Date Pages API (unverified)"

        return False, None, None, None

    except Exception as e:
        print(f"Date Pages API failed: {e}")
        return False, None, None, None


def try_year_search(date_obj):
    """
    Special handler for year-only dates.
    Returns: (success, article_title, context, method_name) or (False, None, None, None)
    """
    try:
        year = date_obj.strftime("%Y")

        # Try getting links from the year page
        params = {
            "action": "query",
            "format": "json",
            "prop": "links",
            "titles": year,
            "pllimit": "max",
            "plnamespace": "0",
        }

        response = requests.get(WIKIPEDIA_API, params=params, headers=HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()

        pages = data.get('query', {}).get('pages', {})
        links = []

        for page_id, page_data in pages.items():
            if 'links' in page_data:
                links = [link['title'] for link in page_data['links']]
                break

        if links:
            article = random.choice(links)
            context = f"Linked from the year {year} page"
            return True, article, context, f"Year Page ({year})"

        # Fallback: Try CirrusSearch for year
        params = {
            "action": "query",
            "format": "json",
            "list": "search",
            "srsearch": f'"{year}" insource:/{year}/',
            "srnamespace": "0",
            "srlimit": "50",
            "srsort": "random",
        }

        response = requests.get(WIKIPEDIA_API, params=params, headers=HEADERS, timeout=30)
        response.raise_for_status()
        data = response.json()

        results = data.get('query', {}).get('search', [])

        if results:
            article = random.choice(results)
            context = f"Contains the year {year}"
            return True, article['title'], context, f"Year Search ({year})"

        return False, None, None, None

    except Exception as e:
        print(f"Year search failed: {e}")
        return False, None, None, None


def find_article_with_date(date_string):
    """
    Find a random Wikipedia article containing the specified date.
    Uses smart hybrid approach based on whether date includes year.
    """
    date_obj = validate_date(date_string)
    has_year = has_year_component(date_string)

    # Check if this is a year-only query
    is_year_only = len(date_string.strip()) == 4 and date_string.strip().isdigit()

    if is_year_only:
        print(f"Searching for articles containing year: {date_obj.strftime('%Y')}\n")
        success, article, context, method = try_year_search(date_obj)
        if success:
            return article, context, method
        print("Year search unsuccessful.\n")
        return None, None, None

    print(f"Searching for articles containing: {date_obj.strftime('%B %d, %Y')}\n")

    # STRATEGY: If user provided a full date with year, prioritize accuracy
    # by searching content first. If just month/day, use curated events.

    if has_year:
        # User wants a specific date - prioritize finding articles that contain it
        print("Specific date requested - searching article content first...\n")

        # Tier 1: CirrusSearch (guarantees date appears in content)
        print("Trying CirrusSearch (content verification)...")
        success, article, context, method = try_cirrus_search(date_obj)
        if success and context:  # Only accept if we have verified context
            return article, context, method
        print("CirrusSearch with verification unsuccessful.\n")

        # Tier 2: Feed API (provides context about why date is relevant)
        print("Trying Feed API (On This Day)...")
        success, article, context, method = try_feed_api(date_obj)
        if success:
            return article, context, method
        print("Feed API returned no results.\n")

        # Tier 3: Date Pages API with verification
        print("Trying Date Pages API with verification...")
        success, article, context, method = try_date_pages_api(date_obj, verify=True)
        if success:
            return article, context, method
        print("Date Pages API unsuccessful.\n")

    else:
        # User wants any event from this day - curated events are fine
        print("General date (no year) - using curated events...\n")

        # Tier 1: Feed API (curated events from any year)
        print("Trying Feed API (On This Day)...")
        success, article, context, method = try_feed_api(date_obj)
        if success:
            return article, context, method
        print("Feed API returned no results.\n")

        # Tier 2: Date Pages API (less verification needed)
        print("Trying Date Pages API...")
        success, article, context, method = try_date_pages_api(date_obj, verify=False)
        if success:
            return article, context, method
        print("Date Pages API unsuccessful.\n")

    return None, None, None


def main():
    parser = argparse.ArgumentParser(
        description="Find a random Wikipedia article that includes a specific date.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python wikipedia_date_finder.py "11/20/1968"
  python wikipedia_date_finder.py "January 15, 2024"
  python wikipedia_date_finder.py "2024-07-04"
  python wikipedia_date_finder.py "1999"

Smart search strategy:
  - Dates with year: Searches content to verify date appears in article
  - Dates without year: Returns curated "On This Day" events
  - Always shows context explaining the date's relevance
        """
    )

    parser.add_argument(
        "date",
        help="Date to search for (formats: YYYY-MM-DD, MM/DD/YYYY, 'Month DD, YYYY', or YYYY for year only)"
    )

    args = parser.parse_args()

    try:
        article, context, method = find_article_with_date(args.date)

        if article:
            print(f"\n{'='*70}")
            print(f"SUCCESS!")
            print(f"{'='*70}")
            print(f"Article: {article}")
            print(f"Method: {method}")
            print(f"URL: https://en.wikipedia.org/wiki/{quote(article.replace(' ', '_'))}")
            if context:
                print(f"\nContext:")
                print(f"{context}")
            print(f"{'='*70}")
            return 0
        else:
            print(f"\n{'='*70}")
            print(f"No article found after trying all methods.")
            print(f"This date may not have significant Wikipedia coverage.")
            print(f"{'='*70}")
            return 1

    except ValueError as e:
        print(f"Error: {e}")
        return 1
    except KeyboardInterrupt:
        print("\n\nSearch interrupted by user.")
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
