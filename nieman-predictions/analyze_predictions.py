#!/usr/bin/env python3
"""
Helper script to analyze Nieman Lab predictions using an LLM.

This provides utilities to:
- Load all downloaded predictions
- Search predictions by keyword
- Group predictions by year/author
- Prepare text for LLM analysis
"""

import json
from pathlib import Path
from typing import List, Dict, Optional
from collections import defaultdict
from datetime import datetime
import re


class PredictionsAnalyzer:
    """Analyze downloaded Nieman Lab predictions."""

    def __init__(self, predictions_dir: str = "predictions_data"):
        """Initialize analyzer with predictions directory."""
        self.predictions_dir = Path(predictions_dir)
        self.predictions = []
        self.load_predictions()

    def load_predictions(self):
        """Load all prediction JSON files."""
        print(f"Loading predictions from {self.predictions_dir}")

        for json_file in self.predictions_dir.glob("*.json"):
            if json_file.name == "example_prediction.json":
                continue  # Skip example file

            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Only include predictions
                    if data.get('is_prediction', False):
                        self.predictions.append(data)
            except Exception as e:
                print(f"Error loading {json_file}: {e}")

        print(f"Loaded {len(self.predictions)} predictions")

    def get_by_year(self) -> Dict[str, List[Dict]]:
        """Group predictions by year."""
        by_year = defaultdict(list)

        for pred in self.predictions:
            # Extract year from published date or URL
            year = None

            # Try to extract from date
            published = pred.get('published', '')
            if published:
                # Try common date formats
                for pattern in [r'202\d', r'201\d']:
                    match = re.search(pattern, published)
                    if match:
                        year = match.group()
                        break

            # Fallback to URL
            if not year:
                url = pred.get('url', '')
                match = re.search(r'/202\d/', url)
                if match:
                    year = match.group().strip('/')

            if year:
                by_year[year].append(pred)

        return dict(sorted(by_year.items()))

    def get_by_author(self) -> Dict[str, List[Dict]]:
        """Group predictions by author."""
        by_author = defaultdict(list)

        for pred in self.predictions:
            author = pred.get('author', 'Unknown')
            by_author[author].append(pred)

        return dict(sorted(by_author.items()))

    def search(self, keyword: str, in_content: bool = True) -> List[Dict]:
        """Search predictions by keyword."""
        keyword = keyword.lower()
        results = []

        for pred in self.predictions:
            # Search in title
            if keyword in pred.get('title', '').lower():
                results.append(pred)
                continue

            # Search in content if requested
            if in_content:
                content = pred.get('content_text', '').lower()
                if keyword in content:
                    results.append(pred)
                    continue

            # Search in tags
            tags = pred.get('tags', [])
            if any(keyword in tag.lower() for tag in tags):
                results.append(pred)

        return results

    def get_summary_text(self, prediction: Dict, max_length: int = 1000) -> str:
        """Get a summary of a prediction suitable for LLM input."""
        parts = []

        # Basic info
        parts.append(f"Title: {prediction.get('title', 'N/A')}")
        parts.append(f"Author: {prediction.get('author', 'N/A')}")
        parts.append(f"Date: {prediction.get('published', 'N/A')}")
        parts.append(f"URL: {prediction.get('url', 'N/A')}")

        # Tags
        tags = prediction.get('tags', [])
        if tags:
            parts.append(f"Tags: {', '.join(tags)}")

        # Content (truncated if needed)
        content = prediction.get('content_text', '')
        if content:
            if len(content) > max_length:
                content = content[:max_length] + "..."
            parts.append(f"\nContent:\n{content}")

        return "\n".join(parts)

    def export_for_llm(self, output_file: str = "predictions_for_llm.txt",
                       year: Optional[str] = None):
        """Export predictions to a text file formatted for LLM analysis."""
        predictions = self.predictions

        # Filter by year if specified
        if year:
            by_year = self.get_by_year()
            predictions = by_year.get(year, [])

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"NIEMAN LAB PREDICTIONS\n")
            f.write(f"Total predictions: {len(predictions)}\n")
            if year:
                f.write(f"Year: {year}\n")
            f.write("=" * 80 + "\n\n")

            for i, pred in enumerate(predictions, 1):
                f.write(f"\n{'='*80}\n")
                f.write(f"PREDICTION #{i}\n")
                f.write(f"{'='*80}\n\n")
                f.write(self.get_summary_text(pred, max_length=2000))
                f.write("\n\n")

        print(f"Exported {len(predictions)} predictions to {output_file}")

    def print_stats(self):
        """Print statistics about the predictions."""
        print("\n" + "=" * 80)
        print("PREDICTIONS STATISTICS")
        print("=" * 80)

        print(f"\nTotal predictions: {len(self.predictions)}")

        # By year
        by_year = self.get_by_year()
        print(f"\nPredictions by year:")
        for year, preds in by_year.items():
            print(f"  {year}: {len(preds)}")

        # By author (top 10)
        by_author = self.get_by_author()
        print(f"\nTop 10 authors:")
        sorted_authors = sorted(by_author.items(), key=lambda x: len(x[1]), reverse=True)[:10]
        for author, preds in sorted_authors:
            print(f"  {author}: {len(preds)}")

        # Tags
        all_tags = defaultdict(int)
        for pred in self.predictions:
            for tag in pred.get('tags', []):
                all_tags[tag] += 1

        if all_tags:
            print(f"\nTop 10 tags:")
            sorted_tags = sorted(all_tags.items(), key=lambda x: x[1], reverse=True)[:10]
            for tag, count in sorted_tags:
                print(f"  {tag}: {count}")


def main():
    """Main entry point with example usage."""
    analyzer = PredictionsAnalyzer()

    # Print statistics
    analyzer.print_stats()

    # Export all predictions to a single file for LLM analysis
    print("\nExporting all predictions for LLM analysis...")
    analyzer.export_for_llm("all_predictions_for_llm.txt")

    # Export by year
    by_year = analyzer.get_by_year()
    for year in by_year.keys():
        print(f"Exporting {year} predictions...")
        analyzer.export_for_llm(f"predictions_{year}_for_llm.txt", year=year)

    # Example search
    print("\n" + "=" * 80)
    print("Example: Searching for 'AI' predictions...")
    ai_predictions = analyzer.search('AI')
    print(f"Found {len(ai_predictions)} predictions mentioning 'AI'")

    if ai_predictions:
        print("\nFirst result:")
        print(analyzer.get_summary_text(ai_predictions[0], max_length=500))


if __name__ == '__main__':
    main()
