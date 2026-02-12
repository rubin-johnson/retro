import json
import os
import sqlite3
import subprocess
import sys
from datetime import datetime, timedelta

DB_SCRIPT = os.path.join(os.path.dirname(__file__), "..", "scripts", "db.py")


def run_cmd(subcommand, stdin_data=None, extra_args=None, env_override=None):
    env = os.environ.copy()
    if env_override:
        env.update(env_override)
    cmd = [sys.executable, DB_SCRIPT, subcommand]
    if extra_args:
        cmd.extend(extra_args)
    result = subprocess.run(
        cmd,
        input=stdin_data,
        capture_output=True,
        text=True,
        env=env,
    )
    return result


def run_ok(subcommand, stdin_data=None, extra_args=None, env_override=None):
    result = run_cmd(subcommand, stdin_data, extra_args, env_override)
    assert result.returncode == 0, f"stderr: {result.stderr}"
    return json.loads(result.stdout)


# --- init ---


class TestInit:
    def test_init_creates_db(self, db_path):
        out = run_ok("init")
        assert out["status"] == "ok"
        assert out["path"] == db_path
        assert os.path.exists(db_path)

    def test_init_creates_tables(self, db_path):
        run_ok("init")
        conn = sqlite3.connect(db_path)
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        assert "entries" in tables
        assert "metadata" in tables
        assert "schema_version" in tables
        conn.close()

    def test_init_idempotent(self, db_path):
        run_ok("init")
        out = run_ok("init")
        assert out["status"] == "ok"

    def test_init_wal_mode(self, db_path):
        run_ok("init")
        conn = sqlite3.connect(db_path)
        mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
        assert mode == "wal"
        conn.close()

    def test_init_creates_parent_dirs(self, tmp_path):
        nested = str(tmp_path / "a" / "b" / "test.db")
        out = run_ok("init", env_override={"RETRO_DB": nested})
        assert out["status"] == "ok"
        assert os.path.exists(nested)


# --- log-error ---


class TestLogError:
    def make_error(self, **overrides):
        entry = {
            "summary": "Claude deleted my test file",
            "description": "Asked Claude to refactor and it removed the test file entirely",
            "triggering_prompt": "Refactor the auth module",
            "category": "harness",
            "subcategory": "no-guardrails",
            "project": "myapp",
            "lesson": "Always specify what NOT to touch",
            "corrective_action": "Add constraint: do not delete test files",
            "tags": ["refactor", "tests"],
        }
        entry.update(overrides)
        return entry

    def test_log_error_basic(self, db_path):
        entry = self.make_error()
        out = run_ok("log-error", json.dumps(entry))
        assert out["status"] == "ok"
        assert out["id"] == 1

    def test_log_error_stored_correctly(self, db_path):
        entry = self.make_error()
        run_ok("log-error", json.dumps(entry))
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        row = dict(conn.execute("SELECT * FROM entries WHERE id = 1").fetchone())
        conn.close()
        assert row["type"] == "error"
        assert row["summary"] == entry["summary"]
        assert row["description"] == entry["description"]
        assert row["triggering_prompt"] == entry["triggering_prompt"]
        assert row["category"] == entry["category"]
        assert row["subcategory"] == entry["subcategory"]
        assert row["project"] == entry["project"]
        assert row["lesson"] == entry["lesson"]
        assert row["corrective_action"] == entry["corrective_action"]
        assert json.loads(row["tags"]) == entry["tags"]

    def test_log_error_auto_inits(self, db_path):
        """DB should be created on first write without explicit init."""
        entry = self.make_error()
        out = run_ok("log-error", json.dumps(entry))
        assert out["status"] == "ok"
        assert os.path.exists(db_path)

    def test_log_error_minimal_fields(self, db_path):
        entry = {
            "summary": "Something broke",
            "description": "It broke bad",
            "category": "prompt",
        }
        out = run_ok("log-error", json.dumps(entry))
        assert out["status"] == "ok"

    def test_log_error_missing_required_field(self, db_path):
        entry = {"summary": "oops"}
        result = run_cmd("log-error", json.dumps(entry))
        assert result.returncode != 0

    def test_log_error_invalid_category(self, db_path):
        entry = {
            "summary": "x",
            "description": "y",
            "category": "not-a-real-category",
        }
        result = run_cmd("log-error", json.dumps(entry))
        assert result.returncode != 0

    def test_log_error_increments_id(self, db_path):
        entry = self.make_error()
        out1 = run_ok("log-error", json.dumps(entry))
        out2 = run_ok("log-error", json.dumps(entry))
        assert out2["id"] == out1["id"] + 1


# --- log-success ---


