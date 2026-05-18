import json
from datetime import datetime
from pathlib import Path

from capture_state import get_active_capture


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def parse_csv(value: str | list[str] | None) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [item.strip() for item in value if isinstance(item, str) and item.strip()]
    return [item.strip() for item in value.split(",") if item.strip()]


def record_active_event(
    skill_root: Path,
    event_type: str,
    summary: str,
    *,
    tags: str | list[str] | None = None,
    files: str | list[str] | None = None,
    command: str | None = None,
    artifacts: str | list[str] | None = None,
    reason: str | None = None,
    outcome: str | None = None,
    next_step: str | None = None,
) -> Path | None:
    capture_dir = get_active_capture(skill_root)
    if capture_dir is None:
        return None

    event = {
        "timestamp": now_iso(),
        "type": event_type,
        "summary": summary,
        "tags": parse_csv(tags),
    }
    parsed_files = parse_csv(files)
    parsed_artifacts = parse_csv(artifacts)
    if parsed_files:
        event["files"] = parsed_files
    if command:
        event["command"] = command
    if parsed_artifacts:
        event["artifacts"] = parsed_artifacts
    if reason:
        event["reason"] = reason
    if outcome:
        event["outcome"] = outcome
    if next_step:
        event["next_step"] = next_step

    events_path = capture_dir / "events.jsonl"
    with events_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=True) + "\n")
    return events_path
