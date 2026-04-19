import subprocess, sys, json


def test_scripts_shim_works():
    result = subprocess.run(
        [sys.executable, "scripts/db.py", "stats"],
        input=b"{}",
        capture_output=True,
        env={**__import__("os").environ, "RETRO_DB": "/tmp/test-shim.db"},
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert "total" in data
