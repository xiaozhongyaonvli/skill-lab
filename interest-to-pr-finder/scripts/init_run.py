#!/usr/bin/env python3
"""Initialize a governed run directory in the global cache tree."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


ARTIFACT_NAMES = [
    "runtime-input.json",
    "intent-contract.json",
    "requirement-surface.json",
    "execution-plan.json",
    "stage-status.json",
    "events.jsonl",
    "raw_repo_candidates.json",
    "repo_candidates.json",
    "selected_repos.json",
    "repo-selection-receipt.json",
    "selection-gate.json",
    "raw_issue_candidates.json",
    "issue_candidates.json",
    "fallback-receipt.json",
    "final-report.md",
    "cleanup-receipt.json",
]


def slugify(value: str) -> str:
    chars = []
    previous_dash = False
    for ch in value.lower():
        if ch.isalnum():
            chars.append(ch)
            previous_dash = False
        elif not previous_dash:
            chars.append("-")
            previous_dash = True
    slug = "".join(chars).strip("-")
    return slug[:40] if slug else "run"


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a governed run directory for interest-to-pr-finder.")
    parser.add_argument("--topic", required=True, help="User topic for this run")
    return parser.parse_args(list(argv))


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv or __import__("sys").argv[1:])
    skill_root = Path(__file__).resolve().parent.parent
    base_dir = skill_root / "cache" / slugify(args.topic)
    base_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    run_dir = base_dir / timestamp
    run_dir.mkdir(parents=True, exist_ok=False)

    runtime_input = {
        "skill": "interest-to-pr-finder",
        "topic": args.topic,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "cwd": str(Path.cwd().resolve()),
        "skill_root": str(skill_root),
        "cache_topic_dir": str(base_dir),
        "run_dir": str(run_dir),
        "route_snapshot": {
            "selected_skill": "interest-to-pr-finder",
            "entry_mode": "root",
        },
        "authority_flags": {
            "can_freeze_requirement": True,
            "can_advance_stage": True,
            "can_declare_completion": True,
            "can_invoke_fallback": True,
            "can_spawn_issue_triage_children": True,
        },
        "artifacts": {name: str(run_dir / name) for name in ARTIFACT_NAMES},
    }
    stage_status = {
        "current_stage": "runtime_init",
        "completed_stages": [],
        "blocked_stage": None,
        "truth_level": "authoritative",
        "fallback_active": False,
    }

    (run_dir / "runtime-input.json").write_text(
        json.dumps(runtime_input, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (run_dir / "stage-status.json").write_text(
        json.dumps(stage_status, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (run_dir / "events.jsonl").write_text("", encoding="utf-8")

    print(
        json.dumps(
            {
                "run_dir": str(run_dir),
                "runtime_input": str(run_dir / "runtime-input.json"),
                "stage_status": str(run_dir / "stage-status.json"),
                "cache_topic_dir": str(base_dir),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
