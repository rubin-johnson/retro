---
description: Log an agentic coding error with a structured interview
---

# /error

You are logging an agentic coding error. The goal is to trace the error back to the USER's input -- what they prompted, what context they provided, what guardrails they set (or didn't).

## Setup

1. Load the `agentic-interview` skill for taxonomy and interview methodology.
2. Determine the plugin root: use `${CLAUDE_PLUGIN_ROOT}` if available, otherwise find the `retro` plugin directory containing `scripts/db.py`.

## Interview Flow

### Step 1: Review Context

Before asking anything, review the recent conversation. Look for:
- What went wrong
- What the user asked for vs what happened
- The turning point where things diverged

If the user provided an optional description with the command, use it as a starting point.

### Step 2: Conduct Interview

Ask 3-5 specific questions, **one at a time**, using AskUserQuestion. Adapt to the user's verbosity.

Essential questions (pick the most relevant):
- "What exactly did you tell Claude before this went wrong? Can you paste or paraphrase the prompt?"
- "What did you expect to happen vs what actually happened?"
- "Looking back, what could you have done differently in your prompt or setup?"
- "Was there context Claude was missing, or context that was misleading?"
- "Were there any constraints you meant to set but didn't?"

### Step 3: Capture Triggering Prompt

The verbatim triggering prompt is the most valuable data point. If the user hasn't provided it yet, ask specifically.

### Step 4: Propose Category

Based on the conversation and interview answers, propose a category and subcategory from the taxonomy. Frame it as: "This looks like a `category/subcategory` issue -- [brief explanation]. Sound right?"

Use AskUserQuestion with the proposed category as the recommended option and 2-3 alternatives.

### Step 5: Confirm and Write

Present a summary of what will be logged:
- **Summary**: One-line description
- **Category**: category/subcategory
- **Lesson**: What was learned
- **Corrective action**: What to do differently next time

Ask the user to confirm with AskUserQuestion.

### Step 6: Write to Database

Run:
```bash
echo '<json_payload>' | python3 "${CLAUDE_PLUGIN_ROOT}/scripts/db.py" log-error
```

The JSON payload must include:
- `summary` (required)
- `description` (required)
- `category` (required)
- `triggering_prompt` (the verbatim prompt)
- `subcategory`
- `project` (if determinable from cwd or conversation)
- `lesson`
- `corrective_action`
- `tags` (array of relevant keywords)

### Step 7: Rewind Prompt

After successfully logging, tell the user:

---

**Error logged.** Now clean the slate.

The error is captured -- the debugging context in this conversation is now dead weight. Rewind to before the error occurred:

1. Press **Escape twice** to open the conversation navigator
2. Find the message just before the error started
3. Select **"Restore conversation only"** (keeps your code changes, removes the debugging context)

This gives Claude a clean mental model going forward. The lesson lives in the database, not in a polluted conversation.

---

This is not optional advice. Stale debugging context causes follow-on errors. Clean the slate.
