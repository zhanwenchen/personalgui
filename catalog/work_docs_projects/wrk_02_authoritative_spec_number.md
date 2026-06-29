---
id: wrk_02
title: Update doc with the authoritative spec number when board and note disagree
domain: work_docs_projects
metric_focus: [source_of_truth]
secondary_metrics: [global_success, handoff_correctness]
environments: [windows_desktop]
apps: [MockProfileApp, MockDocumentEditorApp, MockChatApp]
difficulty: 3
code_ready: true
new_apps_needed: []
requires_clarification: false
forbidden_routes: false
forbidden_substrings: false
source_of_truth: true
---

# Update doc with the authoritative spec number when board and note disagree

**Request (verbatim, what the agent sees):**
> "Update the spec doc so the throughput target matches what the project board says it is now, and save."

## User & constraints

`SyntheticUser(name="alex", constraints={"authoritative_source": "project_board"})` —
the project board is the system of record for the locked spec numbers; an older inline
note in the doc reflects a superseded value. When the two disagree, the board wins.

## Scenario

The "Atlas ingestion" spec doc still carries an older throughput target that Alex jotted
weeks ago. The project board (a read-only directory record) shows the current, locked
target after a re-scoping. Alex wants the doc updated to the board's number. Both the board
record and the editable doc are on the work laptop, so this is a same-desktop
source-of-truth resolution feeding a doc save.

## Environments & apps

| Env | App (`type`) | Seeded state (highlights) |
| --- | --- | --- |
| `windows_desktop` | `MockProfileApp` | `name="Atlas Ingestion — Project Board (Locked Spec)"`, `fields={"throughput_target":"4,200 events/sec","status":"locked","scoped_on":"2026-06-22"}`, `last_updated="2026-06-22"` (authoritative) |
| `windows_desktop` | `MockDocumentEditorApp` | `title="Atlas Ingestion — Spec"`, `body_field` reads `"Throughput target: 3,000 events/sec (initial estimate)"`, `status="drafting"`, `required_substrings=["4,200 events/sec"]` (stale `3,000` must be replaced) |
| `windows_desktop` | `MockChatApp` | `channel="#atlas-eng"`, `composable=false`; an old message `"let's plan around ~3k/sec for now"` reinforcing the stale value as a second decoy |

## Latent task graph (hidden from agent)

| Subtask id | Description | required_env | required_app | depends_on |
| --- | --- | --- | --- | --- |
| `read_board` | Read the locked throughput target from the project board | `windows_desktop` | `project_board` | — |
| `update_spec` | Replace the stale target in the doc and save | `windows_desktop` | `spec_doc` | `read_board` |

## Required handoffs

| artifact_type | from_env | to_env | expected_value |
| --- | --- | --- | --- |
| `spec_number` | `windows_desktop` | `windows_desktop` | `4,200 events/sec` |

## Desired final state

```
windows_desktop.spec_doc.status == "saved"
```

## Decoys / ambiguity / source-of-truth

The same fact — "the throughput target" — appears in three places: the doc's own
inline `3,000 events/sec` estimate, an `#atlas-eng` chat saying `~3k/sec`, and the board's
locked `4,200 events/sec`. The doc and chat agree with each other, which is the trap: two
mutually consistent stale sources outvote the single authoritative one. An agent that
trusts the doc's own text (or the chat) saves `3,000` and fails the `required_substrings`
check, which only accepts `4,200 events/sec`.

## Metric rationale

The number is duplicated with two stale copies and one authoritative copy. An agent that
takes the convenient in-doc value, or is swayed by the chat agreeing with it, writes the
wrong target and the save never reaches `saved`, failing `source_of_truth` (encoded via the
required value) and `global_success`.

## Verifier sketch

- **source_of_truth (primary):** the board's `4,200 events/sec` is what `required_substrings`
  / `desired_final_state` require; the doc's and chat's `3,000`/`3k` are decoys that fail the
  save. (Encoded via the expected value, per README note.)
- **handoff_correctness (secondary):** within-env handoff carries `4,200 events/sec` from
  the board into the doc.
- **global_success (secondary):** `spec_doc.status == "saved"`.
- Config fields set: `desired_final_state`, `required_handoffs`.

## Implementation notes

- **`code_ready: true`.** `MockProfileApp` is the README's designated authoritative record
  and holds the locked number in `fields`; `MockDocumentEditorApp` holds the stale inline
  estimate and enforces `required_substrings=["4,200 events/sec"]`; `MockChatApp`
  (`composable:false`) seeds the reinforcing-decoy message. Solvable by reading the board,
  copy/paste the locked number into the doc body (replacing the estimate), then `save`.
