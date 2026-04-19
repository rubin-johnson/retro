import os, tempfile, importlib, pytest

@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "mcp_test.db")

def _get_fns(db_path):
    """Import mcp_server with a test DB path."""
    import retro.mcp_server as m
    return m

def test_log_error_returns_id(db_path, monkeypatch):
    monkeypatch.setenv("RETRO_DB", db_path)
    import retro.mcp_server as m
    result = m.log_error_fn("test error", "it broke", "prompt", agent="codex")
    assert result["status"] == "ok"
    assert isinstance(result["id"], int)

def test_log_success_returns_id(db_path, monkeypatch):
    monkeypatch.setenv("RETRO_DB", db_path)
    import retro.mcp_server as m
    result = m.log_success_fn("test success", "it worked", "workflow", agent="gemini")
    assert result["status"] == "ok"

def test_query_returns_list(db_path, monkeypatch):
    monkeypatch.setenv("RETRO_DB", db_path)
    import retro.mcp_server as m
    m.log_error_fn("e", "d", "prompt", agent="claude")
    results = m.query_fn(limit=10)
    assert isinstance(results, list)
    assert len(results) >= 1
    assert results[0]["agent"] == "claude"

def test_stats_returns_totals(db_path, monkeypatch):
    monkeypatch.setenv("RETRO_DB", db_path)
    import retro.mcp_server as m
    m.log_error_fn("x", "y", "context", agent="codex")
    s = m.stats_fn()
    assert s["total"] >= 1
    assert any(c["category"] == "context" for c in s["categories"])

def test_query_filter_by_agent(db_path, monkeypatch):
    monkeypatch.setenv("RETRO_DB", db_path)
    import retro.mcp_server as m
    m.log_error_fn("a", "d", "prompt", agent="claude")
    m.log_error_fn("b", "d", "prompt", agent="codex")
    results = m.query_fn(agent="claude")
    assert all(r["agent"] == "claude" for r in results)
