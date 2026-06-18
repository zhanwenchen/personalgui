"""OpenAI-style tool schemas for the agent's action space, plus tool_call -> Action."""

from __future__ import annotations

from typing import Any

from ..schemas import Action


def _function_tool(name: str, description: str, properties: dict[str, Any], required: list[str]) -> dict[str, Any]:
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required,
                "additionalProperties": False,
            },
        },
    }


_ENV = {"type": "string", "description": "ID of the device/environment (one of the agent_visible environments)."}


def build_tools() -> list[dict[str, Any]]:
    """Return the OpenAI tool list. Stable across an episode so the server can prefix-cache."""
    return [
        _function_tool(
            "open_app",
            "Open (focus) a named app on a device. Switches the agent's focus to that environment and app. Pass app_id=null to go to the device's home screen.",
            {"environment_id": _ENV, "app_id": {"type": ["string", "null"], "description": "ID of the app to open, or null to go home."}},
            ["environment_id", "app_id"],
        ),
        _function_tool(
            "tap",
            "Tap a UI element on a phone. Use on mobile environments.",
            {"environment_id": _ENV, "target": {"type": "string", "description": "ID of the UI element to tap (e.g. 'submit')."}},
            ["environment_id", "target"],
        ),
        _function_tool(
            "click",
            "Click a UI element on a desktop. Use on desktop environments.",
            {"environment_id": _ENV, "target": {"type": "string", "description": "ID of the UI element to click (e.g. 'submit')."}},
            ["environment_id", "target"],
        ),
        _function_tool(
            "mouse_click",
            "Click at pixel (x, y) on the currently focused app of the named environment. The server hit-tests against the app's element_bounds (exposed in the observation) and dispatches the appropriate action. Use this when you want to drive the GUI like a real mouse rather than naming a semantic target.",
            {
                "environment_id": _ENV,
                "x": {"type": "number", "description": "Logical x pixel within the app content area."},
                "y": {"type": "number", "description": "Logical y pixel within the app content area."},
            },
            ["environment_id", "x", "y"],
        ),
        _function_tool(
            "key_press",
            "Press a single special key (Enter, Escape, Tab) on the focused environment. Enter while an input is focused triggers the focused app's submit/save button. Escape clears the focused input.",
            {
                "environment_id": _ENV,
                "key": {"type": "string", "enum": ["Enter", "Escape", "Tab"], "description": "The key to press."},
            },
            ["environment_id", "key"],
        ),
        _function_tool(
            "type_text",
            "Type a string into a focused input field.",
            {
                "environment_id": _ENV,
                "target": {"type": "string", "description": "ID of the input field (e.g. 'otp')."},
                "value": {"type": "string", "description": "Text to type."},
            },
            ["environment_id", "target", "value"],
        ),
        _function_tool(
            "view",
            "Read/refresh the visible state of the currently focused app. Use to re-examine without changing state.",
            {"environment_id": _ENV, "target": {"type": "string", "description": "Optional UI element to focus on."}},
            ["environment_id"],
        ),
        _function_tool(
            "copy_value",
            "Copy a value to this environment's clipboard. The value is then available to paste on any environment.",
            {"environment_id": _ENV, "value": {"type": "string", "description": "The value to copy."}},
            ["environment_id", "value"],
        ),
        _function_tool(
            "paste_value",
            "Paste the current clipboard contents into a focused input field. The harness records a cross-environment handoff if the value was copied on a different environment.",
            {"environment_id": _ENV, "target": {"type": "string", "description": "ID of the input field receiving the paste."}},
            ["environment_id", "target"],
        ),
        _function_tool(
            "ask_clarification",
            "Ask the user a clarifying question when the task is genuinely ambiguous. Only use when proceeding would risk a wrong-recipient, wrong-account, or irreversible action.",
            {"environment_id": _ENV, "question": {"type": "string", "description": "The clarification question."}},
            ["environment_id", "question"],
        ),
        _function_tool(
            "declare_done",
            "Signal that the user's request is complete. Use as the final action only.",
            {"environment_id": _ENV},
            ["environment_id"],
        ),
    ]


# Map a tool name -> (action_type, arg_layout).
_TOOL_TO_ACTION_TYPE: dict[str, str] = {
    "open_app": "open_app",
    "tap": "tap",
    "click": "click",
    "type_text": "type",
    "view": "view",
    "copy_value": "copy_value",
    "paste_value": "paste_value",
    "ask_clarification": "ask_clarification",
    "declare_done": "declare_done",
    "mouse_click": "mouse_click",
    "key_press": "key_press",
}


def tool_call_to_action(name: str, arguments: dict[str, Any]) -> Action:
    if name not in _TOOL_TO_ACTION_TYPE:
        raise ValueError(f"unknown tool name: {name}")
    action_type = _TOOL_TO_ACTION_TYPE[name]
    env_id = arguments.get("environment_id", "")

    match name:
        case "open_app":
            return Action(environment_id=env_id, type=action_type, target=arguments.get("app_id"))
        case "tap" | "click" | "paste_value" | "view":
            return Action(environment_id=env_id, type=action_type, target=arguments.get("target"))
        case "type_text":
            return Action(environment_id=env_id, type=action_type, target=arguments.get("target"), value=arguments.get("value"))
        case "copy_value":
            return Action(environment_id=env_id, type=action_type, value=arguments.get("value"))
        case "ask_clarification":
            return Action(environment_id=env_id, type=action_type, value=arguments.get("question"))
        case "declare_done":
            return Action(environment_id=env_id, type=action_type)
        case "mouse_click":
            return Action(environment_id=env_id, type=action_type, x=arguments.get("x"), y=arguments.get("y"))
        case "key_press":
            return Action(environment_id=env_id, type=action_type, key=arguments.get("key"))
        case _:
            raise AssertionError(f"unhandled tool {name}")  # should be unreachable
