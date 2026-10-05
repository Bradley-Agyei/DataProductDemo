import shutil
from datetime import date, datetime

import pytest

from src.member_360 import config
from src.member_360.run import build

AS_OF = date(2026, 10, 4)
LOAD_TS = datetime(2026, 10, 4, 6, 0, 0)


def run_build(tmp_path, src_dir=config.SOURCE_DIR, **kwargs):
    kwargs.setdefault("as_of", AS_OF)
    kwargs.setdefault("load_ts", LOAD_TS)
    kwargs.setdefault("db_path", tmp_path / "member_360.db")
    kwargs.setdefault("out_dir", tmp_path / "out")
    return build(src_dir=src_dir, **kwargs)


@pytest.fixture(scope="session")
def result(tmp_path_factory):
    """One end-to-end build on the real sample sources, shared by read-only tests."""
    return run_build(tmp_path_factory.mktemp("run"), batch_id="test-batch")


@pytest.fixture
def src_copy(tmp_path):
    """Writable copy of the sources for tests that inject bad data."""
    target = tmp_path / "src"
    shutil.copytree(config.SOURCE_DIR, target)
    return target


def edit_csv(path, old, new):
    text = path.read_text(encoding="utf-8")
    assert old in text, f"{old!r} not found in {path.name}"
    path.write_text(text.replace(old, new, 1), encoding="utf-8")
