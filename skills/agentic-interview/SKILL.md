---
name: agentic-interview
description: Use when conducting error or success interviews for retro logging. Provides taxonomy, interview methodology, and category classification for agentic coding patterns.
---

# Agentic Interview

Interview methodology for logging errors and successes in agentic coding workflows. The goal: trace every outcome back to YOUR input -- what you prompted, what context you provided, what guardrails you set (or didn't).

## Core Principle

The agent does what you tell it to. If the outcome was bad, the question is: **what could YOU have done differently?** Not "Claude messed up" -- that's a symptom. The root cause is always in the prompt, the context, the harness, or the meta-decisions around how you engaged.

## Interview Methodology

### Error Interviews

1. **Review conversation context** before asking anything. Look at what happened, what went wrong, and where the turning point was.

2. **Ask 3-5 specific questions, one at a time.** Adapt to the user's verbosity -- if they give detailed answers, ask fewer questions. If they're terse, probe deeper.

3. **Always capture the triggering prompt verbatim.** This is the single most valuable data point. Ask: "What exactly did you tell Claude before this went wrong? Can you paste or paraphrase the prompt?"

4. **Propose a category -- don't ask the user to classify.** Based on the conversation and answers, suggest: "This looks like a `prompt/missing-constraints` issue -- you told Claude what to do but not what NOT to do. Sound right?" Let them confirm or correct.

5. **Focus on the user's contribution.** Every question should orient toward: "What could you have done differently in your prompt, context setup, or tool configuration to prevent this?"

### Success Interviews

Same structure, adapted:

1. Review what worked in the conversation.
2. Ask 2-4 questions about what the user did that led to the good outcome.
3. Capture the triggering prompt or technique verbatim.
4. Propose a category.
5. Focus on what's repeatable -- "What specifically about your approach made this work?"

### Adapting Depth

- **Verbose user**: 2-3 focused questions, they're already giving you what you need.
- **Terse user**: 4-5 questions, probe for specifics. "Can you tell me more about what you expected vs what happened?"
- **User provides optional description**: Use it as a starting point, skip questions it already answers.

## Error Taxonomy

### prompt
Errors in how the user formulated their instruction to Claude.

| Subcategory | Description |
|------------|-------------|
| `ambiguous-instruction` | Prompt could be interpreted multiple ways; Claude picked the wrong one |
| `missing-constraints` | Told Claude what to do but not what NOT to do or what boundaries to respect |
| `too-verbose` | Prompt was so long Claude lost the actual requirement in the noise |
| `reference-vs-requirements` | Referenced a file/pattern but didn't specify what to do with it |
| `implicit-expectations` | Expected Claude to know something that wasn't stated |
| `no-success-criteria` | No way to verify if the output was correct |
| `wrong-abstraction-level` | Asked at the wrong level -- too high-level or too micro |

### context
Errors in the information environment Claude was operating in.

| Subcategory | Description |
|------------|-------------|
| `context-rot` | Conversation got so long that early context degraded or contradicted later context |
| `stale-context` | Claude was working with outdated information about the codebase or state |
| `context-overflow` | Too much context caused Claude to miss or deprioritize the actual task |
| `missing-context` | Claude didn't have access to information it needed |
| `wrong-context` | Claude had context but it was misleading or from the wrong source |

### harness
Errors in how tools, subagents, and the agentic harness were configured.

| Subcategory | Description |
|------------|-------------|
| `subagent-context-loss` | Spawned a subagent that lacked critical context from the parent conversation |
| `wrong-agent-type` | Used the wrong subagent type for the task |
| `no-guardrails` | Didn't set constraints on what Claude could modify/delete |
| `parallel-when-sequential` | Ran tasks in parallel that had dependencies |
| `sequential-when-parallel` | Ran tasks sequentially that could have been parallelized |
| `missing-validation` | Didn't verify Claude's output before moving on |
| `trusted-without-verification` | Accepted Claude's claim that something worked without checking |

### meta
Errors in the overall approach to working with the agent.

| Subcategory | Description |
|------------|-------------|
| `didnt-ask-clarifying-questions` | Dove into a task without understanding the full scope |
| `rushed-to-implementation` | Started coding before understanding the problem |
| `assumed-competence` | Assumed Claude knew something domain-specific without verifying |

## Success Taxonomy

### prompt
| Subcategory | Description |
|------------|-------------|
| `clarity` | Prompt was clear, structured, and unambiguous |

### context
| Subcategory | Description |
|------------|-------------|
| `management` | Effectively managed context -- rewound, compacted, or structured context to keep Claude focused |

### harness
| Subcategory | Description |
|------------|-------------|
| `tool-selection` | Chose the right tool/agent type for the job |
| `subagent-orchestration` | Effectively coordinated multiple agents or tool calls |

### workflow
| Subcategory | Description |
|------------|-------------|
| `design` | Good overall workflow design -- TDD, incremental steps, verification loops |

## Category Selection Guide

When proposing a category, use this decision tree:

1. **Was the prompt itself the problem?** -> `prompt/*`
   - Could Claude have done the right thing with a better prompt? Then it's a prompt issue.

2. **Did Claude have the wrong information?** -> `context/*`
   - Was the conversation too long, stale, or missing key info?

3. **Was the tooling/harness misconfigured?** -> `harness/*`
   - Wrong agent type, no guardrails, bad parallelization?

4. **Was the approach itself wrong?** -> `meta/*`
   - Should you have asked clarifying questions first? Planned before coding?

For successes, the same categories apply -- just flip the question: "What did the user do RIGHT in their prompt/context/harness/workflow?"
