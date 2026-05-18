# Event Schema

## Required Fields

Every event in `events.jsonl` should contain:

- `timestamp`
- `type`
- `summary`
- `tags`

## Optional Fields

Use these when relevant:

- `files`
- `command`
- `artifacts`
- `reason`
- `outcome`
- `next_step`

## Event Types

### `user_request`

Use for a user instruction or scope change.

### `assistant_action`

Use for a meaningful action such as reading files, running a command, or preparing a draft.

### `file_change`

Use for creating, editing, renaming, or removing files that materially affect the workflow.

### `decision`

Use for trade-offs, assumptions, or narrowing a path.

### `result`

Use for a meaningful output or milestone.

## Example Event

```json
{
  "timestamp": "2026-04-03T10:30:00+08:00",
  "type": "assistant_action",
  "summary": "Reviewed the existing repository layout and skill format before scaffolding a new skill",
  "files": ["README.md", "interest-to-pr-finder/SKILL.md"],
  "tags": ["discovery", "skill-structure"]
}
```

## Synthesis Mapping

Map captured events into draft-skill sections like this:

- `user_request` -> trigger patterns, user intent
- `assistant_action` -> workflow steps
- `file_change` -> outputs, reusable assets, scripts
- `decision` -> decision rules, guardrails
- `result` -> outputs, completion criteria

## Recommended Tags

Use lightweight tags to improve SOP grouping during synthesis:

- `discovery`
- `context`
- `analysis`
- `execution`
- `edit`
- `output`
- `finalize`
- `cleanup`
