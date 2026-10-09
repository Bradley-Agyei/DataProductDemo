import shutil
from datetime import datetime

import pytest

from src.payment_transaction import config
from src.payment_transaction.run import build

LOAD_TS = datetime(2026, 10, 8, 6, 0, 0)


def run_build(tmp_path, src_dir=config.SOURCE_DIR, **kwargs):
    kwargs.setdefault("load_ts", LOAD_TS)
    kwargs.setdefault("db_path", tmp_path / "payment_transaction.db")
    kwargs.setdefault("out_dir", tmp_path / "out")
    return build(src_dir=src_dir, **kwargs)


@pytest.fixture(scope="session")
def result(tmp_path_factory):
    """One build on the real sample sources, shared by read-only tests."""
    return run_build(tmp_path_factory.mktemp("run"), batch_id="0b9d7f5e-6a43-4c1e-9a52-3f1d2c7e8a10")


@pytest.fixture
def src_copy(tmp_path):
    """Writable copy of the sources for tests that change a header."""
    target = tmp_path / "src"
    shutil.copytree(config.SOURCE_DIR, target)
    return target


def rewrite_header(path, header):
    """Replace only the header line; data rows are left as they are."""
    lines = path.read_text(encoding="utf-8-sig").splitlines(keepends=True)
    lines[0] = ",".join(header) + "\n"
    path.write_text("".join(lines), encoding="utf-8")
