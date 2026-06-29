---
id: wrk_03
title: Insert the three required sections into a report before saving
domain: work_docs_projects
metric_focus: [global_success]
secondary_metrics: [routing_accuracy]
environments: [windows_desktop]
apps: [MockDocumentEditorApp]
difficulty: 2
code_ready: true
new_apps_needed: []
requires_clarification: false
forbidden_routes: false
forbidden_substrings: false
source_of_truth: false
---

# Insert the three required sections into a report before saving

**Request (verbatim, what the agent sees):**
> "Get the Q2 incident report ready to submit — it needs the standard sections before it can be saved."

## User & constraints

`SyntheticUser(name="alex", constraints={"report_standard": "incident_v3"})` — the team's
incident report standard requires three named sections to be present before the document
editor will accept a save. The agent must know (from the doc's own checklist) which three.

## Scenario

Alex has a partially drafted Q2 incident report open on the work laptop. The report
template includes a checklist at the top listing the three mandatory sections —
**Summary**, **Root Cause**, and **Action Items** — but the body currently only has a
Summary. The editor's save is gated on all three section headings being present. This is a
single-app document-completion task: the agent reads the checklist, adds the missing
sections, and saves.

## Environments & apps

| Env | App (`type`) | Seeded state (highlights) |
| --- | --- | --- |
| `windows_desktop` | `MockDocumentEditorApp` | `title="Q2 Incident Report — INC-2026-118"`, `body_field` starts with a `<!-- required: Summary / Root Cause / Action Items -->` checklist comment and only a `## Summary` section filled in, `status="drafting"`, `required_substrings=["## Summary", "## Root Cause", "## Action Items"]` |

## Latent task graph (hidden from agent)

| Subtask id | Description | required_env | required_app | depends_on |
| --- | --- | --- | --- | --- |
| `read_checklist` | Read which three sections the standard requires | `windows_desktop` | `report_doc` | — |
| `add_sections_save` | Add the two missing section headings and save | `windows_desktop` | `report_doc` | `read_checklist` |

## Required handoffs

None — single-environment, single-app task. The carrying metric is `global_success`: the
save only succeeds when every required section heading is present in the body.

## Desired final state

```
windows_desktop.report_doc.status == "saved"
```

## Decoys / ambiguity / source-of-truth

The decoy is partial completeness: the report already *looks* done because it has a filled
Summary and prose, so an agent that skims may save prematurely. A second trap is heading
phrasing — the checklist names them precisely (`## Root Cause`, not `## Cause` or
`## RCA`); an agent that invents a near-synonym heading fails the exact-substring save
gate.

## Metric rationale

An agent that treats "ready to submit" as "click save on the existing draft" leaves out
Root Cause and Action Items; the editor stays in `drafting` because `required_substrings`
is unmet, failing `global_success`. Only adding all three exact headings reaches `saved`.

## Verifier sketch

- **global_success (primary):** `required_substrings=["## Summary", "## Root Cause",
  "## Action Items"]` gates the save; `desired_final_state` checks `status == "saved"`. A
  naive partial draft fails; a complete one passes.
- **routing_accuracy (secondary):** the only valid app is `report_doc` on
  `windows_desktop`; fails only if the agent invents an external route.
- Config fields set: `desired_final_state`.

## Implementation notes

- **`code_ready: true`.** `MockDocumentEditorApp` seeded with the checklist comment and a
  partial body, and `required_substrings` listing all three exact section headings.
  Solvable by `type` to append the missing `## Root Cause` and `## Action Items` headings
  (with any body text), then `click save`. `desired_final_state` references the real
  `status` key. No handoff or second app needed — the difficulty is reading the gate and
  matching headings exactly.
