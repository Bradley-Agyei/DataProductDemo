import shutil
from datetime import date, datetime
from pathlib import Path

import pytest

from src.fraud_case import config
from src.fraud_case.run import build

AS_OF = date(2026, 10, 4)
LOAD_TS = datetime(2026, 10, 4, 6, 0, 0)
# Member 360 as built from today's sources: 10 members, M000001..M000010.
MEMBER_REF = Path(__file__).parent / "data" / "member_360.csv"
# Copy of data/reference/account_id_map.csv: 10 core banking accounts, 100 fraud accounts.
ACCOUNT_REF = Path(__file__).parent / "data" / "account_id_map.csv"
SOURCE_FILE = config.SOURCE_FILES["Fraud_Case_Extract"]


def run_build(tmp_path, src_dir=config.SOURCE_DIR, **kwargs):
    kwargs.setdefault("member_ref", MEMBER_REF)
    kwargs.setdefault("account_ref", ACCOUNT_REF)
    kwargs.setdefault("as_of", AS_OF)
    kwargs.setdefault("load_ts", LOAD_TS)
    kwargs.setdefault("db_path", tmp_path / "fraud_case.db")
    kwargs.setdefault("out_dir", tmp_path / "out")
    return build(src_dir=src_dir, **kwargs)


@pytest.fixture(scope="session")
def result(tmp_path_factory):
    """One end-to-end build on the real extract, shared by read-only tests."""
    return run_build(tmp_path_factory.mktemp("run"), batch_id="test-batch")


@pytest.fixture
def src_copy(tmp_path):
    """Writable copy of the extract for tests that inject bad data."""
    target = tmp_path / "src"
    target.mkdir()
    shutil.copy(config.SOURCE_DIR / SOURCE_FILE, target / SOURCE_FILE)
    return target


def edit_extract(src_dir, old, new):
    path = src_dir / SOURCE_FILE
    text = path.read_text(encoding="utf-8")
    assert text.count(old) == 1, f"{old!r} must appear exactly once"
    path.write_text(text.replace(old, new), encoding="utf-8")


def by_case(frame):
    return frame.set_index("case_id")
