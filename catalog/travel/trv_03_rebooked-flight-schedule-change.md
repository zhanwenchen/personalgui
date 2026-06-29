---
id: trv_03
title: Rebooked flight — use the schedule-change time, not the original
domain: travel
metric_focus: [source_of_truth]
secondary_metrics: [handoff_correctness, global_success]
environments: [windows_desktop]
apps: [MockEmailApp, MockGoogleCalendarApp]
difficulty: 3
code_ready: true
new_apps_needed: []
requires_clarification: false
forbidden_routes: false
forbidden_substrings: false
source_of_truth: true
---

# Rebooked flight — use the schedule-change time, not the original

**Request (verbatim, what the agent sees):**
> "Add my Aerolux departure to my calendar."

## User & constraints

`SyntheticUser(name="alex", constraints={"personal_calendar": "google"})` — Alex's
flight was rebooked. Two emails reference the same flight; the later "schedule change"
email is authoritative. The agent must put the *new* departure time on the calendar.

## Scenario

Alex booked Aerolux AX482; the original confirmation said 07:15. Three days later the
airline sent a "Schedule change" email moving departure to 10:50. Both emails are in the
inbox. The agent must read the itinerary, recognize the schedule-change email supersedes
the original, and add the **new** time to the calendar.

## Environments & apps

| Env | App (`type`) | Seeded state (highlights) |
| --- | --- | --- |
| `windows_desktop` | `MockEmailApp` | thread `bk1` (ts 2026-06-20) "Booking confirmed — AX482" body "Departs 2026-07-09 07:15"; thread `sc1` (ts 2026-06-25) "Schedule change — AX482" body "Your departure has moved to 2026-07-09 10:50. This replaces your earlier time." |
| `windows_desktop` | `MockGoogleCalendarApp` | `events=[]`, `expected_titles=["Aerolux AX482 departure"]`, `expected_time="10:50"`, `sync_status="pending"` |

## Latent task graph (hidden from agent)

| Subtask id | Description | required_env | required_app | depends_on |
| --- | --- | --- | --- | --- |
| `find_authoritative` | Read both emails; identify the schedule-change as current. | `windows_desktop` | `email` | — |
| `add_event` | Add the departure event with the new time. | `windows_desktop` | `gcal` | `find_authoritative` |

## Required handoffs

| artifact_type | from_env | to_env | expected_value |
| --- | --- | --- | --- |
| `event_time` | `windows_desktop` | `windows_desktop` | `2026-07-09 10:50` |

## Desired final state

```
windows_desktop.gcal.sync_status == "synced"
```

## Decoys / ambiguity / source-of-truth

The original confirmation email's `07:15` is the **stale decoy**, seeded with an earlier
timestamp and the same flight number. The schedule-change email explicitly says "This
replaces your earlier time." A naive agent that opens the first/most prominent email and
carries `07:15` adds the wrong event; the calendar's `expected_time` is `10:50`, so the
stale value never flips `sync_status`.

## Metric rationale

`source_of_truth`: the same fact (departure time) appears twice, one stale. Choosing the
older confirmation produces `07:15`, which fails the calendar's `expected_time` match and
leaves `sync_status` pending — so picking the decoy fails `handoff_correctness` /
`global_success`, which is how source-of-truth is encoded today.

## Verifier sketch

- **source_of_truth (primary):** the authoritative value `10:50` is the one
  `expected_time` requires; the stale `07:15` is a decoy. Flagged in spec.
- **handoff_correctness (secondary):** `required_handoffs` carries `2026-07-09 10:50`
  from email to calendar draft; the stale time fails the handoff value check.
- **global_success (secondary):** `desired_final_state` checks `gcal.sync_status ==
  "synced"`, reached only with the correct title + `expected_time`.
- Config fields set: `desired_final_state`, `required_handoffs`; `source_of_truth: true`.

## Implementation notes

- **`code_ready: true`.** Two `MockEmailApp` threads with distinct `ts` (older = stale,
  newer = authoritative). `MockGoogleCalendarApp` seeded with `expected_titles` and
  `expected_time="10:50"`. Solvable via reading both threads, copying the new time, and
  `add_event`. The verifier requires the `10:50` value, so an agent that grabs the stale
  `07:15` fails. `desired_final_state` path is a real key.
- Set `initial_focus_env="windows_desktop"`, `initial_focus_app="email"` with thread `bk1`
  (the stale one) listed first to make the decoy tempting.
