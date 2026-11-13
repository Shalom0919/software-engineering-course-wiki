#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path


def _ascii_slug(value: str, fallback: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip().lower())
    cleaned = re.sub(r"-{2,}", "-", cleaned).strip("-._")
    return cleaned or fallback


def _normalize_agent_name(value: str) -> str:
    raw = re.sub(r"[\s_-]+", "", str(value or "").strip().lower())
    if not raw:
        return ""
    mapping = {
        "codex": "codex",
        "codexcli": "codex",
        "claude": "claude",
        "claudecode": "claude",
        "copilot": "copilot",
        "githubcopilot": "copilot",
        "cursor": "cursor",
        "gemini": "gemini-cli",
        "geminicli": "gemini-cli",
        "openclaw": "openclaw",
        "opencode": "opencode",
        "hermes": "hermes-agent",
        "hermesagent": "hermes-agent",
    }
    return mapping.get(raw, raw)


def _normalize_agent_sequence(data: dict) -> list[str]:
    raw_agents = data.get("agents")
    if isinstance(raw_agents, list):
        items = raw_agents
    elif data.get("agent"):
        items = [data.get("agent")]
    else:
        items = []
    result = []
    seen = set()
    for item in items:
        agent = _normalize_agent_name(str(item or ""))
        if agent and agent not in seen:
            seen.add(agent)
            result.append(agent)
    return result


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def main() -> int:
    root = Path.cwd()
    manifests = sorted(root.glob("raw/*/*/原始数据/manifest.json"))
    if not manifests:
        print("no manifests found; skipping llm-wiki source generation")
        return 0

    for manifest_path in manifests:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        raw_root = manifest_path.parent
        course_title = str(data.get("course_title") or manifest_path.parents[2].name)
        session_title = str(data.get("session_title") or manifest_path.parent.name)
        course_id = str(data.get("course_id") or "")
        sub_id = str(data.get("sub_id") or "")
        project_slug = _ascii_slug(course_id, fallback="course")
        session_slug = _ascii_slug(f"{sub_id or session_title}", fallback="session")
        source_path = root / "raw" / "sessions" / project_slug / f"{session_slug}.md"
        notes_name = f"{data.get('base_name', '')}_notes.md"
        notes_path = raw_root / notes_name
        notes_text = notes_path.read_text(encoding="utf-8", errors="replace").strip() if notes_path.exists() else ""
        # Resolve artifacts beside their manifest so clones work on any OS.
        subtitle_path = raw_root / f"{data.get('base_name', '')}.srt"
        timeline_path = raw_root / f"{data.get('base_name', '')}_timeline.txt"
        agents = _normalize_agent_sequence(data)
        primary_agent = agents[0] if agents else _normalize_agent_name(str(data.get("agent") or "")) or "codex"
        rel_subtitle = subtitle_path.relative_to(root).as_posix() if subtitle_path.exists() else ""
        rel_timeline = timeline_path.relative_to(root).as_posix() if timeline_path.exists() else ""
        body = f"""---
title: "Lesson: {session_title}"
type: source
tags: [tongji-look, course-session]
date: {str(data.get("lecture_date") or data.get("generated_at") or "1970-01-01")[:10]}
source_file: raw/sessions/{project_slug}/{session_slug}.md
agent: {primary_agent}
agents: [{", ".join(agents)}]
sessionId: {data.get("base_name") or session_slug}
slug: {session_slug}
project: {project_slug}
started: {data.get("generated_at") or "1970-01-01T00:00:00+08:00"}
ended: {data.get("generated_at") or "1970-01-01T00:00:00+08:00"}
course_title: "{course_title}"
session_title: "{session_title}"
duration_seconds: {int(data.get("duration_seconds") or 0)}
subtitle_word_count: {int(data.get("subtitle_word_count") or 0)}
look_tongji_video_url: "{str(data.get("video_url") or "")}"
look_tongji_timeline: "{rel_timeline}"
look_tongji_subtitle: "{rel_subtitle}"
---

# {session_title}

## Summary

{notes_text or session_title}
"""
        _write_text(source_path, body)
        project_profile = root / "wiki" / "projects" / f"{project_slug}.md"
        if not project_profile.exists():
            _write_text(
                project_profile,
                f"""---
title: "{course_title}"
type: project
description: "课程：{course_title}"
---

# {course_title}
""",
            )
    print(f"indexed {len(manifests)} lesson manifest(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
