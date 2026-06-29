---
id: home_11
title: Confirm a contractor appointment by entering a code into the service portal
domain: home_family
metric_focus: [handoff_correctness]
secondary_metrics: [global_success, routing_accuracy]
environments: [android_phone, windows_desktop]
apps: [MockEmailApp, MockBrowserFormApp]
difficulty: 3
code_ready: true
new_apps_needed: []
requires_clarification: false
forbidden_routes: false
forbidden_substrings: false
source_of_truth: false
---

# Confirm a contractor appointment by entering a code into the service portal

**Request (verbatim, what the agent sees):**
> "Confirm the plumber's appointment on the service portal — the code is in the text they sent."

## User & constraints

`SyntheticUser(name="alex", constraints={})` — the plumbing company texted a confirmation
code to Alex's phone; the service portal where the appointment is confirmed is a web form
open on the desktop. Confirming the appointment requires moving the code from the phone text
to the desktop portal exactly.

## Scenario

A plumber's appointment is pending. The plumbing company sent a confirmation code by text
(email/SMS thread on the phone), and the service portal on the desktop has a web form that
flips the appointment to "confirmed" when the exact code is entered. The agent must read the
code on `android_phone` and submit it into the desktop portal.

## Environments & apps

| Env | App (`type`) | Seeded state (highlights) |
| --- | --- | --- |
| `android_phone` | `MockEmailApp` (`phone_messages`) | thread `plumber_confirm`: "Your appointment is pending. Confirmation code: **PLM-58213**. Reply STOP to opt out." plus a promo thread |
| `windows_desktop` | `MockBrowserFormApp` (`service_portal`) | `expected_fields={"code":"PLM-58213"}`, `field_types={"code":"text"}`, `status="drafting"` |

## Latent task graph (hidden from agent)

| Subtask id | Description | required_env | required_app | depends_on |
| --- | --- | --- | --- | --- |
| `read_code` | Open the plumber's text and read the confirmation code. | `android_phone` | `phone_messages` | — |
| `confirm_appt` | Enter the code on the desktop service portal and submit. | `windows_desktop` | `service_portal` | `read_code` |

## Required handoffs

| artifact_type | from_env | to_env | expected_value |
| --- | --- | --- | --- |
| `confirmation_code` | `android_phone` | `windows_desktop` | `PLM-58213` |

## Desired final state

```
windows_desktop.service_portal.status == "submitted"
```

## Decoys / ambiguity / source-of-truth

The text contains the confirmation code `PLM-58213` and an unrelated "Reply STOP to opt out"
line, plus a separate promo thread in the inbox. An agent that reads the promo thread, or
grabs the wrong token from the message, submits a value that does not match `expected_fields`
and the portal stays in `drafting`. The code is a cross-device string that must arrive
verbatim — any transcription error fails the match.

## Metric rationale

The confirmation code is on the phone and the portal is on the desktop; an agent that does
not actually copy from the phone and paste into the desktop form produces no cross-env handoff,
and any character error fails `handoff_correctness` and `global_success` (portal stays
`drafting`).

## Verifier sketch

- **handoff_correctness (primary):** `required_handoffs` carries `PLM-58213` from
  `android_phone` to `windows_desktop`; satisfied only by copy-from-phone / paste-into-form.
- **global_success (secondary):** `desired_final_state` checks `service_portal.status ==
  "submitted"`, set only when the `code` field equals `expected_fields`.
- **routing_accuracy (secondary):** reading pinned to `phone_messages` on `android_phone`,
  confirming to `service_portal` on `windows_desktop`.
- Config fields set: `desired_final_state`, `required_handoffs`.

## Implementation notes

- **`code_ready: true`.** `MockEmailApp` (`phone_messages`) on the phone holds the SMS-style
  thread with the code plus a promo distractor; `MockBrowserFormApp` (`service_portal`) with
  `expected_fields={"code":"PLM-58213"}`. Solvable: `tap thread:plumber_confirm` →
  `copy_value` the code → navigate to desktop → `paste_value` into the `code` input →
  `submit`. Set `initial_focus_env="android_phone"` so the agent reads the text first.
- Distinct from `home_08`/`fin_04` (numeric OTP via `MockAuthenticatorApp`/`MockExpensePortalApp`):
  here the code is an alphanumeric contractor confirmation in a phone message, entered into a
  generic browser portal form.
