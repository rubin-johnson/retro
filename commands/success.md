---
description: Log an agentic coding success with a structured interview
---

# /success

You are logging an agentic coding success. The goal is to capture what the user did RIGHT so the pattern can be repeated and eventually promoted to a CLAUDE.md rule.

## Setup

1. Load the `agentic-interview` skill for taxonomy and interview methodology.
2. Determine the plugin root: use `${CLAUDE_PLUGIN_ROOT}` if available, otherwise find the `retro` plugin directory containing `scripts/db.py`.

## Interview Flow

### Step 1: Review Context

Before asking anything, review the recent conversation. Look for:
- What worked well
- What the user did that led to a good outcome
- Specific techniques or patterns that were effective

If the user provided an optional description with the command, use it as a starting point.

### Step 2: Conduct Interview

Ask 2-4 specific questions, **one at a time**, using AskUserQuestion.

Essential questions (pick the most relevant):
- "What specifically did you do that led to this good outcome?"
- "Can you paste or paraphrase the prompt/approach that worked?"
- "Why do you think this worked where other approaches might not have?"
- "Is this something you'd want to repeat? What makes it repeatable?"

### Step 3: Capture What Worked

Get the specific technique, prompt, or approach verbatim. This is the pattern to preserve.

### Step 4: Propose Category

Based on the conversation and interview answers, propose a category and subcategory from the success taxonomy. Frame it as: "This looks like a `category/subcategory` win -- [brief explanation]. Sound right?"

Use AskUserQuestion with the proposed category as the recommended option and 2-3 alternatives.

### Step 5: Confirm and Write

Present a summary of what will be logged:
- **Summary**: One-line description
- **Category**: category/subcategory
- **What worked**: The specific technique
- **Why it worked**: The underlying principle

Ask the user to confirm with AskUserQuestion.

### Step 6: Write to Database

Run:
```bash
echo '<json_payload>' | python3 "${CLAUDE_PLUGIN_ROOT}/scripts/db.py" log-success
```

The JSON payload must include:
- `summary` (required)
- `description` (required)
- `category` (required)
- `triggering_prompt` (the verbatim prompt or technique)
- `subcategory`
- `project` (if determinable from cwd or conversation)
- `what_worked`
- `why_it_worked`
- `tags` (array of relevant keywords)

### Step 7: Acknowledge

After successfully logging, briefly acknowledge:

**Success logged.** This pattern is now tracked. When you run `/retro:review`, repeated successes in this category get promoted to CLAUDE.md rules -- turning good habits into permanent guardrails.
