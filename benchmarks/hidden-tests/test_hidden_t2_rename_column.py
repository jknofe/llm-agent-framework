"""Hidden gate test for sequence task T2 (rename-column). Copied into the work
dir's tests/ AFTER the agent finishes; the agent never sees it."""
import pytest
from click.testing import CliRunner
from sqlite_utils import Database
from sqlite_utils import cli


def test_api_rename_column(fresh_db):
    t = fresh_db["books"]
    t.insert({"id": 1, "title": "A", "author": "X"}, pk="id")
    t.rename_column("author", "writer")
    assert t.columns_dict == {"id": int, "title": str, "writer": str}
    assert list(t.rows) == [{"id": 1, "title": "A", "writer": "X"}]
    assert t.pks == ["id"]


def test_api_rename_column_collision_raises(fresh_db):
    t = fresh_db["books"]
    t.insert({"id": 1, "title": "A", "author": "X"}, pk="id")
    with pytest.raises(Exception):
        t.rename_column("author", "title")
    # nothing lost
    assert t.columns_dict == {"id": int, "title": str, "author": str}


def test_cli_rename_column(tmpdir):
    db_path = str(tmpdir / "test.db")
    db = Database(db_path)
    db["books"].insert({"id": 1, "title": "A", "author": "X"}, pk="id")
    result = CliRunner().invoke(
        cli.cli, ["rename-column", db_path, "books", "author", "writer"]
    )
    assert result.exit_code == 0, result.output
    assert Database(db_path)["books"].columns_dict == {
        "id": int, "title": str, "writer": str
    }
