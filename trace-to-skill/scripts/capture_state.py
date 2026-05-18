import os
import json
from pathlib import Path

def config_path() -> Path:
    local_appdata = os.environ.get("LOCALAPPDATA", "").strip()
    if local_appdata:
        return Path(local_appdata) / "trace-to-skill" / "config.json"
    return Path.home() / ".trace-to-skill" / "config.json"


def read_configured_data_root() -> Path | None:
    path = config_path()
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    value = str(payload.get("data_root", "")).strip()
    if not value:
        return None
    return Path(value)


def write_configured_data_root(data_root: Path) -> None:
    payload = {
        "data_root": str(data_root),
    }
    config_path().parent.mkdir(parents=True, exist_ok=True)
    config_path().write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def ensure_data_root_writable(data_root: Path) -> None:
    try:
        data_root.mkdir(parents=True, exist_ok=True)
        probe = data_root / ".write-test"
        probe.write_text("ok\n", encoding="utf-8")
        probe.unlink()
    except OSError as exc:
        raise SystemExit(
            "trace-to-skill data root is not writable: "
            f"{data_root}\n"
            "Please rerun with --data-root <writable-path> to choose a writable location."
        ) from exc


def data_root(skill_root: Path) -> Path:
    override = os.environ.get("TRACE_TO_SKILL_DATA_ROOT", "").strip()
    if override:
        return Path(override)
    configured = read_configured_data_root()
    if configured is not None:
        return configured
    raise SystemExit(
        "trace-to-skill has no configured default data root.\n"
        f"Create a config file at {config_path()} with a data_root value,\n"
        "or rerun with --data-root <writable-path> to select one."
    )


def state_dir(skill_root: Path) -> Path:
    return data_root(skill_root) / "state"


def captures_dir(skill_root: Path) -> Path:
    return data_root(skill_root) / "captures"


def state_path(skill_root: Path) -> Path:
    return state_dir(skill_root) / "active-capture.json"


def write_active_capture(skill_root: Path, capture_dir: Path) -> None:
    state_dir(skill_root).mkdir(parents=True, exist_ok=True)
    payload = {
        "capture_dir": str(capture_dir),
    }
    state_path(skill_root).write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def clear_active_capture(skill_root: Path) -> None:
    path = state_path(skill_root)
    if path.exists():
        path.unlink()


def get_active_capture(skill_root: Path) -> Path | None:
    path = state_path(skill_root)
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    capture_dir = payload.get("capture_dir", "").strip()
    if not capture_dir:
        return None
    return Path(capture_dir)


def read_active_capture(skill_root: Path) -> Path:
    path = state_path(skill_root)
    capture_dir = get_active_capture(skill_root)
    if capture_dir is None:
        raise FileNotFoundError(f"No active capture state found at: {path}")
    return capture_dir
