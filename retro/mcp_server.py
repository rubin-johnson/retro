from mcp.server.fastmcp import FastMCP
from retro.db import get_db_path, ensure_db, validate_entry, insert_entry, build_where
import json
import sqlite3

mcp = FastMCP("retro")

def log_error_fn(summary, description, category, agent="unknown",
                  subcategory="", project="", lesson="", corrective_action="",
                  triggering_prompt="", tags=None):
    data = {k: v for k, v in {
        "summary": summary, "description": description, "category": category,
        "agent": agent, "subcategory": subcategory or None, "project": project or None,
        "lesson": lesson or None, "corrective_action": corrective_action or None,
        "triggering_prompt": triggering_prompt or None,
        "tags": tags or None,
    }.items() if v is not None}
    validate_entry(data, "error")
    conn = ensure_db(get_db_path())
    entry_id = insert_entry(conn, "error", data)
    conn.close()
    return {"status": "ok", "id": entry_id}

def log_success_fn(summary, description, category, agent="unknown",
                    subcategory="", project="", lesson="", what_worked="",
                    why_it_worked="", tags=None):
    data = {k: v for k, v in {
        "summary": summary, "description": description, "category": category,
        "agent": agent, "subcategory": subcategory or None, "project": project or None,
        "lesson": lesson or None, "what_worked": what_worked or None,
        "why_it_worked": why_it_worked or None,
        "tags": tags or None,
    }.items() if v is not None}
    validate_entry(data, "success")
    conn = ensure_db(get_db_path())
    entry_id = insert_entry(conn, "success", data)
    conn.close()
    return {"status": "ok", "id": entry_id}

def query_fn(type="", category="", agent="", project="", limit=20):
    filters = {k: v for k, v in {"type": type, "category": category, "agent": agent, "project": project}.items() if v}
    filters["limit"] = limit
    conn = ensure_db(get_db_path())
    conn.row_factory = sqlite3.Row
    where, params = build_where(filters)
    rows = conn.execute(
        f"SELECT * FROM entries {where} ORDER BY created_at DESC LIMIT {int(limit)}", params
    ).fetchall()
    conn.close()
    results = []
    for row in rows:
        d = dict(row)
        if d.get("tags"):
            d["tags"] = json.loads(d["tags"])
        results.append(d)
    return results

def stats_fn(type="", category="", agent=""):
    filters = {k: v for k, v in {"type": type, "category": category, "agent": agent}.items() if v}
    conn = ensure_db(get_db_path())
    where, params = build_where(filters)
    total = conn.execute(f"SELECT COUNT(*) FROM entries {where}", params).fetchone()[0]
    cats = conn.execute(
        f"SELECT category, COUNT(*) as count FROM entries {where} GROUP BY category ORDER BY count DESC", params
    ).fetchall()
    conn.close()
    return {"total": total, "categories": [{"category": c[0], "count": c[1]} for c in cats]}

@mcp.tool()
def log_error(summary: str, description: str, category: str, agent: str = "unknown",
              subcategory: str = "", project: str = "", lesson: str = "",
              corrective_action: str = "", triggering_prompt: str = "",
              tags: list[str] = []) -> dict:
    """Log an agentic coding error."""
    return log_error_fn(summary, description, category, agent, subcategory,
                        project, lesson, corrective_action, triggering_prompt, tags or None)

@mcp.tool()
def log_success(summary: str, description: str, category: str, agent: str = "unknown",
                subcategory: str = "", project: str = "", lesson: str = "",
                what_worked: str = "", why_it_worked: str = "",
                tags: list[str] = []) -> dict:
    """Log an agentic coding success."""
    return log_success_fn(summary, description, category, agent, subcategory,
                          project, lesson, what_worked, why_it_worked, tags or None)

@mcp.tool()
def query(type: str = "", category: str = "", agent: str = "", project: str = "",
          limit: int = 20) -> list:
    """Query retro entries. Filter by type, category, agent, or project."""
    return query_fn(type, category, agent, project, limit)

@mcp.tool()
def stats(type: str = "", category: str = "", agent: str = "") -> dict:
    """Get entry counts by category."""
    return stats_fn(type, category, agent)

def main():
    mcp.run()

if __name__ == "__main__":
    main()
