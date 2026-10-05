"""Validate the account ID mapping reference table.

    python -m tools.validate_account_id_map [path]     # exit 1 and list problems if invalid
"""
from __future__ import annotations

import csv
import re
import sys
from collections import Counter
from pathlib import Path

from tools.build_account_id_map import COLUMNS, CORE_SYSTEM, MAP_PATH, conform_account_id

_CANONICAL = re.compile(r"A\d{7}")


def validate_rows(rows: list[dict]) -> list[str]:
    problems = []
    keys = Counter((r["source_system"], r["source_account_id"]) for r in rows)
    problems += [f"duplicate key {k[0]}/{k[1]}" for k, n in keys.items() if n > 1]

    per_system = Counter((r["source_system"], r["account_id"]) for r in rows)
    problems += [f"collision in {s}: {n} source IDs map to {c}" for (s, c), n in per_system.items() if n > 1]

    core = {r["account_id"] for r in rows if r["source_system"] == CORE_SYSTEM}
    for r in rows:
        key = f"{r['source_system']}/{r['source_account_id']}"
        if not _CANONICAL.fullmatch(r["account_id"]):
            problems.append(f"{key}: account_id {r['account_id']!r} is not A + 7 digits")
            continue
        try:
            if conform_account_id(r["source_account_id"]) != r["account_id"]:
                problems.append(f"{key}: maps to {r['account_id']}, rule gives {conform_account_id(r['source_account_id'])}")
        except ValueError as exc:
            problems.append(f"{key}: {exc}")
        expected = "TRUE" if r["account_id"] in core else "FALSE"
        if r["in_core_banking"] != expected:
            problems.append(f"{key}: in_core_banking {r['in_core_banking']} should be {expected}")
    return problems


def validate_file(path: Path = MAP_PATH) -> list[str]:
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != COLUMNS:
            return [f"header {reader.fieldnames} != {COLUMNS}"]
        return validate_rows(list(reader))


def main(argv: list[str] | None = None) -> int:
    path = Path(argv[0]) if argv else MAP_PATH
    problems = validate_file(path)
    for p in problems:
        print(p)
    print(f"{path}: {'valid' if not problems else f'{len(problems)} problem(s)'}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
