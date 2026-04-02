#!/usr/bin/env python3
"""Find the latest cached run for a topic."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable


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
    parser = argparse.ArgumentParser(description="Find the latest cached run for a topic.")
    parser.add_argument("--topic", required=True, help="User topic")
    return parser.parse_args(list(argv))


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv or __import__("sys").argv[1:])
    skill_root = Path(__file__).resolve().parent.parent
    topic_dir = skill_root / "cache" / slugify(args.topic)
    if not topic_dir.exists():
        print(json.dumps({"found": False, "topic_dir": str(topic_dir)}, ensure_ascii=False))
        return 0

    run_dirs = sorted([path for path in topic_dir.iterdir() if path.is_dir()], reverse=True)
    if not run_dirs:
        print(json.dumps({"found": False, "topic_dir": str(topic_dir)}, ensure_ascii=False))
        return 0

    latest = run_dirs[0]
    payload = {
        "found": True,
        "topic_dir": str(topic_dir),
        "latest_run_dir": str(latest),
        "has_repo_candidates": (latest / "repo_candidates.json").exists(),
        "has_issue_candidates": (latest / "issue_candidates.json").exists(),
        "has_final_report": (latest / "final-report.md").exists(),
    }
    print(json.dumps(payload, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
