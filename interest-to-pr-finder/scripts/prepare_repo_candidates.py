#!/usr/bin/env python3
"""Normalize repository search results for the interactive picker."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable


def load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def extract_items(payload: object) -> list[dict]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        for key in ("items", "repositories", "results", "data"):
            value = payload.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
    raise ValueError("Unsupported repository payload shape.")


def pick_first(item: dict, *keys: str) -> object:
    for key in keys:
        value = item.get(key)
        if value not in (None, ""):
            return value
    return None


def normalize_item(item: dict) -> dict:
    owner = item.get("owner")
    owner_login = owner.get("login") if isinstance(owner, dict) else None
    full_name = pick_first(item, "full_name", "name_with_owner", "repo")
    if not full_name:
        name = pick_first(item, "name")
        if owner_login and name:
            full_name = f"{owner_login}/{name}"
        else:
            full_name = name or "unknown"

    stars = pick_first(item, "stargazers_count", "stars", "star_count")
    description = pick_first(item, "description", "summary") or ""
    html_url = pick_first(item, "html_url", "url", "repository_url") or ""
    language = pick_first(item, "language", "primary_language")
    updated_at = pick_first(item, "updated_at", "pushed_at", "last_updated")
    reason = pick_first(item, "reason", "match_reason")

    normalized = {
        "full_name": full_name,
        "url": html_url,
        "description": description,
        "stars": stars,
    }
    if language:
        normalized["language"] = language
    if updated_at:
        normalized["updated_at"] = updated_at
    if reason:
        normalized["reason"] = reason
    return normalized


def sort_candidates(items: list[dict]) -> list[dict]:
    return sorted(
        items,
        key=lambda item: (
            -(item.get("stars") or 0),
            item.get("full_name") or "",
        ),
    )


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Normalize repository candidates for interactive selection.")
    parser.add_argument("--input", required=True, help="Path to raw repository JSON")
    parser.add_argument("--output", required=True, help="Path to normalized candidate JSON")
    parser.add_argument("--limit", type=int, default=None, help="Optional maximum number of candidates to keep")
    return parser.parse_args(list(argv))


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv or [])
    payload = load_json(Path(args.input))
    candidates = [normalize_item(item) for item in extract_items(payload)]
    candidates = [item for item in candidates if item.get("full_name")]
    candidates = sort_candidates(candidates)
    if args.limit is not None:
        candidates = candidates[: args.limit]
    Path(args.output).write_text(
        json.dumps(candidates, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(__import__("sys").argv[1:]))
