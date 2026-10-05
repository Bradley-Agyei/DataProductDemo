"""Every product carries its own dp_framework copy; the copies must stay byte-identical."""
from pathlib import Path

import pytest

CODE_DIR = Path(__file__).resolve().parents[1]
PRODUCT_DIR = CODE_DIR.parent
FRAMEWORK = Path("src") / "dp_framework"


def sibling_frameworks() -> list[Path]:
    return [p / "04_code" / FRAMEWORK for p in PRODUCT_DIR.parent.iterdir()
            if p.is_dir() and p != PRODUCT_DIR and (p / "04_code" / FRAMEWORK).is_dir()]


def test_framework_matches_sibling_products():
    siblings = sibling_frameworks()
    if not siblings:
        pytest.skip("no sibling product checked out")
    mine = {f.name: f.read_bytes() for f in (CODE_DIR / FRAMEWORK).glob("*.py")}
    for other in siblings:
        theirs = {f.name: f.read_bytes() for f in other.glob("*.py")}
        assert sorted(theirs) == sorted(mine), f"file sets differ: {other}"
        stale = [name for name in mine if mine[name] != theirs[name]]
        assert not stale, f"dp_framework differs from {other}: {stale}"
