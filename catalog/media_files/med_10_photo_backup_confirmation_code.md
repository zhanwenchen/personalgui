---
id: med_10
title: Confirm photo backup with a code from the phone
domain: media_files
metric_focus: [handoff_correctness]
secondary_metrics: [global_success, routing_accuracy]
environments: [android_phone, windows_desktop]
apps: [MockAuthenticatorApp, MockBrowserFormApp]
difficulty: 2
code_ready: true
new_apps_needed: []
requires_clarification: false
forbidden_routes: false
forbidden_substrings: false
source_of_truth: false
---

# Confirm photo backup with a code from the phone

**Request (verbatim, what the agent sees):**
> "Confirm the photo backup on the desktop using the code my phone shows."

## User & constraints

`SyntheticUser(name="alex", constraints={"backup_device": "windows_desktop"})` — Alex started
a cloud photo backup and the service requires confirming it on the desktop with a one-time code
that the phone's authenticator app displays. The code lives on the phone; the confirmation form
lives on the desktop.

## Scenario

To finish backing up the phone's camera roll, the cloud service shows a confirmation code on
the phone and asks Alex to enter it on the desktop backup page to verify the device. The agent
must read the code off the phone and transfer it to the desktop confirmation form, crossing
from `android_phone` to `windows_desktop`.

## Environments & apps

| Env | App (`type`) | Seeded state (highlights) |
| --- | --- | --- |
| `android_phone` | `MockAuthenticatorApp` | `otp_code="491-302"` (the copyable backup confirmation code) |
| `windows_desktop` | `MockBrowserFormApp` | `fields={confirm_code:""}`, `expected_fields={confirm_code:"491-302"}`, `field_types={confirm_code:"text"}`, `status="drafting"`, page titled "Confirm photo backup" |

## Latent task graph (hidden from agent)

| Subtask id | Description | required_env | required_app | depends_on |
| --- | --- | --- | --- | --- |
| `read_code` | Read the confirmation code from the phone authenticator. | `android_phone` | `phone_auth` | — |
| `confirm_backup` | Paste the code into the desktop backup confirmation form and submit. | `windows_desktop` | `backup_form` | `read_code` |

## Required handoffs

| artifact_type | from_env | to_env | expected_value |
| --- | --- | --- | --- |
| `confirmation_code` | `android_phone` | `windows_desktop` | `491-302` |

## Desired final state

```
windows_desktop.backup_form.status == "submitted"
```

## Decoys / ambiguity / source-of-truth

The phone authenticator also shows a small countdown timer "expires in 0:48" and a numeric
account id near the code; an agent might transfer the timer/id digits instead of the code.
Only `491-302` matches `expected_fields`. A naive agent that re-types a remembered/mis-read code
(e.g., `491302` without the hyphen, or transposing digits) fails the form match. One code — the
trap is fidelity of the transferred value, including its formatting.

## Metric rationale

An agent that hand-types a remembered or mis-formatted code never copies the authoritative value
from the phone, so no `from_env=android_phone → to_env=windows_desktop` handoff is recorded and
any drift fails the form's `expected_fields` check. Only copy-from-phone / paste-into-form both
records the handoff and matches the expected code.

## Verifier sketch

- **handoff_correctness (primary):** `required_handoffs` carries `expected_value="491-302"` from
  `android_phone` to `windows_desktop`; satisfied only when the phone code is copied and pasted
  into the form input.
- **global_success (secondary):** `desired_final_state` checks `backup_form.status ==
  "submitted"`, set when `fields.confirm_code == expected_fields.confirm_code`.
- **routing_accuracy (secondary):** reading pinned to `android_phone/phone_auth`, confirming to
  `windows_desktop/backup_form`.
- Config fields set: `desired_final_state`, `required_handoffs`.

## Implementation notes

- **`code_ready: true`.** `MockAuthenticatorApp` exposes the copyable `otp_code` (reused here as
  a generic backup confirmation code, view-only per README); `MockBrowserFormApp` seeded with
  `expected_fields={confirm_code:"491-302"}`, `field_types={confirm_code:"text"}`,
  `status="drafting"`. Solvable via `copy_value` on `otp_code`, `paste_value` into `confirm_code`,
  `click submit`. `desired_final_state` path `windows_desktop.backup_form.status` is a real key.
- Set `initial_focus_env="windows_desktop"`, `initial_focus_app="backup_form"` so the agent must
  navigate to the phone to read the code. Differs from `auth_handoff` (sign-in OTP into the
  expense portal): here the destination is a generic backup-confirmation web form, framed as a
  media-backup flow.
