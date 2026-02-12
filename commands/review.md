---
description: Review logged errors and successes, spot patterns, generate CLAUDE.md rules
---

# /review

You are reviewing the user's agentic coding log to surface patterns, track improvement, and generate CLAUDE.md rules.

## Setup

1. Determine the plugin root: use `${CLAUDE_PLUGIN_ROOT}` if available, otherwise find the `retro` plugin directory containing `scripts/db.py`.
2. Set the DB script path: `"${CLAUDE_PLUGIN_ROOT}/scripts/db.py"`

## Data Gathering

Run these queries to gather data. If the user provided a filter (e.g., `/log-review prompt` or `/log-review --project myapp`), pass it through.

```bash
# Overall stats
echo '{}' | python3 "${CLAUDE_PLUGIN_ROOT}/scripts/db.py" stats

# Stats filtered by errors only
echo '{"type":"error"}' | python3 "${CLAUDE_PLUGIN_ROOT}/scripts/db.py" stats

# Stats filtered by successes only
echo '{"type":"success"}' | python3 "${CLAUDE_PLUGIN_ROOT}/scripts/db.py" stats

# Weekly trends
echo '{}' | python3 "${CLAUDE_PLUGIN_ROOT}/scripts/db.py" trends

# Recent entries (last 20)
echo '{"limit":20}' | python3 "${CLAUDE_PLUGIN_ROOT}/scripts/db.py" query

# All entries for pattern analysis
echo '{}' | python3 "${CLAUDE_PLUGIN_ROOT}/scripts/db.py" query
```

If the DB is empty or doesn't exist, say: "No entries yet. Use `/retro:error` or `/retro:success` to start tracking patterns."

## Presentation

Present the review in this order:

### 1. Overview
- Total entries (errors vs successes)
- Date range covered
- Most active project(s)

### 2. Top Failure Modes
- Categories with 3+ errors, ranked by count
- For each: count, subcategory breakdown, example summary

### 3. Patterns
- Look for clusters: same category appearing across different projects or time periods
- Look for sequences: errors that tend to follow each other
- Call out any category where errors are INCREASING over recent weeks

### 4. Wins
- List successes, grouped by category
- Highlight any category where the user has both errors AND recent successes (milestone detection)

### 5. Milestone Detection
For any category where the user has errors AND recent successes (successes logged AFTER the errors), call it out:

> You logged N errors in `category/subcategory`, but your last M entries in that area are successes. You've leveled up here.

This is the payoff -- visible proof that the training loop works.

### 6. CLAUDE.md Rule Generation

**From errors (threshold: 3+ occurrences in a category):**
For each qualifying category, generate a specific, actionable CLAUDE.md rule. Format as a copy-paste-ready block:

```markdown
## retro: [category/subcategory]
<!-- Generated from N error entries. Remove if no longer relevant. -->
[Specific, actionable rule derived from the pattern. Not generic advice -- reference the actual failure mode.]
```

**From successes (threshold: 2+ occurrences in a category):**
Same format, but framed as a reinforcement:

```markdown
## retro: [category/subcategory]
<!-- Generated from N success entries. This pattern works -- keep doing it. -->
[Specific technique or approach to continue using.]
```

### 7. Offer to Write Rules

After presenting recommendations, ask:

"Want me to add any of these to your project CLAUDE.md? I'll put them under an `## retro rules` section."

If yes, use Edit to append the selected rules under `## retro rules` in the project's CLAUDE.md. If the section doesn't exist, create it. If it does, append below existing rules.

### 8. Offer Drill-Down

"Want to drill into any specific category or time period?"

## Update Review Timestamp

After presenting the review, update the last-reviewed timestamp:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/db.py" set-metadata last_reviewed_at "$(date -Iseconds)"
```

This resets the session reminder counter so the user won't be nagged until new entries accumulate.