class TestLogSuccess:
    def make_success(self, **overrides):
        entry = {
            "summary": "Used XML tags to structure complex prompt",
            "description": "Wrapped requirements in XML tags, Claude followed perfectly",
            "triggering_prompt": "Using <requirements> tags in prompt",
            "category": "prompt",
            "subcategory": "clarity",
            "project": "myapp",
            "what_worked": "XML tag structure for prompt sections",
            "why_it_worked": "Gave Claude clear boundaries between context and requirements",
            "tags": ["prompt-engineering"],
        }
        entry.update(overrides)
        return entry

    def test_log_success_basic(self, db_path):
        entry = self.make_success()
        out = run_ok("log-success", json.dumps(entry))
        assert out["status"] == "ok"
        assert out["id"] == 1

    def test_log_success_stored_as_success_type(self, db_path):
        entry = self.make_success()
        run_ok("log-success", json.dumps(entry))
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        row = dict(conn.execute("SELECT * FROM entries WHERE id = 1").fetchone())
        conn.close()
        assert row["type"] == "success"
        assert row["what_worked"] == entry["what_worked"]
        assert row["why_it_worked"] == entry["why_it_worked"]

    def test_log_success_minimal_fields(self, db_path):
        entry = {
            "summary": "Good result",
            "description": "It worked well",
            "category": "prompt",
        }
        out = run_ok("log-success", json.dumps(entry))
        assert out["status"] == "ok"


# --- query ---


class TestQuery:
    def seed(self, db_path):
        entries = [
            {
                "summary": "Error 1",
                "description": "Desc 1",
                "category": "prompt",
                "subcategory": "ambiguous-instruction",
                "project": "alpha",
            },
            {
                "summary": "Error 2",
                "description": "Desc 2",
                "category": "harness",
                "subcategory": "no-guardrails",
                "project": "alpha",
            },
            {
                "summary": "Error 3",
                "description": "Desc 3",
                "category": "prompt",
                "subcategory": "missing-constraints",
                "project": "beta",
            },
        ]
        for e in entries:
            run_ok("log-error", json.dumps(e))
        run_ok(
            "log-success",
            json.dumps(
                {
                    "summary": "Success 1",
                    "description": "Desc S1",
                    "category": "prompt",
                    "subcategory": "clarity",
                    "project": "alpha",
                }
            ),
        )

    def test_query_all(self, db_path):
        self.seed(db_path)
        out = run_ok("query", json.dumps({}))
        assert len(out) == 4

    def test_query_by_type(self, db_path):
        self.seed(db_path)
        out = run_ok("query", json.dumps({"type": "error"}))
        assert len(out) == 3
        assert all(e["type"] == "error" for e in out)

    def test_query_by_category(self, db_path):
        self.seed(db_path)
        out = run_ok("query", json.dumps({"category": "prompt"}))
        assert len(out) == 3

    def test_query_by_subcategory(self, db_path):
        self.seed(db_path)
        out = run_ok("query", json.dumps({"subcategory": "no-guardrails"}))
        assert len(out) == 1

    def test_query_by_project(self, db_path):
        self.seed(db_path)
        out = run_ok("query", json.dumps({"project": "beta"}))
        assert len(out) == 1

    def test_query_with_limit(self, db_path):
        self.seed(db_path)
        out = run_ok("query", json.dumps({"limit": 2}))
        assert len(out) == 2

    def test_query_empty_db(self, db_path):
        out = run_ok("query", json.dumps({}))
        assert out == []

    def test_query_by_date_range(self, db_path):
        self.seed(db_path)
        today = datetime.now().strftime("%Y-%m-%d")
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        out = run_ok("query", json.dumps({"date_from": today, "date_to": tomorrow}))
        assert len(out) == 4

    def test_query_future_date_returns_empty(self, db_path):
        self.seed(db_path)
        future = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        out = run_ok("query", json.dumps({"date_from": future}))
        assert len(out) == 0

    def test_query_combined_filters(self, db_path):
        self.seed(db_path)
        out = run_ok(
            "query", json.dumps({"type": "error", "category": "prompt", "project": "alpha"})
        )
        assert len(out) == 1
        assert out[0]["summary"] == "Error 1"


# --- stats ---


class TestStats:
    def seed(self, db_path):
        for cat in ["prompt", "prompt", "prompt", "harness", "context"]:
            run_ok(
                "log-error",
                json.dumps(
                    {"summary": f"err {cat}", "description": "d", "category": cat}
                ),
            )
        run_ok(
            "log-success",
            json.dumps({"summary": "win", "description": "d", "category": "prompt"}),
        )

    def test_stats_totals(self, db_path):
        self.seed(db_path)
        out = run_ok("stats", json.dumps({}))
        assert out["total"] == 6

    def test_stats_categories(self, db_path):
        self.seed(db_path)
        out = run_ok("stats", json.dumps({}))
        cats = {c["category"]: c["count"] for c in out["categories"]}
        assert cats["prompt"] == 4
        assert cats["harness"] == 1
        assert cats["context"] == 1

    def test_stats_filtered_by_type(self, db_path):
        self.seed(db_path)
        out = run_ok("stats", json.dumps({"type": "error"}))
        assert out["total"] == 5

    def test_stats_empty_db(self, db_path):
        out = run_ok("stats", json.dumps({}))
        assert out["total"] == 0
        assert out["categories"] == []


