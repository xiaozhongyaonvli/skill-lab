#!/usr/bin/env python3
"""Render repository and issue candidates into Markdown."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Iterable


def load_payload(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, list):
        raise ValueError("Input must be a JSON array.")
    return [item for item in data if isinstance(item, dict)]


def label_text(labels: object) -> str:
    if not isinstance(labels, list):
        return "-"
    values = [str(label) for label in labels if str(label).strip()]
    return ", ".join(values) if values else "-"


def render_issue(issue: dict) -> list[str]:
    title = issue.get("title") or "Untitled issue"
    url = issue.get("url") or ""
    confidence = issue.get("unclaimed_confidence") or "unknown"
    fit_reason = issue.get("fit_reason") or ""
    caveat = issue.get("thread_caveat") or ""
    updated_at = issue.get("updated_at") or "unknown"
    labels = label_text(issue.get("labels"))

    lines = [f"- [{title}]({url})"]
    lines.append(f"  Labels: {labels}")
    lines.append(f"  Updated: {updated_at}")
    lines.append(f"  Unclaimed confidence: {confidence}")
    if fit_reason:
        lines.append(f"  Fit: {fit_reason}")
    if caveat:
        lines.append(f"  Caveat: {caveat}")
    return lines


def render_repo(repo: dict) -> list[str]:
    name = repo.get("repository") or repo.get("full_name") or "unknown"
    repo_url = repo.get("repository_url") or repo.get("url") or ""
    description = repo.get("description") or ""
    stars = repo.get("stars")
    issues = repo.get("issues")
    lines = [f"## [{name}]({repo_url})" if repo_url else f"## {name}"]
    meta = []
    if stars is not None:
        meta.append(f"{stars} stars")
    if description:
        meta.append(description)
    if meta:
        lines.append("")
        lines.append(" | ".join(meta))
    lines.append("")

    if isinstance(issues, list) and issues:
        for issue in issues:
            if isinstance(issue, dict):
                lines.extend(render_issue(issue))
    else:
        lines.append("- No matching issues found.")
    lines.append("")
    return lines


def render_markdown(payload: list[dict]) -> str:
    lines = ["# Contribution Candidates", ""]
    for repo in payload:
        lines.extend(render_repo(repo))
    return "\n".join(lines).rstrip() + "\n"


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render repository issue candidates as Markdown.")
    parser.add_argument("--input", required=True, help="Path to JSON payload")
    parser.add_argument("--output", help="Optional output Markdown file")
    return parser.parse_args(list(argv))


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    payload = load_payload(Path(args.input))
    markdown = render_markdown(payload)
    if args.output:
        Path(args.output).write_text(markdown, encoding="utf-8")
    else:
        sys.stdout.write(markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
