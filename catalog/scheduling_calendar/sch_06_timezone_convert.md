---
id: sch_06
title: Store the call in local time after a timezone conversion
domain: scheduling_calendar
metric_focus: [source_of_truth]
secondary_metrics: [handoff_correctness, global_success]
environments: [windows_desktop]
apps: [MockEmailApp, MockReminderApp]
difficulty: 3
code_ready: true
new_apps_needed: []
requires_clarification: false
forbidden_routes: false
forbidden_substrings: false
source_of_truth: true
---

# Store the call in local time after a timezone conversion

**Request (verbatim, what the agent sees):**
> "Set a reminder for the investor call — the email has the time."

## User & constraints

`SyntheticUser(name="alex", constraints={"home_timezone": "America/New_York (ET)"})` — Alex is in ET; the email quotes the call time in PT. The reminder must store the correct *local* time.

## Scenario

An email schedules the investor call for **11:00 AM PT** on Thursday. Alex is in Eastern Time, so the local time is **2:00 PM ET → 14:00**. The agent must convert and store `14:00`, not the raw `11:00` from the email. The email even includes a tempting pre-formatted "11:00" that pastes cleanly.

## Environments & apps

| Env | App (`type`) | Seeded state (highlights) |
| --- | --- | --- |
| `windows_desktop` | `MockEmailApp` (`email`) | thread: "Investor call Thu **11:00 AM PT** (8:00 AM if you're on the West Coast)" — **raw decoy** |
| `windows_desktop` | `MockReminderApp` (`reminder_app`) | `expected_time:"14:00"`, note required |

## Latent task graph (hidden from agent)

| Subtask id | Description | required_env | required_app | depends_on |
| --- | --- | --- | --- | --- |
| `read_call_time` | Read `11:00 AM PT` from the email | `windows_desktop` | `email` | — |
| `set_reminder_local` | Convert to ET (`14:00`) and save the reminder | `windows_desktop` | `reminder_app` | `read_call_time` |

## Required handoffs

None across environments — single-desktop. `handoff_correctness` covers the within-app carry, but the load-bearing check is that the *converted* `14:00` (not the raw `11:00`) lands in the reminder.

## Desired final state

```
windows_desktop.reminder_app.status == "saved"
windows_desktop.reminder_app.time_field == "14:00"
```

## Decoys / ambiguity / source-of-truth

The raw "11:00" string in the email is the decoy — it is copyable and pastes cleanly, so a literal handoff stores the wrong local time. A second decoy ("8:00 AM if you're on the West Coast") tempts an agent that over-corrects in the wrong direction. The authoritative value is the ET equivalent of the PT time; only `14:00` is correct.

## Metric rationale

An agent that pastes the email's raw `11:00` (or mis-converts) saves a reminder (literal request done) at the wrong moment — failing `source_of_truth`/`global_success` because `expected_time` is the converted `14:00`. This isolates "did the agent reason about the authoritative *local* representation" rather than copy a surface string.

## Verifier sketch

- **source_of_truth:** `14:00` is the value `expected_time`/`desired_final_state` requires; raw `11:00` and `08:00` both fail.
- **handoff_correctness:** the call time must be carried (converted) into the reminder.
- **global_success:** `reminder_app.status == "saved"` and `time_field == "14:00"`.
- Config fields set: `desired_final_state`.

## Implementation notes

- **`code_ready: true`.** `email` = `MockEmailApp`, one thread containing the PT time and both decoys. `reminder_app` = `MockReminderApp`, `expected_time:"14:00"`, note required. Solvable with read email → `type time`("14:00")/`note` → `save`. The conversion is the agent's reasoning step; no new app field is needed because the reminder only checks the final 24h string.
