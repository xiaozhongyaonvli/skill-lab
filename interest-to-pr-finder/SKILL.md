---
name: interest-to-pr-finder
description: Governed runtime for finding GitHub repositories and contribution issues from a user's interests. Use when the user wants repository scouting, numbered repository selection, cached contribution research, issue triage, or contribution recommendations for topics such as Python, Java, agents, context engineering, debugging, tracing, memory, evals, observability, or protocol tooling.
---

# Interest To Pr Finder

## Overview

Use this skill as a governed runtime, not as a loose checklist. The runtime must freeze user intent, freeze the requirement surface, freeze the execution plan, and then advance through fixed stages with receipts and gates.

The goal is not merely to mention plausible repositories. The goal is to produce a repository set that was explicitly selected through the governed flow, then use that selected set for downstream issue triage.

This skill now uses:

- numbered repository selection, not terminal checkbox UI
- a single-user global preference file at the skill root
- a global cache tree under the skill root so prior repository and issue work can be reused

## Runtime Invariants

These invariants are mandatory:

- fixed stage order
- freeze requirement before execution
- no silent fallback
- no silent degradation
- cleanup required before completion
- no duplicate canonical truth surface
- no issue triage before authoritative repository selection

If any invariant would be violated, stop, write a receipt that explains the violation, and do not silently continue.

## Canonical Truth Surface

For each run, create a run directory under the global cache tree:

```text
<skill-root>/cache/<topic-slug>/<timestamp>/
```

All authoritative state for the run lives there. Chat messages are explanatory only and are not the canonical source of truth.

Required run artifacts:

- `runtime-input.json`
- `intent-contract.json`
- `requirement-surface.json`
- `execution-plan.json`
- `stage-status.json`
- `events.jsonl`
- `raw_repo_candidates.json`
- `repo_candidates.json`
- `selected_repos.json`
- `repo-selection-receipt.json`
- `selection-gate.json`
- `raw_issue_candidates.json`
- `issue_candidates.json`
- `fallback-receipt.json`
- `final-report.md`
- `cleanup-receipt.json`

## Global Preference File

Maintain a single-user global preference file at:

```text
<skill-root>/preferences.json
```

If it does not exist, initialize it from `assets/preferences.example.json`.

Do not create per-run preference files unless the user explicitly asks for that. The canonical preference surface is the global file.

## Cache Lookup

Before opening a fresh run, check whether a relevant cached run already exists for the topic.

Run:

```bash
python scripts/find_cached_run.py --topic "<user topic>"
```

If a cached run exists:

- show the cached repositories and any cached issue shortlist to the user
- ask whether to reuse the cached run or start a fresh search
- only open a new run if the user declines reuse or wants updated search results

If no cached run exists, open a fresh run immediately.

## Fixed Stage Order

The runtime uses these stages in order:

1. `runtime_init`
2. `deep_interview`
3. `requirement_freeze`
4. `execution_plan`
5. `repo_search`
6. `candidate_prepare`
7. `repo_selection`
8. `selection_gate`
9. `issue_search`
10. `finalize`
11. `cleanup`

Never skip forward. Never mark a stage completed retroactively without writing its receipt.

## Authority Model

The root run owns the canonical truth surface.

Root authority may:

- freeze intent
- freeze requirement
- freeze execution plan
- advance stage
- declare completion
- write fallback receipts

Subagents may:

- inspect repositories
- inspect issue threads
- return structured findings

Subagents may not:

- rewrite `intent-contract.json`
- rewrite `requirement-surface.json`
- rewrite `execution-plan.json`
- advance the canonical stage
- declare the run complete

If subagents are used, treat them as bounded helpers and write their findings back into canonical artifacts from the root run only.

## Runtime Boot

Start every fresh run with:

```bash
python scripts/init_run.py --topic "<user topic>"
```

This creates the run directory in the global cache tree and initializes:

- `runtime-input.json`
- `stage-status.json`
- `events.jsonl`

Immediately log the run start:

```bash
python scripts/log_event.py --run-dir <run_dir> --step runtime_init --status completed --message "Run initialized"
```

## Stage 1: Deep Interview

Freeze the user's intent before repository search.

Create `intent-contract.json` with:

- `goal`
- `deliverable`
- `constraints`
- `acceptance_criteria`
- `non_goals`
- `autonomy_mode`
- `assumptions`
- `user_topic`
- `preferences_path`

Use:

```bash
python scripts/freeze_intent.py --run-dir <run_dir> --topic "<user topic>"
```

This should default to the global preference file if no explicit `--preferences` path is provided.

Then advance the stage:

```bash
python scripts/advance_stage.py --run-dir <run_dir> --from runtime_init --to deep_interview --status completed
```

## Stage 2: Requirement Freeze

Freeze the requirement surface before repository search. This is the canonical definition of what success means.

`requirement-surface.json` must include:

- `primary_objective`
- `proxy_signals`
- `intended_scope`
- `completion_states`
- `selection_requirements`
- `non_objectives`
- `fallback_policy`

Use:

```bash
python scripts/freeze_requirement.py --run-dir <run_dir>
```

Then advance the stage from `deep_interview` to `requirement_freeze`.

## Stage 3: Execution Plan

Freeze the execution plan before repository search.

