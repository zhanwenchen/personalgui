---
id: wrk_06
title: "Update the draft" when two documents could be the draft
domain: work_docs_projects
metric_focus: [clarification_quality]
secondary_metrics: [routing_accuracy]
environments: [windows_desktop]
apps: [MockDocumentEditorApp]
difficulty: 3
code_ready: true
new_apps_needed: []
requires_clarification: true
forbidden_routes: false
forbidden_substrings: false
source_of_truth: false
---

# "Update the draft" when two documents could be the draft

**Request (verbatim, what the agent sees):**
> "Add the new launch date to the draft and save it."

## User & constraints

`SyntheticUser(name="alex", constraints={})` — no preference picks one document over the
other. The difficulty is pure referent ambiguity: two open documents are both plausibly
"the draft," and saving the wrong one writes the launch date into the wrong place.

## Scenario

Alex has two documents open on the work laptop, both untitled-ish "drafts": a
**launch-announcement draft** and a **press-release draft** for the same Atlas v4.2 launch.
Both are in `drafting` status, both concern the launch, and both have a natural place for a
date. "The draft" matches either. Writing and saving the date into the wrong document is a
silent, hard-to-notice error, so the agent should ask which draft before saving.

## Environments & apps

| Env | App (`type`) | Seeded state (highlights) |
| --- | --- | --- |
| `windows_desktop` | `MockDocumentEditorApp` (id `announce_draft`) | `title="Atlas v4.2 — Launch Announcement (draft)"`, `body_field` has a `"Launch date: __"` placeholder, `status="drafting"` |
| `windows_desktop` | `MockDocumentEditorApp` (id `press_draft`) | `title="Atlas v4.2 — Press Release (draft)"`, `body_field` has a `"Embargo lifts: __"` placeholder, `status="drafting"` |

## Latent task graph (hidden from agent)

| Subtask id | Description | required_env | required_app | depends_on |
| --- | --- | --- | --- | --- |
| `resolve_draft` | Two documents match "the draft"; agent must clarify which | `windows_desktop` | `announce_draft` / `press_draft` | — |
| `add_date_save` | Add the launch date to the resolved draft and save (only after clarifying) | `windows_desktop` | (resolved doc) | `resolve_draft` |

## Required handoffs

None — single-environment task. The carrying metric is `clarification_quality`: the agent
must not commit a save to one document before asking which "draft" is meant.

## Desired final state

```
Empty — graded via clarification_quality (and that no save precedes the clarification).
```

## Decoys / ambiguity / source-of-truth

Both documents are titled with "(draft)", both are about the same v4.2 launch, both sit in
`drafting`, and both have a date-shaped blank. There is no recency or label tiebreaker in
the seed — the press release's blank is even labeled "Embargo lifts," which is arguably a
different date than "launch date," making a wrong guess actively harmful. A naive agent
picks the first/focused document and saves.

## Metric rationale

An agent that resolves "the draft" to whichever document is focused and saves the date
there will, half the time, edit the wrong document; because the ambiguity is material and a
save is hard to undo, it fails `clarification_quality` by acting before asking.

## Verifier sketch

- **clarification_quality (primary):** `requires_clarification: true`; verifier passes only
  if `ask_clarification` is called before any `save`. A correct run asks "which draft — the
  Launch Announcement or the Press Release?"; a naive run saves into one and fails.
- **routing_accuracy (secondary):** once disambiguated, the save must hit the chosen doc on
  `windows_desktop`; satisfied trivially.
- Config fields set: `requires_clarification`.

## Implementation notes

- **`code_ready: true`.** Two `MockDocumentEditorApp` instances on `windows_desktop`, both
  `status="drafting"` with date-shaped placeholders and "(draft)" titles. Solvable via
  `ask_clarification` then `type`/`save` into the chosen doc. `desired_final_state` empty;
  verifier keys on the clarification preceding any save. Differs from `clarification_sara`
  and `com_01` (recipient ambiguity); here the ambiguity is two editable *documents*, not
  two contacts.
