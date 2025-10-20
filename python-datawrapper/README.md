# Datawrapper Annual Totals Chart

This is an example project demonstrating the [datawrapper](https://github.com/chekos/Datawrapper) Python library. It was created by having Claude Code read the library's [documentation](https://datawrapper.readthedocs.io/en/latest/index.html) and then writing working code.

**Credit:** This project uses the excellent [datawrapper Python library](https://github.com/chekos/Datawrapper) by the news apps team at Reuters, which provides a clean Python wrapper for the Datawrapper API.

## What It Does

Creates a column chart visualization of annual totals from `data-for-claude.csv` using the Datawrapper Python API.

## Setup

1. **Install dependencies:**
   ```bash
   pip install datawrapper pandas
   ```

2. **Prepare your data:**

   Create a CSV file named `data-for-claude.csv` in this directory with the following structure:
   - First column: organization names
   - Subsequent columns: years (2008, 2009, 2010, ..., 2025)
   - Each row contains numeric values for each year

   Example:
   ```csv
   org,2008,2009,2010,2011,2012,...,2025
   org1,10,20,30,40,50,...,100
   org2,5,15,25,35,45,...,90
   ```

3. **Get a Datawrapper API token:**
   - Log in to [Datawrapper](https://www.datawrapper.de/)
   - Go to Settings → API Tokens
   - Click "Create new token"
   - Select scopes: **Chart, Folder, Theme, Visualization** (these were tested and work)
   - Copy the token

4. **Set the environment variable:**

   **Windows (Command Prompt):**
   ```cmd
   set DATAWRAPPER_ACCESS_TOKEN=your_token_here
   ```

   **Windows (PowerShell):**
   ```powershell
   $env:DATAWRAPPER_ACCESS_TOKEN="your_token_here"
   ```

   **Linux/Mac:**
   ```bash
   export DATAWRAPPER_ACCESS_TOKEN=your_token_here
   ```

## Usage

### Create and publish a new chart:

```bash
python create_annual_totals_chart.py
```

This script will:
- Read `data-for-claude.csv`
- Sum values for each year (2008-2025) across all organizations
- Create a column chart on Datawrapper
- Publish the chart and display the public URL

### Get URL for existing chart:

```bash
python get_chart_url.py
```

This retrieves the public URL for the already-created chart (ID: aO8Gv).

## Security

**IMPORTANT:** Never commit sensitive data to version control!

- API tokens are loaded from the `DATAWRAPPER_ACCESS_TOKEN` environment variable
- No credentials are stored in the code files
- The token is only valid for your session
- `data-for-claude.csv` is excluded from git commits via `.gitignore` to protect your data

## Chart Output

The generated chart shows annual totals from 2008-2025:
- **Peak**: 2016 with 2,097 total
- **Latest**: 2025 with 243 total

**Public Chart URL:** https://datawrapper.dwcdn.net/aO8Gv/1/