# --- trends ---


class TestTrends:
    def test_trends_empty_db(self, db_path):
        out = run_ok("trends", json.dumps({}))
        assert out["weeks"] == []

    def test_trends_groups_by_week(self, db_path):
        run_ok(
            "log-error",
            json.dumps({"summary": "e1", "description": "d", "category": "prompt"}),
        )
        out = run_ok("trends", json.dumps({}))
        assert len(out["weeks"]) >= 1
        assert out["weeks"][0]["count"] >= 1

    def test_trends_filtered_by_type(self, db_path):
        run_ok(
            "log-error",
            json.dumps({"summary": "e1", "description": "d", "category": "prompt"}),
        )
        run_ok(
            "log-success",
            json.dumps({"summary": "s1", "description": "d", "category": "prompt"}),
        )
        out = run_ok("trends", json.dumps({"type": "error"}))
        total = sum(w["count"] for w in out["weeks"])
        assert total == 1


# --- check-reminder ---


class TestCheckReminder:
    def test_no_entries_no_reminder(self, db_path):
        out = run_ok("check-reminder")
        assert out["should_remind"] is False

    def test_few_entries_no_reminder(self, db_path):
        for i in range(3):
            run_ok(
                "log-error",
                json.dumps(
                    {"summary": f"e{i}", "description": "d", "category": "prompt"}
                ),
            )
        out = run_ok("check-reminder")
        assert out["should_remind"] is False

    def test_enough_entries_triggers_reminder(self, db_path):
        for i in range(6):
            run_ok(
                "log-error",
                json.dumps(
                    {"summary": f"e{i}", "description": "d", "category": "prompt"}
                ),
            )
        out = run_ok("check-reminder")
        assert out["should_remind"] is True
        assert out["unreviewed"] == 6

    def test_recent_review_suppresses_reminder(self, db_path):
        for i in range(6):
            run_ok(
                "log-error",
                json.dumps(
                    {"summary": f"e{i}", "description": "d", "category": "prompt"}
                ),
            )
        run_ok("set-metadata", extra_args=["last_reviewed_at", datetime.now().isoformat()])
        out = run_ok("check-reminder")
        assert out["should_remind"] is False


# --- set-metadata ---


class TestSetMetadata:
    def test_set_and_read(self, db_path):
        run_ok("set-metadata", extra_args=["last_reviewed_at", "2026-01-01T00:00:00"])
        conn = sqlite3.connect(db_path)
        val = conn.execute(
            "SELECT value FROM metadata WHERE key = 'last_reviewed_at'"
        ).fetchone()[0]
        conn.close()
        assert val == "2026-01-01T00:00:00"

    def test_set_overwrites(self, db_path):
        run_ok("set-metadata", extra_args=["last_reviewed_at", "2026-01-01"])
        run_ok("set-metadata", extra_args=["last_reviewed_at", "2026-02-01"])
        conn = sqlite3.connect(db_path)
        val = conn.execute(
            "SELECT value FROM metadata WHERE key = 'last_reviewed_at'"
        ).fetchone()[0]
        conn.close()
        assert val == "2026-02-01"

    def test_set_metadata_missing_args(self, db_path):
        result = run_cmd("set-metadata")
        assert result.returncode != 0


# --- edge cases ---


class TestEdgeCases:
    def test_unknown_subcommand(self, db_path):
        result = run_cmd("bogus")
        assert result.returncode != 0

    def test_no_subcommand(self, db_path):
        result = run_cmd("")
        assert result.returncode != 0

    def test_invalid_json_stdin(self, db_path):
        result = run_cmd("log-error", "not json")
        assert result.returncode != 0

    def test_tags_stored_as_json_array(self, db_path):
        entry = {
            "summary": "s",
            "description": "d",
            "category": "prompt",
            "tags": ["a", "b"],
        }
        run_ok("log-error", json.dumps(entry))
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        row = dict(conn.execute("SELECT tags FROM entries WHERE id = 1").fetchone())
        conn.close()
        assert json.loads(row["tags"]) == ["a", "b"]

    def test_null_optional_fields(self, db_path):
        entry = {
            "summary": "s",
            "description": "d",
            "category": "meta",
        }
        run_ok("log-error", json.dumps(entry))
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        row = dict(conn.execute("SELECT * FROM entries WHERE id = 1").fetchone())
        conn.close()
        assert row["triggering_prompt"] is None
        assert row["subcategory"] is None
        assert row["project"] is None
        assert row["tags"] is None

    def test_default_db_path(self, tmp_path):
        """Without RETRO_DB, uses ~/.retro/retro.db."""
        env = os.environ.copy()
        env.pop("RETRO_DB", None)
        env["HOME"] = str(tmp_path)
        result = run_cmd("init", env_override=env)
        assert result.returncode == 0
        out = json.loads(result.stdout)
        assert out["path"] == str(tmp_path / ".retro" / "retro.db")
