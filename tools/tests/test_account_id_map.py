"""Account ID mapping reference table: conversion rule, collisions, validation and freshness."""
import csv

import pytest

from tools.build_account_id_map import (MAP_PATH, build_rows, conform_account_id, read_source_ids,
                                        render)
from tools.validate_account_id_map import validate_file, validate_rows


@pytest.mark.parametrize("source", ["A0001", "A00001", "A0000001", "A1", " A00001 "])
def test_any_width_converts_to_canonical(source):
    assert conform_account_id(source) == "A0000001"


@pytest.mark.parametrize("bad", ["A12345678", "X1", "A", "A12B", ""])
def test_malformed_ids_are_rejected(bad):
    with pytest.raises(ValueError):
        conform_account_id(bad)


def test_same_account_across_systems_is_allowed():
    rows, rejects = build_rows({"core_banking": ["A00001"], "fraud_case_mgmt": ["A0000001"]})
    assert not rejects
    assert {(r["source_system"], r["source_account_id"], r["account_id"]) for r in rows} == {
        ("core_banking", "A00001", "A0000001"), ("fraud_case_mgmt", "A0000001", "A0000001")}
    assert {r["in_core_banking"] for r in rows} == {"TRUE"}


def test_collision_within_a_system_rejects_both():
    rows, rejects = build_rows({"core_banking": ["A00002"], "legacy": ["A0001", "A00001"]})
    assert [r["source_account_id"] for r in rows] == ["A00002"]
    assert {r["source_account_id"] for r in rejects} == {"A0001", "A00001"}
    assert all("collides" in r["reason"] for r in rejects)


def test_unconvertible_id_is_rejected_not_mapped():
    rows, rejects = build_rows({"core_banking": ["A00001", "A123456789"]})
    assert [r["source_account_id"] for r in rows] == ["A00001"]
    assert rejects[0]["source_account_id"] == "A123456789"


def test_in_core_banking_flag():
    rows, _ = build_rows({"core_banking": ["A00001"], "fraud_case_mgmt": ["A0000001", "A0000011"]})
    flags = {r["source_account_id"]: r["in_core_banking"] for r in rows}
    assert flags == {"A00001": "TRUE", "A0000001": "TRUE", "A0000011": "FALSE"}


def test_committed_table_is_current():
    rows, rejects = build_rows(read_source_ids())
    assert not rejects
    assert MAP_PATH.read_text(encoding="utf-8") == render(rows), "run: python -m tools.build_account_id_map"


def test_committed_table_contents():
    with open(MAP_PATH, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 110
    assert sum(r["source_system"] == "core_banking" for r in rows) == 10
    assert len({r["account_id"] for r in rows if r["in_core_banking"] == "TRUE"}) == 10
    assert sum(r["in_core_banking"] == "FALSE" for r in rows) == 90


def test_committed_table_is_valid():
    assert validate_file() == []


@pytest.mark.parametrize("mutate, expected", [
    (lambda rows: rows.append(dict(rows[0])), "duplicate key"),
    (lambda rows: rows[0].update(account_id="A00001"), "not A + 7 digits"),
    (lambda rows: rows[0].update(in_core_banking="FALSE"), "in_core_banking"),
    (lambda rows: rows.append({**rows[0], "source_account_id": "A0001"}), "collision"),
])
def test_validator_catches_problems(mutate, expected):
    rows, _ = build_rows({"core_banking": ["A00001", "A00002"]})
    mutate(rows)
    assert any(expected in p for p in validate_rows(rows))
