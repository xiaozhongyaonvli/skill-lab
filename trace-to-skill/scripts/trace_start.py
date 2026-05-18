import argparse
import subprocess
import sys
from pathlib import Path

from auto_record import record_active_event
from capture_state import ensure_data_root_writable, write_configured_data_root


def main() -> None:
    parser = argparse.ArgumentParser(description="User-facing start action for trace-to-skill")
    parser.add_argument("--skill-root", required=True)
    parser.add_argument("--topic", default="captured-workflow")
    parser.add_argument("--data-root")
    parser.add_argument("--force-switch", action="store_true")
    args = parser.parse_args()

    if args.data_root:
        data_root = Path(args.data_root).expanduser()
        ensure_data_root_writable(data_root)
        write_configured_data_root(data_root)

    script_path = Path(__file__).with_name("start_capture.py")
    command = [sys.executable, str(script_path), "--skill-root", args.skill_root, "--topic", args.topic]
    if args.force_switch:
        command.append("--force-switch")
    subprocess.run(command, check=True)

    record_active_event(
        Path(args.skill_root),
        "user_request",
        args.topic,
        tags=["capture", "start"],
    )
    record_active_event(
        Path(args.skill_root),
        "assistant_action",
        "Opened a trace window and began internal workflow capture",
        tags=["capture", "execution"],
    )


if __name__ == "__main__":
    main()
