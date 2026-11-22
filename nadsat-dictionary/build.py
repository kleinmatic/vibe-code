#!/usr/bin/env python3
"""
Regenerate the embedded data from data/*.csv.

  - Writes the DICTIONARY_DATA block into `lexicon`.
  - Writes dictionary.js (Nadsat only) for the web page.

The CSV files are the only place to edit dictionary data.
Run: python3 build.py
"""

import csv
import json
from pathlib import Path

HERE = Path(__file__).parent
DATA = HERE / 'data'
SCRIPT = HERE / 'lexicon'
WEB_JS = HERE / 'dictionary.js'

BEGIN = '# BEGIN GENERATED DATA - edit data/*.csv and run build.py\n'
END = '# END GENERATED DATA\n'

# Dictionaries in the order they appear in the script.
DICTIONARY_FILES = ['nadsat', 'newspeak']


def read_rows(name):
    with open(DATA / f'{name}.csv', newline='', encoding='utf-8') as f:
        rows = list(csv.DictReader(f))
    # Drop empty optional columns so each row only carries the fields it uses.
    return [{k: v for k, v in row.items() if v != '' or k == 'Origin'} for row in rows]


def build_script(all_rows):
    lines = [BEGIN, 'DICTIONARY_DATA = {\n']
    for name in DICTIONARY_FILES:
        lines.append(f'    {json.dumps(name)}: [\n')
        for row in all_rows[name]:
            lines.append(f'        {json.dumps(row)},\n')
        lines.append('    ],\n')
    lines.append('}\n')
    lines.append(END)
    block = ''.join(lines)

    src = SCRIPT.read_text(encoding='utf-8')
    start = src.index(BEGIN)
    stop = src.index(END) + len(END)
    new_src = src[:start] + block + src[stop:]
    if new_src != src:
        SCRIPT.write_text(new_src, encoding='utf-8')
        return True
    return False


def build_web_js(all_rows):
    # The web page still uses the original Nadsat field names.
    legacy = [
        {'Nadsat': r['Term'], 'English': r['Meaning'], 'Word origin': r['Origin']}
        for r in all_rows['nadsat']
    ]
    text = 'const DICTIONARY_DATA = ' + json.dumps(legacy, indent=2) + ';\n'
    if not WEB_JS.exists() or WEB_JS.read_text(encoding='utf-8') != text:
        WEB_JS.write_text(text, encoding='utf-8')
        return True
    return False


def main():
    all_rows = {name: read_rows(name) for name in DICTIONARY_FILES}
    for name, rows in all_rows.items():
        print(f'{name}: {len(rows)} rows')
    print('lexicon:', 'updated' if build_script(all_rows) else 'unchanged')
    print('dictionary.js:', 'updated' if build_web_js(all_rows) else 'unchanged')


if __name__ == '__main__':
    main()
