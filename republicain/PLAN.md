# Republicain: OpenVMS proof-of-concept plan

## Goal

Build a small portable command-line application that reads the current
local civil date, converts it to the French Republican calendar, and prints:

- the Republican weekday, day, month, and year;
- the rural-calendar item commemorated on that day (usually a plant/crop, with
  animals on quintidi and tools on decadi);
- the named civic festival on complementary days.

Example shape (exact wording to be finalized):

    7 Fructidor, an CCXXXIV (septidi) - Sucrion

The no-argument invocation should work as a message of the day (MOTD):
print one newline-terminated line to standard output so a login script can
display it directly. OpenVMS is a first-class target; the same C sources
should also build on Unix-like systems, Windows, and other hosted C platforms.

## Technical direction

- Language: portable ISO C (C89-compatible where practical), suitable for the
  VSI/HP OpenVMS C compiler and easy to exercise on Unix-like development hosts.
- Runtime: standard C date/time facilities only; no third-party libraries.
- Build: an OpenVMS `DESCRIP.MMS` file plus a small portable Makefile for local
  development and tests.
- Character compatibility: source files, build files, and default output will
  be strictly 7-bit ASCII. French names will use ASCII transliterations such
  as `Vendemiaire`, `Nivose`, `Floreal`, and `decadi`. The program will not
  depend on Unicode, UTF-8 locales, wide-character APIs, or Unicode-capable
  terminals, so it remains usable on OpenVMS versions that pre-date Unicode.
- Keep display strings isolated in one table module so a future optional DEC
  Multinational Character Set or ISO-8859-1 table can be added without changing
  the calendar logic. Such a table will not be required for the proof of
  concept or enabled by default.

## Calendar policy

The historical calendar began on 22 September 1792. Historical years I-XIV
will follow their actual year boundaries. For later, proleptic dates, the first
implementation will use the Romme arithmetic proposal: Republican years
divisible by 4 are leap years, with Gregorian century exceptions and year 4000
also common. This is deterministic and suitable for a program, but it was
proposed rather than formally adopted; the README and output documentation must
say so.

The implementation will avoid platform-dependent `time_t` arithmetic for date
conversion. Instead it will convert Gregorian dates to an integer day number,
then locate the Republican year and day within that year. This also makes tests
reproducible across OpenVMS architectures and Unix hosts.

## Proposed layout

    republicain/
      README.md
      PLAN.md
      shared/
        include/republicain/   public types and platform interface
        src/                   CLI, calendar arithmetic, rural-day tables
        adapters/              reusable ISO C clock implementation
      targets/
        linux/
        openvms/               includes native DESCRIP.MMS when implemented
        ultrix/                prospective
        tru64/                 prospective
      tests/
        test_calendar.c
      Makefile

Each build compiles the same shared core and selects exactly one clock
implementation. Use the ISO C adapter by default. Put private headers, adapter
overrides, platform libraries, and native build settings under the owning
target; never add another target's include or library directory to a build.
The root Makefile will be the convenience entry point for local builds.

## Implementation stages

1. Define the calendar API and a result structure containing Republican year,
   month/day or complementary day, decade weekday, and rural-calendar label.
2. Implement Gregorian-to-integer-day conversion and Republican year/day
   conversion under the documented leap-year policy.
3. Add the twelve month names, ten decade-day names, 360 rural-calendar labels,
   and six complementary-day festival names as static read-only tables.
4. Implement the CLI: no arguments means today's local date; an optional
   `YYYY-MM-DD` argument enables testing and useful historical queries.
5. Add native OpenVMS and portable local build recipes, including the OpenVMS
   `RUN REPUBLICAIN` invocation.
6. Add an automated check that rejects bytes outside the 7-bit ASCII range in
   source, headers, build files, and test fixtures.
7. Test, document, and verify on an available C compiler; record any remaining
   OpenVMS-specific verification needed if no OpenVMS host is available.

## Acceptance checks

- Epoch: 1792-09-22 converts to 1 Vendemiaire, year I, and the expected rural
  entry (Raisin).
- Known historical boundaries and observed leap years III, VII, and XI convert
  correctly.
- All 360 ordinary days select the correct rural-calendar entry; days ending in
  5 are animals and days ending in 0 are tools.
- Complementary days select the correct festival; the sixth exists only in a
  leap year.
- Invalid Gregorian input and pre-epoch dates fail with a clear message and a
  nonzero status.
- All required project and runtime text is valid 7-bit ASCII, and execution does
  not require Unicode support or locale configuration.
- The same test vectors pass in the local development build and on OpenVMS.

## Reference

- https://en.wikipedia.org/wiki/French_Republican_calendar
