#!/bin/sh
# retro session reminder
# Checks for unreviewed entries and prints a reminder if needed.

# Find db.py relative to this script
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DB_SCRIPT="${SCRIPT_DIR}/../scripts/db.py"

if [ ! -f "$DB_SCRIPT" ]; then
    exit 0
fi

RESULT=$(python3 "$DB_SCRIPT" check-reminder 2>/dev/null)
if [ $? -ne 0 ]; then
    exit 0
fi

# Parse JSON with pure shell (avoid jq dependency)
SHOULD_REMIND=$(printf '%s' "$RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('should_remind', False))" 2>/dev/null)
UNREVIEWED=$(printf '%s' "$RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('unreviewed', 0))" 2>/dev/null)

if [ "$SHOULD_REMIND" = "True" ]; then
    printf 'retro: You have %s unreviewed log entries. Run /retro:review to check your patterns.\n' "$UNREVIEWED"
fi
