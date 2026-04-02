#!/usr/bin/env python3
"""Verify governed gates for the runtime."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify runtime gates for interest-to-pr-finder.")
    parser.add_argument("--run-dir", required=True, help="Run directory")
    parser.add_argument("--gate", required=True, help="Gate name")
    return parser.parse_args(list(argv))


def repo_selection_required(run_dir: Path) -> dict:
    receipt_path = run_dir / "repo-selection-receipt.json"
    fallback_path = run_dir / "fallback-receipt.json"
    selected_path = run_dir / "selected_repos.json"
    result = {
        "gate": "repo-selection-required",
        "passed": False,
        "checks": [],
    }
    result["checks"].append({"name": "selection_receipt_exists", "passed": receipt_path.exists()})
    result["checks"].append({"name": "selected_repos_exists", "passed": selected_path.exists()})
    if receipt_path.exists():
        receipt = json.loads(receipt_path.read_text(encoding="utf-8-sig"))
        selected = receipt.get("selected_repositories", [])
        result["checks"].append({"name": "selected_repositories_present", "passed": bool(selected), "count": len(selected)})
    else:
        selected = []
    fallback_exists = fallback_path.exists()
    result["checks"].append({"name": "no_fallback_receipt_present", "passed": not fallback_exists})
    result["passed"] = all(check["passed"] for check in result["checks"])
    result["truth_level"] = "authoritative" if result["passed"] else "non_authoritative"
    return result


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv or __import__("sys").argv[1:])
    run_dir = Path(args.run_dir).resolve()
    if args.gate != "repo-selection-required":
        raise SystemExit(f"Unsupported gate: {args.gate}")

    result = repo_selection_required(run_dir)
    (run_dir / "selection-gate.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    if not result["passed"]:
        stage_path = run_dir / "stage-status.json"
        if stage_path.exists():
            stage = json.loads(stage_path.read_text(encoding="utf-8-sig"))
            stage["current_stage"] = "repo_selection"
            stage["blocked_stage"] = "selection_gate"
            stage["truth_level"] = "non_authoritative"
            stage_path.write_text(json.dumps(stage, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        raise SystemExit("Selection gate failed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
