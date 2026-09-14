"""Hidden gate test for sequence task T3 (drop-column). Copied into the work
dir's tests/ AFTER the agent finishes; the agent never sees it."""
import pytest
from click.testing import CliRunner
from sqlite_utils import Database
from sqlite_utils import cli


def test_api_drop_column(fresh_db):
    t = fresh_db["books"]
    t.insert({"id": 1, "title": "A", "author": "X"}, pk="id")
    t.drop_column("author")
    assert t.columns_dict == {"id": int, "title": str}
    assert list(t.rows) == [{"id": 1, "title": "A"}]
    assert t.pks == ["id"]


def test_api_drop_missing_column_raises(fresh_db):
    t = fresh_db["books"]
    t.insert({"id": 1, "title": "A"}, pk="id")
    with pytest.raises(Exception):
        t.drop_column("nope")
    assert t.columns_dict == {"id": int, "title": str}


def test_cli_drop_column(tmpdir):
    db_path = str(tmpdir / "test.db")
    db = Database(db_path)
    db["books"].insert({"id": 1, "title": "A", "author": "X"}, pk="id")
    result = CliRunner().invoke(cli.cli, ["drop-column", db_path, "books", "author"])
    assert result.exit_code == 0, result.output
    assert Database(db_path)["books"].columns_dict == {"id": int, "title": str}
