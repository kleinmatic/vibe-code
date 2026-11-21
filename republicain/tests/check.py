"""Run from the source root. Python is needed only for this test runner."""
import datetime
import json
import os
import time
from pathlib import Path
import subprocess
import sys

exe = sys.argv[1]


def line(*args):
    data = subprocess.check_output([exe, "--format=line", "--no-month-gloss", "--no-decimal-time", *args])
    assert data.endswith(b"\n") and data.count(b"\n") == 1
    assert b"\033" not in data
    return data.decode("ascii").rstrip("\n")


epoch = datetime.date(1792, 9, 22)
def check_review_cases():
    help_result = subprocess.run([exe, "--help"], capture_output=True, check=True)
    assert help_result.stdout.startswith(b"Usage:") and not help_result.stderr
    for date, has_note in [("1805-09-23", False), ("1806-09-23", True), ("1806-09-24", False)]:
        note = json.loads(subprocess.check_output([exe, "--format=json", "--lang=en", date]))["note"]
        assert bool(note) == has_note, date
        assert ("Romme" in line("--lang=en", date)) == has_note, date
    narrow = subprocess.check_output([exe, "--lang=en", "2026-07-14"], env=dict(os.environ, COLUMNS="40"))
    assert b"(Harvest)," in narrow and b"citoyens!" in narrow
    wide = subprocess.check_output([exe, "--lang=en", "1792-10-01"], env=dict(os.environ, COLUMNS="180"))
    assert b"rest day of the first ten-day week" in wide
    assert b"Heure decimale : " in subprocess.check_output([exe, "--format=line"])


check_review_cases()
for width in [81, 40, 13, 9]:
    rows = subprocess.check_output([exe, "--lang=en", "2026-11-21"],
                                  env=dict(os.environ, COLUMNS=str(width))).decode("ascii").rstrip("\n").splitlines()
    margin = 2 if width >= 17 else 0
    assert all(row.startswith(" " * margin) and len(row) <= width-margin for row in rows)
    if width >= 13:
        assert len(set(map(len, rows))) == 1
        rules = [i for i, row in enumerate(rows) if row.lstrip().startswith("+")]
        body = rows[rules[2]+1:-1]
        values = ["".join(row.split("|")[col].replace(" ", "") for row in body)
                  for col in range(1, 4)]
        assert values == ["1Frimaire(Frost),YearCCXXXV", "Primidi,day1of10", "Rampion,anediblebellflower"]
assert subprocess.check_output([exe, "--format=table", "--no-month-gloss", "--lang=en", "--numerals=arabic", "2026-01-03"]) == (
    b"  +-------------------------------------------------------------+\n"
    b"  | Today in the French Republican Calendar                     |\n"
    b"  +---------------------+-----------------------+---------------+\n"
    b"  | Date                | Decade                | Rural Almanac |\n"
    b"  +---------------------+-----------------------+---------------+\n"
    b"  | 14 Nivose, Year 234 | Quartidi, day 4 of 10 | Sandstone     |\n"
    b"  +---------------------+-----------------------+---------------+\n\n")
festival = subprocess.check_output([exe, "--format=table", "--lang=en", "1795-09-22"])
festival_body = festival.rstrip(b"\n").splitlines()[5:-1]
assert b"day 6 of 6" in b" ".join(r.split(b"|")[1].strip() for r in festival_body)
assert b" ".join(r.split(b"|")[2].strip() for r in festival_body).strip() == b"Outside the ten-day week"
assert b" ".join(r.split(b"|")[3].strip() for r in festival_body).strip() == b"Fete de la Revolution"
assert line("--lang=en", "--month-gloss", "2026-11-21").startswith("1 Frimaire (Frost), Year CCXXXV")
assert line("--lang=en", "2026-07-14").endswith("  Aux armes, citoyens!")
holiday = subprocess.check_output([exe, "--format=table", "2024-07-14"]).rstrip(b"\n").splitlines()
assert holiday[-2].split(b"|")[1].strip() == b"Aux armes, citoyens!"
assert holiday[-1].strip().startswith(b"+")
assert "Aux armes" not in line("2026-07-13")
assert line("--month-gloss", "1795-09-22") == line("1795-09-22")
# Compare the live snapshot with the civil clock in a known non-UTC zone.
start = int(time.time())
clock_output = subprocess.check_output([exe, "--lang=en"],
                                       env=dict(os.environ, TZ="EST5")).decode("ascii")
possible = [((s - 5 * 3600) % 86400) * 100000 // 86400
            for s in range(start, int(time.time()) + 1)]
