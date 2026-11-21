"""Independently check every supported year boundary via the public CLI."""
import datetime
import json
import subprocess
import sys


def check(date, year, first, complementary):
    data = json.loads(subprocess.check_output([sys.argv[1], "--format=json", date.isoformat()]))
    actual = (data["year"], data["month"], data["day"], data["complementary_day"])
    expected = (year, "Vend\u00e9miaire" if first else None, 1 if first else None, complementary)
    assert actual == expected, (date, expected, actual)


def check_boundaries():
    start = datetime.date(1792, 9, 22).toordinal()
    limit = datetime.date.max.toordinal()
    year = 1
    while start <= limit:
        check(datetime.date.fromordinal(start), year, True, None)
        leap = year in (3, 7, 11) if year <= 14 else (
            year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) and year % 4000 != 0)
        start += 365 + leap
        if start - 1 <= limit:
            check(datetime.date.fromordinal(start - 1), year, False, 5 + leap)
        year += 1
    print(f"Checked all supported year boundaries ({year - 1} Republican years).")


check_boundaries()
