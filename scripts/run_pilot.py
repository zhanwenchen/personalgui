"""CLI: run baselines on one or more PersonalGUI v0 tasks and print results as JSON.

Always runs the two scripted baselines by default. Pass --llm to also run the local LLM
agent. Pass --viz to spin up the live web viewer at http://localhost:8765.

Examples:
    python scripts/run_pilot.py
    python scripts/run_pilot.py --tasks all
    python scripts/run_pilot.py --tasks standup_reminder_v0_01,receipt_amount_v0_01
    python scripts/run_pilot.py --tasks all --agents llm --llm
    python scripts/run_pilot.py --viz --step-delay 0.5
    python scripts/run_pilot.py --llm --viz \\
        --llm-base-url http://localhost:8080/v1 \\
        --llm-model Qwen3.5-4B-Q4_K_M.gguf --llm-api-key local
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from personalgui.agents import Agent, ScriptedNaiveAgent, ScriptedOracleAgent
from personalgui.harness import evaluate_task
from personalgui.schemas import Task
from personalgui.tasks import TASK_REGISTRY, build_task
from personalgui.verifiers import DEFAULT_VERIFIERS


_DEFAULT_TASK = "auth_handoff_v0_01"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run PersonalGUI v0 baselines.")
    parser.add_argument(
        "--tasks",
        default=_DEFAULT_TASK,
        help=(
            f"Comma-separated task ids, or 'all' to run every registered task. "
            f"Default: {_DEFAULT_TASK}. Available: {sorted(TASK_REGISTRY)}."
        ),
    )
    parser.add_argument(
        "--agents",
        default="oracle,naive",
        help="Comma-separated scripted baselines (oracle, naive). LLM added separately by --llm. Default: oracle,naive.",
    )
    parser.add_argument("--llm", action="store_true", help="Also run the local LLM agent.")
    parser.add_argument("--llm-base-url", help="LLM server base URL ending in /v1.")
    parser.add_argument("--llm-model", help="Model name registered on the LLM server.")
    parser.add_argument("--llm-api-key", help="API key for the LLM server (most local ones don't validate it).")
    parser.add_argument("--llm-temperature", type=float, default=0.0)
    parser.add_argument(
        "--llm-max-messages",
        type=int,
        default=24,
        help=(
            "Rolling-history cap for the LLM agent. Older (assistant, tool, user) triples "
            "are dropped to fit the server's context window. Default 24 (≈ 7 turns) is sized "
            "for an 8K context; raise to 36–48 for 16K, 64+ for 32K."
        ),
    )
    parser.add_argument("--viz", action="store_true", help="Spin up the live web viewer.")
    parser.add_argument("--viz-port", type=int, default=8765)
    parser.add_argument(
        "--step-delay",
        type=float,
        default=0.0,
        help="Seconds to pause after each agent step. Auto-defaults to 0.4 with --viz so scripted agents are watchable.",
    )
    parser.add_argument(
        "--print-trajectories",
        action="store_true",
        help="Also print each run's compact action trajectory to stdout.",
    )
    parser.add_argument(
        "--results-dir",
        default=None,
        metavar="DIR",
        help="Base results directory. Each run writes to <DIR>/<YYYYMMDDHHMM>/. "
        "Default: <repo>/results.",
    )
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Disable writing results to disk (stdout only).",
    )
    return parser.parse_args()


def _resolve_tasks(spec: str) -> list[Task]:
    """Resolve --tasks 'all' or 'id1,id2' into a list of Task instances."""
    spec = (spec or "").strip()
    if spec == "" or spec == "all":
        return [build() for build in TASK_REGISTRY.values()]
    out: list[Task] = []
    for tid in spec.split(","):
        tid = tid.strip()
        if not tid:
            continue
        if tid not in TASK_REGISTRY:
            raise SystemExit(f"unknown task: {tid!r}; valid: {sorted(TASK_REGISTRY)}")
        out.append(build_task(tid))
    if not out:
        raise SystemExit("--tasks resolved to an empty list")
    return out


def _build_baselines(names: list[str]) -> dict[str, Agent]:
    pool: dict[str, Agent] = {"oracle": ScriptedOracleAgent(), "naive": ScriptedNaiveAgent()}
    out: dict[str, Agent] = {}
    for n in names:
        n = n.strip()
        if not n:
            continue
        if n not in pool:
            raise SystemExit(f"unknown baseline: {n}; valid: {list(pool)}")
        out[n] = pool[n]
    return out


_METRIC_SHORT = {
    "routing_accuracy": "routing",
    "handoff_correctness": "handoff",
    "global_success": "success",
    "boundary_adherence": "boundary",
    "clarification_quality": "clarify",
    "minimal_transfer": "min-xfer",
    "decomposition_recall": "decomp",
}


def _step_deltas(prev: dict | None, curr: dict | None) -> dict[str, float]:
    """Numeric deltas between two cumulative_metrics snapshots, skipping no-ops."""
    if not curr:
        return {}
    prev = prev or {}
    out: dict[str, float] = {}
    for k, v_now in curr.items():
        if not isinstance(v_now, (int, float)) or isinstance(v_now, bool):
            # Booleans are a subclass of int — treat global_success True/False numerically below.
            if isinstance(v_now, bool):
                v_now = 1.0 if v_now else 0.0
            else:
                continue
        v_prev = prev.get(k)
        if isinstance(v_prev, bool):
            v_prev = 1.0 if v_prev else 0.0
        if isinstance(v_prev, (int, float)):
            d = float(v_now) - float(v_prev)
            if abs(d) > 1e-9:
                out[k] = d
        elif v_prev is None and float(v_now) != 0.0:
            out[k] = float(v_now)
    return out


def _fmt_deltas(d: dict[str, float]) -> str:
    if not d:
        return ""
    parts = []
    for k, v in d.items():
        label = _METRIC_SHORT.get(k, k)
        parts.append(f"{label}{'+' if v >= 0 else ''}{v:.2f}")
    return "  Δ " + " ".join(parts)


def _format_trajectory(agent_name: str, task_id: str, log: list[dict]) -> str:
    """Compact one-line-per-action printout for a single (agent, task) run."""
    lines = [f"=== {agent_name} · {task_id}  ({len(log)} steps) ==="]
    prev_cum: dict | None = None
    for i, rec in enumerate(log, 1):
        a = rec["action"]
        e = rec["event"]
        ok = "·" if e.get("accepted") else "✗"
        env = (a.get("environment_id") or "")[:18]
        atype = (a.get("type") or "")[:12]
        bits: list[str] = []
        if a.get("target"):
            bits.append(f"target={a['target']}")
        if a.get("value") is not None:
            v = str(a["value"])
            if len(v) > 60:
                v = v[:57] + "..."
            bits.append(f"value={v!r}")
        if a.get("x") is not None and a.get("y") is not None:
            bits.append(f"@({a['x']},{a['y']})")
        if a.get("key"):
            bits.append(f"key={a['key']}")
        argstr = " ".join(bits)
        annotation = ""
        if not e.get("accepted"):
            annotation = f"  ← {e.get('error') or 'rejected'}"
        else:
            sc = e.get("state_changes") or {}
            ho = e.get("handoff") or {}
            if isinstance(sc.get("status"), list):
                annotation = f"  → status: {sc['status'][0]} → {sc['status'][1]}"
            elif ho.get("to_env"):
                v = str(ho.get("value", ""))[:40]
                annotation = f"  → handoff {ho.get('from_env','?')}→{ho.get('to_env','?')}: {v!r}"
            elif "appended" in sc:
                annotation = f"  → appended {sc['appended']}"
        cum = rec.get("cumulative_metrics")
        delta_str = _fmt_deltas(_step_deltas(prev_cum, cum))
        prev_cum = cum
        lines.append(f"  {ok} {i:>2}  {env:<18}  {atype:<12}  {argstr}{annotation}{delta_str}")
    return "\n".join(lines)


def _summary_table(results: dict[str, list[dict]]) -> str:
    """Compact ASCII grid: agent rows × task columns showing global_success."""
    if not results:
        return ""
    agent_names = list(results.keys())
    task_ids = []
    for runs in results.values():
        for run in runs:
            if run["task_id"] not in task_ids:
                task_ids.append(run["task_id"])
    col_w = max(12, max((len(t) for t in task_ids), default=0))
    agent_w = max(8, max(len(a) for a in agent_names))
    lines = []
    header = "agent".ljust(agent_w) + " │ " + " │ ".join(t.ljust(col_w) for t in task_ids)
    sep = "─" * agent_w + "─┼─" + "─┼─".join("─" * col_w for _ in task_ids)
    lines.append(header)
    lines.append(sep)
    for agent in agent_names:
        run_by_id = {r["task_id"]: r for r in results[agent]}
        cells = []
        for tid in task_ids:
            r = run_by_id.get(tid)
            if r is None:
                cells.append("-".ljust(col_w))
                continue
            m = r["metrics"]
            gs = m.get("global_success")
            ra = m.get("routing_accuracy")
            ha = m.get("handoff_correctness")
            tag = "PASS" if gs else "FAIL" if gs is False else "—"
            timeout = "⏱" if m.get("terminated_by") == "max_steps" else ""
            steps = m.get("steps_used")
            ra_s = f"{ra * 100:.0f}%" if ra is not None else "—"
            ha_s = f"{ha * 100:.0f}%" if ha is not None else "—"
            steps_s = f" {steps}st" if steps is not None else ""
            cells.append(f"{tag}{timeout} r={ra_s} h={ha_s}{steps_s}".ljust(col_w))
        lines.append(agent.ljust(agent_w) + " │ " + " │ ".join(cells))
    return "\n".join(lines)


def main() -> None:
    args = _parse_args()

    tasks = _resolve_tasks(args.tasks)
    agents = _build_baselines(args.agents.split(","))
    if args.llm:
        from personalgui.llm import LLMAgent, OpenAICompatBackend
        backend = OpenAICompatBackend(
            model=args.llm_model,
            base_url=args.llm_base_url,
            api_key=args.llm_api_key,
            temperature=args.llm_temperature,
        )
        agents["llm"] = LLMAgent(backend=backend, max_messages=args.llm_max_messages)

    if not agents:
        raise SystemExit("no agents selected (pass --agents and/or --llm)")

    on_setup = None
    viewer = None
    if args.viz:
        from personalgui.viz import start_viewer
        viewer = start_viewer(port=args.viz_port)
        on_setup = viewer.attach
        if args.step_delay == 0.0:
            args.step_delay = 0.4
            print("[viewer] --step-delay defaulted to 0.4s for visibility")

    # Per-run results go to results/<YYYYMMDDHHMM>/ unless --no-save.
    run_dir = None
    if not args.no_save:
        from datetime import datetime
        run_id = datetime.now().strftime("%Y%m%d%H%M")
        base = Path(args.results_dir) if args.results_dir else (Path(__file__).resolve().parents[1] / "results")
        run_dir = base / run_id
        run_dir.mkdir(parents=True, exist_ok=True)

    print(f"[pilot] {len(tasks)} task(s) × {len(agents)} agent(s) = {len(tasks) * len(agents)} runs")
    if run_dir is not None:
        print(f"[pilot] saving to {run_dir}")

    results: dict[str, list[dict]] = {}
    trajectories: list[str] = []
    for name, agent in agents.items():
        results[name] = []
        for task in tasks:
            label = f"{name} · {task.task_id}"
            print(f"[run] {label}…", flush=True)
            if viewer is not None:
                viewer.set_current_agent(label)
            metrics, log = evaluate_task(
                task, agent, DEFAULT_VERIFIERS,
                step_delay=args.step_delay, on_setup=on_setup,
            )
            if viewer is not None:
                viewer.set_metrics(metrics)
            results[name].append({"task_id": task.task_id, "metrics": metrics, "log_steps": len(log)})
            traj = _format_trajectory(name, task.task_id, log)
            trajectories.append(traj)
            if args.print_trajectories:
                print(traj)
            if run_dir is not None:
                (run_dir / f"{name}__{task.task_id}.json").write_text(
                    json.dumps({"task_id": task.task_id, "metrics": metrics, "log": log}, indent=2, default=str),
                    encoding="utf-8",
                )
            if viewer is not None and (len(tasks) > 1 or len(agents) > 1):
                import time as _t
                _t.sleep(1.5)

    table = _summary_table(results)
    print()
    print(table)
    print()
    print(json.dumps(results, indent=2, default=str))

    if run_dir is not None:
        (run_dir / "summary.txt").write_text(table + "\n", encoding="utf-8")
        (run_dir / "results.json").write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")
        (run_dir / "trajectories.txt").write_text("\n\n".join(trajectories) + "\n", encoding="utf-8")
        print(f"\n[pilot] results saved to {run_dir}")

    if args.viz:
        print("\n[viewer] all runs complete. Server still running — Ctrl-C to exit.")
        try:
            import time
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