clock_rows = clock_output.splitlines()
assert clock_rows[3].split("|")[1].strip() == "Date and Time"
clock_cell = " ".join(row.split("|")[1].strip() for row in clock_rows[5:] if row.lstrip().startswith("|"))
lookup = subprocess.check_output([exe, "2026-11-21"])
assert b"Aujourd'hui dans le calendrier republicain francais" in lookup
data = json.loads(subprocess.check_output([exe, "--format=json", "--lang=en", "2026-07-14"]))
assert data["greeting"] == "Aux armes, citoyens!" and data["day_of_decade"] == 6
assert data["year_label"] == "CCXXXIV" and data["year"] == 234 and data["decimal_time"] is None
data = json.loads(subprocess.check_output([exe, "--format=json", "1795-09-22"]))
assert data["complementary_day"] == 6 and data["decade"] is None and data["festival"]
assert b"an CCXXXV" in lookup and b"Heure decimale" not in lookup
assert any("Decimal time: %d:%02d:%02d" %
            (v // 10000, v // 100 % 100, v % 100) in clock_cell for v in possible)
assert line(epoch.isoformat()) == "1 Vendemiaire, an I  -  Primidi ouvre la decade ; a l'honneur : Raisin.  Bonne annee, citoyen!"
for date, phrase in [
    ("1793-01-21", "Year I: Louis XVI"),
    ("1793-10-16", "Year II: Marie Antoinette"),
    ("1794-06-08", "Year II: Festival of the Supreme Being"),
    ("1794-07-28", "Year II: Robespierre"),
    ("1799-11-09", "Year VIII: Bonaparte"),
    ("1792-12-25", "Joyeux Jour du Chien!"),
    ("1800-11-09", "Year VIII: Bonaparte"),
]:
    assert phrase in line("--lang=en", date), date
assert "Bonaparte" not in line("--lang=en", "1792-11-08")
assert line("--style=auto", epoch.isoformat()) == line(epoch.isoformat())
assert line("--lang=fr", epoch.isoformat()) == line(epoch.isoformat())
assert line("--lang=en", "1792-11-21") == (
    "1 Frimaire, Year I  -  Primidi opens the ten-day week with a dedication: Rampion, an edible bellflower.")
assert line("--lang=fr", "1792-11-21").endswith("a l'honneur : Raiponce.")
assert "rest day" in line("--lang=en", "1792-11-20")
assert "day 5 of the ten-day week, honours an animal: Horse." in line("--lang=en", "1792-09-26")
assert "day 7 of the ten-day week" in line("--lang=en", "1792-09-28")
assert line("--numerals=roman", epoch.isoformat()) == line(epoch.isoformat())
assert line("--numerals=arabic", "1805-09-23").startswith("1 Vendemiaire, an 14  -  ")
assert line("--style=auto", "1795-09-22", "--lang=en") == (
    "complementary day 6, Year III  -  Outside the ten-day week, the calendar celebrates Fete de la Revolution.")
assert line("--numerals=roman", "--lang=en", "1795-09-22").startswith("complementary day 6, Year III ")
assert line("--lang=en", "--numerals=arabic", "1795-09-22").startswith("complementary day 6, Year 3 ")
labels = {line((epoch + datetime.timedelta(days=i)).isoformat()).rsplit(" : ", 1)[1]
          for i in range(360)}
assert len(labels) == 360 and "" not in labels
for date, expected in [
    ("1793-09-21", "jour complementaire 5, an I"),
    ("1795-09-22", "jour complementaire 6, an III"),
    ("1799-09-23", "1 Vendemiaire, an VIII"),
    ("1803-09-24", "1 Vendemiaire, an XII"),
    ("1805-09-23", "1 Vendemiaire, an XIV"),
    ("1808-09-22", "jour complementaire 6, an XVI"),
]:
    assert line(date).split("  -  ")[0] == expected, (date, line(date))
for bad in ["1792-09-21", "1900-02-29", "2024-04-31", "2020-00-00",
            "2020-13-01", "2000-2-29", "2000-02-29!", "--bad", "--lang=zz"]:
    result = subprocess.run([exe, bad], capture_output=True)
    assert result.returncode and result.stderr and not result.stdout
assert line("2000-02-29") and line("9999-12-31") and line()
for root in ["shared", "targets", "tests", "Makefile"]:
    path = Path(root)
    for file in path.rglob("*") if path.is_dir() else [path]:
        if file.is_file() and file.suffix.lower() in {"", ".c", ".h", ".inc", ".mk", ".mms", ".py"}:
            file.read_bytes().decode("ascii")
print("Calendar, CLI, and ASCII checks passed.")
