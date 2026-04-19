import json, os, sys
import sqlite3
import pytest
from retro import db as rdb


def _make_db(tmp_path):
    path = str(tmp_path / "test.db")
    conn = rdb.ensure_db(path)
    conn.close()
    return path


def test_agent_column_exists(tmp_path):
    path = _make_db(tmp_path)
    conn = rdb.ensure_db(path)
    cols = [r[1] for r in conn.execute("PRAGMA table_info(entries)").fetchall()]
    conn.close()
    assert "agent" in cols


def test_agent_stored(tmp_path):
    path = _make_db(tmp_path)
    conn = rdb.ensure_db(path)
    entry_id = rdb.insert_entry(conn, "error", {
        "summary": "test", "description": "desc", "category": "prompt", "agent": "codex"
    })
    row = conn.execute("SELECT agent FROM entries WHERE id = ?", (entry_id,)).fetchone()
    conn.close()
    assert row[0] == "codex"


def test_migration_v1_to_v2(tmp_path):
    """Existing v1 DB gets agent column without data loss."""
    path = str(tmp_path / "v1.db")
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("CREATE TABLE schema_version (version INTEGER PRIMARY KEY)")
    conn.execute("INSERT INTO schema_version VALUES (1)")
    conn.execute("""CREATE TABLE entries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT (datetime('now')),
        summary TEXT NOT NULL, description TEXT NOT NULL,
        triggering_prompt TEXT, category TEXT NOT NULL, subcategory TEXT,
        project TEXT, lesson TEXT, corrective_action TEXT,
        what_worked TEXT, why_it_worked TEXT, tags TEXT
    )""")
    conn.execute("INSERT INTO entries (type, summary, description, category) VALUES ('error','old','old','prompt')")
    conn.execute("CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
    conn.commit()
    conn.close()

    conn = rdb.ensure_db(path)
    cols = [r[1] for r in conn.execute("PRAGMA table_info(entries)").fetchall()]
    count = conn.execute("SELECT COUNT(*) FROM entries").fetchone()[0]
    conn.close()
    assert "agent" in cols
    assert count == 1  # existing row preserved


def test_filter_by_agent(tmp_path):
    path = _make_db(tmp_path)
    conn = rdb.ensure_db(path)
    rdb.insert_entry(conn, "error", {"summary": "a", "description": "d", "category": "prompt", "agent": "claude"})
    rdb.insert_entry(conn, "error", {"summary": "b", "description": "d", "category": "prompt", "agent": "codex"})
    where, params = rdb.build_where({"agent": "claude"})
    rows = conn.execute(f"SELECT * FROM entries {where}", params).fetchall()
    conn.close()
    assert len(rows) == 1
