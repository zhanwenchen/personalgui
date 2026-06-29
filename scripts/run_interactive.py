"""Interactive mode: no in-process agent. Browser or HTTP client drives the task.

Workflow (browser):
  1. Pick a task from the top-of-page dropdown (or pass --task to preselect).
  2. Decompose the task in the Plan panel: list subtasks + which environment handles each.
     Click "Submit plan" to lock it in for scoring.
  3. Interact with the rendered phone and desktop — tap the phone to copy, click Paste or
     type into desktop fields, click Submit, etc.
  4. Click "Declare done" in the header. Metrics freeze.

Same surface for an external agent via HTTP:
    GET  /tasks
    POST /select_task   {task_id}
    POST /decomposition {subtasks: [{id, description, env}]}
    GET  /state         -> observation + ground truth + live metrics
    POST /action        {environment_id, type, target?, value?}

Run with no --task to start at the picker, or with --task to jump straight in:
    uv run python scripts/run_interactive.py
    uv run python scripts/run_interactive.py --task receipt_amount_v0_01
"""

import argparse
from argparse import Namespace
import json
from json import JSONDecodeError
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from personalgui.tasks import TASK_REGISTRY
from personalgui.viz import start_viewer


def _scan_runs(results_base: Path) -> list[dict[str, str]]:
    """Find every saved run JSON under results/<ts>/ so the viewer can offer replay."""
    runs: list[dict[str, str]] = []
    if not results_base.is_dir():
        return runs
    for run_dir in sorted(results_base.iterdir(), reverse=True):
        if not run_dir.is_dir():
            continue
        for p in sorted(run_dir.glob("*.json")):
            if p.name == "results.json":
                continue
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
            except (OSError, JSONDecodeError):
                continue
            if 'log' not in data or 'task_id' not in data:
                continue
            agent = p.stem.split("__", 1)[0]
            runs.append({
                'file': str(p.resolve()),
                'agent': f'{run_dir.name}/{agent}',
                'task_id': data['task_id'],
            })
    return runs


def _parse_args() -> Namespace:
    parser = argparse.ArgumentParser(description='Run PersonalGUI in interactive mode (no in-process agent).')
    parser.add_argument('--viz-port', type=int, default=8765)
    parser.add_argument('--task', choices=sorted(TASK_REGISTRY.keys()), default=None, help=f'Preselect a task. Default: leave on picker. Available: {sorted(TASK_REGISTRY.keys())}',)
    parser.add_argument('--driver', default='human', help='Label shown in the viewer for who is driving (e.g. human, external, ui-tars). Default: human.',)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    viewer = start_viewer(port=args.viz_port)
    viewer.set_current_agent(args.driver)

    # Advertise saved runs so the browser can drop into replay mode from the live viewer.
    runs = _scan_runs(Path(__file__).resolve().parents[1] / "results")
    viewer.set_replay_runs(runs)

    if args.task is not None:
        viewer.attach_to_task(args.task)
        print(f'[interactive] task={args.task}')
    else:
        print(f'[interactive] no task selected; pick one in the browser ({len(TASK_REGISTRY)} available)')
    print(f'[interactive] driver={args.driver}')
    print(f'[interactive] {len(runs)} saved run(s) available for replay')
    print(f'[interactive] open http://localhost:{args.viz_port}/')
    print('[interactive] Ctrl-C to exit.')

    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print('\n[interactive] shutting down.')


if __name__ == '__main__':
    main()
