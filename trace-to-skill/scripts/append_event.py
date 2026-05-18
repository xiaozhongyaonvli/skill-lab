import argparse
import json
from datetime import datetime
from pathlib import Path

from capture_state import read_active_capture


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def parse_csv(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def build_event_from_args(args: argparse.Namespace) -> dict:
    event = {
        "timestamp": args.timestamp or now_iso(),
        "type": args.type,
        "summary": args.summary,
        "tags": parse_csv(args.tags),
    }

    if args.files:
        event["files"] = parse_csv(args.files)
    if args.command:
        event["command"] = args.command
    if args.artifacts:
        event["artifacts"] = parse_csv(args.artifacts)
    if args.reason:
        event["reason"] = args.reason
    if args.outcome:
        event["outcome"] = args.outcome
    if args.next_step:
        event["next_step"] = args.next_step

    return event


def main() -> None:
    parser = argparse.ArgumentParser(description="Append an event to a capture")
    parser.add_argument("--capture-dir")
    parser.add_argument("--skill-root")
    parser.add_argument("--event-file")
    parser.add_argument("--type", choices=["user_request", "assistant_action", "file_change", "decision", "result"])
    parser.add_argument("--summary")
    parser.add_argument("--timestamp")
    parser.add_argument("--tags")
    parser.add_argument("--files")
    parser.add_argument("--command")
    parser.add_argument("--artifacts")
    parser.add_argument("--reason")
    parser.add_argument("--outcome")
    parser.add_argument("--next-step", dest="next_step")
    args = parser.parse_args()

    if not args.capture_dir and not args.skill_root:
        parser.error("Provide either --capture-dir or --skill-root.")
    if args.capture_dir and args.skill_root:
        parser.error("Provide only one of --capture-dir or --skill-root.")

    capture_dir = Path(args.capture_dir) if args.capture_dir else read_active_capture(Path(args.skill_root))
    events_path = capture_dir / "events.jsonl"

    if args.event_file:
        event_file = Path(args.event_file)
        event = json.loads(event_file.read_text(encoding="utf-8-sig"))
    else:
        if not args.type or not args.summary:
            parser.error("Provide either --event-file or both --type and --summary.")
        event = build_event_from_args(args)

    with events_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=True) + "\n")

    print(str(events_path))


if __name__ == "__main__":
    main()
