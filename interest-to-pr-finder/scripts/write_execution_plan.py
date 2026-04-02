#!/usr/bin/env python3
"""Write execution-plan.json from frozen inputs."""

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
    parser = argparse.ArgumentParser(description="Write execution plan for interest-to-pr-finder.")
    parser.add_argument("--run-dir", required=True, help="Run directory")
    return parser.parse_args(list(argv))


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv or __import__("sys").argv[1:])
    run_dir = Path(args.run_dir).resolve()
    runtime_input = json.loads((run_dir / "runtime-input.json").read_text(encoding="utf-8-sig"))
    requirement = json.loads((run_dir / "requirement-surface.json").read_text(encoding="utf-8-sig"))
    payload = {
        "frozen_inputs": {
            "topic": runtime_input.get("topic"),
            "cwd": runtime_input.get("cwd"),
            "authority_flags": runtime_input.get("authority_flags", {}),
            "selection_requirements": requirement.get("selection_requirements", {}),
        },
        "stage_order": STAGE_ORDER,
        "verification_commands": [
            "verify_stage_gate.py --gate repo-selection-required",
            "render_candidates.py --input <issue_candidates> --output <final-report>",
        ],
        "rollback_rules": [
            "Do not advance to issue_search if selection gate fails.",
            "On fallback, downgrade truth level and stop unless user explicitly approves degraded mode.",
        ],
        "cleanup_contract": {
            "cleanup_receipt_required": True,
            "final_report_required": True,
        },
        "selection_gate_rule": "repo-selection-receipt.json must exist and contain at least one selected repository before issue_search.",
    }
    (run_dir / "execution-plan.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
