#!/usr/bin/env python3
"""
Check data/newspeak.csv against the text of Nineteen Eighty-Four.

Every searchable form of every term must appear in the novel. The
"First appearance" column must name a part and chapter where the term occurs.

  python3 tools/check_newspeak.py          # check; exit 1 on any problem
  python3 tools/check_newspeak.py --fill   # also fill empty First appearance cells

The novel is in the public domain in Australia but not in the United States,
so this script downloads it to .cache/ (git-ignored). Do not commit the text.

Matching rules: terms with a capital letter match case-sensitively, or in all
capitals (the appendix prints Newspeak words in capitals). Lower-case terms
match in any case. A filled-in First appearance is kept if the term occurs
there, so a cell can name the first use in the Newspeak sense when the
same spelling appears earlier as an ordinary English word.
"""

import csv
import html
import importlib.machinery
import importlib.util
import re
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
SOURCE_URL = 'https://gutenberg.net.au/ebooks01/0100021h.html'
CACHE = HERE / '.cache' / '1984.html'
CSV_PATH = HERE / 'data' / 'newspeak.csv'
PARTS = {'ONE': 1, 'TWO': 2, 'THREE': 3}


def load_lexicon():
    path = str(HERE / 'lexicon')
    loader = importlib.machinery.SourceFileLoader('lexicon', path)
    spec = importlib.util.spec_from_loader('lexicon', loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def fetch_text():
    if not CACHE.exists():
        CACHE.parent.mkdir(exist_ok=True)
        req = urllib.request.Request(SOURCE_URL, headers={'User-Agent': 'lexicon-check'})
        with urllib.request.urlopen(req, timeout=60) as resp:
            CACHE.write_bytes(resp.read())
    return CACHE.read_text(encoding='latin-1')


def sections(raw_html):
    """Split the novel into (location, text) pairs, in reading order."""
    out = []
    location, buf = None, []
    part = None

    def flush():
        if location and buf:
            text = html.unescape(re.sub(r'<[^>]+>', ' ', ' '.join(buf)))
            out.append((location, re.sub(r'\s+', ' ', text)))

    for line in raw_html.split('\n'):
        m_part = re.search(r'<h1>PART (ONE|TWO|THREE)</h1>', line)
        m_ch = re.search(r'<h2><a name="ch\d+"></a>Chapter (\d+)', line)
        m_app = re.search(r'<h2><a name="ch\d+"></a>APPENDIX', line)
        if m_part:
            part = PARTS[m_part.group(1)]
            continue
        if part and (m_ch or m_app):
            flush()
            buf = []
            location = f'Part {part}, Ch {m_ch.group(1)}' if m_ch else 'Appendix'
            continue
        if location:
            buf.append(line)
    flush()
    return out


def _regex(form):
    body = r'\s+'.join(re.escape(w) for w in form.split())
    return r'(?<![A-Za-z])' + body + r'(?![A-Za-z])'


def pattern_for(form):
    if form != form.lower():
        return re.compile(f'{_regex(form)}|{_regex(form.upper())}')
    return re.compile(_regex(form), re.IGNORECASE)


def locations_of(form, secs):
    pat = pattern_for(form)
    return [loc for loc, text in secs if pat.search(text)]


def main():
    fill = '--fill' in sys.argv[1:]
    lexicon = load_lexicon()
    secs = sections(fetch_text())

    with open(CSV_PATH, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames
        rows = list(reader)

    problems = 0
    for row in rows:
        term = row['Term']
        all_locs = []
        for form in lexicon.searchable_forms(term):
            locs = locations_of(form, secs)
            if not locs:
                print(f'NOT IN TEXT: {form!r} (from {term!r})')
                problems += 1
            all_locs.extend(locs)

        order = [loc for loc, _ in secs]
        first = min(all_locs, key=order.index) if all_locs else ''
        stated = row.get('First appearance', '')

        if not stated:
            if fill and first:
                row['First appearance'] = first
            else:
                print(f'NO FIRST APPEARANCE: {term!r} (text suggests {first or "none"})')
                problems += 1
        elif stated not in all_locs:
            print(f'WRONG FIRST APPEARANCE: {term!r} says {stated!r}, '
                  f'but it occurs in: {", ".join(dict.fromkeys(all_locs)) or "nowhere"}')
            problems += 1

    if fill:
        with open(CSV_PATH, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)

    print(f'{len(rows)} terms checked, {problems} problem(s).')
    sys.exit(1 if problems else 0)


if __name__ == '__main__':
    main()