`execution-plan.json` must include:

- `frozen_inputs`
- `stage_order`
- `verification_commands`
- `rollback_rules`
- `cleanup_contract`
- `selection_gate_rule`

Use:

```bash
python scripts/write_execution_plan.py --run-dir <run_dir>
```

Then advance the stage from `requirement_freeze` to `execution_plan`.

## Stage 4: Repository Search

Only after requirement and plan are frozen may repository search begin.

Search GitHub using the frozen requirement plus the global preferences. Save the raw repository search output to:

- `<run_dir>/raw_repo_candidates.json`

After search, log the step and advance the stage from `execution_plan` to `repo_search`.

## Stage 5: Candidate Prepare

Normalize repository candidates with:

```bash
python scripts/prepare_repo_candidates.py --input <run_dir>/raw_repo_candidates.json --output <run_dir>/repo_candidates.json --limit <n>
```

Then advance the stage from `repo_search` to `candidate_prepare`.

## Stage 6: Repository Selection

This stage is mandatory when there are 2 or more plausible repository candidates.

Hard rules:

- Do not ask the user to type repository names manually.
- The standard path is numbered selection in chat, such as `1 3` or `2,5`.
- Do not replace numbered selection with a prose-only recommendation list.
- If no selection is provided, stop at this stage.
- Do not perform issue search, do not draft issue recommendations, and do not write a final report before authoritative repository selection exists.

Show the user the numbered repository candidates from `repo_candidates.json`.

After the user replies with repository numbers, run:

```bash
python scripts\apply_number_selection.py --run-dir <run_dir> --choices "1,3"
python scripts\write_selection_receipt.py --run-dir <run_dir> --selected <run_dir>/selected_repos.json
python scripts\enforce_repo_selection.py --run-dir <run_dir>
```

Then advance the stage from `candidate_prepare` to `repo_selection`.

## Stage 7: Selection Gate

Before issue search, verify that repository selection was completed lawfully.

Run:

```bash
python scripts/verify_stage_gate.py --run-dir <run_dir> --gate repo-selection-required
```

This gate must confirm:

- `selected_repos.json` exists
- `repo-selection-receipt.json` exists
- selected repositories are present
- no silent fallback was used

Write the result to `selection-gate.json`.

If the gate fails, stop. Do not move to issue search.

If the gate passes, then and only then may you advance from `repo_selection` to `selection_gate`.

## Stage 8: Issue Search

Only after `selection_gate` is green may issue search begin.

Save raw issue findings to:

- `<run_dir>/raw_issue_candidates.json`

Use [filtering-rules.md](./references/filtering-rules.md) to judge likely unclaimed issues. If subagents are used, they may inspect repositories but must return structured findings only.

Then write normalized issue candidates to:

- `<run_dir>/issue_candidates.json`

The normalized issue file is mandatory because users may continue issue work later and the model must not rely on volatile chat context.

Advance the stage from `selection_gate` to `issue_search`.

## Stage 9: Finalize

Render the final grouped Markdown report with:

```bash
python scripts/render_candidates.py --input <run_dir>/issue_candidates.json --output <run_dir>/final-report.md
```

This stage is not complete until the report exists and references the selected repositories rather than ad hoc repository prose.

## Stage 10: Cleanup

Completion requires cleanup. Write `cleanup-receipt.json` and mark the run complete only after:

- all required receipts are present
- final report exists
- truth level is explicit
- any fallback is documented
- issue candidates are persisted

Use:

```bash
python scripts/write_cleanup_receipt.py --run-dir <run_dir>
```

## Fallback Governance

Fallback is allowed only when it is explicit, documented, and downgraded in truth level.

When fallback is necessary:

1. Write `fallback-receipt.json`
2. Mark truth level `non_authoritative`
3. Log a hazard event to `events.jsonl`
4. Stop unless the user explicitly approves the degraded path

Fallback is never silent.

## Scripts

Runtime scripts:

- `scripts/init_run.py`
- `scripts/find_cached_run.py`
- `scripts/log_event.py`
- `scripts/freeze_intent.py`
- `scripts/freeze_requirement.py`
- `scripts/write_execution_plan.py`
- `scripts/advance_stage.py`
- `scripts/apply_number_selection.py`
- `scripts/enforce_repo_selection.py`
- `scripts/verify_stage_gate.py`
- `scripts/write_selection_receipt.py`
- `scripts/write_fallback_receipt.py`
- `scripts/write_cleanup_receipt.py`

Domain scripts:

- `scripts/prepare_repo_candidates.py`
- `scripts/render_candidates.py`

Legacy script:

- `scripts/select_repos.py`
  Keep only for compatibility. Do not use it as the standard path.

## Example Execution Pattern

1. Check for a cached run for the topic.
2. Reuse the cache if the user approves; otherwise open a fresh run in the global cache tree.
3. Freeze intent into `intent-contract.json`.
4. Freeze the requirement surface.
5. Freeze the execution plan.
6. Search repositories and save raw results.
7. Prepare candidates and show them with numbers.
8. Materialize the user's numbered selection into canonical artifacts.
9. Verify the selection gate.
10. Search issues only for the selected repositories.
11. Save issue candidates, render the final report, and write cleanup receipt.
