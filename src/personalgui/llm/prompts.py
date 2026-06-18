"""System-prompt template + compact renderers for observations and events."""

from __future__ import annotations

import json
from typing import Any

from ..schemas import Event, Observation

SYSTEM_PROMPT = """You are a computer-using agent. The user has multiple devices ("environments"), each with apps. You receive the user's request and a description of the current screen, and you decide what to do next by calling exactly one tool per turn.

Rules:
- Each turn, call exactly one tool. Do not produce free-form text.
- Inspect the visible state of the current app before acting. If you need information from a different app or device, open or switch to it first.
- To move information between devices (a code, a value, a file), copy_value on the source environment, then paste_value on the destination.
- When the user's request is fully satisfied, call declare_done.
- Only call ask_clarification when proceeding would risk an irreversible mistake (wrong recipient, wrong account, deleting the wrong item).
"""


def render_initial_user_message(request: str, environments: list[dict[str, Any]], observation: Observation) -> str:
    env_lines = []
    for env in environments:
        apps = ", ".join(a["id"] for a in env["apps"])
        env_lines.append(f"  - {env['id']} ({env['display_name']}): apps = [{apps}]")
    env_block = "\n".join(env_lines)
    return (
        f"User request: {request}\n\n"
        f"Available environments:\n{env_block}\n\n"
        f"Current screen:\n{render_observation(observation)}\n\n"
        f"Decide the next action and call one tool."
    )


def render_observation(observation: Observation) -> str:
    app = observation.app_id or "(home)"
    clip = observation.clipboard_preview
    clip_line = f"clipboard: {clip!r}" if clip is not None else "clipboard: (empty)"
    return (
        f"[{observation.environment_id} / {app}]\n"
        f"{json.dumps(observation.visible_state, sort_keys=True)}\n"
        f"{clip_line}"
    )


def render_event(event: Event) -> str:
    parts: list[str] = []
    parts.append(f"accepted: {event.accepted}")
    if event.error:
        parts.append(f"error: {event.error}")
    if event.handoff:
        parts.append(f"handoff: {json.dumps(event.handoff, sort_keys=True)}")
    if event.state_changes:
        parts.append(f"state_changes: {json.dumps(event.state_changes, sort_keys=True)}")
    return "\n".join(parts) if parts else "ok"
