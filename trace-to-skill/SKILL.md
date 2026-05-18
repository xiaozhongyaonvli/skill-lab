---
name: trace-to-skill
description: Capture a bounded user-assistant workflow as structured events and synthesize the captured trace into a reusable skill draft. Use when the user wants to start recording a workflow, stop recording later, and convert the recorded pipeline into a draft skill with trigger guidance, workflow steps, reusable resources, and a SKILL.md scaffold.
---

# Trace To Skill

## Overview

Use this skill when the user wants to turn a real interaction sequence into a reusable skill.

This skill is a governed capture runtime with three phases:

1. start capture
2. append structured events during the session
3. stop capture and synthesize a skill draft

Preferred explicit aliases:

- `@trace-start`
- `@trace-stop`

Do not treat the chat transcript as the canonical source of truth. The canonical source is the capture folder and its structured artifacts.

This skill is intentionally narrow. Its job is to extract a reusable SOP and produce a draft skill. It is not responsible for fully auditing or optimizing the generated skill.

## User Experience Goal

From the user's perspective, this skill should feel nearly zero-intrusion.

The intended user flow is:

1. the user says `@trace-start`
2. the user continues normal work without extra bookkeeping
3. the user says `@trace-stop`
4. the skill returns a synthesized SOP and draft skill

Between start and stop, the user should not need to manually write events, classify steps, manage JSON files, or point the skill at a capture directory.

Those capture details are internal responsibilities of this skill.

The user-facing contract is strict:

- the user starts with `@trace-start`
- the user stops with `@trace-stop`
- everything else is internal implementation detail

## Scope Boundary

This skill is responsible for:

- capturing a bounded workflow
- structuring the workflow as events
- extracting a reusable SOP
- generating a draft skill

This skill is not responsible for:

- deep context-engineering review
- subagent overlap analysis
- canonical truth-surface governance audits across multiple agents
- memory architecture design
- KV-cache or prompt-prefix optimization
- turning the draft into a fully optimized production-ready skill

Treat those as follow-on work for separate evaluator or refiner skills.

## Runtime Invariants

These invariants are mandatory:

- capture must have an explicit start
- capture must have an explicit stop
- events must be structured, not free-form transcript dumps
- internal chain-of-thought must not be logged
- terminal output must be summarized, not copied in full
- synthesis must separate raw trace facts from generalized workflow guidance

If an invariant would be violated, stop and explain the constraint instead of silently degrading.

## Canonical Artifact Surface

Runtime capture data must be written to a user-writable data root, not the installed skill code directory.

Configured runtime data root:

```text
<data-root> from %LOCALAPPDATA%\trace-to-skill\config.json
```

If `TRACE_TO_SKILL_DATA_ROOT` is set, use that directory instead.
If the user passes `--data-root`, persist that choice and use it for later capture commands.
The persisted runtime config is stored in `%LOCALAPPDATA%\trace-to-skill\config.json`.
See [assets/runtime-config.example.json](assets/runtime-config.example.json) for the expected format.
If there is no configured `data_root`, or the configured path is not writable, stop and require the user to rerun with `--data-root "<writable-path>"`.

For each capture, create a run directory under:

```text
<data-root>/captures/<capture-id>/
```

Required artifacts:

- `capture-meta.json`
- `events.jsonl`
- `summary.md`
- `skill-draft.md`
- `<data-root>/state/active-capture.json` while a capture is active

Recommended optional artifacts:

- `draft-skill/SKILL.md`
- `draft-skill/agents/openai.yaml`
- `draft-skill/references/`
- `draft-skill/scripts/`

## Event Model

The default event types are:

- `user_request`
- `assistant_action`
- `file_change`
- `decision`
- `result`

Each event should include:

- `timestamp`
- `type`
- `summary`
- `tags`

Optional fields:

- `files`
- `command`
- `artifacts`
- `reason`
- `outcome`
- `next_step`

Read [references/event-schema.md](references/event-schema.md) when you need the exact schema and synthesis mapping.

## Start Capture

When the user explicitly starts recording, prefer the alias `@trace-start`:

1. normalize a capture name or topic
2. initialize a new capture directory
3. write `capture-meta.json`
4. register the active capture in runtime state
5. acknowledge the capture scope

User-facing command:

```text
python scripts/trace_start.py --skill-root "<skill-root>" --topic "<topic>" [--data-root "<data-root>"]
```

If the user does not provide a topic, derive a short topic from their request or let the script use the default topic.

Internal implementation may use `start_capture.py`, but that is not part of the user-facing flow.
The implementation must not assume `<skill-root>` is writable.

## Append Events

During the capture window, append only high-value events.

Good events:

- user requests that change direction
- important file reads
- meaningful commands
- file edits with outcome
- decisions and trade-offs
- final results

Do not log:

- every tiny exploratory step
- full command output
- raw hidden reasoning

Prefer a concise structured summary over verbose raw text.
Do not expose event append operations to the user. Event creation, event grouping, and capture bookkeeping are internal responsibilities of the skill runtime.

## Stop Capture

When the user explicitly ends recording, prefer the alias `@trace-stop`:

1. close the capture
2. summarize the trace into a readable markdown summary
3. synthesize a draft skill from the event stream
4. clear the active capture state
5. present the draft path to the user

User-facing command:

```text
python scripts/trace_stop.py --skill-root "<skill-root>" [--data-root "<data-root>"] [--emit-draft-skill]
```

Internal implementation may use `finish_capture.py`, `stop_capture.py`, and `synthesize_skill.py`, but those are not part of the user-facing flow.
Finalization must continue to use the runtime data root rather than writing back into the installed skill directory.

## Internal Runtime

These scripts are internal building blocks, not user actions:

- `start_capture.py`
- `append_event.py`
- `capture_status.py`
- `stop_capture.py`
- `finish_capture.py`
- `synthesize_skill.py`

If the user is interacting through the intended experience, they should never need to call these directly.

## Synthesis Rules

When generating the draft skill:

- infer the recurring user intent
- extract only the stable reusable SOP
- separate one-off details from reusable guidance
- propose scripts only for repeated deterministic steps
- keep the generated `SKILL.md` concise

The generated draft should contain these sections:

1. capture summary
2. likely trigger patterns
3. inputs and dependencies
4. structured SOP grouped into discovery, execution, and finalize
5. decision rules
6. outputs
7. suggested reusable resources
8. draft `SKILL.md`

## Output Strategy

Default to writing:

- a human-readable summary in `summary.md`
- a synthesis report in `skill-draft.md`

If the user explicitly wants a scaffolded draft skill folder, run synthesis with `--emit-draft-skill` and also generate:

```text
<capture-dir>/draft-skill/
```

## Editing Guidance

When refining this skill later:

- keep the capture schema stable
- treat event names as a compatibility surface
- prefer additive changes to the schema
- keep synthesis deterministic where possible
