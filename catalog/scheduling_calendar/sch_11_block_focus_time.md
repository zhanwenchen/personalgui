---
id: sch_11
title: Block focus time on the work calendar after a conflict check
domain: scheduling_calendar
metric_focus: [routing_accuracy]
secondary_metrics: [global_success]
environments: [work_laptop]
apps: [MockOutlookApp, MockGoogleCalendarApp]
difficulty: 3
code_ready: true
new_apps_needed: []
requires_clarification: false
forbidden_routes: false
forbidden_substrings: false
source_of_truth: false
---

# Block focus time on the work calendar after a conflict check

**Request (verbatim, what the agent sees):**
> "If I'm free Wednesday 2–4, block it as focus time on my work calendar."

## User & constraints

`SyntheticUser(name="alex", constraints={"work_account": "alex@work.example"})` — focus time is a *work* commitment and belongs on the work calendar (Outlook), not the personal one. The block is conditional on Wednesday 2–4 being free on the **work** calendar.

## Scenario

Alex wants a "Focus time" block Wednesday 2–4 PM on the work calendar, but only if that window is actually free at work. The work Outlook calendar has Wednesday meetings at 10:00 and 4:30 — the 2–4 window is clear. A *personal* Google Calendar event sits at Wednesday 2:30 ("Dentist", later moved) — but personal events do not block work focus time. The agent signs in, confirms the work window is free, and adds the block on the work calendar.

## Environments & apps

| Env | App (`type`) | Seeded state (highlights) |
| --- | --- | --- |
| `work_laptop` | `MockOutlookApp` (`outlook`) | sign-in required; Wed events `[{title:"Standup", time:"10:00 AM"}, {title:"1:1", time:"4:30 PM"}]` — **2–4 PM is free** |
| `work_laptop` | `MockGoogleCalendarApp` (`google_calendar`) | personal `[{title:"Dentist", time:"14:30"}]` — **non-blocking decoy**; editable, but NOT the target |

## Latent task graph (hidden from agent)

| Subtask id | Description | required_env | required_app | depends_on |
| --- | --- | --- | --- | --- |
| `sign_in_outlook` | Sign in to the work calendar | `work_laptop` | `outlook` | — |
| `check_conflict` | Confirm Wednesday 2–4 PM is free on the work calendar | `work_laptop` | `outlook` | `sign_in_outlook` |
| `block_focus` | Add "Focus time" Wed 2–4 PM on the work calendar | `work_laptop` | `outlook` | `check_conflict` |

## Required handoffs

None — single-environment task; routing (which calendar) and the conditional check are the crux. Carried by `routing_accuracy` and `global_success`.

## Desired final state

```
work_laptop.outlook.events contains {title:"Focus time", time:"2:00 PM"}
```

(Encoded via the editable-calendar success field; see implementation notes — the runnable target is whichever app models the writable work calendar.)

## Decoys / ambiguity / source-of-truth

Two traps. (1) The personal Google "Dentist" at 2:30 looks like a conflict but does not block *work* focus time — an agent that treats it as a conflict wrongly refuses to add the block. (2) The personal calendar is editable and tempting, but focus time is a work commitment, so adding it there would be the wrong route. The work window is genuinely free, so the correct outcome is: add the block on the work calendar.

## Metric rationale

An agent that adds the block to the personal Google Calendar (wrong device/app) or that aborts because of the personal "Dentist" decoy fails `routing_accuracy` (subtask routed to the wrong calendar / not done) and `global_success`. Correct play routes the write to the work calendar after a work-only conflict check.

## Verifier sketch

- **routing_accuracy:** the `block_focus` subtask is pinned to `work_laptop/outlook`; writing to the personal calendar fails it.
- **global_success:** the "Focus time" 2–4 block must exist on the work calendar.
- Config fields set: `desired_final_state`.

## Implementation notes

- **`code_ready: true`** with one modeling choice: `MockOutlookApp` is the read/sign-in work calendar but is not described as writable. The runnable encoding makes the **work** calendar the editable target by representing the writable work calendar as a `MockGoogleCalendarApp` instance on the `work_laptop` (work account) with `expected_titles:["Focus time"]`, while a *second* `MockGoogleCalendarApp` (personal account) holds the "Dentist" decoy and is the forbidden write target. Outlook stays the read-only conflict source post-sign-in. Then: `sign_in` Outlook → read Wed events (confirm 2–4 free) → `type title`("Focus time")/`time`("14:00") → `add_event` on the work-account calendar; `sync_status → synced`. If `MockOutlookApp` later gains event-add, the work Outlook app can be the direct target and the second calendar dropped.
