"""Regenerate catalog/INDEX.md from task-doc frontmatter.

Run from the repo root:  python scripts/build_catalog_index.py

Reads every catalog/<domain>/*.md, parses the YAML frontmatter, and writes a grouped
index table. Tasks whose catalog id appears in catalog/.built_ids are marked with a star
(they have a runnable build_*_task() in src/personalgui/tasks/).
"""

from __future__ import annotations

import re
from pathlib import Path

CATALOG = Path(__file__).resolve().parents[1] / "catalog"

DOMAIN_ORDER = [
    ("finance_expenses", "Finance & expenses"),
    ("scheduling_calendar", "Scheduling & calendar"),
    ("comms_messaging", "Communication & messaging"),
    ("travel", "Travel"),
    ("health_wellness", "Health & wellness"),
    ("auth_security", "Auth & security"),
    ("work_docs_projects", "Work docs & projects"),
    ("shopping_orders", "Shopping & orders"),
    ("home_family", "Home & family"),
    ("media_files", "Media & files"),
]


def parse_frontmatter(text: str) -> dict[str, str]:
    m = re.match(r"^---\n(.*?)\n---", text, re.S)
    if not m:
        return {}
    fm: dict[str, str] = {}
    for line in m.group(1).splitlines():
        if ":" not in line:
            continue
        k, _, v = line.partition(":")
        fm[k.strip()] = v.strip()
    return fm


def strip_list(v: str) -> str:
    return v.strip("[]").strip()


def main() -> None:
    built: set[str] = set()
    built_path = CATALOG / ".built_ids"
    if built_path.exists():
        built = {x.strip() for x in built_path.read_text().splitlines() if x.strip()}

    rows_by_domain: dict[str, list[dict]] = {}
    all_rows: list[dict] = []
    for folder, _title in DOMAIN_ORDER:
        rows = []
        for p in sorted((CATALOG / folder).glob("*.md")):
            fm = parse_frontmatter(p.read_text(encoding="utf-8"))
            if not fm.get("id"):
                continue
            row = {
                "id": fm.get("id", ""),
                "title": fm.get("title", ""),
                "metric": strip_list(fm.get("metric_focus", "")),
                "envs": strip_list(fm.get("environments", "")),
                "difficulty": fm.get("difficulty", ""),
                "code_ready": fm.get("code_ready", ""),
                "file": f"{folder}/{p.name}",
            }
            rows.append(row)
            all_rows.append(row)
        rows_by_domain[folder] = rows

    metric_counts: dict[str, int] = {}
    for r in all_rows:
        metric_counts[r["metric"]] = metric_counts.get(r["metric"], 0) + 1
    code_ready_true = sum(1 for r in all_rows if r["code_ready"] == "true")

    built_count = sum(1 for r in all_rows if r["id"] in built)
    out: list[str] = []
    out.append("# PersonalGUI Task Catalog — Index\n")
    out.append(
        f"**{len(all_rows)} candidate tasks** across {len(DOMAIN_ORDER)} life domains — "
        f"**all {built_count} have a runnable `build_*_task()` builder** in "
        "[`src/personalgui/tasks/`](../src/personalgui/tasks/), each verified solvable by an "
        "oracle test. "
        f"{code_ready_true} were expressible with the 14 original mock apps; "
        f"{len(all_rows) - code_ready_true} needed a small new app surface "
        "(MockInvitePhotoApp / MockFileShareApp / MockFileDropApp / MockProfilePhotoApp and an "
        "enrollment mode on MockAuthenticatorApp), now added.\n"
    )
    out.append(
        "Generated from task-doc frontmatter by `scripts/build_catalog_index.py`. See "
        "[README.md](README.md) for the schema and metric taxonomy. **★** in the *Built* "
        "column = registered + oracle-verified.\n"
    )
    out.append("## Metric coverage\n")
    out.append("| Primary metric | Tasks |\n| --- | --- |")
    for metric in sorted(metric_counts, key=lambda m: -metric_counts[m]):
        out.append(f"| {metric} | {metric_counts[metric]} |")
    out.append("")

    for folder, title in DOMAIN_ORDER:
        out.append(f"## {title}  (`{folder}/`)\n")
        out.append("| id | Title | Primary metric | Envs | Diff | code_ready | Built |")
        out.append("| --- | --- | --- | --- | --- | --- | --- |")
        for r in rows_by_domain[folder]:
            mark = "★" if r["id"] in built else ""
            cr = "yes" if r["code_ready"] == "true" else "**new app**"
            out.append(
                f"| [{r['id']}]({r['file']}) | {r['title']} | {r['metric']} | "
                f"{r['envs']} | {r['difficulty']} | {cr} | {mark} |"
            )
        out.append("")

    (CATALOG / "INDEX.md").write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"Wrote {CATALOG/'INDEX.md'}: {len(all_rows)} tasks, "
          f"code_ready={code_ready_true}, built={len(built)}")


if __name__ == "__main__":
    main()
