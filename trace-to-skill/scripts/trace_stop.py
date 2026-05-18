import argparse
import subprocess
import sys
from pathlib import Path

from auto_record import record_active_event
from capture_state import ensure_data_root_writable, write_configured_data_root


def main() -> None:
    parser = argparse.ArgumentParser(description="User-facing stop action for trace-to-skill")
    parser.add_argument("--skill-root", required=True)
    parser.add_argument("--data-root")
    parser.add_argument("--emit-draft-skill", action="store_true")
    args = parser.parse_args()

    if args.data_root:
        data_root = Path(args.data_root).expanduser()
        ensure_data_root_writable(data_root)
        write_configured_data_root(data_root)

    script_path = Path(__file__).with_name("finish_capture.py")
    command = [sys.executable, str(script_path), "--skill-root", args.skill_root]
    if args.emit_draft_skill:
        command.append("--emit-draft-skill")
    record_active_event(
        Path(args.skill_root),
        "assistant_action",
        "Received the user stop action and began capture finalization",
        tags=["finalize", "execution"],
    )
    subprocess.run(command, check=True)


if __name__ == "__main__":
    main()
