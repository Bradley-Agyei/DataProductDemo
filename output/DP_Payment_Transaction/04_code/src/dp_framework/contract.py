"""Data contracts: the single definition of every table's columns, types and constraints."""
from __future__ import annotations

import re
from dataclasses import dataclass

READY = "ready"
PENDING = "pending"

SUPPORTED_TYPES = {"VARCHAR", "CHAR", "TEXT", "INT", "SMALLINT", "DECIMAL", "DATE", "TIMESTAMP", "BOOLEAN"}
_TYPE_RE = re.compile(r"^(?P<base>[A-Z]+)(?:\((?P<args>\d+(?:,\d+)?)\))?$")


class SchemaError(Exception):
    """A file or frame does not match its contract."""


def parse_type(physical_type: str) -> tuple[str, tuple[int, ...]]:
    match = _TYPE_RE.match(physical_type.replace(" ", "").upper())
    if not match or match["base"] not in SUPPORTED_TYPES:
        raise ValueError(f"Unsupported physical type: {physical_type}")
    args = tuple(int(a) for a in match["args"].split(",")) if match["args"] else ()
    return match["base"], args


@dataclass(frozen=True)
class Column:
    name: str
    type: str
    nullable: bool = False
    key: str = ""                      # "PK", "UNIQUE" or "FK:<Table>.<column>"
    allowed: tuple[str, ...] = ()
    pattern: str | None = None
    status: str = READY                # pending = no source feed yet; published as NULL
    description: str = ""

    def __post_init__(self):
        parse_type(self.type)
        if self.status not in (READY, PENDING):
            raise ValueError(f"{self.name}: unknown status {self.status!r}")

    @property
    def base_type(self) -> str:
        return parse_type(self.type)[0]

    @property
    def type_args(self) -> tuple[int, ...]:
        return parse_type(self.type)[1]

    @property
    def is_pending(self) -> bool:
        return self.status == PENDING

    @property
    def foreign_key(self) -> tuple[str, str] | None:
        if not self.key.startswith("FK:"):
            return None
        table, column = self.key[3:].split(".")
        return table, column


@dataclass(frozen=True)
class Table:
    name: str
    columns: tuple[Column, ...]
    grain: str = ""
    description: str = ""

    @property
    def column_names(self) -> list[str]:
        return [c.name for c in self.columns]

    @property
    def primary_key(self) -> list[str]:
        return [c.name for c in self.columns if c.key == "PK"]

    def column(self, name: str) -> Column:
        for c in self.columns:
            if c.name == name:
                return c
        raise KeyError(f"{self.name} has no column {name}")


def ddl(table: Table, name: str | None = None) -> str:
    """CREATE TABLE statement. Pending columns stay nullable until their feed is live."""
    lines = []
    for c in table.columns:
        not_null = " NOT NULL" if not c.nullable and not c.is_pending else ""
        lines.append(f"    {c.name} {c.type}{not_null}")
    if table.primary_key:
        lines.append(f"    PRIMARY KEY ({', '.join(table.primary_key)})")
    return f"CREATE TABLE {name or table.name} (\n" + ",\n".join(lines) + "\n);\n"
