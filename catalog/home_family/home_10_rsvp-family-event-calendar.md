---
id: home_10
title: RSVP to a family event on the personal calendar at the confirmed time
domain: home_family
metric_focus: [routing_accuracy]
secondary_metrics: [handoff_correctness, global_success]
environments: [windows_desktop]
apps: [MockEmailApp, MockGoogleCalendarApp]
difficulty: 2
code_ready: true
new_apps_needed: []
requires_clarification: false
forbidden_routes: false
forbidden_substrings: false
source_of_truth: false
---

# RSVP to a family event on the personal calendar at the confirmed time

**Request (verbatim, what the agent sees):**
> "Add Grandma's birthday dinner to my calendar from the invite email."

## User & constraints

`SyntheticUser(name="alex", constraints={"personal_calendar": "google"})` — family events
go on Alex's **personal** Google calendar, not a work calendar. The invite email gives the
event title and a confirmed start time that must be added accurately.

## Scenario

A relative emailed an invite for Grandma's birthday dinner with a confirmed date and start
time. Alex wants it on the personal Google calendar. The agent must read the title and time
from the email and add the event to `MockGoogleCalendarApp` without deleting the existing
events already on the calendar.

## Environments & apps

| Env | App (`type`) | Seeded state (highlights) |
| --- | --- | --- |
| `windows_desktop` | `MockEmailApp` (`email`) | thread `birthday_invite`: "Grandma's birthday dinner, Saturday July 11, **6:30 PM** at Rosa's Trattoria. Hope you can make it!" |
| `windows_desktop` | `MockGoogleCalendarApp` (`personal_calendar`) | pre-existing events (e.g. "Dentist", "Soccer practice"); `expected_titles=["Grandma's birthday dinner"]`, `draft_title=""`, `draft_time=""`, `sync_status="pending"` |

## Latent task graph (hidden from agent)

| Subtask id | Description | required_env | required_app | depends_on |
| --- | --- | --- | --- | --- |
| `read_invite` | Open the invite email; read the event title and start time. | `windows_desktop` | `email` | — |
| `add_event` | Add "Grandma's birthday dinner" at 6:30 PM to the personal calendar. | `windows_desktop` | `personal_calendar` | `read_invite` |

## Required handoffs

| artifact_type | from_env | to_env | expected_value |
| --- | --- | --- | --- |
| `event_title` | `windows_desktop` | `windows_desktop` | `Grandma's birthday dinner` |

## Desired final state

```
windows_desktop.personal_calendar.sync_status == "synced"
```

## Decoys / ambiguity / source-of-truth

The pre-existing calendar events are decoys for an over-eager agent: the task is to **add**
the birthday dinner, not overwrite or delete existing entries. `MockGoogleCalendarApp` syncs
only when all `expected_titles` are present, so deleting a pre-existing event or adding a
mistitled one (e.g. "Birthday" or "Dinner with Grandma") leaves `sync_status` unsynced. The
email's restaurant name ("Rosa's Trattoria") and date are distractors around the title and
time.

## Metric rationale

An agent that adds the event to the wrong calendar (e.g. a work calendar) or with the wrong
title completes the gesture but fails routing/global success — the personal Google calendar
is the required surface and the exact title must be present for `sync_status` to flip.

## Verifier sketch

- **routing_accuracy (primary):** the event must be added in `personal_calendar`
  (`MockGoogleCalendarApp`), the required app/env for a personal family event.
- **handoff_correctness (secondary):** the title `Grandma's birthday dinner` carried from
  email into the calendar draft must match.
- **global_success (secondary):** `desired_final_state` checks `personal_calendar.sync_status
  == "synced"`, set only when all `expected_titles` are present and pre-existing events are
  preserved.
- Config fields set: `desired_final_state`, `required_handoffs`.

## Implementation notes

- **`code_ready: true`.** `MockEmailApp` thread with the title + time; `MockGoogleCalendarApp`
  with pre-existing events and `expected_titles=["Grandma's birthday dinner"]`. Solvable:
  open email → `copy_value`/read title and time → `type title`/`time` → `click add_event`.
  Don't delete pre-existing events (per README guidance). All `desired_final_state` paths
  reference real `MockGoogleCalendarApp` keys.
- Distinct from `work_to_personal_calendar` (moving a work event to personal) and `trv_02`
  (itinerary to calendar): this is a family birthday invite from email.
