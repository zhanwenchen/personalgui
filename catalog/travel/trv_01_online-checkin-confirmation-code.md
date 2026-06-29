---
id: trv_01
title: Online check-in with confirmation code from email
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

# Online check-in with confirmation code from email

**Request (verbatim, what the agent sees):**
> "Check me in for my Aerolux flight tomorrow."

## User & constraints

`SyntheticUser(name="alex", constraints={"checkin_device": "windows_desktop"})` — Alex
does online check-in from the desktop. The airline confirmation code lives in a booking
email; the check-in web form is a separate browser app on the same desktop.

## Scenario

Alex has an Aerolux flight on 2026-06-29. The airline's online check-in opened and the
booking-confirmation email holds the six-character record locator. To check in, the agent
must read the confirmation code out of the email and type it into the check-in web form —
a handoff *within* the desktop, from the email app to the browser form.

## Environments & apps

| Env | App (`type`) | Seeded state (highlights) |
| --- | --- | --- |
| `windows_desktop` | `MockEmailApp` | thread `bk1` from `Aerolux`, subject "Booking confirmed — AX482", body: "Confirmation code: QPZ4K9. Flight AX482, 2026-06-29 07:15." |
| `windows_desktop` | `MockBrowserFormApp` | `fields={confirmation_code:""}`, `expected_fields={confirmation_code:"QPZ4K9"}`, `status="drafting"`, page titled "Aerolux check-in" |

## Latent task graph (hidden from agent)

| Subtask id | Description | required_env | required_app | depends_on |
| --- | --- | --- | --- | --- |
| `read_code` | Open the booking email and read the confirmation code. | `windows_desktop` | `email` | — |
| `submit_checkin` | Paste the code into the check-in form and submit. | `windows_desktop` | `checkin_form` | `read_code` |

## Required handoffs

| artifact_type | from_env | to_env | expected_value |
| --- | --- | --- | --- |
| `confirmation_code` | `windows_desktop` | `windows_desktop` | `QPZ4K9` |

(Within-env handoff: `from_env == to_env`, carrying the code from the email app to the
browser form on the same device.)

## Desired final state

```
windows_desktop.checkin_form.status == "submitted"
```

## Decoys / ambiguity / source-of-truth

The same email body shows the flight number `AX482` and the gate-area note "seat 14C" in
the same line as the code — both look like things to type. Only the confirmation code
`QPZ4K9` matches `expected_fields`. A naive agent that types the flight number, or that
re-types a remembered/OCR-mangled code, fails the form match. There is exactly one flight
email, so no referent ambiguity — the trap is fidelity of the transferred code.

## Metric rationale

An agent that hand-types a remembered or misread code never copies the authoritative value
from the email, so no within-env handoff is recorded and any character drift fails the
form's `expected_fields` check. Only copy-from-email / paste-into-form both records the
handoff and matches the expected code.

## Verifier sketch

- **handoff_correctness (primary):** `required_handoffs` carries `expected_value="QPZ4K9"`
  with `from_env == to_env == windows_desktop`; satisfied only when the email code is
  copied and pasted into the form input.
- **global_success (secondary):** `desired_final_state` checks
  `checkin_form.status == "submitted"`, set when `fields.confirmation_code ==
  expected_fields.confirmation_code`.
- **routing_accuracy (secondary):** both subtasks pinned to `windows_desktop`.
- Config fields set: `desired_final_state`, `required_handoffs`.

## Implementation notes

- **`code_ready: true`.** `MockEmailApp` thread body holds the code as readable/copyable
  text; `MockBrowserFormApp` seeded with `expected_fields={confirmation_code:"QPZ4K9"}`,
  `field_types={confirmation_code:"text"}`, `status="drafting"`. Solvable via `tap
  thread:bk1`, `copy_value` on the code, `paste_value` into `confirmation_code`, `click
  submit`. `desired_final_state` path `windows_desktop.checkin_form.status` is a real key.
- Set `initial_focus_env="windows_desktop"`, `initial_focus_app="checkin_form"` so the
  agent must navigate to the email to find the code.
