import argparse
import json
from collections import Counter
from pathlib import Path

from auto_record import record_active_event
from capture_state import clear_active_capture, read_active_capture


def slugify(value: str) -> str:
    cleaned = "".join(ch.lower() if ch.isalnum() else "-" for ch in value.strip())
    parts = [part for part in cleaned.split("-") if part]
    return "-".join(parts) or "draft-skill"


def load_events(events_path: Path) -> list[dict]:
    events: list[dict] = []
    for line in events_path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            events.append(json.loads(line))
    return events


def unique_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result


def classify_step(summary: str, tags: list[str]) -> str:
    lowered = summary.lower()
    lowered_tags = {tag.lower() for tag in tags}

    if lowered_tags & {"discovery", "context", "analysis", "research"}:
        return "discovery"
    if lowered_tags & {"finalize", "final", "output", "wrap-up", "cleanup"}:
        return "finalize"
    if any(token in lowered for token in ["read ", "review", "inspect", "discover", "analyze", "summarize context"]):
        return "discovery"
    if any(token in lowered for token in ["finalize", "generate", "write summary", "close", "present", "output"]):
        return "finalize"
    return "execution"


def is_process_result(event: dict) -> bool:
    tags = {tag.lower() for tag in event.get("tags", []) if isinstance(tag, str)}
    return bool(tags & {"process", "step", "execution", "discovery", "finalize"})


def summarize_events(meta: dict, events: list[dict]) -> dict:
    counts = Counter(event.get("type", "unknown") for event in events)
    user_requests = [event["summary"] for event in events if event.get("type") == "user_request"]
    assistant_actions = [event["summary"] for event in events if event.get("type") == "assistant_action"]
    file_changes = [event["summary"] for event in events if event.get("type") == "file_change"]
    decisions = [event["summary"] for event in events if event.get("type") == "decision"]
    results = [event["summary"] for event in events if event.get("type") == "result"]
    terminal_results = [
        event["summary"]
        for event in events
        if event.get("type") == "result" and not is_process_result(event)
    ]
    files = unique_preserve_order(
        [file for event in events for file in event.get("files", []) if isinstance(file, str)]
    )
    artifacts = unique_preserve_order(
        [
            artifact
            for event in events
            for artifact in event.get("artifacts", [])
            if isinstance(artifact, str)
        ]
    )
    output_artifacts = unique_preserve_order(
        [
            artifact
            for event in events
            if event.get("type") in {"result", "file_change"}
            for artifact in event.get("artifacts", [])
            if isinstance(artifact, str)
        ]
    )
    commands = unique_preserve_order(
        [event.get("command", "").strip() for event in events if isinstance(event.get("command"), str)]
    )
    tags = unique_preserve_order(
        [tag for event in events for tag in event.get("tags", []) if isinstance(tag, str)]
    )
    sop_sections = {
        "discovery": [],
        "execution": [],
        "finalize": [],
    }
    for event in events:
        event_type = event.get("type")
        if event_type not in {"assistant_action", "file_change", "result"}:
            continue
        if event_type == "result" and not is_process_result(event):
            continue
        summary = event.get("summary", "").strip()
        if not summary:
            continue
        phase = classify_step(summary, event.get("tags", []))
        sop_sections[phase].append(summary)

    output_items = unique_preserve_order(terminal_results + file_changes)
    completion_outputs = unique_preserve_order(
        output_items
        + output_artifacts
        + ["Generated `summary.md` and `skill-draft.md` for this capture."]
    )
    return {
        "topic": meta.get("topic", "Captured workflow"),
        "capture_id": meta.get("capture_id", ""),
        "started_at": meta.get("started_at", ""),
        "ended_at": meta.get("ended_at", ""),
        "counts": counts,
        "user_requests": user_requests,
        "assistant_actions": assistant_actions,
        "file_changes": file_changes,
        "decisions": decisions,
        "results": results,
        "output_items": output_items,
        "completion_outputs": completion_outputs,
        "files": files,
        "artifacts": artifacts,
        "output_artifacts": output_artifacts,
        "commands": commands,
        "tags": tags,
        "sop_sections": {key: unique_preserve_order(value) for key, value in sop_sections.items()},
    }


