---
id: trv_02
title: Add flight and hotel itinerary events to the calendar
domain: travel
metric_focus: [handoff_correctness]
secondary_metrics: [global_success, routing_accuracy]
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

# Add flight and hotel itinerary events to the calendar

**Request (verbatim, what the agent sees):**
> "Put my Denver trip flights and hotel on my calendar."

## User & constraints

`SyntheticUser(name="alex", constraints={"personal_calendar": "google"})` — Alex keeps
personal events in the Google calendar (read-write). The itinerary lives in a single
confirmation email; the agent must lift the right event titles out and add them.

## Scenario

Alex's trip-confirmation email bundles an outbound flight, a return flight, and a hotel
stay. None are on the calendar yet. The agent must read the itinerary from the email and
create the matching events in the personal Google calendar so the trip shows up — a
read-from-email, write-to-calendar handoff within the desktop.

## Environments & apps

| Env | App (`type`) | Seeded state (highlights) |
| --- | --- | --- |
| `windows_desktop` | `MockEmailApp` | thread `it1` "Your Denver itinerary", body lists: "Outbound AX610 DEN 2026-07-10 08:40", "Return AX617 2026-07-13 18:05", "Hotel: Cascade Suites, check-in 2026-07-10". |
| `windows_desktop` | `MockGoogleCalendarApp` | `events=[{title:"Dentist", time:"2026-07-02 09:00"}]`, `expected_titles=["Aerolux AX610 to Denver","Aerolux AX617 home","Cascade Suites check-in"]`, `sync_status="pending"` |

## Latent task graph (hidden from agent)

| Subtask id | Description | required_env | required_app | depends_on |
| --- | --- | --- | --- | --- |
| `read_itinerary` | Open the itinerary email and read the three legs. | `windows_desktop` | `email` | — |
| `add_outbound` | Add the outbound flight event. | `windows_desktop` | `gcal` | `read_itinerary` |
| `add_return` | Add the return flight event. | `windows_desktop` | `gcal` | `read_itinerary` |
| `add_hotel` | Add the hotel check-in event. | `windows_desktop` | `gcal` | `read_itinerary` |

## Required handoffs

| artifact_type | from_env | to_env | expected_value |
| --- | --- | --- | --- |
| `event_time` | `windows_desktop` | `windows_desktop` | `2026-07-10 08:40` |
| `event_time` | `windows_desktop` | `windows_desktop` | `2026-07-13 18:05` |
| `event_time` | `windows_desktop` | `windows_desktop` | `2026-07-10` |

(Within-env handoffs carrying each leg's time from the email into the calendar's
`draft_time` input.)

## Desired final state

```
windows_desktop.gcal.sync_status == "synced"
```

## Decoys / ambiguity / source-of-truth

The email also lists a seat assignment ("12A") and a frequent-flyer number on the same
lines as the times — neither is an event. The calendar already holds an unrelated
"Dentist" event; the agent must **not** delete it (deleting pre-existing events is a
failure). Three legs must all be added before `sync_status` flips, so dropping the hotel
or one flight leaves the task incomplete.

## Metric rationale

An agent that adds only the flights (the salient items) and skips the hotel never
satisfies all `expected_titles`, so `sync_status` stays `pending` and `global_success`
fails. An agent that re-types times from memory instead of carrying them from the email
breaks the per-leg handoffs.

## Verifier sketch

- **handoff_correctness (primary):** three `required_handoffs` carry each leg's time from
  email to the calendar draft input.
- **global_success (secondary):** `desired_final_state` checks `gcal.sync_status ==
  "synced"`, which flips only when all three `expected_titles` are present.
- **routing_accuracy (secondary):** reads pinned to `email`, writes to `gcal`.
- Config fields set: `desired_final_state`, `required_handoffs`.

## Implementation notes

- **`code_ready: true`.** `MockEmailApp` thread body holds the three legs; seed
  `MockGoogleCalendarApp` with one pre-existing event plus `expected_titles` (three) and
  `sync_status="pending"`. Solvable via `tap thread:it1`, then for each leg `type title`
  / `copy_value` the time / `paste_value` into `draft_time` / `click add_event`.
  `sync_status` flips to `synced` when all `expected_titles` present; the pre-existing
  "Dentist" event must remain. `desired_final_state` path `windows_desktop.gcal.sync_status`
  is a real key.
- Set `initial_focus_env="windows_desktop"`, `initial_focus_app="gcal"`.
