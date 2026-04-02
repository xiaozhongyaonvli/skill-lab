#!/usr/bin/env python3
"""Write fallback-receipt.json and downgrade truth level."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Write fallback receipt for interest-to-pr-finder.")
    parser.add_argument("--run-dir", required=True, help="Run directory")
    parser.add_argument("--reason", required=True, help="Fallback reason")
    parser.add_argument("--degraded-mode", required=True, help="Degraded path description")
    return parser.parse_args(list(argv))


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv or __import__("sys").argv[1:])
    run_dir = Path(args.run_dir).resolve()
    payload = {
        "reason": args.reason,
        "degraded_mode": args.degraded_mode,
        "truth_level": "non_authoritative",
    }
    (run_dir / "fallback-receipt.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    stage_path = run_dir / "stage-status.json"
    stage = json.loads(stage_path.read_text(encoding="utf-8-sig"))
    stage["truth_level"] = "non_authoritative"
    stage["fallback_active"] = True
    if stage.get("current_stage") in {"candidate_prepare", "repo_selection", "selection_gate"}:
        stage["current_stage"] = "repo_selection"
        stage["blocked_stage"] = "repo_selection"
    stage_path.write_text(json.dumps(stage, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
