#!/usr/bin/env python3
"""Append a structured event to the run JSONL log."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Append an event to interest-to-pr-finder events.jsonl.")
    parser.add_argument("--run-dir", required=True, help="Run directory created by init_run.py")
    parser.add_argument("--step", required=True, help="Short step name, for example repo-search")
    parser.add_argument("--status", required=True, help="Status such as started, completed, fallback, or error")
    parser.add_argument("--message", required=True, help="Human-readable description")
    parser.add_argument("--data", help="Optional JSON object as a string")
    return parser.parse_args(list(argv))


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv or __import__("sys").argv[1:])
    run_dir = Path(args.run_dir).resolve()
    payload = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "step": args.step,
        "status": args.status,
        "message": args.message,
    }
    if args.data:
        try:
            payload["data"] = json.loads(args.data)
        except json.JSONDecodeError:
            payload["data"] = args.data

    events_path = run_dir / "events.jsonl"
    with events_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload, ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
