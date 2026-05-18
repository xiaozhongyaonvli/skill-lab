import argparse
import json
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from auto_record import record_active_event
from capture_state import captures_dir, ensure_data_root_writable, get_active_capture, write_active_capture


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def slugify(value: str) -> str:
    cleaned = "".join(ch.lower() if ch.isalnum() else "-" for ch in value.strip())
    parts = [part for part in cleaned.split("-") if part]
    return "-".join(parts) or "capture"


def main() -> None:
    parser = argparse.ArgumentParser(description="Initialize a trace-to-skill capture")
    parser.add_argument("--skill-root", required=True)
    parser.add_argument("--topic", default="captured-workflow")
    parser.add_argument("--force-switch", action="store_true")
    args = parser.parse_args()

    skill_root = Path(args.skill_root)
    ensure_data_root_writable(captures_dir(skill_root).parent)
    existing_capture = get_active_capture(skill_root)
    if existing_capture and not args.force_switch:
        raise SystemExit(
            f"An active capture already exists: {existing_capture}\n"
            "Finish it first or rerun with --force-switch."
        )

    runtime_captures_dir = captures_dir(skill_root)
    capture_id = f"{slugify(args.topic)}-{uuid4().hex[:8]}"
    capture_dir = runtime_captures_dir / capture_id
    capture_dir.mkdir(parents=True, exist_ok=False)

    meta = {
        "capture_id": capture_id,
        "topic": args.topic,
        "status": "active",
        "started_at": now_iso(),
        "ended_at": None,
        "tags": [],
    }

    (capture_dir / "capture-meta.json").write_text(
        json.dumps(meta, ensure_ascii=True, indent=2) + "\n",
        encoding="utf-8",
    )
    (capture_dir / "events.jsonl").write_text("", encoding="utf-8")
    write_active_capture(skill_root, capture_dir)
    record_active_event(
        skill_root,
        "assistant_action",
        "Initialized capture storage and registered the active trace session",
        tags=["capture", "execution"],
        files=["capture-meta.json", "events.jsonl"],
        artifacts=[str(capture_dir)],
    )

    print(str(capture_dir))


if __name__ == "__main__":
    main()
