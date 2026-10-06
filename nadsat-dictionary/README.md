# Nadsat Dictionary

A command-line tool for exploring Nadsat, the fictional slang from Anthony Burgess's "A Clockwork Orange". 

## Usage

```bash
# Get a random word
./nadsat

# Get 3 random words starting with a letter
./nadsat d

# Look up a specific word
./nadsat droog

# Get up to 3 random words with exactly 5 characters
./nadsat --length 5

# Short form
./nadsat -l 5
```

Length is measured against the searchable Nadsat spelling, including spaces and
punctuation in multi-word or hyphenated entries.

## Installation

The `nadsat` script is self-contained with an embedded dictionary. Make it executable and run:

```bash
chmod +x nadsat
./nadsat
```

## Sources

Dictionary data from [Wiktionary](https://en.wiktionary.org/wiki/Appendix:A_Clockwork_Orange), licensed under Creative Commons Attribution-ShareAlike.

Created with Claude Code.
