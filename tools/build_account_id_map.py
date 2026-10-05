"""Build the account ID mapping reference table from each source system's file.

    python -m tools.build_account_id_map            # rewrites data/reference/account_id_map.csv
    python -m tools.build_account_id_map --check    # exit 1 if the committed file is out of date
"""
from __future__ import annotations

import argparse
import csv
import io
import re
import sys
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
MAP_PATH = PROJECT_ROOT / "data" / "reference" / "account_id_map.csv"

CANONICAL_DIGITS = 7
CORE_SYSTEM = "core_banking"
MAPPING_RULE = "pad_to_7_digits"
COLUMNS = ["source_system", "source_account_id", "account_id", "in_core_banking", "mapping_rule"]
_SOURCE_ID = re.compile(r"A(\d+)")


@dataclass(frozen=True)
class SourceSystem:
    name: str
    file_name: str
    id_column: str


# Core banking first: it decides in_core_banking for every other system.
SYSTEMS = (
    SourceSystem(CORE_SYSTEM, "Account.csv", "account_id"),
    SourceSystem("fraud_case_mgmt", "DP_Fraud_Case.csv", "primary_account_id"),
)


def conform_account_id(source_id: str) -> str:
    """Any width of 'A' + digits -> canonical 'A' + 7 digits (A0001, A00001 -> A0000001)."""
    match = _SOURCE_ID.fullmatch(str(source_id).strip())
    if not match:
        raise ValueError(f"not an account ID: {source_id!r}")
    digits = match.group(1).lstrip("0") or "0"
    if len(digits) > CANONICAL_DIGITS:
        raise ValueError(f"{source_id!r} has more than {CANONICAL_DIGITS} digits")
    return "A" + digits.zfill(CANONICAL_DIGITS)


def build_rows(ids_by_system: dict[str, list[str]]) -> tuple[list[dict], list[dict]]:
    """Returns (rows, rejects). Within a system, IDs that collide on one canonical ID are all rejected."""
    rejects, mapped = [], {}
    for system, source_ids in ids_by_system.items():
        by_canonical: dict[str, list[str]] = {}
        for source_id in dict.fromkeys(s.strip() for s in source_ids):
            try:
                by_canonical.setdefault(conform_account_id(source_id), []).append(source_id)
            except ValueError as exc:
                rejects.append({"source_system": system, "source_account_id": source_id, "reason": str(exc)})
        for canonical, sources in by_canonical.items():
            if len(sources) > 1:
                rejects += [{"source_system": system, "source_account_id": s,
                             "reason": f"collides with {sorted(set(sources) - {s})} on {canonical}"} for s in sources]
            else:
                mapped[(system, sources[0])] = canonical

    core = {c for (system, _), c in mapped.items() if system == CORE_SYSTEM}
    rows = [{"source_system": system, "source_account_id": source_id, "account_id": canonical,
             "in_core_banking": "TRUE" if canonical in core else "FALSE", "mapping_rule": MAPPING_RULE}
            for (system, source_id), canonical in mapped.items()]
    return rows, rejects


def read_source_ids(raw_dir: Path = RAW_DIR) -> dict[str, list[str]]:
    ids = {}
    for s in SYSTEMS:
        with open(raw_dir / s.file_name, newline="", encoding="utf-8-sig") as f:
            values = [r[s.id_column] for r in csv.DictReader(f)]
        # Core banking keeps file order; other systems are sorted for a stable diff.
        ids[s.name] = values if s.name == CORE_SYSTEM else sorted(set(values))
    return ids


def render(rows: list[dict]) -> str:
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=COLUMNS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return out.getvalue()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--raw-dir", type=Path, default=RAW_DIR)
    parser.add_argument("--out", type=Path, default=MAP_PATH)
    parser.add_argument("--check", action="store_true", help="only verify the committed file is current")
    args = parser.parse_args(argv)

    rows, rejects = build_rows(read_source_ids(args.raw_dir))
    for r in rejects:
        print(f"REJECT {r['source_system']}/{r['source_account_id']}: {r['reason']}", file=sys.stderr)
    text = render(rows)
    if args.check:
        current = args.out.read_text(encoding="utf-8") if args.out.exists() else ""
        print("up to date" if current == text else f"STALE: {args.out}")
        return 0 if current == text else 1
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(text, encoding="utf-8", newline="")
    print(f"wrote {len(rows)} rows to {args.out} ({len(rejects)} rejected)")
    return 1 if rejects else 0


if __name__ == "__main__":
    sys.exit(main())
