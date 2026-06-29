---
id: sch_02
title: Set out-of-office for the approved leave dates
domain: scheduling_calendar
metric_focus: [handoff_correctness]
secondary_metrics: [global_success]
environments: [windows_desktop]
apps: [MockEmailApp]
difficulty: 2
code_ready: true
new_apps_needed: []
requires_clarification: false
forbidden_routes: false
forbidden_substrings: false
source_of_truth: false
---

# Set out-of-office for the approved leave dates

**Request (verbatim, what the agent sees):**
> "HR approved my leave — turn on my email out-of-office for those exact dates."

## User & constraints

`SyntheticUser(name="alex", constraints={})` — the approved date range lives in the approval email body; the OOO fields live in the same email app.

## Scenario

Alex's manager replied "Approved" to a vacation request. The approval email states the leave runs **Mon Aug 17 – Fri Aug 21, 2026**. The agent must read the start and end dates out of that thread and turn on out-of-office for exactly that range. (Distinct from the implemented `ooo_setup`, which reads dates from a *calendar*; here the dates come from an email thread and there is a tempting wrong range nearby.)

## Environments & apps

| Env | App (`type`) | Seeded state (highlights) |
| --- | --- | --- |
| `windows_desktop` | `MockEmailApp` (`email`) | approval thread with `2026-08-17`..`2026-08-21`; `ooo_supported: true`, `ooo_enabled: false` |

## Latent task graph (hidden from agent)

| Subtask id | Description | required_env | required_app | depends_on |
| --- | --- | --- | --- | --- |
| `read_approval` | Open the HR approval thread; read approved start/end dates | `windows_desktop` | `email` | — |
| `enable_ooo` | Fill `ooo_start`/`ooo_end` and toggle OOO on | `windows_desktop` | `email` | `read_approval` |

## Required handoffs

None — single-environment, single-app task. The crux value (the date range) moves within one app; the metric is carried by `handoff_correctness` on the within-env carry of each date and by `global_success` on the OOO fields.

## Desired final state

```
windows_desktop.email.ooo_enabled == true
windows_desktop.email.ooo_start_field == "2026-08-17"
windows_desktop.email.ooo_end_field == "2026-08-21"
```

## Decoys / ambiguity / source-of-truth

The approval thread quotes Alex's *original request* lower in the body, which proposed a longer range (**Aug 17 – Aug 24**) before HR trimmed it. The approved line is "Approved for Aug 17 through Aug 21." The trap: an agent that grabs the first date pair it sees (the requested range) enters `2026-08-24` as the end and over-blocks the calendar. Only the "Approved for …" sentence is authoritative.

## Metric rationale

An agent that copies the requested range instead of the approved range turns OOO on (literal request done) but with the wrong `ooo_end_field`, failing `global_success`. Reading the right sentence is the within-app `handoff_correctness` test.

## Verifier sketch

- **handoff_correctness:** the approved `2026-08-17`/`2026-08-21` strings must be the values carried into the OOO fields.
- **global_success:** `desired_final_state` checks `ooo_enabled`, `ooo_start_field`, `ooo_end_field`.
- Config fields set: `desired_final_state`.

## Implementation notes

- **`code_ready: true`.** `email` = `MockEmailApp`, `ooo_supported: true`, `ooo_enabled: false`, empty `ooo_*` fields. Seed one thread whose body has both the approved range and the (decoy) requested range. Solvable with `thread:<id>` tap → `type ooo_start`/`ooo_end`/`ooo_message` → `ooo_toggle`. Differs from `ooo_setup` by source app (email vs calendar) and by the embedded over-block decoy.
