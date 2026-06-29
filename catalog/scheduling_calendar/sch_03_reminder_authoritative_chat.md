---
id: sch_03
title: Reminder at the chat-confirmed time, not the stale calendar time
domain: scheduling_calendar
metric_focus: [source_of_truth]
secondary_metrics: [handoff_correctness, global_success]
environments: [windows_desktop, android_phone]
apps: [MockReminderApp, MockChatApp, MockCalendarApp]
difficulty: 3
code_ready: true
new_apps_needed: []
requires_clarification: false
forbidden_routes: false
forbidden_substrings: false
source_of_truth: true
---

# Reminder at the chat-confirmed time, not the stale calendar time

**Request (verbatim, what the agent sees):**
> "Set me a reminder for the photographer call this afternoon."

## User & constraints

`SyntheticUser(name="alex", constraints={"trust_order": "the most recent message in the thread overrides the calendar entry"})` — the calendar entry is stale; a later chat message moved the call.

## Scenario

Alex's personal calendar lists a "Photographer call" at **2:00 PM** today. But in the chat thread, the photographer wrote 40 minutes ago: "Sorry, can we push to **3:30 PM**?" and Alex replied "works." The agent must set the reminder for the authoritative 15:30, not the stale 14:00. (Distinct from the implemented `standup_reminder`: different scenario, a personal photographer call, the new time arrives via a two-message back-and-forth, and the calendar entry carries an explicit recent-but-pre-message timestamp.)

## Environments & apps

| Env | App (`type`) | Seeded state (highlights) |
| --- | --- | --- |
| `android_phone` | `MockCalendarApp` (`phone_calendar`) | `{title:"Photographer call", time:"2:00 PM", last_updated:"this morning"}` — **stale decoy** |
| `windows_desktop` | `MockChatApp` (`chat`) | photographer: "can we push to 3:30 PM?" (recent); you: "works" — **authoritative** |
| `windows_desktop` | `MockReminderApp` (`reminder_app`) | `expected_time:"15:30"`, pre-existing unrelated reminders |

## Latent task graph (hidden from agent)

| Subtask id | Description | required_env | required_app | depends_on |
| --- | --- | --- | --- | --- |
| `read_chat_time` | Read the latest agreed time `3:30 PM` from the chat thread | `windows_desktop` | `chat` | — |
| `set_reminder` | Save a reminder for `15:30` | `windows_desktop` | `reminder_app` | `read_chat_time` |

## Required handoffs

None across environments — authoritative value lives on the desktop chat; carried within-env into the reminder. `handoff_correctness` covers the within-desktop carry of `3:30 PM`→`15:30`.

## Desired final state

```
windows_desktop.reminder_app.status == "saved"
windows_desktop.reminder_app.time_field == "15:30"
```

## Decoys / ambiguity / source-of-truth

The phone calendar's 2:00 PM is the decoy — it's a calendar, so it *looks* authoritative, and its `last_updated: this morning` is recent enough to seem trustworthy. The trap is that the chat re-negotiation happened *after* that. The agent must also do a 12h→24h conversion (`3:30 PM`→`15:30`) so a raw paste of "3:30" would also miss.

## Metric rationale

An agent that trusts the calendar sets `14:00`, completing the literal request but choosing the stale source — failing `source_of_truth` and thus `global_success` (time_field != `15:30`).

## Verifier sketch

- **source_of_truth:** `15:30` is the value `expected_time`/`desired_final_state` requires; the stale `14:00` fails.
- **handoff_correctness:** the agreed `3:30 PM` must be the value carried into the reminder.
- **global_success:** `reminder_app.status == "saved"` and `time_field == "15:30"`.
- Config fields set: `desired_final_state`.

## Implementation notes

- **`code_ready: true`.** `chat` = `MockChatApp` (composable false; just read) with the two-message exchange. `reminder_app` = `MockReminderApp`, `expected_time:"15:30"`, note required, pre-existing reminders so the addition is a new row. `phone_calendar` = `MockCalendarApp` distractor. Solvable with read chat → `type time`("15:30")/`note` → `save`.
