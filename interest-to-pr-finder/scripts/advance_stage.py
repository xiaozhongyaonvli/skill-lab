#!/usr/bin/env python3
"""Advance the canonical stage-status.json in fixed order."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable


STAGE_ORDER = [
    "runtime_init",
    "deep_interview",
    "requirement_freeze",
    "execution_plan",
    "repo_search",
    "candidate_prepare",
    "repo_selection",
    "selection_gate",
    "issue_search",
    "finalize",
    "cleanup",
]


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Advance stage-status.json in fixed order.")
    parser.add_argument("--run-dir", required=True, help="Run directory")
    parser.add_argument("--from", dest="from_stage", required=True, help="Expected current stage")
    parser.add_argument("--to", dest="to_stage", required=True, help="Next stage")
    parser.add_argument("--status", choices=["completed", "blocked"], default="completed")
    return parser.parse_args(list(argv))


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv or __import__("sys").argv[1:])
    run_dir = Path(args.run_dir).resolve()
    stage_path = run_dir / "stage-status.json"
    payload = json.loads(stage_path.read_text(encoding="utf-8-sig"))

    if payload.get("current_stage") != args.from_stage:
        raise SystemExit(f"Current stage is {payload.get('current_stage')}, expected {args.from_stage}.")

    current_index = STAGE_ORDER.index(args.from_stage)
    next_index = STAGE_ORDER.index(args.to_stage)
    if next_index != current_index + 1:
        raise SystemExit("Stage transition violates fixed stage order.")

    completed = payload.get("completed_stages", [])
    if args.from_stage not in completed:
        completed.append(args.from_stage)

    payload["completed_stages"] = completed
    payload["current_stage"] = args.to_stage
    if args.status == "blocked":
        payload["blocked_stage"] = args.to_stage

    stage_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
