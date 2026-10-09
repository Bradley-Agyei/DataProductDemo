"""Publish artifacts generated from the contract: data contract (JSON + Markdown), CSV export, DDL."""
from __future__ import annotations

import csv
import json
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

import pandas as pd

from .contract import Table, ddl


def format_value(value) -> str:
    if value is None or value is pd.NA or (isinstance(value, float) and value != value):
        return ""
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Decimal):
        return format(value, "f")
    return str(value)


def export_csv(df: pd.DataFrame, table: Table, path: Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(table.column_names)
        for record in df[table.column_names].to_dict("records"):
            writer.writerow(format_value(record[c]) for c in table.column_names)
    return path


def contract_dict(table: Table, meta: dict) -> dict:
    return {
        "name": table.name,
        "description": table.description,
        "grain": table.grain,
        "primary_key": table.primary_key,
        **meta,
        "columns": [{
            "name": c.name, "type": c.type, "nullable": c.nullable or c.is_pending, "key": c.key,
            "allowed_values": list(c.allowed), "pattern": c.pattern, "status": c.status,
            "description": c.description,
        } for c in table.columns],
    }


def write_contract(table: Table, out_dir: Path, meta: dict) -> tuple[Path, Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    spec = contract_dict(table, meta)
    json_path = out_dir / "data_contract.json"
    json_path.write_text(json.dumps(spec, indent=2), encoding="utf-8")

    lines = [f"# Data contract: {table.name}", ""]
    lines += [f"- **{k.replace('_', ' ').title()}:** {v}" for k, v in spec.items()
              if k not in ("name", "columns") and v]
    lines += ["", "| Column | Type | Nullable | Key | Allowed values | Status | Description |",
              "|---|---|---|---|---|---|---|"]
    for c in spec["columns"]:
        lines.append(f"| {c['name']} | {c['type']} | {'Y' if c['nullable'] else 'N'} | {c['key']} | "
                     f"{', '.join(c['allowed_values'])} | {c['status']} | {c['description']} |")
    md_path = out_dir / "data_contract.md"
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return json_path, md_path


def write_ddl(tables: list[Table], ddl_dir: Path) -> list[Path]:
    ddl_dir = Path(ddl_dir)
    ddl_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for i, table in enumerate(tables, 1):
        path = ddl_dir / f"{i:02d}_{table.name}.sql"
        path.write_text(ddl(table), encoding="utf-8")
        paths.append(path)
    return paths
