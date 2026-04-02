#!/usr/bin/env python3
"""Materialize numbered repository selection into selected_repos.json."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Iterable


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Apply numbered repository selection.")
    parser.add_argument("--run-dir", required=True, help="Run directory")
    parser.add_argument("--choices", required=True, help="User choices such as '1 3' or '2,5'")
    return parser.parse_args(list(argv))


def parse_choices(value: str) -> list[int]:
    parts = re.split(r"[\s,]+", value.strip())
    result = []
    for part in parts:
        if not part:
            continue
        result.append(int(part))
    return result


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv or __import__("sys").argv[1:])
    run_dir = Path(args.run_dir).resolve()
    repo_candidates = json.loads((run_dir / "repo_candidates.json").read_text(encoding="utf-8-sig"))
    if not isinstance(repo_candidates, list):
        raise SystemExit("repo_candidates.json must be a list.")

    indexes = parse_choices(args.choices)
    selected = []
    seen = set()
    for index in indexes:
        if index < 1 or index > len(repo_candidates):
            raise SystemExit(f"Selection index out of range: {index}")
        zero_index = index - 1
        if zero_index in seen:
            continue
        seen.add(zero_index)
        selected.append(repo_candidates[zero_index])

    if not selected:
        raise SystemExit("No repositories selected.")

    (run_dir / "selected_repos.json").write_text(
        json.dumps(selected, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
