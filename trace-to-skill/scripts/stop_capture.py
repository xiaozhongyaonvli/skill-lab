import argparse
import json
from datetime import datetime
from pathlib import Path

from auto_record import record_active_event
from capture_state import read_active_capture


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def main() -> None:
    parser = argparse.ArgumentParser(description="Close a trace-to-skill capture")
    parser.add_argument("--capture-dir")
    parser.add_argument("--skill-root")
    args = parser.parse_args()

    if not args.capture_dir and not args.skill_root:
        parser.error("Provide either --capture-dir or --skill-root.")
    if args.capture_dir and args.skill_root:
        parser.error("Provide only one of --capture-dir or --skill-root.")

    capture_dir = Path(args.capture_dir) if args.capture_dir else read_active_capture(Path(args.skill_root))
    meta_path = capture_dir / "capture-meta.json"
    if args.skill_root:
        record_active_event(
            Path(args.skill_root),
            "assistant_action",
            "Closed the active capture window and finalized capture metadata",
            tags=["finalize", "execution"],
            files=["capture-meta.json"],
            artifacts=[str(capture_dir)],
        )
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    meta["status"] = "closed"
    meta["ended_at"] = now_iso()

    meta_path.write_text(json.dumps(meta, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    print(str(meta_path))


if __name__ == "__main__":
    main()
