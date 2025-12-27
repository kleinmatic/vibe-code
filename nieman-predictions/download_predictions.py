#!/usr/bin/env python3
"""
Download Nieman Lab predictions articles with metadata.

This script:
1. Fetches articles from RSS feeds (main feed and tag feed)
2. Attempts to scrape collection pages for article URLs
3. Downloads individual articles with full content and metadata
4. Saves each article as a separate JSON file
"""

import os
import json
import time
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse

import feedparser
import requests
from bs4 import BeautifulSoup


class NiemanPredictionsDownloader:
    """Download and save Nieman Lab predictions articles."""

    RSS_FEEDS = [
        "https://feeds.feedburner.com/NiemanJournalismLab",
        "https://www.niemanlab.org/tag/predictions/feed/",
    ]

    # Collection pages for each year
    COLLECTION_URLS = [
        "https://www.niemanlab.org/collection/predictions-2026/",
        "https://www.niemanlab.org/collection/predictions-2025/",
        "https://www.niemanlab.org/collection/predictions-2024/",
        "https://www.niemanlab.org/collection/predictions-2023/",
        "https://www.niemanlab.org/collection/predictions-2022/",
        "https://www.niemanlab.org/collection/predictions-2021/",
        "https://www.niemanlab.org/collection/predictions-2020/",
        "https://www.niemanlab.org/collection/predictions-2019/",
        "https://www.niemanlab.org/collection/predictions-2018/",
        "https://www.niemanlab.org/collection/predictions-2017/",
    ]

    def __init__(self, output_dir: str = "predictions_data"):
        """Initialize downloader with output directory."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.session = requests.Session()
        # Use browser-like headers to avoid being blocked
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        self.article_urls = set()
        self.downloaded = set()

    def fetch_rss_feeds(self) -> List[Dict]:
        """Fetch articles from all RSS feeds."""
        articles = []

        for feed_url in self.RSS_FEEDS:
            print(f"Fetching RSS feed: {feed_url}")
            try:
                feed = feedparser.parse(feed_url)
                for entry in feed.entries:
                    article_url = entry.get('link', '')
                    if article_url:
                        self.article_urls.add(article_url)
                        articles.append({
                            'url': article_url,
                            'title': entry.get('title', ''),
                            'author': entry.get('author', entry.get('dc_creator', '')),
                            'published': entry.get('published', ''),
                            'summary': entry.get('summary', ''),
                            'categories': [cat.get('term', '') for cat in entry.get('tags', [])],
                        })
                print(f"  Found {len(feed.entries)} articles")
            except Exception as e:
                print(f"  Error fetching RSS feed: {e}")

        return articles

    def scrape_collection_page(self, collection_url: str) -> List[str]:
        """Scrape article URLs from a collection page."""
        article_urls = []

        try:
            print(f"Fetching collection page: {collection_url}")
            response = self.session.get(collection_url, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # Look for article links - try multiple selectors
            # Typical patterns: links within article elements, h2/h3 headings, etc.
            for selector in [
                'article a[href*="/202"]',  # Links in article elements
                '.post a[href*="/202"]',     # Links in post elements
                'h2 a[href*="/202"]',        # Links in h2 headings
                'h3 a[href*="/202"]',        # Links in h3 headings
                'a[href*="niemanlab.org/202"]',  # Any Nieman Lab article links
            ]:
                links = soup.select(selector)
                for link in links:
                    href = link.get('href', '')
                    if href and '/202' in href:  # Articles from 2020s
                        # Ensure absolute URL
                        abs_url = urljoin(collection_url, href)
                        # Filter out non-article pages (like /collection/, /tag/, /author/)
                        if '/collection/' not in abs_url and '/tag/' not in abs_url and '/author/' not in abs_url:
                            article_urls.append(abs_url)

            # Remove duplicates while preserving order
            article_urls = list(dict.fromkeys(article_urls))
            print(f"  Found {len(article_urls)} article URLs")

        except Exception as e:
            print(f"  Error scraping collection page: {e}")

        return article_urls

    def fetch_article_content(self, url: str) -> Optional[Dict]:
        """Fetch full article content and metadata from individual article page."""
        try:
            print(f"  Fetching: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract metadata
            article_data = {
                'url': url,
                'fetched_at': datetime.utcnow().isoformat(),
            }

            # Title
            title_tag = soup.find('h1') or soup.find('title')
            if title_tag:
                article_data['title'] = title_tag.get_text(strip=True)

            # Author
            author_selectors = [
                'meta[name="author"]',
                'meta[property="article:author"]',
                '.author',
                '.byline',
                '[rel="author"]',
            ]
            for selector in author_selectors:
                author_tag = soup.select_one(selector)
                if author_tag:
                    article_data['author'] = author_tag.get('content') or author_tag.get_text(strip=True)
                    break

            # Published date
            date_selectors = [
                'meta[property="article:published_time"]',
                'meta[name="publication_date"]',
                'time[datetime]',
                '.published',
                '.post-date',
            ]
            for selector in date_selectors:
                date_tag = soup.select_one(selector)
                if date_tag:
                    article_data['published'] = date_tag.get('content') or date_tag.get('datetime') or date_tag.get_text(strip=True)
                    break

            # Tags/Categories
            tags = []
            for tag_link in soup.select('a[rel="tag"], .tags a, .categories a'):
                tag_text = tag_link.get_text(strip=True)
                if tag_text:
                    tags.append(tag_text)
            if tags:
                article_data['tags'] = tags

            # Main content
            content_selectors = [
                'article .entry-content',
                '.post-content',
                '.article-content',
                'article',
                '.content',
            ]
            content = None
            for selector in content_selectors:
                content_tag = soup.select_one(selector)
                if content_tag:
                    content = content_tag
                    break

            if content:
                # Get both HTML and plain text versions
                article_data['content_html'] = str(content)
                article_data['content_text'] = content.get_text(separator='\n', strip=True)

            # Meta description
            meta_desc = soup.find('meta', {'name': 'description'}) or soup.find('meta', {'property': 'og:description'})
            if meta_desc:
                article_data['description'] = meta_desc.get('content', '')

            # Check if this is a predictions article
            article_data['is_prediction'] = self.is_prediction_article(article_data)

            return article_data

        except Exception as e:
            print(f"  Error fetching article {url}: {e}")
            return None

    def is_prediction_article(self, article_data: Dict) -> bool:
        """Determine if an article is a prediction article."""
        # Check URL
        if '/collection/predictions-' in article_data.get('url', ''):
            return True

        # Check tags
        tags = article_data.get('tags', [])
        if any('prediction' in tag.lower() for tag in tags):
            return True

        # Check title
        title = article_data.get('title', '').lower()
        if 'prediction' in title or 'my forecast' in title or 'what\'s next' in title:
            return True

        # Check content for prediction indicators
        content = article_data.get('content_text', '').lower()
        if content:
            prediction_phrases = ['my prediction for', 'i predict that', 'what i expect in', 'forecast for']
            if any(phrase in content[:500] for phrase in prediction_phrases):
                return True

        return False

    def save_article(self, article_data: Dict):
        """Save article to a JSON file."""
        # Create filename from URL
        url_path = urlparse(article_data['url']).path
        filename = url_path.strip('/').replace('/', '_') + '.json'
        filepath = self.output_dir / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(article_data, f, indent=2, ensure_ascii=False)

        print(f"  Saved: {filepath}")

    def download_all(self):
        """Download all predictions articles."""
        print("=" * 80)
        print("NIEMAN LAB PREDICTIONS DOWNLOADER")
        print("=" * 80)

        # Step 1: Get articles from RSS feeds
        print("\n[1/3] Fetching RSS feeds...")
        rss_articles = self.fetch_rss_feeds()
        print(f"Total unique URLs from RSS: {len(self.article_urls)}")

        # Step 2: Scrape collection pages for more article URLs
        print("\n[2/3] Scraping collection pages...")
        for collection_url in self.COLLECTION_URLS:
            urls = self.scrape_collection_page(collection_url)
            self.article_urls.update(urls)
            time.sleep(1)  # Be respectful with rate limiting

        print(f"Total unique article URLs: {len(self.article_urls)}")

        # Step 3: Download individual articles
        print(f"\n[3/3] Downloading {len(self.article_urls)} articles...")
        successful = 0
        failed = 0

        for i, url in enumerate(sorted(self.article_urls), 1):
            print(f"\n[{i}/{len(self.article_urls)}]", end=" ")
            article_data = self.fetch_article_content(url)

            if article_data:
                self.save_article(article_data)
                successful += 1
            else:
                failed += 1

            # Rate limiting - be respectful
            time.sleep(2)

        # Summary
        print("\n" + "=" * 80)
        print("DOWNLOAD COMPLETE")
        print("=" * 80)
        print(f"Successfully downloaded: {successful}")
        print(f"Failed: {failed}")
        print(f"Total articles: {len(self.article_urls)}")
        print(f"Output directory: {self.output_dir.absolute()}")

        # Count predictions
        prediction_count = 0
        for file in self.output_dir.glob('*.json'):
            with open(file, 'r') as f:
                data = json.load(f)
                if data.get('is_prediction', False):
                    prediction_count += 1

        print(f"Articles identified as predictions: {prediction_count}")


def main():
    """Main entry point."""
    downloader = NiemanPredictionsDownloader()
    downloader.download_all()


if __name__ == '__main__':
    main()
