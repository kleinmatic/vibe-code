#!/usr/bin/env python3
"""
Script to create a Datawrapper column chart showing annual totals from data-for-claude.csv
"""

import pandas as pd
import datawrapper as dw
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

def main():
    # Read the CSV file
    print("Reading data from data-for-claude.csv...")
    df = pd.read_csv("data-for-claude.csv")

    # Extract year columns (2008 through 2025)
    year_columns = [str(year) for year in range(2008, 2026)]

    # Select only the year columns that exist in the data
    available_years = [col for col in year_columns if col in df.columns]

    print(f"Found year columns: {available_years}")

    # Sum each year column across all organizations
    annual_totals = {}
    for year in available_years:
        total = df[year].sum()
        annual_totals[year] = total
        print(f"{year}: {total}")

    # Create a DataFrame for the chart
    chart_data = pd.DataFrame({
        "Year": list(annual_totals.keys()),
        "Total": list(annual_totals.values())
    })

    print("\nChart data:")
    print(chart_data)

    # Create the ColumnChart
    print("\nCreating Datawrapper ColumnChart...")
    chart = dw.ColumnChart(
        title="Annual Totals (2008-2025)",
        intro="Sum of values across all organizations by year",
        data=chart_data,
        source_name="data-for-claude.csv",
        byline="Created with Datawrapper Python API"
    )

    # Create the chart on Datawrapper (sends data to API)
    print("Sending chart to Datawrapper...")
    chart.create(access_token=ACCESS_TOKEN)

    print(f"Chart created with ID: {chart.chart_id}")

    # Publish the chart
    print("Publishing chart...")
    chart.publish()

    # Get the public URL
    print(f"\n✅ Chart published successfully!")
    print(f"Chart ID: {chart.chart_id}")
    print(f"Editor URL: https://app.datawrapper.de/chart/{chart.chart_id}/edit")

    # Try to get the public URL from the API response
    try:
        from datawrapper import Datawrapper
        client = Datawrapper(access_token=ACCESS_TOKEN)
        chart_info = client.get_chart(chart.chart_id)
        print(f"\nChart Info Keys: {chart_info.keys()}")
        if 'publicUrl' in chart_info:
            print(f"Public URL: {chart_info['publicUrl']}")
        elif 'url' in chart_info:
            print(f"Public URL: {chart_info['url']}")
        else:
            print(f"Available keys in response: {list(chart_info.keys())}")
    except Exception as e:
        print(f"Note: Could not retrieve public URL automatically: {e}")
        print(f"You can view your chart at: https://app.datawrapper.de/chart/{chart.chart_id}/edit")


if __name__ == "__main__":
    main()
