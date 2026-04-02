#!/usr/bin/env python3
"""Interactive repository selector for terminal use."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Iterable


def load_candidates(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, list):
        raise ValueError("Candidate file must contain a JSON array.")
    return [item for item in data if isinstance(item, dict)]


def summarize_candidate(item: dict) -> str:
    name = item.get("full_name") or item.get("name") or "unknown"
    stars = item.get("stars")
    description = (item.get("description") or "").strip()
    pieces = [name]
    if stars is not None:
        pieces.append(f"{stars} stars")
    if description:
        pieces.append(description)
    return " - ".join(pieces)


def clear_screen() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def read_key_windows() -> str:
    import msvcrt

    key = msvcrt.getwch()
    if key in ("\r", "\n"):
        return "enter"
    if key == " ":
        return "space"
    if key.lower() == "q":
        return "quit"
    if key.lower() == "j":
        return "down"
    if key.lower() == "k":
        return "up"
    if key in ("\x00", "\xe0"):
        second = msvcrt.getwch()
        mapping = {"H": "up", "P": "down"}
        return mapping.get(second, "other")
    return "other"


def read_key_posix() -> str:
    import termios
    import tty

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        first = sys.stdin.read(1)
        if first in ("\r", "\n"):
            return "enter"
        if first == " ":
            return "space"
        if first.lower() == "q":
            return "quit"
        if first.lower() == "j":
            return "down"
        if first.lower() == "k":
            return "up"
        if first == "\x1b":
            rest = sys.stdin.read(2)
            mapping = {"[A": "up", "[B": "down"}
            return mapping.get(rest, "other")
        return "other"
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


def read_key() -> str:
    if os.name == "nt":
        return read_key_windows()
    return read_key_posix()


def render(candidates: list[dict], selected: set[int], cursor: int, limit: int | None) -> None:
    clear_screen()
    print("Select repositories")
    print("Use Up/Down or j/k to move, Space to toggle, Enter to confirm, q to cancel.\n")
    if limit is not None:
        print(f"Selection limit: {limit}")
        print()

    for index, item in enumerate(candidates):
        marker = "x" if index in selected else " "
        pointer = ">" if index == cursor else " "
        summary = summarize_candidate(item)
        print(f"{pointer} [{marker}] {index + 1}. {summary}")


def interactive_select(candidates: list[dict], limit: int | None) -> list[dict]:
    if not candidates:
        return []

    cursor = 0
    selected: set[int] = set()

    while True:
        render(candidates, selected, cursor, limit)
        action = read_key()
        if action == "up":
            cursor = (cursor - 1) % len(candidates)
        elif action == "down":
            cursor = (cursor + 1) % len(candidates)
        elif action == "space":
            if cursor in selected:
                selected.remove(cursor)
            else:
                if limit is None or len(selected) < limit:
                    selected.add(cursor)
        elif action == "enter":
            return [candidates[index] for index in sorted(selected)]
        elif action == "quit":
            return []


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Interactively select repositories from JSON input.")
    parser.add_argument("--input", required=True, help="Path to candidate repositories JSON array")
    parser.add_argument("--output", help="Optional path for selected repositories JSON")
    parser.add_argument("--limit", type=int, default=None, help="Maximum number of repositories to select")
    return parser.parse_args(list(argv))


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    candidates = load_candidates(Path(args.input))
    selected = interactive_select(candidates, args.limit)
    payload = json.dumps(selected, indent=2, ensure_ascii=False)
    if args.output:
        Path(args.output).write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
