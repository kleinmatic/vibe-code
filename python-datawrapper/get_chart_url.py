#!/usr/bin/env python3
"""
Get the public URL for the created chart
"""

from datawrapper import Datawrapper
import os
import sys

# Get API token from environment variable
ACCESS_TOKEN = os.getenv("DATAWRAPPER_ACCESS_TOKEN")

if not ACCESS_TOKEN:
    print("Error: DATAWRAPPER_ACCESS_TOKEN environment variable not set!")
    print("Please set it with your Datawrapper API token:")
    print("  Windows: set DATAWRAPPER_ACCESS_TOKEN=your_token_here")
    print("  Linux/Mac: export DATAWRAPPER_ACCESS_TOKEN=your_token_here")
    sys.exit(1)

CHART_ID = "aO8Gv"

client = Datawrapper(access_token=ACCESS_TOKEN)
chart_info = client.get_chart(CHART_ID)

print(f"Chart ID: {CHART_ID}")
print(f"Chart Title: {chart_info.get('title', 'N/A')}")
print(f"Editor URL: https://app.datawrapper.de/chart/{CHART_ID}/edit")

if 'publicUrl' in chart_info:
    print(f"Public URL: {chart_info['publicUrl']}")
elif 'url' in chart_info:
    print(f"Public URL: {chart_info['url']}")
else:
    # Print some info about the response to help debug
    print("\nChart metadata keys:")
    for key in sorted(chart_info.keys()):
        if key in ['metadata', 'theme']:
            continue
        print(f"  - {key}: {chart_info[key]}")
