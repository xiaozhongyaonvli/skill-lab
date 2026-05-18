import argparse
from pathlib import Path

from auto_record import record_active_event


def main() -> None:
    parser = argparse.ArgumentParser(description="Record an event only if a trace capture is active")
    parser.add_argument("--skill-root", required=True)
    parser.add_argument("--type", required=True, choices=["user_request", "assistant_action", "file_change", "decision", "result"])
    parser.add_argument("--summary", required=True)
    parser.add_argument("--timestamp")
    parser.add_argument("--tags")
    parser.add_argument("--files")
    parser.add_argument("--command")
    parser.add_argument("--artifacts")
    parser.add_argument("--reason")
    parser.add_argument("--outcome")
    parser.add_argument("--next-step", dest="next_step")
    args = parser.parse_args()

    events_path = record_active_event(
        Path(args.skill_root),
        args.type,
        args.summary,
        tags=args.tags,
        files=args.files,
        command=args.command,
        artifacts=args.artifacts,
        reason=args.reason,
        outcome=args.outcome,
        next_step=args.next_step,
    )
    if events_path is None:
        print("No active capture. Event skipped.")
        return

    print(str(events_path))


if __name__ == "__main__":
    main()
