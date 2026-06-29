"""Available v0 tasks, keyed by task_id.

Builders are auto-discovered: any module in this package that defines a top-level
``build_*_task`` function (callable with no required args) is imported, the function is
re-exported at the package level, and the task it builds is registered in TASK_REGISTRY
under its ``task_id``. Dropping a new ``catalog/`` task into a new module is enough to make
it runnable — no edit to this file required.
"""

from __future__ import annotations

import importlib
import pkgutil
from typing import Callable, cast

from ..schemas import Task

TASK_REGISTRY: dict[str, Callable[[], Task]] = {}

# Discovered builder function names, populated below and exported for `from ... import`.
_builder_names: list[str] = []

# Non-fatal discovery problems (import error, build error, duplicate id). Kept so a strict
# check (e.g. in tests) can assert the registry is clean, while a single broken/half-written
# module never breaks `import personalgui.tasks` for everything else — important when many
# task modules are being added concurrently.
DISCOVERY_ERRORS: list[str] = []


def _discover() -> None:
    for _finder, modname, ispkg in pkgutil.iter_modules(__path__):
        if ispkg or modname.startswith("_"):
            continue
        try:
            mod = importlib.import_module(f"{__name__}.{modname}")
        except Exception as exc:  # a broken module shouldn't sink the whole package
            DISCOVERY_ERRORS.append(f"import {modname}: {exc!r}")
            continue
        for attr in dir(mod):
            if not (attr.startswith("build_") and attr.endswith("_task")):
                continue
            raw = getattr(mod, attr)
            if not callable(raw):
                continue
            fn = cast(Callable[[], Task], raw)
            try:
                task = fn()
            except Exception as exc:
                DISCOVERY_ERRORS.append(f"build {modname}.{attr}: {exc!r}")
                continue
            if task.task_id in TASK_REGISTRY:
                DISCOVERY_ERRORS.append(f"duplicate task_id {task.task_id!r} from {modname}.{attr}")
                continue
            globals()[attr] = fn  # re-export at package level
            _builder_names.append(attr)
            TASK_REGISTRY[task.task_id] = fn


_discover()


def list_tasks() -> list[dict[str, str]]:
    """Lightweight catalog for the task picker."""
    out = []
    for builder in TASK_REGISTRY.values():
        t = builder()
        out.append({"task_id": t.task_id, "request": t.request})
    return out


def build_task(task_id: str) -> Task:
    if task_id not in TASK_REGISTRY:
        raise KeyError(f"unknown task_id: {task_id}; valid: {sorted(TASK_REGISTRY)}")
    return TASK_REGISTRY[task_id]()


__all__ = ["TASK_REGISTRY", "list_tasks", "build_task", *sorted(set(_builder_names))]
