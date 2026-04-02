#!/usr/bin/env python3
"""Fail closed if authoritative repository selection is missing."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Enforce authoritative repository selection before issue search.")
    parser.add_argument("--run-dir", required=True, help="Run directory")
    return parser.parse_args(list(argv))


def load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def candidate_count(run_dir: Path) -> int:
    path = run_dir / "repo_candidates.json"
    if not path.exists():
        return 0
    payload = load_json(path)
    return len(payload) if isinstance(payload, list) else 0


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv or __import__("sys").argv[1:])
    run_dir = Path(args.run_dir).resolve()
    selected_path = run_dir / "selected_repos.json"
    receipt_path = run_dir / "repo-selection-receipt.json"
    gate_path = run_dir / "selection-gate.json"
    stage_path = run_dir / "stage-status.json"

    candidates = candidate_count(run_dir)
    selected_exists = selected_path.exists()
    receipt_exists = receipt_path.exists()
    selected_count = 0
    if selected_exists:
        payload = load_json(selected_path)
        if isinstance(payload, list):
            selected_count = len(payload)
    gate = {
        "gate": "authoritative-repo-selection-enforcement",
        "passed": selected_exists and receipt_exists and selected_count > 0,
        "checks": [
            {"name": "candidate_count", "passed": candidates > 0, "count": candidates},
            {"name": "selected_repos_exists", "passed": selected_exists},
            {"name": "selection_receipt_exists", "passed": receipt_exists},
            {"name": "selected_repo_count_positive", "passed": selected_count > 0, "count": selected_count},
        ],
        "truth_level": "authoritative" if selected_exists and receipt_exists and selected_count > 0 else "non_authoritative",
    }
    gate_path.write_text(json.dumps(gate, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if not gate["passed"]:
        stage = load_json(stage_path)
        if isinstance(stage, dict):
            stage["current_stage"] = "repo_selection"
            stage["blocked_stage"] = "repo_selection"
            stage["truth_level"] = "non_authoritative"
            stage_path.write_text(json.dumps(stage, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        raise SystemExit(
            "Authoritative repository selection is missing. Stop here and wait for explicit repository selection before issue search."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
