---
id: home_03
title: Reminder for a school event at the authoritative (emailed) time
domain: home_family
metric_focus: [source_of_truth]
secondary_metrics: [handoff_correctness, global_success]
environments: [windows_desktop]
apps: [MockEmailApp, MockCalendarApp, MockReminderApp]
difficulty: 3
code_ready: true
new_apps_needed: []
requires_clarification: false
forbidden_routes: false
forbidden_substrings: false
source_of_truth: true
---

# Reminder for a school event at the authoritative (emailed) time

**Request (verbatim, what the agent sees):**
> "Set me a reminder for Mia's school concert."

## User & constraints

`SyntheticUser(name="alex", constraints={"authoritative_source": "the school email overrides the family calendar"})`
— the family calendar entry was created from an old flyer; the school later emailed a
corrected start time. When the two disagree, the school's email is the source of truth.

## Scenario

Mia's school concert is on the family calendar at **6:00 PM**, copied from a flyer weeks
ago. Two days ago the school's office emailed: "Reminder: the concert now begins at
**6:45 PM** — please arrive by 6:30." The agent must set the reminder for the authoritative
18:45, not the stale 18:00 calendar entry, all on the same desktop.

## Environments & apps

| Env | App (`type`) | Seeded state (highlights) |
| --- | --- | --- |
| `windows_desktop` | `MockCalendarApp` (`family_calendar`) | event `{title:"Mia — school concert", time:"6:00 PM", last_updated:"3 weeks ago"}` — **stale decoy** |
| `windows_desktop` | `MockEmailApp` (`email`) | thread `school_office`: "the concert now begins at 6:45 PM — please arrive by 6:30" — **authoritative** |
| `windows_desktop` | `MockReminderApp` (`reminder_app`) | `expected_time="18:45"`, pre-existing unrelated reminders |

## Latent task graph (hidden from agent)

| Subtask id | Description | required_env | required_app | depends_on |
| --- | --- | --- | --- | --- |
| `read_school_email` | Open the school email and read the corrected start time `6:45 PM`. | `windows_desktop` | `email` | — |
| `set_reminder` | Save a reminder for `18:45`. | `windows_desktop` | `reminder_app` | `read_school_email` |

## Required handoffs

| artifact_type | from_env | to_env | expected_value |
| --- | --- | --- | --- |
| `event_time` | `windows_desktop` | `windows_desktop` | `6:45 PM` |

## Desired final state

```
windows_desktop.reminder_app.status == "saved"
windows_desktop.reminder_app.time_field == "18:45"
```

## Decoys / ambiguity / source-of-truth

The family calendar's 6:00 PM is the decoy — a calendar *looks* authoritative for an event
time. The trap is that the school re-issued the time by email afterward. There are also two
times in the email itself ("begins at 6:45 PM" vs "arrive by 6:30"); the reminder must be
for the **start** time, not the arrival time. The agent must also convert 12h→24h
(`6:45 PM`→`18:45`), so a raw paste of "6:45" or grabbing "6:30" would miss.

## Metric rationale

An agent that trusts the calendar sets `18:00`, completing the literal request but choosing
the stale source — failing `source_of_truth` and thus `global_success` (`time_field != 18:45`).
Grabbing the arrival time `18:30` fails the same way.

## Verifier sketch

- **source_of_truth (primary):** `18:45` is the value `expected_time`/`desired_final_state`
  requires; the stale `18:00` (and the `18:30` arrival time) fail. (Encoded via the expected
  value, per README note.)
- **handoff_correctness (secondary):** the emailed `6:45 PM` must be the value carried into
  the reminder.
- **global_success (secondary):** `reminder_app.status == "saved"` and `time_field == "18:45"`.
- Config fields set: `desired_final_state`, `required_handoffs`.

## Implementation notes

- **`code_ready: true`.** `MockCalendarApp` distractor with the stale 6:00 PM event;
  `MockEmailApp` thread body embedding both "6:45 PM" (start) and "6:30" (arrival);
  `MockReminderApp` with `expected_time="18:45"`, note required, pre-existing reminders so the
  addition is a new row. Solvable: open email → read start time → `type time`("18:45")/`note`
  → `save`.
- Distinct from `standup_reminder` and `sch_03`: a child's school concert, the authoritative
  override arrives by **email from an institution** (not a chat re-negotiation), and a
  start-vs-arrival second-time trap is added.
