"""Check and print one MOTD for each annual greeting."""
import os
import subprocess
import sys


# Gregorian input, expected first cell (ASCII rendering), expected greeting.
cases = [
    ("2026-09-22", "1 Vendemiaire, Year CCXXXV", "Bonne annee, citoyen!"),
    ("1793-10-16", "25 Vendemiaire, Year II", "Year II: Marie Antoinette executed."),
    ("1799-11-09", "18 Brumaire, Year VIII", "Year VIII: Bonaparte's coup; end of the Directory."),
    ("1792-12-25", "5 Nivose, Year I", "Joyeux Jour du Chien!"),
    ("1793-01-21", "2 Pluviose, Year I", "Year I: Louis XVI executed."),
    ("1794-06-08", "20 Prairial, Year II", "Year II: Festival of the Supreme Being."),
    ("2026-07-14", "26 Messidor, Year CCXXXIV", "Aux armes, citoyens!"),
    ("1794-07-28", "10 Thermidor, Year II", "Year II: Robespierre executed. A bientot, la guillotine!"),
]

for civil, republican, greeting in cases:
    table = subprocess.check_output(
        [sys.argv[1], "--lang=en", "--style=plain", "--no-month-gloss", civil],
        env=dict(os.environ, COLUMNS="81"),
    ).decode("ascii")
    # Reassemble the wrapped first column, excluding the spanning title and note.
    rows = [line.split("|") for line in table.splitlines() if line.lstrip().startswith("|")]
    body = [parts[1:4] for parts in rows if len(parts) == 5][1:]
    assert all(any(s.strip() for s in cells) for cells in body)
    date_cell = " ".join(parts[1].strip() for parts in rows
                         if len(parts) == 5 and parts[1].strip() not in ("", "Date"))
    assert date_cell == f"{republican} {greeting}", (civil, date_cell)
    print(f"{civil}\n{table}", end="")