def render_summary(summary: dict) -> str:
    lines = [
        "# Capture Summary",
        "",
        "## Capture",
        "",
        f"- Topic: {summary['topic']}",
        f"- Capture ID: `{summary['capture_id']}`",
    ]

    if summary["started_at"]:
        lines.append(f"- Started: `{summary['started_at']}`")
    if summary["ended_at"]:
        lines.append(f"- Ended: `{summary['ended_at']}`")
    if summary["tags"]:
        lines.append(f"- Tags: {', '.join(f'`{tag}`' for tag in summary['tags'])}")

    lines.extend(["", "## Event Counts", ""])
    for event_type, count in sorted(summary["counts"].items()):
        lines.append(f"- `{event_type}`: {count}")

    if summary["user_requests"]:
        lines.extend(["", "## User Requests", ""])
        lines.extend(f"- {item}" for item in summary["user_requests"])

    if summary["assistant_actions"]:
        lines.extend(["", "## Assistant Actions", ""])
        lines.extend(f"- {item}" for item in summary["assistant_actions"])

    if summary["file_changes"]:
        lines.extend(["", "## File Changes", ""])
        lines.extend(f"- {item}" for item in summary["file_changes"])

    if summary["decisions"]:
        lines.extend(["", "## Decisions", ""])
        lines.extend(f"- {item}" for item in summary["decisions"])

    if summary["results"]:
        lines.extend(["", "## Results", ""])
        lines.extend(f"- {item}" for item in summary["results"])

    return "\n".join(lines) + "\n"


def render_bullet_section(title: str, items: list[str], empty_message: str) -> list[str]:
    lines = [f"## {title}", ""]
    if items:
        lines.extend(f"- {item}" for item in items)
    else:
        lines.append(f"- {empty_message}")
    lines.append("")
    return lines


def render_sop_sections(summary: dict) -> list[str]:
    lines = ["## Structured SOP", ""]
    sections = [
        ("Discovery", summary["sop_sections"]["discovery"], "No discovery steps were captured."),
        ("Execution", summary["sop_sections"]["execution"], "No execution steps were captured."),
        ("Finalize", summary["sop_sections"]["finalize"], "No finalize steps were captured."),
    ]
    for title, items, empty_message in sections:
        lines.append(f"### {title}")
        lines.append("")
        if items:
            lines.extend(f"- {item}" for item in items)
        else:
            lines.append(f"- {empty_message}")
        lines.append("")
    return lines


def render_output_section(summary: dict, empty_message: str) -> list[str]:
    sop_items = {
        item
        for section_items in summary["sop_sections"].values()
        for item in section_items
    }
    outputs = [item for item in summary["completion_outputs"] if item not in sop_items]
    return render_bullet_section("Outputs", outputs, empty_message)


def trigger_patterns(summary: dict) -> list[str]:
    if summary["user_requests"]:
        return summary["user_requests"]
    return [summary["topic"]]


def infer_skill_name(summary: dict) -> str:
    source = summary["topic"]
    if summary["user_requests"]:
        source = summary["user_requests"][0]
    return slugify(source)[:64]


def render_skill_md(summary: dict, skill_name: str) -> str:
    description = (
        "Draft skill generated from a captured workflow. Replace this description with a concise "
        "trigger-oriented statement before production use."
    )
    lines = [
        "---",
        f"name: {skill_name}",
        f"description: {description}",
        "---",
        "",
        f"# {skill_name}",
        "",
        "## Overview",
        "",
        "This is a draft skill synthesized from a captured workflow. Review and tighten it before promoting it to a reusable production skill.",
        "",
    ]
    lines.extend(
        render_bullet_section(
            "Likely Trigger Patterns",
            trigger_patterns(summary),
            "No trigger patterns captured.",
        )
    )
    lines.extend(
        render_bullet_section(
            "Inputs And Dependencies",
            summary["files"] + summary["commands"],
            "No explicit files or commands were captured.",
        )
    )
    lines.extend(
        render_sop_sections(summary)
    )
    lines.extend(render_bullet_section("Decision Rules", summary["decisions"], "No explicit decision rules were captured."))
    lines.extend(render_output_section(summary, "Generated `summary.md` and `skill-draft.md` for this capture."))
    return "\n".join(lines).rstrip() + "\n"


