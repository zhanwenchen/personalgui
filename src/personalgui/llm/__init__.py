"""LLM-backed agent for PersonalGUI.

External entry points:
    LLMAgent         - subclass of Agent that drives an OpenAI-compatible LLM.
    OpenAICompatBackend - HTTP backend for vLLM / llama.cpp / Ollama / etc.
    ScriptedBackend  - deterministic backend for tests.
"""

from .agent import LLMAgent
from .backend import LLMBackend, OpenAICompatBackend, ScriptedBackend, ScriptedToolCall

__all__ = [
    "LLMAgent",
    "LLMBackend",
    "OpenAICompatBackend",
    "ScriptedBackend",
    "ScriptedToolCall",
]
