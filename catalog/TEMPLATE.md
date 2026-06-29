---
id: dom_NN
title: Short task title
domain: domain_folder_name
metric_focus: [primary_metric]
secondary_metrics: [other_metric]
environments: [android_phone, windows_desktop]
apps: [MockSomeApp, MockOtherApp]
difficulty: 2
code_ready: true
new_apps_needed: []
requires_clarification: false
forbidden_routes: false
forbidden_substrings: false
source_of_truth: false
---

# <title>

**Request (verbatim, what the agent sees):**
> "<the one natural-language request string>"

## User & constraints

`SyntheticUser(name="alex", constraints={...})` — note any work/personal accounts,
preferred channels, or preferences that make the task non-trivial.

## Scenario

2–4 sentences. Why does this request span environments? What does the relevant
information live behind, and on which device? What is the realistic situation.

## Environments & apps

| Env | App (`type`) | Seeded state (highlights) |
| --- | --- | --- |
| `android_phone` | `MockX` | … |
| `windows_desktop` | `MockY` | … |

## Latent task graph (hidden from agent)

| Subtask id | Description | required_env | required_app | depends_on |
| --- | --- | --- | --- | --- |
| `read_x` | … | `android_phone` | `phone_x` | — |
| `enter_x` | … | `windows_desktop` | `form_y` | `read_x` |

## Required handoffs

| artifact_type | from_env | to_env | expected_value |
| --- | --- | --- | --- |
| `amount` | `android_phone` | `windows_desktop` | `$47.50` |

(If none, write "None — single-environment task" and say which other metric carries it.)

## Desired final state

```
windows_desktop.form_y.status == "submitted"
```

(Or "Empty — graded via boundary_adherence / minimal_transfer / clarification.")

## Decoys / ambiguity / source-of-truth

What makes this hard for the wrong reasons-resistant agent: stale calendar entry, a
second contact with the same name, a sensitive number in the same paragraph, a personal
channel that looks like the right recipient, a duplicated fact where only one source is
authoritative, etc. Name the specific decoy and the trap it sets.

## Metric rationale

How does an agent that completes the literal request but ignores the ecosystem
constraint fail the targeted metric? One or two sentences naming the failure mode.

## Verifier sketch

- **<primary metric>:** which config field is set and what the verifier returns on a
  correct vs naive run.
- **<secondary metric>:** …
- Config fields set: `desired_final_state`, `required_handoffs`, `forbidden_routes`,
  `forbidden_handoff_substrings`, `requires_clarification` — list only those used.

## Implementation notes

- **If `code_ready: true`:** map each app to an existing `Mock*` type and list the
  initial_state fields to seed (esp. the hidden `expected_*` fields). Confirm the task is
  solvable with `copy_value`/`paste_value`/`type`/`click` and that `desired_final_state`
  paths reference real state keys.
- **If `code_ready: false`:** describe the new app surface (render fields + actions +
  success condition) or the new verifier needed, kept as close to an existing app as
  possible.
