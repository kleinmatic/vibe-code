# Republicain

A French Republican almanac for your terminal. Run it at login and it tells
you the date in the calendar of the French Revolution, the decimal time, and
the plant, animal, or tool the day is dedicated to.

```
$ republicain --lang=en
  +--------------------------------------------------------------------------+
  | Today in the French Republican Calendar                                  |
  +-------------------------+----------------------+-------------------------+
  | Date and Time           | Decade               | Rural Almanac           |
  +-------------------------+----------------------+-------------------------+
  | 1 Frimaire (Frost),     | Primidi, day 1 of 10 | Rampion, an edible      |
  | Year CCXXXV             |                      | bellflower              |
  | Decimal time: 7:53:40   |                      |                         |
  +-------------------------+----------------------+-------------------------+
```

It is written in portable C89 and needs nothing but a C compiler and the C
runtime. Python 3 is used only by the tests.

## The calendar, very briefly

Revolutionary France used this calendar from 1793 until Napoleon abolished
it at the end of 1805. Years count from 22 September 1792, the first day of
the Republic.

- A year has twelve months of 30 days, named for the weather and the farm
  year: Vendémiaire (grape harvest), Brumaire (mist), Frimaire (frost),
  and so on.
- Each month has three ten-day weeks called *décades*. The days are
  numbered, not named for gods: primidi, duodi, tridi, up to décadi,
  the rest day.
- Instead of a saint, every day honours something from rural life. Most
  days have a plant or mineral; each fifth day (quintidi) has an animal and
  each tenth (décadi) a tool.
- The five or six days left over at the end of the year are festivals, the
  *Sansculottides*, outside any month or week.
- Time was decimal too: 10 hours in a day, 100 minutes in an hour, 100
  seconds in a minute. Noon is 5:00:00.

