import os
import tempfile

import pytest


@pytest.fixture
def db_path(tmp_path):
    path = str(tmp_path / "test.db")
    os.environ["RETRO_DB"] = path
    yield path
    os.environ.pop("RETRO_DB", None)


@pytest.fixture
def db_script():
    return os.path.join(os.path.dirname(__file__), "..", "scripts", "db.py")
