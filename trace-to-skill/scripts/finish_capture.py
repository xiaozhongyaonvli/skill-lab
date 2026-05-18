import argparse
import subprocess
import sys
from pathlib import Path


def run_script(script_name: str, args: list[str], workdir: Path) -> None:
    script_path = Path(__file__).with_name(script_name)
    command = [sys.executable, str(script_path), *args]
    subprocess.run(command, cwd=workdir, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Close and synthesize the active trace-to-skill capture")
    parser.add_argument("--skill-root", required=True)
    parser.add_argument("--emit-draft-skill", action="store_true")
    args = parser.parse_args()

    workdir = Path.cwd()
    run_script(
        "record_if_active.py",
        [
            "--skill-root",
            args.skill_root,
            "--type",
            "assistant_action",
            "--summary",
            "Finalize the active trace and synthesize a draft skill",
            "--tags",
            "finalize,output",
        ],
        workdir,
    )
    run_script("stop_capture.py", ["--skill-root", args.skill_root], workdir)
    synth_args = ["--skill-root", args.skill_root]
    if args.emit_draft_skill:
        synth_args.append("--emit-draft-skill")
    run_script("synthesize_skill.py", synth_args, workdir)


if __name__ == "__main__":
    main()
