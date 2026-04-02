#!/usr/bin/env python3
"""Freeze requirement-surface.json from intent-contract.json."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Freeze requirement surface for interest-to-pr-finder.")
    parser.add_argument("--run-dir", required=True, help="Run directory")
    return parser.parse_args(list(argv))


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv or __import__("sys").argv[1:])
    run_dir = Path(args.run_dir).resolve()
    intent = json.loads((run_dir / "intent-contract.json").read_text(encoding="utf-8-sig"))
    payload = {
        "primary_objective": "Produce a governed repository selection before any issue triage.",
        "proxy_signals": [
            "Large star counts",
            "Repository popularity",
            "Plausible-sounding repository names",
        ],
        "intended_scope": "Repository discovery, repository selection, issue triage, and final reporting.",
        "completion_states": {
            "complete": "Selection gate passed, final report written, cleanup receipt written.",
            "partial": "Some repository evidence gathered but governed selection not completed.",
            "blocked": "Required stage or gate could not be completed.",
        },
        "selection_requirements": {
            "interactive_selection_required_when_candidate_count_at_least": 2,
            "selection_receipt_required": True,
            "selection_gate_required_before_issue_search": True,
        },
        "non_objectives": intent.get("non_goals", []),
        "fallback_policy": {
            "silent_fallback_allowed": False,
            "silent_degradation_allowed": False,
            "fallback_requires_receipt": True,
            "fallback_truth_level": "non_authoritative",
        },
    }
    (run_dir / "requirement-surface.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
