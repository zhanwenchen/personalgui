---
id: trv_09
title: Confirm a hotel reservation with the code from email
domain: travel
metric_focus: [handoff_correctness]
secondary_metrics: [global_success, routing_accuracy]
environments: [windows_desktop]
apps: [MockEmailApp, MockBrowserFormApp]
difficulty: 2
code_ready: true
new_apps_needed: []
requires_clarification: false
forbidden_routes: false
forbidden_substrings: false
source_of_truth: false
---

# Confirm a hotel reservation with the code from email

**Request (verbatim, what the agent sees):**
> "Confirm my Cascade Suites reservation on their website."

## User & constraints

`SyntheticUser(name="alex", constraints={"booking_device": "windows_desktop"})` — The
hotel requires confirming the reservation through its web form using a reservation code
that arrived by email. Both apps are on the desktop.

## Scenario

Alex booked Cascade Suites; the hotel emailed a reservation code and asked Alex to confirm
the stay on their site within 24 hours. The agent must read the reservation code from the
email and enter it into the hotel's confirmation web form — a desktop email-to-browser
handoff.

## Environments & apps

| Env | App (`type`) | Seeded state (highlights) |
| --- | --- | --- |
| `windows_desktop` | `MockEmailApp` | thread `hk1` from `Cascade Suites`, subject "Confirm your stay", body "Reservation code: CS-8841-RT. Check-in 2026-07-10. Room rate $189/night." |
| `windows_desktop` | `MockBrowserFormApp` | hotel confirm form; `fields={reservation_code:""}`, `expected_fields={reservation_code:"CS-8841-RT"}`, `status="drafting"` |

## Latent task graph (hidden from agent)

| Subtask id | Description | required_env | required_app | depends_on |
| --- | --- | --- | --- | --- |
| `read_code` | Open the hotel email and read the reservation code. | `windows_desktop` | `email` | — |
| `confirm_resv` | Paste the code into the hotel form and submit. | `windows_desktop` | `hotel_form` | `read_code` |

## Required handoffs

| artifact_type | from_env | to_env | expected_value |
| --- | --- | --- | --- |
| `reservation_code` | `windows_desktop` | `windows_desktop` | `CS-8841-RT` |

## Desired final state

```
windows_desktop.hotel_form.status == "submitted"
```

## Decoys / ambiguity / source-of-truth

The same email shows the room rate `$189/night` and check-in date `2026-07-10` alongside
the code — both look like form-fillable values. Only the reservation code `CS-8841-RT`
matches `expected_fields`. The hyphenated format is easy to mistype if re-keyed from
memory, so the trap is fidelity of the transferred code. One reservation, no referent
ambiguity.

## Metric rationale

An agent that re-types the code from memory or transposes the hyphenated segments never
records the within-env handoff with the correct value and fails the form match. Only
copy-from-email / paste-into-form satisfies both `handoff_correctness` and the form's
`expected_fields`.

## Verifier sketch

- **handoff_correctness (primary):** `required_handoffs` carries
  `expected_value="CS-8841-RT"` with `from_env == to_env == windows_desktop`.
- **global_success (secondary):** `desired_final_state` checks `hotel_form.status ==
  "submitted"`, set when `fields.reservation_code == expected_fields.reservation_code`.
- **routing_accuracy (secondary):** read on `email`, submit on `hotel_form`.
- Config fields set: `desired_final_state`, `required_handoffs`.

## Implementation notes

- **`code_ready: true`.** `MockEmailApp` thread holds the reservation code as copyable
  text; `MockBrowserFormApp` seeded with `expected_fields={reservation_code:"CS-8841-RT"}`,
  `field_types={reservation_code:"text"}`, `status="drafting"`. Solvable via `tap
  thread:hk1`, `copy_value` the code, `paste_value` into `reservation_code`, `click
  submit`. Distinct from trv_01 (airline check-in) by app role, code format, and seed.
  `desired_final_state` path is a real key.
- Set `initial_focus_env="windows_desktop"`, `initial_focus_app="hotel_form"`.
