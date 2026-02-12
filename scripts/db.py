#!/usr/bin/env python3
"""retro database operations. stdlib only."""

import json
import os
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path

VALID_CATEGORIES = {
    "prompt",
    "context",
    "harness",
    "meta",
    "workflow",
}

SCHEMA_VERSION = 1


def get_db_path():
    if "RETRO_DB" in os.environ:
        return os.environ["RETRO_DB"]
    return os.path.join(Path.home(), ".retro", "retro.db")


def ensure_db(path):
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS schema_version (
            version INTEGER PRIMARY KEY
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL CHECK(type IN ('error', 'success')),
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            summary TEXT NOT NULL,
            description TEXT NOT NULL,
            triggering_prompt TEXT,
            category TEXT NOT NULL,
            subcategory TEXT,
            project TEXT,
            lesson TEXT,
            corrective_action TEXT,
            what_worked TEXT,
            why_it_worked TEXT,
            tags TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS metadata (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)
    existing = conn.execute("SELECT version FROM schema_version").fetchone()
    if not existing:
        conn.execute("INSERT INTO schema_version (version) VALUES (?)", (SCHEMA_VERSION,))
    conn.commit()
    return conn


def validate_entry(data, entry_type):
    required = ["summary", "description", "category"]
    for field in required:
        if field not in data:
            raise ValueError(f"Missing required field: {field}")
    if data["category"] not in VALID_CATEGORIES:
        raise ValueError(
            f"Invalid category: {data['category']}. Must be one of: {sorted(VALID_CATEGORIES)}"
        )


def insert_entry(conn, entry_type, data):
    tags = data.get("tags")
    if tags is not None:
        tags = json.dumps(tags)
    conn.execute(
        """INSERT INTO entries
           (type, summary, description, triggering_prompt, category,
            subcategory, project, lesson, corrective_action,
            what_worked, why_it_worked, tags)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            entry_type,
            data["summary"],
            data["description"],
            data.get("triggering_prompt"),
            data["category"],
            data.get("subcategory"),
            data.get("project"),
            data.get("lesson"),
            data.get("corrective_action"),
            data.get("what_worked"),
            data.get("why_it_worked"),
            tags,
        ),
    )
    conn.commit()
    return conn.execute("SELECT last_insert_rowid()").fetchone()[0]


def build_where(filters):
    clauses = []
    params = []
    for key in ("type", "category", "subcategory", "project"):
        if key in filters:
            clauses.append(f"{key} = ?")
            params.append(filters[key])
    if "date_from" in filters:
        clauses.append("date(created_at) >= date(?)")
        params.append(filters["date_from"])
    if "date_to" in filters:
        clauses.append("date(created_at) <= date(?)")
        params.append(filters["date_to"])
    where = ""
    if clauses:
        where = "WHERE " + " AND ".join(clauses)
    return where, params


def cmd_init():
    path = get_db_path()
    conn = ensure_db(path)
    conn.close()
    return {"status": "ok", "path": path}


def cmd_log(entry_type):
    data = json.loads(sys.stdin.read())
    validate_entry(data, entry_type)
    path = get_db_path()
    conn = ensure_db(path)
    entry_id = insert_entry(conn, entry_type, data)
    conn.close()
    return {"status": "ok", "id": entry_id}


def cmd_query():
    raw = sys.stdin.read().strip()
    filters = json.loads(raw) if raw else {}
    path = get_db_path()
    conn = ensure_db(path)
    conn.row_factory = sqlite3.Row
    where, params = build_where(filters)
    limit = ""
    if "limit" in filters:
        limit = f"LIMIT {int(filters['limit'])}"
    rows = conn.execute(
        f"SELECT * FROM entries {where} ORDER BY created_at DESC {limit}", params
    ).fetchall()
    conn.close()
    results = []
    for row in rows:
        d = dict(row)
        if d["tags"]:
            d["tags"] = json.loads(d["tags"])
        results.append(d)
    return results


def cmd_stats():
    raw = sys.stdin.read().strip()
    filters = json.loads(raw) if raw else {}
    path = get_db_path()
    conn = ensure_db(path)
    where, params = build_where(filters)
    total = conn.execute(
        f"SELECT COUNT(*) FROM entries {where}", params
    ).fetchone()[0]
    cats = conn.execute(
        f"SELECT category, COUNT(*) as count FROM entries {where} GROUP BY category ORDER BY count DESC",
        params,
    ).fetchall()
    conn.close()
    return {
        "total": total,
        "categories": [{"category": c[0], "count": c[1]} for c in cats],
    }


def cmd_trends():
    raw = sys.stdin.read().strip()
    filters = json.loads(raw) if raw else {}
    path = get_db_path()
    conn = ensure_db(path)
    where, params = build_where(filters)
    rows = conn.execute(
        f"""SELECT strftime('%Y-W%W', created_at) as week, COUNT(*) as count
            FROM entries {where}
            GROUP BY week ORDER BY week""",
        params,
    ).fetchall()
    conn.close()
    return {"weeks": [{"week": r[0], "count": r[1]} for r in rows]}


def cmd_check_reminder():
    path = get_db_path()
    conn = ensure_db(path)
    last_reviewed = conn.execute(
        "SELECT value FROM metadata WHERE key = 'last_reviewed_at'"
    ).fetchone()
    if last_reviewed:
        last_dt = datetime.fromisoformat(last_reviewed[0])
        days_since = (datetime.now() - last_dt).days
        if days_since < 7:
            conn.close()
            return {"should_remind": False, "unreviewed": 0, "days_since": days_since}
        unreviewed = conn.execute(
            "SELECT COUNT(*) FROM entries WHERE created_at > ?",
            (last_reviewed[0],),
        ).fetchone()[0]
    else:
        days_since = -1
        unreviewed = conn.execute("SELECT COUNT(*) FROM entries").fetchone()[0]
    conn.close()
    should_remind = unreviewed >= 5
    return {
        "should_remind": should_remind,
        "unreviewed": unreviewed,
        "days_since": days_since,
    }


def cmd_set_metadata():
    if len(sys.argv) < 4:
        raise ValueError("Usage: db.py set-metadata <key> <value>")
    key = sys.argv[2]
    value = sys.argv[3]
    path = get_db_path()
    conn = ensure_db(path)
    conn.execute(
        "INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)", (key, value)
    )
    conn.commit()
    conn.close()
    return {"status": "ok"}


COMMANDS = {
    "init": cmd_init,
    "log-error": lambda: cmd_log("error"),
    "log-success": lambda: cmd_log("success"),
    "query": cmd_query,
    "stats": cmd_stats,
    "trends": cmd_trends,
    "check-reminder": cmd_check_reminder,
    "set-metadata": cmd_set_metadata,
}


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        valid = ", ".join(sorted(COMMANDS))
        print(f"Usage: db.py <command>\nCommands: {valid}", file=sys.stderr)
        sys.exit(1)
    try:
        result = COMMANDS[sys.argv[1]]()
        print(json.dumps(result))
    except Exception as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
