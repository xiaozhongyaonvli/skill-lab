#!/usr/bin/env python3
"""Freeze the user intent into intent-contract.json."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Freeze interest-to-pr-finder intent contract.")
    parser.add_argument("--run-dir", required=True, help="Run directory")
    parser.add_argument("--topic", required=True, help="User topic")
    parser.add_argument("--preferences", default="", help="Preference file path when present")
    parser.add_argument("--goal", default="Find repositories and issues aligned to the user's interests")
    parser.add_argument("--deliverable", default="Selected repositories and a contribution shortlist")
    parser.add_argument("--constraints", default="Use governed runtime flow and avoid silent fallback")
    parser.add_argument("--acceptance", default="Repositories must be selected through the governed flow before issue triage")
    parser.add_argument("--non-goals", default="Ad hoc prose-only repository recommendation")
    parser.add_argument("--autonomy-mode", default="guided")
    parser.add_argument("--assumptions", default="GitHub search and local scripts are available")
    return parser.parse_args(list(argv))


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv or __import__("sys").argv[1:])
    run_dir = Path(args.run_dir).resolve()
    preference_path = args.preferences
    if not preference_path:
        skill_root = Path(__file__).resolve().parent.parent
        global_preferences = skill_root / "preferences.json"
        preference_path = str(global_preferences) if global_preferences.exists() else ""
    payload = {
        "user_topic": args.topic,
        "preferences_path": preference_path,
        "goal": args.goal,
        "deliverable": args.deliverable,
        "constraints": [item.strip() for item in args.constraints.split(";") if item.strip()],
        "acceptance_criteria": [item.strip() for item in args.acceptance.split(";") if item.strip()],
        "non_goals": [item.strip() for item in args.non_goals.split(";") if item.strip()],
        "autonomy_mode": args.autonomy_mode,
        "assumptions": [item.strip() for item in args.assumptions.split(";") if item.strip()],
    }
    (run_dir / "intent-contract.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
