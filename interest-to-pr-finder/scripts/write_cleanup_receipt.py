#!/usr/bin/env python3
"""Write cleanup-receipt.json if required artifacts exist."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable


REQUIRED_FOR_CLEANUP = [
    "runtime-input.json",
    "intent-contract.json",
    "requirement-surface.json",
    "execution-plan.json",
    "stage-status.json",
    "repo-selection-receipt.json",
    "selection-gate.json",
    "issue_candidates.json",
]


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Write cleanup receipt for interest-to-pr-finder.")
    parser.add_argument("--run-dir", required=True, help="Run directory")
    return parser.parse_args(list(argv))


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv or __import__("sys").argv[1:])
    run_dir = Path(args.run_dir).resolve()
    missing = [name for name in REQUIRED_FOR_CLEANUP if not (run_dir / name).exists()]
    final_report_exists = (run_dir / "final-report.md").exists()
    gate_passed = False
    gate_path = run_dir / "selection-gate.json"
    if gate_path.exists():
        gate = json.loads(gate_path.read_text(encoding="utf-8-sig"))
        gate_passed = bool(gate.get("passed"))
    payload = {
        "cleanup_completed": not missing and final_report_exists and gate_passed,
        "missing_required_artifacts": missing,
        "final_report_exists": final_report_exists,
        "selection_gate_passed": gate_passed,
    }
    (run_dir / "cleanup-receipt.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    if missing or not final_report_exists or not gate_passed:
        raise SystemExit("Cleanup requirements are not satisfied.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
