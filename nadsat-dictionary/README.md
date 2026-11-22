# Nadsat and Newspeak Dictionary

A command-line tool for two invented languages from fiction:

- **Nadsat**, the teenage slang from Anthony Burgess's *A Clockwork Orange*
- **Newspeak**, the official language of George Orwell's *Nineteen Eighty-Four*

One script, `lexicon`, holds both dictionaries. The `nadsat` and `newspeak`
launchers run it with one dictionary already chosen.

## Usage

```bash
# Get a random word
./nadsat
./newspeak

# Get 3 random words starting with a letter
./nadsat d

# Look up a specific word (case does not matter)
./nadsat droog
./newspeak doubleplusungood
./newspeak "Ministry of Truth"

# Get up to 3 random words with exactly 5 characters
./newspeak --length 5
./newspeak -l 5

# Use the main script and choose a dictionary (default: nadsat)
./lexicon --dict newspeak minitrue
./lexicon -d nadsat horrorshow

# Help and credits
./newspeak --help
./newspeak --version
```

Length is measured against the searchable spelling, including spaces and
punctuation in multi-word or hyphenated entries.

## The Newspeak dictionary

It has 90 entries. Every one appears in the novel. There are no invented
examples. The main use is naming servers, so each term is one word (hyphens
are allowed). The only exceptions are *Big Brother* and *Airstrip One*. A long
name is included only through its abbreviation: *Minitrue* has the meaning of
"Ministry of Truth", and *thinkpol* has the meaning of "Thought Police". Abbreviations are kept only when they work as names.

The entries cover:

- Newspeak words, from both the story and the appendix "The Principles of
  Newspeak" (for example *doublethink*, *crimestop*, *doubleplusungood*,
  *Minitrue*, *Recdep*)
- Jargon from Winston's work orders (*upsub*, *antefiling*, *malreported*)
- Party names for things and organizations (*telescreen*, *versificator*,
  *Spies*, *Brotherhood*)
- Real abbreviations that the appendix gives as models (*Comintern*,
  *Agitprop*, *Inprecorr*)
- People and places (*Big Brother*, *Goldstein*, *Airstrip One*, *Oceania*)

Each entry gives a meaning, notes on how the word was formed, a type, and the
part and chapter where the term first appears.

## Files

| File | Purpose |
|------|---------|
| `lexicon` | The tool. Self-contained, with both dictionaries embedded. |
| `nadsat`, `newspeak` | Launchers that run `lexicon` with one dictionary. |
| `data/nadsat.csv`, `data/newspeak.csv` | The dictionary data. Edit these, not the script. |
| `build.py` | Copies the CSV data into `lexicon` and writes `dictionary.js`. |
| `tools/check_newspeak.py` | Checks every Newspeak term against the novel. |
| `index.html`, `app.js`, `dictionary.js` | Web page (Nadsat only). |
| `test_lexicon.py` | Tests. |

## Editing the dictionaries

```bash
# 1. Edit data/nadsat.csv or data/newspeak.csv
# 2. Copy the data into the script and the web page
python3 build.py
# 3. For Newspeak: confirm every term is in the novel and the chapters are right
python3 tools/check_newspeak.py           # add --fill to fill empty chapter cells
# 4. Run the tests
python3 -m unittest test_lexicon
```

`check_newspeak.py` downloads the novel to `.cache/`, which git ignores.
*Nineteen Eighty-Four* is in the public domain in Australia but not in the
United States, so do not commit the text.

## Installation

The scripts need only Python 3. Make them executable and run:

```bash
chmod +x lexicon nadsat newspeak
./newspeak
```

Keep the launchers in the same folder as `lexicon`.

## Sources

Nadsat data from [Wiktionary](https://en.wiktionary.org/wiki/Appendix:A_Clockwork_Orange),
licensed under Creative Commons Attribution-ShareAlike.

Newspeak terms from George Orwell's *Nineteen Eighty-Four* (1949), checked
against the [Project Gutenberg Australia text](https://gutenberg.net.au/ebooks01/0100021h.html).
The definitions are original summaries written for this tool.

Created with Claude Code.
