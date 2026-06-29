---
id: hlth_08
title: Add telehealth visit to the personal calendar at the confirmed time
domain: health_wellness
metric_focus: [routing_accuracy]
secondary_metrics: [handoff_correctness, global_success]
environments: [windows_desktop]
apps: [MockEmailApp, MockGoogleCalendarApp]
difficulty: 3
code_ready: true
new_apps_needed: []
requires_clarification: false
forbidden_routes: false
forbidden_substrings: false
source_of_truth: false
---

# Add telehealth visit to the personal calendar at the confirmed time

**Request (verbatim, what the agent sees):**
> "Put my telehealth visit on my calendar at the time in the confirmation email."

## User & constraints

`SyntheticUser(name="alex", constraints={"personal_calendar": "MockGoogleCalendarApp"})`
— Telehealth visits are personal, so the event belongs on Alex's personal Google
Calendar, not a work calendar. The confirmed time and visit link are in the confirmation
email.

## Scenario

NorthStar Telehealth emailed a visit confirmation: "Video visit confirmed for 2026-07-10
at 11:00. Join link: https://nsth.example/v/8821." Alex wants the visit added to the
personal calendar at the confirmed time. The agent must read the confirmed time/title from
the email and create the event on the personal (read-write) calendar at that time.

## Environments & apps

| Env | App (`type`) | Seeded state (highlights) |
| --- | --- | --- |
| `windows_desktop` | `MockEmailApp` (inbox) | thread `t_telehealth`: sender "NorthStar Telehealth", body "Video visit confirmed for 2026-07-10 at 11:00. Join link: https://nsth.example/v/8821" |
| `windows_desktop` | `MockGoogleCalendarApp` (personal, target) | `events=[...existing...]`, `draft_title=""`, `draft_time=""`, `expected_titles=["Telehealth visit"]`, `sync_status="unsynced"` |

## Latent task graph (hidden from agent)

| Subtask id | Description | required_env | required_app | depends_on |
| --- | --- | --- | --- | --- |
| `read_confirm` | Read the confirmed time + visit detail from the email. | `windows_desktop` | `email` | — |
| `add_event` | Add the visit to the personal calendar at that time. | `windows_desktop` | `personal_calendar` | `read_confirm` |

## Required handoffs

| artifact_type | from_env | to_env | expected_value |
| --- | --- | --- | --- |
| `time` | `windows_desktop` | `windows_desktop` | `11:00` |

## Desired final state

```
windows_desktop.personal_calendar.sync_status == "synced"
```

## Decoys / ambiguity / source-of-truth

The body contains both the confirmed `11:00` and a "you originally requested 09:30" line,
plus the join URL (URL-shaped, not a time). The trap is grabbing the originally-requested
`09:30` or the URL instead of the confirmed `11:00`, and routing the event to the wrong
calendar. The pre-existing calendar events must be preserved, not overwritten.

## Metric rationale

Routing is the crux: the personal calendar is the correct surface for a telehealth visit.
The calendar reaches `synced` only when `expected_titles` (["Telehealth visit"]) are
present at the confirmed time. An agent that adds the event to the wrong calendar fails
`routing_accuracy`; one that uses `09:30` or deletes existing events fails
`handoff_correctness`/`global_success`.

## Verifier sketch

- **routing_accuracy (primary):** subtask `add_event` pins the target to the personal
  `MockGoogleCalendarApp`; adding elsewhere fails.
- **handoff_correctness (secondary):** `required_handoffs` carries `expected_value="11:00"`
  within `windows_desktop` (confirmed time, not the original request).
- **global_success (secondary):** `desired_final_state` checks `personal_calendar.sync_status
  == "synced"`, set when `expected_titles` are present (without deleting pre-existing events).
- Config fields set: `desired_final_state`, `required_handoffs`.

## Implementation notes

- **`code_ready: true`.** `MockEmailApp` thread holds the confirmed time. `MockGoogleCalendarApp`
  seeded with pre-existing events plus `expected_titles=["Telehealth visit"]`,
  `sync_status="unsynced"`. Solvable via reading the email time, `copy_value`/`type` the
  time into `draft_time`, `type` "Telehealth visit" into `draft_title`, `click add_event`.
- Note: `sync_status → synced` requires all `expected_titles` present; keep existing events
  intact. Set `initial_focus_env="windows_desktop"`, `initial_focus_app="email"`.
