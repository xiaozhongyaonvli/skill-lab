import argparse
import json
from pathlib import Path

from capture_state import ensure_data_root_writable, get_active_capture, state_path, write_configured_data_root


def main() -> None:
    parser = argparse.ArgumentParser(description="Show the current active trace-to-skill capture")
    parser.add_argument("--skill-root", required=True)
    parser.add_argument("--data-root")
    args = parser.parse_args()

    if args.data_root:
        data_root = Path(args.data_root).expanduser()
        ensure_data_root_writable(data_root)
        write_configured_data_root(data_root)

    skill_root = Path(args.skill_root)
    capture_dir = get_active_capture(skill_root)
    if capture_dir is None:
        print("No active capture.")
        return

    meta_path = capture_dir / "capture-meta.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    payload = {
        "state_file": str(state_path(skill_root)),
        "capture_dir": str(capture_dir),
        "capture_id": meta.get("capture_id", ""),
        "topic": meta.get("topic", ""),
        "status": meta.get("status", ""),
        "started_at": meta.get("started_at", ""),
    }
    print(json.dumps(payload, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
