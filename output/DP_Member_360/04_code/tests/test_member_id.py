"""Member ID conformance: M + 6 digits, with a 1:1 crosswalk to the source ID."""
import re

import pytest

from src.member_360.transform import conform_member_id


@pytest.mark.parametrize("source, expected", [
    ("M0001", "M000001"),
    ("M0010", "M000010"),
    (" M42 ", "M000042"),
    ("M000100", "M000100"),
])
def test_conform_member_id(source, expected):
    assert conform_member_id(source) == expected


@pytest.mark.parametrize("bad", ["X0001", "M", "M12A", "M1234567"])
def test_unconformable_ids_raise(bad):
    with pytest.raises(ValueError):
        conform_member_id(bad)


def test_xref_maps_every_source_member_one_to_one(result):
    xref = result.xref
    assert len(xref) == 10
    assert xref["source_member_id"].is_unique and xref["member_id"].is_unique
    assert dict(zip(xref["source_member_id"], xref["member_id"]))["M0001"] == "M000001"
    assert set(xref["source_system"]) == {"core_csv"}


def test_product_ids_match_standard_pattern(result):
    assert all(re.fullmatch(r"M\d{6}", m) for m in result.product["member_id"])
