# Working on Republicain

Republicain is a French Republican almanac for a terminal login message
(MOTD). Its job is to give you the date **and something worth reading about
that day**. The default is the full almanac; flags make it simpler. See
`README.md` for usage. `PLAN.md` records the original OpenVMS proof of
concept, not the current defaults.

## Where changes belong

- `shared/src/calendar.c` converts a validated Gregorian civil date to a
  Republican year and zero-based day of year. Keep this integer arithmetic
  independent of the clock, time zones, display language, and OS.
- `shared/src/names.c` holds names, month meanings, festivals, and Republican
  observances; `shared/src/rural_en.inc` holds the English rural entries in
  calendar order. `shared/src/main.c` handles the CLI and the three renderers.
- `shared/include/republicain/` defines the interfaces. `shared/adapters/`
  contains reusable implementations for the clock and terminal. Keep private
  headers, libraries, compiler settings, and recipes unique to one OS under
  `targets/<target>/`; do not fork the calendar for a new target.
  Keep named Ultrix and Tru64 profiles even while they select the same
  adapter as `portable`: they are entry points for future native ports,
  not claims that those ports have been tested.
- Write portable C89. Keep sources, headers, build files, and test fixtures
  7-bit ASCII; use the existing escaped UTF-8 literals for accented text.
  The executable needs no third-party libraries. Python 3 is for tests only.

## Calendar decisions

- Supported input runs from 1792-09-22 (1 Vendemiaire, an I) to 9999-12-31.
  Historical leap years are III, VII, and XI. The calendar was abolished
  during XIV; we finish XIV as a common year.
- From XV on, use the proposed Romme arithmetic rule: leap years are
  divisible by 4, except centuries not divisible by 400 and multiples of
  4000. We do not calculate the Paris equinox. Do not assume Republican New
  Year always falls on September 22. Explain this choice on New Year's Day
  rather than adding a disclaimer to every MOTD.
- Twelve 30-day months each contain three ten-day weeks (*decades*).
  Quintidi honours an animal; decadi is the rest day and honours a tool.
  Ordinals 360 onward are the five or six Sansculottides: show the festival
  and complementary day number, with no month, weekday, or decade.
- Take the live date and clock from one local-time snapshot. Decimal time
  divides a civil day into 10 hours of 100 minutes of 100 seconds; local
  noon is `5:00:00`. A `YYYY-MM-DD` lookup has no live clock.

## Display decisions

- Default to French, a bordered three-column table, Roman years, month
  meanings, decimal time, and automatic terminal styling. English changes
  the language, not the defaults. Use `an CCXXXIV` or `Year CCXXXIV` in a
  displayed date; `--numerals=arabic` changes the numeral, not the label.
- Keep month, decade-day, and festival names French. A month meaning is a
  gloss, not a replacement: `Frimaire (Frost)`. In English, translate the
  rural item and explain unfamiliar ones: `Rampion, an edible bellflower`.
- Give the table a localized full-width title. The first cell holds the
  date, then decimal time if live, then any anniversary greeting. Keep the
  greeting **inside that cell, without a blank spacer row**. The other two
  cells explain the decade and rural dedication (or festival).
- An 81-column terminal is a real use case. Wrap cells within their
  visible widths, including borders and two-column side margins where they
  fit. Accented letters count as one display cell. Use the detected width,
  then `COLUMNS`, then 80. Keep the narrow stacked fallback. Use ASCII
  borders everywhere; redirected human-readable output has no ANSI or UTF-8
  requirement.
- Keep `--format=line` for a compact greeting and `--format=json` for
  scripts. JSON is UTF-8 with stable English keys, a numeric `year`, a
  formatted `year_label`, and `null` for inapplicable fields.

## Adding an observance

Use the Republican month and day for recurring greetings. For a one-time
historical event, include its original Republican year in the message and
start showing anniversaries only in that year. Keep English copy in
headline style: `Year II: Marie Antoinette executed.` Distinguish 18
Brumaire's end of the Directory from the later end of the Republic.

Bastille Day is the exception: `Aux armes, citoyens!` follows **Gregorian
July 14**. Dog Day follows **5 Nivose**, not a fixed December 25. Check the
greeting in the date cell, line output, and JSON `greeting` field. Add a
dated case to `tests/special_days.py` so the visual gallery stays complete.

## Build and verify

```sh
make                         # build/linux/republicain
make test                    # regression suite, including the gallery
make test-special            # print and check each special-day table
make TARGET=portable test CFLAGS='-std=c89 -pedantic-errors -Wall -Wextra'
```

Linux and the plain ISO C profile have been tested locally. macOS has a
POSIX profile; OpenVMS has native `targets/openvms/DESCRIP.MMS`. Ultrix and
Tru64 are prospective targets. A successful Linux build is not native
verification of any of these systems. When changing the CLI or display,
update `README.md` examples and `tests/check.py` alongside the implementation.
