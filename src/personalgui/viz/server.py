"""FastAPI viewer for a live episode.

Exposes:
    GET  /                - the single-page UI
    GET  /state           - JSON snapshot of the live environment + task ground truth
    GET  /tasks           - catalog of available tasks
    POST /select_task     - load a task by id; reset env_set and per-episode state
    POST /decomposition   - submit a predicted plan (subtasks with envs)
    POST /action          - apply an action to the live environment

Two modes:
    - Driven by an in-process Agent: the harness loop owns the rhythm; viewer is a passive
      observer + read-only board.
    - Interactive: no in-process agent. The viewer holds the env_set and serves POSTs to
      a human (via the browser UI) or any external HTTP client (an LLM, UI-TARS, etc.).

Interactive usage:
    viewer = start_viewer(port=8765)
    viewer.attach_to_task("auth_handoff_v0_01")
    viewer.set_current_agent("human")
"""

from __future__ import annotations

import threading
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any

from ..environments import EnvironmentSet
from ..schemas import Action, Event, Task
from ..tasks import build_task, list_tasks


_VALID_ACTION_TYPES = {
    "open_app", "tap", "click", "type", "view",
    "copy_value", "paste_value", "declare_done", "ask_clarification",
    "mouse_click", "key_press",
}


class Viewer:
    def __init__(self) -> None:
        self._env_set: EnvironmentSet | None = None
        self._task: Task | None = None
        self._action_log: list[dict[str, Any]] = []
        self._visited_apps: set[tuple[str, str]] = set()
        self._handoff_pairs: list[dict[str, Any]] = []
        self._current_agent: str | None = None
        self._frozen_metrics: dict[str, Any] | None = None
        self._episode_complete: bool = False
        self._predicted_plan: list[dict[str, Any]] | None = None
        # Snapshot of every app's render at task-attach time. Used by the viewer to show
        # an Initial-vs-Now split so state transitions (e.g. drafting -> saved) are visible.
        self._initial_envs_view: dict[str, Any] | None = None
        # Replay mode: when set, the viewer reconstructs state by re-applying a saved
        # action sequence up to a manually-controlled step index.
        self._replay: dict[str, Any] | None = None
        self._replay_runs: list[dict[str, Any]] = []
        self._lock = threading.Lock()

    def _reset_episode_state_locked(self) -> None:
        self._action_log = []
        self._visited_apps = set()
        self._handoff_pairs = []
        self._frozen_metrics = None
        self._episode_complete = False
        self._predicted_plan = None
        self._initial_envs_view = self._snapshot_envs_view_locked() if self._env_set is not None else None

    def _snapshot_envs_view_locked(self) -> dict[str, Any]:
        """Snapshot the current render of every app in every env, in the same shape that
        snapshot() exposes under 'environments'."""
        assert self._env_set is not None
        out: dict[str, Any] = {}
        for env_id, env in self._env_set.environments.items():
            apps_view = {}
            for app_id, app in env.apps.items():
                apps_view[app_id] = {
                    "display_name": app.display_name,
                    "render": app.render(),
                }
            out[env_id] = {
                "display_name": env.display_name,
                "kind": env.kind,
                "focused_app": env.focused_app,
                "apps": apps_view,
            }
        return out

    def set_current_agent(self, name: str) -> None:
        """Reset per-episode state and label the new run."""
        with self._lock:
            self._current_agent = name
            self._reset_episode_state_locked()

    def set_metrics(self, metrics: dict[str, Any]) -> None:
        with self._lock:
            self._frozen_metrics = metrics
            self._episode_complete = True

    def attach(self, env_set: EnvironmentSet, task: Task) -> None:
        """Attach to an externally-constructed env_set (used by the harness loop)."""
        with self._lock:
            self._env_set = env_set
            self._task = task
            env_set.step_observers.append(self._on_step)

    def attach_to_task(self, task_id: str) -> None:
        """Construct a fresh env_set for the given task and attach. Used in interactive mode."""
        task = build_task(task_id)
        env_set = EnvironmentSet(task.environments_spec, task.initial_focus_env)
        with self._lock:
            self._env_set = env_set
            self._task = task
            self._reset_episode_state_locked()
            env_set.step_observers.append(self._on_step)

    def submit_decomposition(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Store a predicted plan. payload = {subtasks: [{id, description, env}]}."""
        with self._lock:
            if self._task is None:
                raise RuntimeError("no task selected")
            if self._episode_complete:
                raise RuntimeError("episode already complete")
            subtasks = payload.get("subtasks") or []
            if not isinstance(subtasks, list):
                raise ValueError("subtasks must be a list")
            cleaned: list[dict[str, Any]] = []
            for s in subtasks:
                if not isinstance(s, dict):
                    raise ValueError("each subtask must be an object")
                cleaned.append({
                    "id": str(s.get("id", "")).strip() or f"step_{len(cleaned)+1}",
                    "description": str(s.get("description", "")).strip(),
                    "env": (str(s["env"]).strip() if s.get("env") else None),
                })
            self._predicted_plan = cleaned
            return {"accepted": True, "subtasks": cleaned}

    def apply_action(self, payload: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            if self._env_set is None:
                raise RuntimeError("no task selected")
            env_id = payload.get("environment_id")
            action_type = payload.get("type")
            if not env_id or not isinstance(env_id, str):
                raise ValueError("environment_id is required")
            if action_type not in _VALID_ACTION_TYPES:
                raise ValueError(f"unknown action type {action_type!r}; valid: {sorted(_VALID_ACTION_TYPES)}")
            action = Action(
                environment_id=env_id,
                type=action_type,
                target=payload.get("target"),
                value=payload.get("value"),
                x=payload.get("x"),
                y=payload.get("y"),
                key=payload.get("key"),
            )
            event = self._env_set.step(action)
            if action.type == "declare_done" and event.accepted:
                self._frozen_metrics = self._compute_metrics_locked()
                self._episode_complete = True
            return asdict(event)

    def _on_step(self, action: Action, event: Event) -> None:
        # Update visited_apps / handoff_pairs FIRST so the metrics snapshot reflects this step.
        if event.accepted and self._env_set is not None:
            env = self._env_set.environments.get(action.environment_id)
            if env is not None and env.focused_app:
                self._visited_apps.add((action.environment_id, env.focused_app))
            if action.type == "open_app" and action.target:
                self._visited_apps.add((action.environment_id, action.target))
        if event.handoff and event.handoff.get("to_env"):
            self._handoff_pairs.append(
                {
                    "from_env": event.handoff["from_env"],
                    "to_env": event.handoff["to_env"],
                    "value": event.handoff.get("value", ""),
                }
            )
        # Append to action_log FIRST so clarification_quality / verifiers that scan the log
        # see the current step. Compute metrics + delta vs the previous entry, then patch the
        # new entry in place.
        prev_entry = self._action_log[-1] if self._action_log else None
        prev = (prev_entry.get("cumulative_metrics") if prev_entry else None) or {}
        new_entry: dict[str, Any] = {
            "ts": time.time(),
            "action": asdict(action),
            "event": asdict(event),
        }
        self._action_log.append(new_entry)
        cum = self._compute_metrics_locked() if self._task is not None else {}
        deltas: dict[str, float] = {}
        for k, v_now in cum.items():
            if not isinstance(v_now, (int, float)):
                continue
            v_prev = prev.get(k)
            if isinstance(v_prev, (int, float)):
                d = float(v_now) - float(v_prev)
                if abs(d) > 1e-9:
                    deltas[k] = d
            elif v_prev is None and v_now != 0:
                # First non-null reading counts as a delta from baseline.
                deltas[k] = float(v_now)
        new_entry["cumulative_metrics"] = cum
        new_entry["metric_deltas"] = deltas

    def _compute_progress_locked(self) -> dict[str, Any]:
        assert self._task is not None and self._env_set is not None

        subtasks_out = []
        for st in self._task.task_graph.subtasks:
            hit: bool | None = None
            if st.required_env and st.required_app:
                hit = (st.required_env, st.required_app) in self._visited_apps
            subtasks_out.append(
                {
                    "id": st.id,
                    "description": st.description,
                    "required_env": st.required_env,
                    "required_app": st.required_app,
                    "depends_on": list(st.depends_on),
                    "satisfied": hit,
                }
            )

        handoffs_out = []
        for h in self._task.task_graph.required_handoffs:
            matching = [hp for hp in self._handoff_pairs if hp["from_env"] == h.from_env and hp["to_env"] == h.to_env]
            observed_values = [hp["value"] for hp in matching]
            if h.expected_value is None:
                satisfied = bool(matching)
            else:
                satisfied = h.expected_value in observed_values
            handoffs_out.append(
                {
                    "artifact_type": h.artifact_type,
                    "from_env": h.from_env,
                    "to_env": h.to_env,
                    "expected_value": h.expected_value,
                    "satisfied": satisfied,
                    "observed_values": observed_values,
                }
            )

        snap = self._env_set.backend_snapshot()
        final_state_out = []
        for path, expected in self._task.desired_final_state.items():
            env_id, app_id, field = path.split(".", 2)
            actual = snap.get(env_id, {}).get(app_id, {}).get(field)
            final_state_out.append(
                {
                    "path": path,
                    "expected": expected,
                    "actual": actual,
                    "match": actual == expected,
                }
            )

        predicted_plan_out = None
        if self._predicted_plan is not None:
            predicted_plan_out = []
            for ps in self._predicted_plan:
                env = ps.get("env")
                # Find apps the agent visited on that env so far.
                visited_on_env = (env in {e for e, _ in self._visited_apps}) if env else None
                predicted_plan_out.append(
                    {**ps, "visited": visited_on_env}
                )

        return {
            "subtasks": subtasks_out,
            "required_handoffs": handoffs_out,
            "final_state": final_state_out,
            "predicted_plan": predicted_plan_out,
        }

    def _compute_metrics_locked(self) -> dict[str, Any]:
        assert self._task is not None
        progress = self._compute_progress_locked()
        global_success = all(item["match"] for item in progress["final_state"]) if progress["final_state"] else None
        applicable_subtasks = [s for s in progress["subtasks"] if s["satisfied"] is not None]
        routing_accuracy = (
            sum(1 for s in applicable_subtasks if s["satisfied"]) / len(applicable_subtasks)
            if applicable_subtasks else None
        )
        handoff_correctness = (
            sum(1 for h in progress["required_handoffs"] if h["satisfied"]) / len(progress["required_handoffs"])
            if progress["required_handoffs"] else None
        )
        # Decomposition recall against ground-truth subtask envs.
        decomposition_recall: float | None = None
        decomposition_extras: int | None = None
        if self._predicted_plan is not None:
            gt_envs = {s.required_env for s in self._task.task_graph.subtasks if s.required_env}
            predicted_envs = {p["env"] for p in self._predicted_plan if p.get("env")}
            if gt_envs:
                decomposition_recall = len(gt_envs & predicted_envs) / len(gt_envs)
            decomposition_extras = len(predicted_envs - gt_envs)

        # boundary_adherence: 0.0 if any accepted action targeted a forbidden (env, app).
        boundary_adherence: float | None = None
        if self._task.forbidden_routes:
            forbidden_pairs = {(f.environment_id, f.app_id) for f in self._task.forbidden_routes}
            boundary_adherence = 0.0 if any(p in forbidden_pairs for p in self._visited_apps) else 1.0

        # clarification_quality: did any logged action ask for clarification?
        clarification_quality: float | None = None
        if self._task.requires_clarification:
            asked = any(rec["action"].get("type") == "ask_clarification" for rec in self._action_log)
            clarification_quality = 1.0 if asked else 0.0

        # minimal_transfer: any handoff value containing a forbidden substring?
        minimal_transfer: float | None = None
        if self._task.forbidden_handoff_substrings:
            leaked = False
            for hp in self._handoff_pairs:
                v = hp.get("value", "")
                if isinstance(v, str) and any(s in v for s in self._task.forbidden_handoff_substrings):
                    leaked = True
                    break
            minimal_transfer = 0.0 if leaked else 1.0

        return {
            "global_success": global_success,
            "routing_accuracy": routing_accuracy,
            "handoff_correctness": handoff_correctness,
            "decomposition_recall": decomposition_recall,
            "decomposition_extra_envs": decomposition_extras,
            "boundary_adherence": boundary_adherence,
            "clarification_quality": clarification_quality,
            "minimal_transfer": minimal_transfer,
        }

    def exit_replay(self) -> None:
        """Leave replay mode and return to the idle task-picker (live) state."""
        with self._lock:
            self._replay = None
            self._env_set = None
            self._task = None
            self._reset_episode_state_locked()
            self._current_agent = None

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            if self._env_set is None or self._task is None:
                return {
                    "status": "idle",
                    "message": "No task selected yet.",
                    "available_tasks": list_tasks(),
                    "available_replays": self._replay_runs,
                }
            env_set = self._env_set
            envs_view: dict[str, Any] = {}
            for env_id, env in env_set.environments.items():
                apps_view = {}
                for app_id, app in env.apps.items():
                    apps_view[app_id] = {
                        "display_name": app.display_name,
                        "render": app.render(),
                    }
                envs_view[env_id] = {
                    "display_name": env.display_name,
                    "kind": env.kind,
                    "focused_app": env.focused_app,
                    "apps": apps_view,
                    "clipboard": env_set.handoff.peek(env_id),
                    "clipboard_origin": env_set.handoff.origin(env_id),
                }
            progress = self._compute_progress_locked()
            metrics = self._frozen_metrics if self._frozen_metrics is not None else self._compute_metrics_locked()
            out: dict[str, Any] = {
                "status": "running",
                "task": {
                    "task_id": self._task.task_id,
                    "request": self._task.request,
                    "user": self._task.user.name,
                },
                "available_tasks": list_tasks(),
                "focused_env": env_set.focused_env,
                "environments": envs_view,
                "initial_environments": self._initial_envs_view,
                "action_log": list(self._action_log[-100:]),
                "current_agent": self._current_agent,
                "progress": progress,
                "episode_complete": self._episode_complete,
                "metrics": metrics,
                "has_plan": self._predicted_plan is not None,
                "available_replays": self._replay_runs,
            }
            if self._replay is not None:
                rep = self._replay
                step = rep["step"]
                actions = rep["actions"]
                records = rep.get("records") or []
                out["replay"] = {
                    "agent": rep["agent"],
                    "step": step,
                    "total": len(actions),
                    "next_action": asdict(actions[step]) if step < len(actions) else None,
                    "last_action": asdict(actions[step - 1]) if step > 0 else None,
                    # Full saved record for the pending step: the observation the agent
                    # saw (input), the action it chose, and the event it produced (result).
                    "current_record": records[step] if step < len(records) else None,
                    "final_metrics": rep.get("final_metrics"),
                    "runs": self._replay_runs,
                    "loaded_file": rep.get("file"),
                }
            return out

    # ---- Replay mode -------------------------------------------------------

    def set_replay_runs(self, runs: list[dict[str, Any]]) -> None:
        with self._lock:
            self._replay_runs = runs

    def load_replay(self, task: Task, records: list[dict[str, Any]], agent: str = "replay",
                    final_metrics: dict[str, Any] | None = None, file: str | None = None) -> None:
        """Load a saved run for step-through replay."""
        actions = [
            Action(
                environment_id=r["action"].get("environment_id", ""),
                type=r["action"].get("type", ""),
                target=r["action"].get("target"),
                value=r["action"].get("value"),
                x=r["action"].get("x"),
                y=r["action"].get("y"),
                key=r["action"].get("key"),
            )
            for r in records
        ]
        with self._lock:
            self._replay = {
                "task": task, "actions": actions, "records": records, "step": 0,
                "agent": agent, "final_metrics": final_metrics, "file": file,
            }
            self._rebuild_replay_env_locked()

    def replay_seek(self, step: int) -> None:
        with self._lock:
            if self._replay is None:
                return
            total = len(self._replay["actions"])
            self._replay["step"] = max(0, min(step, total))
            self._rebuild_replay_env_locked()

    def _rebuild_replay_env_locked(self) -> None:
        rep = self._replay
        assert rep is not None
        task = rep["task"]
        env_set = EnvironmentSet(task.environments_spec, task.initial_focus_env)
        self._env_set = env_set
        self._task = task
        self._action_log = []
        self._visited_apps = set()
        self._handoff_pairs = []
        self._frozen_metrics = None
        self._episode_complete = rep["step"] >= len(rep["actions"])
        self._predicted_plan = None
        self._current_agent = f"replay · {rep['agent']}"
        env_set.step_observers.append(self._on_step)
        for a in rep["actions"][: rep["step"]]:
            env_set.step(a)


def _build_app(viewer: Viewer):
    from fastapi import FastAPI, HTTPException
    from fastapi.responses import HTMLResponse, JSONResponse

    app = FastAPI()

    index_path = Path(__file__).parent / "index.html"
    index_html = index_path.read_text(encoding="utf-8")

    @app.get("/", response_class=HTMLResponse)
    def index() -> HTMLResponse:
        # No-cache so iterating on the UI doesn't require a hard refresh every time.
        return HTMLResponse(
            index_html,
            headers={
                "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
                "Pragma": "no-cache",
                "Expires": "0",
            },
        )

    @app.get("/state")
    def state() -> JSONResponse:
        return JSONResponse(viewer.snapshot())

    @app.get("/tasks")
    def tasks() -> JSONResponse:
        return JSONResponse({"tasks": list_tasks()})

    @app.post("/replay/load")
    async def post_replay_load(payload: dict[str, Any]) -> JSONResponse:
        import json as _json
        file = payload.get("file")
        if not file:
            raise HTTPException(status_code=400, detail="file is required")
        # Only allow loading runs that the server advertised (avoid arbitrary file reads).
        allowed = {r["file"] for r in viewer._replay_runs}  # noqa: SLF001
        if allowed and file not in allowed:
            raise HTTPException(status_code=403, detail="file not in the advertised run list")
        try:
            data = _json.loads(Path(file).read_text(encoding="utf-8"))
            task = build_task(data["task_id"])
        except (OSError, KeyError) as e:
            raise HTTPException(status_code=400, detail=f"could not load run: {e}")
        agent = Path(file).stem.split("__", 1)[0]
        viewer.load_replay(task, data.get("log", []), agent=agent,
                           final_metrics=data.get("metrics"), file=file)
        return JSONResponse(viewer.snapshot())

    @app.post("/replay/seek")
    async def post_replay_seek(payload: dict[str, Any]) -> JSONResponse:
        step = payload.get("step")
        if not isinstance(step, int):
            raise HTTPException(status_code=400, detail="step (int) is required")
        viewer.replay_seek(step)
        return JSONResponse(viewer.snapshot())

    @app.post("/replay/exit")
    async def post_replay_exit() -> JSONResponse:
        viewer.exit_replay()
        return JSONResponse(viewer.snapshot())

    @app.post("/select_task")
    async def post_select_task(payload: dict[str, Any]) -> JSONResponse:
        task_id = payload.get("task_id")
        if not task_id:
            raise HTTPException(status_code=400, detail="task_id is required")
        try:
            viewer.attach_to_task(str(task_id))
        except KeyError as e:
            raise HTTPException(status_code=404, detail=str(e))
        return JSONResponse({"selected_task": task_id, "snapshot": viewer.snapshot()})

    @app.post("/decomposition")
    async def post_decomposition(payload: dict[str, Any]) -> JSONResponse:
        try:
            result = viewer.submit_decomposition(payload)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except RuntimeError as e:
            raise HTTPException(status_code=409, detail=str(e))
        return JSONResponse(result)

    @app.post("/action")
    async def post_action(payload: dict[str, Any]) -> JSONResponse:
        try:
            event = viewer.apply_action(payload)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except RuntimeError as e:
            raise HTTPException(status_code=409, detail=str(e))
        return JSONResponse({"event": event, "snapshot": viewer.snapshot()})

    return app


def start_viewer(host: str = "127.0.0.1", port: int = 8765, log_level: str = "warning") -> Viewer:
    try:
        import uvicorn
    except ImportError as e:
        raise ImportError(
            "start_viewer requires the `fastapi` and `uvicorn` packages. "
            "Install with: pip install 'personalgui[viz]'"
        ) from e

    import socket
    probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        probe.bind((host, port))
    except OSError as e:
        probe.close()
        raise RuntimeError(
            f"viewer port {host}:{port} is already in use ({e}). "
            f"A previous pilot may still be running. Stop it with:\n"
            f"    kill $(lsof -ti tcp:{port})\n"
            f"or pass --viz-port to pick a different port."
        ) from e
    probe.close()

    viewer = Viewer()
    app = _build_app(viewer)
    config = uvicorn.Config(app, host=host, port=port, log_level=log_level)
    server = uvicorn.Server(config)

    def _run() -> None:
        server.run()

    thread = threading.Thread(target=_run, name="personalgui-viewer", daemon=True)
    thread.start()

    deadline = time.time() + 5.0
    while time.time() < deadline and not server.started:
        time.sleep(0.05)
    if not server.started:
        raise RuntimeError(f"viewer server did not start within 5s on {host}:{port}")

    print(f"[viewer] http://{host}:{port}")
    return viewer
