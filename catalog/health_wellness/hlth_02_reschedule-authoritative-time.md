---
id: hlth_02
title: Reschedule reminder to clinic's authoritative time, not stale calendar
domain: health_wellness
metric_focus: [source_of_truth]
secondary_metrics: [handoff_correctness, global_success]
environments: [android_phone, windows_desktop]
apps: [MockChatApp, MockCalendarApp, MockReminderApp]
difficulty: 3
code_ready: true
new_apps_needed: []
requires_clarification: false
forbidden_routes: false
forbidden_substrings: false
source_of_truth: true
---

# Reschedule reminder to clinic's authoritative time, not stale calendar

**Request (verbatim, what the agent sees):**
> "Set a reminder for my dermatology appointment at the new time the clinic gave me."

## User & constraints

`SyntheticUser(name="alex", constraints={})` — The clinic moved Alex's appointment and
sent the new time over its SMS/chat thread. Alex's calendar still shows the OLD time
(stale). The reminder must reflect the clinic's authoritative chat time, not the calendar.

## Scenario

Alphawave Dermatology texted Alex that the Thursday appointment was moved from 09:30 to
14:15. The chat thread on the phone is the authoritative source; the desktop calendar
entry was never updated and still reads 09:30. The agent must read the new time from the
chat and save a reminder at 14:15, ignoring the stale calendar decoy.

## Environments & apps

| Env | App (`type`) | Seeded state (highlights) |
| --- | --- | --- |
| `android_phone` | `MockChatApp` (clinic SMS) | `channel="Alphawave Dermatology"`, last message: "Your 2026-07-09 visit is rescheduled to 14:15. Reply CONFIRM." `composable=false` |
| `windows_desktop` | `MockCalendarApp` (stale) | `events=[{title:"Dermatology", time:"09:30"}]` (copyable but STALE) |
| `windows_desktop` | `MockReminderApp` (target) | `time_field=""`, `note_field=""`, `expected_time="14:15"`, `status="idle"` |

## Latent task graph (hidden from agent)

| Subtask id | Description | required_env | required_app | depends_on |
| --- | --- | --- | --- | --- |
| `read_new_time` | Read the rescheduled time from the clinic chat. | `android_phone` | `clinic_chat` | — |
| `set_reminder` | Save a reminder at the new time. | `windows_desktop` | `reminder` | `read_new_time` |

## Required handoffs

| artifact_type | from_env | to_env | expected_value |
| --- | --- | --- | --- |
| `time` | `android_phone` | `windows_desktop` | `14:15` |

## Desired final state

```
windows_desktop.reminder.status == "saved"
```

## Decoys / ambiguity / source-of-truth

The desktop `MockCalendarApp` event time `09:30` is copyable and sits right next to the
reminder app — the obvious local value to grab. It is stale. The authoritative new time
`14:15` lives only in the clinic chat on the phone. An agent that copies the calendar's
`09:30` (the convenient, same-device value) saves the wrong reminder. This is the
source-of-truth trap: two times exist, only the chat one is correct.

## Metric rationale

The reminder app only appends and reaches `saved` when `time_field == expected_time
("14:15")`. An agent that trusts the stale calendar `09:30` fails `global_success` and
records a handoff with the wrong value, failing `handoff_correctness`. Choosing the
authoritative chat time is the only path that passes — this is how `source_of_truth` is
encoded (authoritative value is the one `expected_time` requires).

## Verifier sketch

- **source_of_truth (primary):** encoded by making `14:15` (chat) the value
  `expected_time` requires; the stale calendar `09:30` is a decoy. Picking the decoy fails
  `global_success`/`handoff_correctness`. Task flagged `source_of_truth: true`.
- **handoff_correctness (secondary):** `required_handoffs` carries `expected_value="14:15"`
  from `android_phone` to `windows_desktop`.
- **global_success (secondary):** `desired_final_state` checks `reminder.status == "saved"`.
- Config fields set: `desired_final_state`, `required_handoffs`.

## Implementation notes

- **`code_ready: true`.** `MockChatApp` holds the new time in its last message (read +
  copy from phone). `MockCalendarApp` seeded with the stale `09:30` event as a decoy.
  `MockReminderApp` seeded with `expected_time="14:15"`, `status="idle"`. Solvable via
  `copy_value` the chat time, `paste_value` into `time_field`, `type` a note, `click save`.
- Set `initial_focus_env="windows_desktop"`, `initial_focus_app="calendar"` so the stale
  calendar is what the agent sees first, maximizing the decoy's pull.
