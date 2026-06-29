---
id: sch_01
title: Fix dentist appointment to the clinic's confirmed date
domain: scheduling_calendar
metric_focus: [source_of_truth]
secondary_metrics: [handoff_correctness, global_success]
environments: [android_phone, windows_desktop]
apps: [MockCalendarApp, MockEmailApp, MockGoogleCalendarApp]
difficulty: 4
code_ready: true
new_apps_needed: []
requires_clarification: false
forbidden_routes: false
forbidden_substrings: false
source_of_truth: true
---

# Fix dentist appointment to the clinic's confirmed date

**Request (verbatim, what the agent sees):**
> "My dentist cleaning got moved — make sure my calendar has the right date."

## User & constraints

`SyntheticUser(name="alex", constraints={"trust_order": "clinic confirmation email is authoritative over the phone calendar entry"})` — the phone calendar holds a stale personal entry; the clinic's email is the system of record for the appointment date.

## Scenario

Alex's phone calendar still shows the dentist cleaning on **Tue, July 14, 2026** — the date from the original booking. The clinic later emailed a rescheduling confirmation putting the cleaning on **Wed, July 15, 2026**. The agent must read the authoritative email date and correct the editable Google Calendar, not trust the stale phone entry.

## Environments & apps

| Env | App (`type`) | Seeded state (highlights) |
| --- | --- | --- |
| `android_phone` | `MockCalendarApp` (`phone_calendar`) | event `{title:"Dentist cleaning", time:"9:00 AM", date:"2026-07-14", last_updated:"3 weeks ago"}` — **stale decoy** |
| `windows_desktop` | `MockEmailApp` (`email`) | thread from clinic confirming **2026-07-15**, `ts` recent |
| `windows_desktop` | `MockGoogleCalendarApp` (`google_calendar`) | pre-existing wrong entry `{title:"Dentist cleaning", time:"09:00"}`; editable target |

## Latent task graph (hidden from agent)

| Subtask id | Description | required_env | required_app | depends_on |
| --- | --- | --- | --- | --- |
| `read_email_date` | Open the clinic thread; read the confirmed reschedule date `2026-07-15` | `windows_desktop` | `email` | — |
| `fix_calendar` | Add/correct the Google Calendar entry to the confirmed date | `windows_desktop` | `google_calendar` | `read_email_date` |

## Required handoffs

| artifact_type | from_env | to_env | expected_value |
| --- | --- | --- | --- |
| `date` | `windows_desktop` | `windows_desktop` | `2026-07-15` |

(Within-env handoff: copy the date out of Email, paste into the Google Calendar draft on the same desktop.)

## Desired final state

```
windows_desktop.google_calendar.sync_status == "synced"
```

(`expected_titles` set so the corrected "Dentist cleaning · 2026-07-15" entry must be present.)

## Decoys / ambiguity / source-of-truth

The phone calendar's `2026-07-14` entry is the stale decoy. It is the most prominent, "calendar-shaped" source and is exactly what a naive agent copies. The trap: the phone entry looks authoritative because it lives in a calendar, but its `last_updated: 3 weeks ago` pre-dates the clinic's reschedule email. Only the email carries the current date.

## Metric rationale

An agent that reads the phone calendar and mirrors `2026-07-14` into Google Calendar completes the literal request ("calendar has the right date") but enters the stale value — failing `source_of_truth` (wrong authoritative source) and therefore `handoff_correctness`/`global_success` because `expected_titles` requires the 07-15 entry.

## Verifier sketch

- **source_of_truth:** encoded by making `2026-07-15` the value required by `expected_titles` / `desired_final_state`; copying the stale `2026-07-14` leaves `sync_status` != `synced`.
- **handoff_correctness:** `required_handoffs` requires the date `2026-07-15` to cross from Email into the calendar draft.
- **global_success:** `google_calendar.sync_status == "synced"`.
- Config fields set: `desired_final_state`, `required_handoffs`.

## Implementation notes

- **`code_ready: true`.** `phone_calendar` = `MockCalendarApp` with the stale event (`time` copyable, used as the distractor source). `email` = `MockEmailApp` with one thread whose body contains `2026-07-15` (copyable on open). `google_calendar` = `MockGoogleCalendarApp` with the pre-existing wrong entry, `draft_title`/`draft_time` empty, and `expected_titles=["Dentist cleaning · 2026-07-15"]`. Solvable with `thread:<id>` tap → `copy_value`(date) → `paste_value`/`type` title+time → `add_event`. The editable target is Google Calendar because `MockCalendarApp` is view-only.
