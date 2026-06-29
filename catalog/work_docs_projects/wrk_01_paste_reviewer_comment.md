---
id: wrk_01
title: Paste reviewer comment from chat into the doc and save
domain: work_docs_projects
metric_focus: [handoff_correctness]
secondary_metrics: [global_success, routing_accuracy]
environments: [windows_desktop]
apps: [MockChatApp, MockDocumentEditorApp]
difficulty: 2
code_ready: true
new_apps_needed: []
requires_clarification: false
forbidden_routes: false
forbidden_substrings: false
source_of_truth: false
---

# Paste reviewer comment from chat into the doc and save

**Request (verbatim, what the agent sees):**
> "Maya left a review note in the doc-review chat — paste her exact comment into the design doc under 'Open questions' and save it."

## User & constraints

`SyntheticUser(name="alex", constraints={"work_account": "alex@northwind.example"})` —
the reviewer's wording is authoritative and must be carried verbatim; paraphrasing the
comment changes its meaning, so the literal string has to cross from chat into the doc.

## Scenario

Alex is finalizing the "Atlas onboarding" design doc on the work laptop. The reviewer,
Maya, posted a specific blocking comment in the `#atlas-doc-review` chat thread instead of
in the doc itself. Alex wants that exact comment captured in the document's "Open
questions" section before the doc is saved and circulated. Both apps are on the same
desktop, so this is a within-desktop chat -> doc handoff.

## Environments & apps

| Env | App (`type`) | Seeded state (highlights) |
| --- | --- | --- |
| `windows_desktop` | `MockChatApp` | `channel="#atlas-doc-review"`, `composable=false`; messages include Maya's note: `"Confirm the retry budget is 3 attempts, not 5 — the SLA math assumes 3."` plus two off-topic messages (lunch, a thumbs-up emoji) as distractors |
| `windows_desktop` | `MockDocumentEditorApp` | `title="Atlas Onboarding — Design Doc"`, `body_field` has an `## Open questions` heading with an empty bullet, `status="drafting"`, `required_substrings=["Confirm the retry budget is 3 attempts, not 5 — the SLA math assumes 3."]` |

## Latent task graph (hidden from agent)

| Subtask id | Description | required_env | required_app | depends_on |
| --- | --- | --- | --- | --- |
| `read_comment` | Locate Maya's review comment in the chat thread | `windows_desktop` | `doc_chat` | — |
| `paste_and_save` | Paste the comment verbatim into the doc and save | `windows_desktop` | `doc_editor` | `read_comment` |

## Required handoffs

| artifact_type | from_env | to_env | expected_value |
| --- | --- | --- | --- |
| `reviewer_comment` | `windows_desktop` | `windows_desktop` | `Confirm the retry budget is 3 attempts, not 5 — the SLA math assumes 3.` |

## Desired final state

```
windows_desktop.doc_editor.status == "saved"
```

## Decoys / ambiguity / source-of-truth

The chat thread holds three messages; two are off-topic noise ("anyone want coffee?", a
"👍"). A naive agent that grabs the most recent or shortest message pastes the wrong text
and the save fails the `required_substrings` check. The trap is that the genuine review
comment is *not* the last message in the thread, so reading order alone misleads.

## Metric rationale

An agent that summarizes or paraphrases Maya's comment instead of carrying it verbatim
produces a body that misses the exact `required_substrings` value; the save stays in
`drafting` and both `handoff_correctness` and `global_success` fail. Only the exact string
saved.

## Verifier sketch

- **handoff_correctness (primary):** `required_handoffs` carries the exact comment from
  `doc_chat` to `doc_editor` (same env). Pass only if the verbatim string was copied and
  pasted.
- **global_success (secondary):** `doc_editor.status == "saved"`, which the editor only
  reaches when `required_substrings` is present.
- **routing_accuracy (secondary):** both subtasks must run on `windows_desktop`; trivially
  satisfied, fails only if the agent invents another channel.
- Config fields set: `desired_final_state`, `required_handoffs`.

## Implementation notes

- **`code_ready: true`.** `MockChatApp` seeded `composable:false` (read-only thread) with
  the three messages; `MockDocumentEditorApp` seeded with the `## Open questions` skeleton
  body and `required_substrings=[Maya's exact comment]`. Solvable with `copy_value` on the
  chat message, `paste_value` into the doc body, then `click save`. `desired_final_state`
  references the real `status` key.