def render_skill_draft(summary: dict) -> str:
    skill_name = infer_skill_name(summary)
    lines = [
        "# Skill Draft",
        "",
        "## Capture Summary",
        "",
        f"- Topic: {summary['topic']}",
        f"- Suggested skill name: `{skill_name}`",
        "",
    ]
    lines.extend(
        render_bullet_section(
            "Trigger Patterns",
            trigger_patterns(summary),
            "No user requests were captured. Add a trigger statement manually.",
        )
    )
    lines.extend(
        render_bullet_section(
            "Inputs And Dependencies",
            summary["files"] + summary["commands"],
            "No files or commands were captured.",
        )
    )
    lines.extend(
        render_sop_sections(summary)
    )
    lines.extend(
        render_bullet_section(
            "Decision Rules",
            summary["decisions"],
            "No explicit decisions were captured. Review the trace before finalizing.",
        )
    )
    lines.extend(render_output_section(summary, "Generated `summary.md` and `skill-draft.md` for this capture."))

    resource_suggestions: list[str] = []
    if summary["commands"]:
        resource_suggestions.append("Consider extracting repeated command flows into `scripts/` helpers.")
    if summary["files"]:
        resource_suggestions.append("Consider documenting stable file conventions or schemas in `references/`.")
    if not resource_suggestions:
        resource_suggestions.append("No reusable resource suggestion was inferred from the current trace.")
    lines.extend(render_bullet_section("Reusable Resource Suggestions", resource_suggestions, "No suggestions."))

    lines.extend(
        [
            "## Draft SKILL.md",
            "",
            "```md",
            render_skill_md(summary, skill_name).rstrip(),
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def write_draft_skill_folder(capture_dir: Path, summary: dict) -> None:
    skill_name = infer_skill_name(summary)
    draft_root = capture_dir / "draft-skill"
    agents_dir = draft_root / "agents"
    draft_root.mkdir(parents=True, exist_ok=True)
    agents_dir.mkdir(parents=True, exist_ok=True)

    (draft_root / "SKILL.md").write_text(render_skill_md(summary, skill_name), encoding="utf-8")
    (agents_dir / "openai.yaml").write_text(
        "\n".join(
            [
                "interface:",
                f'  display_name: "{skill_name.replace("-", " ").title()}"',
                '  short_description: "Draft skill synthesized from a captured workflow"',
                f'  default_prompt: "Use ${skill_name} to execute the captured workflow."',
                "",
            ]
        ),
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Synthesize a skill draft from captured events")
    parser.add_argument("--capture-dir")
    parser.add_argument("--skill-root")
    parser.add_argument("--emit-draft-skill", action="store_true")
    args = parser.parse_args()

    if not args.capture_dir and not args.skill_root:
        parser.error("Provide either --capture-dir or --skill-root.")
    if args.capture_dir and args.skill_root:
        parser.error("Provide only one of --capture-dir or --skill-root.")

    capture_dir = Path(args.capture_dir) if args.capture_dir else read_active_capture(Path(args.skill_root))
    meta = json.loads((capture_dir / "capture-meta.json").read_text(encoding="utf-8"))
    events = load_events(capture_dir / "events.jsonl")
    summary = summarize_events(meta, events)

    (capture_dir / "summary.md").write_text(render_summary(summary), encoding="utf-8")
    (capture_dir / "skill-draft.md").write_text(render_skill_draft(summary), encoding="utf-8")
    if args.emit_draft_skill:
        write_draft_skill_folder(capture_dir, summary)
    if args.skill_root:
        generated_artifacts = ["summary.md", "skill-draft.md"]
        if args.emit_draft_skill:
            generated_artifacts.extend(["draft-skill/SKILL.md", "draft-skill/agents/openai.yaml"])
        record_active_event(
            Path(args.skill_root),
            "result",
            "Synthesized capture artifacts into a SOP summary and draft skill",
            tags=["output"],
            artifacts=generated_artifacts,
            outcome="Draft skill artifacts generated",
        )
    if args.skill_root:
        clear_active_capture(Path(args.skill_root))
    print(str(capture_dir / "skill-draft.md"))


if __name__ == "__main__":
    main()