Nobody keeps this calendar officially now, so dates after 1805 depend on a
leap-year rule. See [Calendar convention](#calendar-convention) for the one
used here.

## Install

You need a C compiler and GNU make.

```
git clone https://github.com/kleinmatic/vibe-code.git
cd vibe-code/republicain
make
sudo install -m 755 build/linux/republicain /usr/local/bin/republicain
```

On macOS, build with `make TARGET=macos` and install
`build/macos/republicain`. Other systems are covered under
[Build targets](#build-targets). `make test` runs the regression suite.

### Show it at login

To greet every interactive shell, add this to your shell's startup file
(`~/.zshrc`, `~/.bashrc`, or similar):

```
republicain --lang=en
```

To greet SSH logins only, on Linux systems that use PAM, add this line to
`/etc/pam.d/sshd` after the `pam_motd.so` line:

```
session    optional     pam_exec.so type=open_session stdout quiet /usr/local/bin/republicain --lang=en
```

This runs the program fresh at each login, so the decimal time is current
and no cron job or cached file is involved. It is skipped for non-interactive
commands such as `scp`. PAM runs it as root with no terminal attached, so
keep the binary root-owned, and expect plain ASCII at 80 columns.

## Usage

No arguments prints today's bordered table with a full-width title, month
meaning, Roman year, and local decimal clock. Pass a Gregorian date to look
up another day without the live clock.

```
$ republicain --format=line --no-month-gloss 1792-09-22
1 Vendemiaire, an I  -  Primidi ouvre la decade ; a l'honneur : Raisin.  Bonne annee, citoyen!
```

On Linux and macOS the header is bold on a non-dumb terminal, with French
accents in a UTF-8 locale. Redirected output is plain ASCII. To simplify the
display, combine `--format=line`, `--no-month-gloss`, `--no-decimal-time`,
or `--style=plain` as desired.

For scripts, `--format=json` emits one UTF-8 JSON object with stable English
keys, a numeric `year` and a formatted `year_label`. Inapplicable fields are
`null`: for example, a Sansculottides festival has no month or decade.
The `note` field explains the Romme convention on proleptic New Year's
Day and is `null` otherwise. The same note appears in both text layouts.
Run `republicain --help` for option syntax.

French is the default (`--lang=fr`). `--lang=en` translates labels such as
"Year" and "complementary day" and gives the English name of the plant,
animal, or tool, with short descriptions for selected entries. Months,
weekdays, and festivals keep their French names. Years use Roman numerals
in both languages; use `--numerals=arabic` for decimal years.
On Gregorian July 14, both layouts add `Aux armes, citoyens!` for Bastille Day.
Other observances follow Republican month and day: New Year on 1 Vendemiaire,
Dog Day on 5 Nivose, and historical anniversaries labelled with the original
Republican year. These appear in the date cell, the one-line greeting, or
the JSON `greeting` field. Dog Day does not always fall on December 25.

```
$ republicain --lang=en --format=line --no-month-gloss 1792-11-21
1 Frimaire, Year I  -  Primidi opens the ten-day week with a dedication: Rampion, an edible bellflower.
```

## Table layout

For a table with decimal years and shorter month labels:

```
$ republicain --lang=en --no-month-gloss --numerals=arabic 2026-01-03
+-------------------------------------------------------------+
| Today in the French Republican Calendar                     |
+---------------------+-----------------------+---------------+
| Date                | Decade                | Rural Almanac |
+---------------------+-----------------------+---------------+
| 14 Nivose, Year 234 | Quartidi, day 4 of 10 | Sandstone     |
+---------------------+-----------------------+---------------+
```

On complementary days the third column shows the festival instead.
The table ends with one blank line to separate it from the shell prompt.
Table cells wrap inside two-column side margins, splitting long words only
when needed. The live decimal clock and July 14 greeting appear inside the
first cell, headed `Date and Time` when the clock is shown.
If the terminal width is unavailable (including redirected output), the
renderer uses `COLUMNS` or defaults to 80 columns.

For a live login almanac with month meanings, Roman years, and decimal time:

```
republicain --lang=en
```

`--month-gloss` adds a short meaning such as `Frimaire (Frost)` without
replacing the month name. `--decimal-time` samples the local clock once with
the date: midnight is `0:00:00`, noon `5:00:00`, and 11:08 AM `4:63:88`.
It shows a snapshot at login and is only available without a date argument.
A cached MOTD shows the time the cache was generated.

## Build targets

The root GNUmake-compatible Makefile defaults to Linux. Use
`make TARGET=macos` on macOS. `make TARGET=portable` builds the ISO C version
without terminal detection. Each executable is in `build/<target>/`.
`make test` (with the same TARGET if needed) runs the regression suite using
Python 3. The executable itself requires only the C runtime.

Run `make test-special` to check and print an 81-column MOTD for each of the
eight annual greetings, labelled with its Gregorian test date.
`make test-boundaries` performs a slower independent sweep of every supported
Republican year start and end.

On OpenVMS, from the project root:

```
$ SET DEFAULT [.TARGETS.OPENVMS]
$ MMS
$ RUN REPUBLICAIN
```

The OpenVMS recipe and candidate Ultrix and Tru64 profiles still need native
verification. The latter use the plain terminal adapter; try GNU make with
`TARGET=ultrix` or `TARGET=tru64` and an ANSI C compiler.

## Calendar convention

Supported Gregorian dates are 1792-09-22 through 9999-12-31. Historical leap
years are III, VII, and XI. The calendar was abolished during XIV; we finish
that year as a common year. From XV onward we use the proposed Romme
arithmetic convention, not an officially adopted calendar: leap every fourth
Republican year, except centuries not divisible by 400 and multiples of 4000.

French rural names are transcribed from the [French Republican calendar
tables](https://en.wikipedia.org/wiki/French_Republican_calendar#Rural_calendar).
ASCII transliterations and UTF-8 spellings are compiled in; no network or
locale database is needed for plain output.

## License

Copyright (C) 2026 Scott Klein

Republicain is free software, licensed under the GNU General Public License,
version 2. It comes with no warranty. See [LICENSE](LICENSE) for the full
text. This applies to this folder only; the rest of the vibe-code repository
is under its own license.
