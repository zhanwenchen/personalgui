---
id: trv_07
title: Set out-of-office for the exact travel dates from the itinerary
domain: travel
metric_focus: [handoff_correctness]
secondary_metrics: [global_success, routing_accuracy]
environments: [windows_desktop]
apps: [MockEmailApp]
difficulty: 3
code_ready: true
new_apps_needed: []
requires_clarification: false
forbidden_routes: false
forbidden_substrings: false
source_of_truth: false
---

# Set out-of-office for the exact travel dates from the itinerary

**Request (verbatim, what the agent sees):**
> "Turn on my out-of-office for while I'm away."

## User & constraints

`SyntheticUser(name="alex", constraints={"ooo_email": "primary"})` — Alex's email app
supports an out-of-office responder. The away dates must come from the itinerary email, not
a guess. The OOO start/end have to match the trip exactly.

## Scenario

Alex is travelling and wants the auto-responder on for precisely the trip window. The trip
dates live in the itinerary email in the same inbox. The agent must read the start and end
dates from the itinerary and configure the OOO responder with those exact dates, then
enable it.

## Environments & apps

| Env | App (`type`) | Seeded state (highlights) |
| --- | --- | --- |
| `windows_desktop` | `MockEmailApp` | `ooo_supported=true`, `ooo_enabled=false`; thread `it1` "Your itinerary" body "Trip: depart 2026-07-21, return 2026-07-26." Also a decoy thread `pr1` "Long weekend?" mentioning 2026-08-01. |

## Latent task graph (hidden from agent)

| Subtask id | Description | required_env | required_app | depends_on |
| --- | --- | --- | --- | --- |
| `read_dates` | Read trip start/end from the itinerary email. | `windows_desktop` | `email` | — |
| `set_ooo` | Set `ooo_start`/`ooo_end`, add a message, enable OOO. | `windows_desktop` | `email` | `read_dates` |

## Required handoffs

| artifact_type | from_env | to_env | expected_value |
| --- | --- | --- | --- |
| `ooo_start` | `windows_desktop` | `windows_desktop` | `2026-07-21` |
| `ooo_end` | `windows_desktop` | `windows_desktop` | `2026-07-26` |

(Within-env handoff: dates read from the itinerary thread flow into the OOO `ooo_start` /
`ooo_end` inputs in the same app.)

## Desired final state

```
windows_desktop.email.ooo_enabled == true
```

## Decoys / ambiguity / source-of-truth

A second inbox thread "Long weekend?" mentions an unrelated `2026-08-01` date — a tempting
wrong window if the agent grabs the first date it sees. The itinerary thread holds the
real trip window `2026-07-21`–`2026-07-26`. An agent that uses the social-plan date, or
enables OOO with no/wrong dates, sets the responder for the wrong window.

## Metric rationale

The naive failure is enabling OOO with a guessed window or the decoy date, not the
itinerary's. `handoff_correctness` requires the actual trip start/end to flow into the OOO
fields; `global_success` only checks `ooo_enabled`, so the date handoffs are what make
"set OOO for *while I'm away*" non-trivial.

## Verifier sketch

- **handoff_correctness (primary):** two `required_handoffs` carry `2026-07-21` and
  `2026-07-26` from the itinerary thread into the OOO start/end inputs.
- **global_success (secondary):** `desired_final_state` checks `email.ooo_enabled ==
  true` after `ooo_toggle`.
- **routing_accuracy (secondary):** both subtasks on `windows_desktop/email`.
- Config fields set: `desired_final_state`, `required_handoffs`.

## Implementation notes

- **`code_ready: true`.** `MockEmailApp` with `ooo_supported=true`, seeded itinerary
  thread plus a decoy thread. Solvable via `tap thread:it1`, `type ooo_start` /
  `type ooo_end` (carrying the itinerary dates), `type ooo_message`, `click ooo_toggle`,
  which flips `ooo_enabled`. Mirrors the `ooo_setup` task but ties dates to a travel
  itinerary with a decoy thread; distinct seed keeps it from duplicating that task.
  `desired_final_state` path `windows_desktop.email.ooo_enabled` is a real key.
- Set `initial_focus_env="windows_desktop"`, `initial_focus_app="email"`.
