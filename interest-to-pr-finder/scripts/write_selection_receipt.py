#!/usr/bin/env python3
"""Write repo-selection-receipt.json from selected repositories."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Write repository selection receipt.")
    parser.add_argument("--run-dir", required=True, help="Run directory")
    parser.add_argument("--selected", required=True, help="Path to selected_repos.json")
    parser.add_argument("--selection-mode", default="numbered", help="Selection mode label")
    return parser.parse_args(list(argv))


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv or __import__("sys").argv[1:])
    run_dir = Path(args.run_dir).resolve()
    selected_path = Path(args.selected).resolve()
    selected = json.loads(selected_path.read_text(encoding="utf-8-sig"))
    names = []
    for item in selected:
        if isinstance(item, dict):
            name = item.get("full_name") or item.get("name")
            if name:
                names.append(name)
    payload = {
        "selected_repositories": names,
        "selected_count": len(names),
        "source_file": str(selected_path),
        "selection_mode": args.selection_mode,
    }
    (run_dir / "repo-selection-receipt.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
