---
id: sec_11
title: Enroll the authenticator by entering a desktop setup key into the phone
domain: auth_security
metric_focus: [handoff_correctness]
secondary_metrics: [global_success, routing_accuracy]
environments: [windows_desktop, android_phone]
apps: [MockBrowserFormApp, MockAuthenticatorApp]
difficulty: 3
code_ready: false
new_apps_needed: [MockAuthenticatorApp (add enrollment input + status)]
requires_clarification: false
forbidden_routes: false
forbidden_substrings: false
source_of_truth: false
---

# Enroll the authenticator by entering a desktop setup key into the phone

**Request (verbatim, what the agent sees):**
> "Set up my authenticator app for Quillstone — the setup key is on the website."

## User & constraints

`SyntheticUser(name="alex", constraints={"authenticator_device": "android_phone"})` —
Quillstone's "Set up two-factor" page on the desktop shows a manual **setup key** (the
secret you type into an authenticator app to enroll). Unlike every other task in this set,
the value flows **desktop → phone**: the agent must read the setup key on the desktop and
enter it into the authenticator on the phone to enroll. The phone app is currently
view-only.

## Scenario

Quillstone's desktop 2FA setup page displays a manual entry setup key for Alex to add to
the authenticator. The authenticator app on the phone needs that key typed in to enroll
the account. The handoff direction is reversed (desktop → phone), and it requires the
phone authenticator to *accept input*, which the current view-only `MockAuthenticatorApp`
does not support.

## Environments & apps

| Env | App (`type`) | Seeded state (highlights) |
| --- | --- | --- |
| `windows_desktop` | `MockBrowserFormApp` (`twofa_setup`) | shows `Setup key: QSTN-7H4K-2M9P`; also shows a decoy `Account: alex@quillstone.io`; view-only display of the key (copyable) |
| `android_phone` | `MockAuthenticatorApp` (`mock_authenticator`) | **needs new surface:** a `setup_key_field`, `expected_setup_key="QSTN-7H4K-2M9P"`, `enroll_status="unenrolled"` |

## Latent task graph (hidden from agent)

| Subtask id | Description | required_env | required_app | depends_on |
| --- | --- | --- | --- | --- |
| `read_setup_key` | Read the setup key `QSTN-7H4K-2M9P` on the desktop 2FA page. | `windows_desktop` | `twofa_setup` | — |
| `enroll_phone` | Enter the setup key into the phone authenticator to enroll. | `android_phone` | `mock_authenticator` | `read_setup_key` |

## Required handoffs

| artifact_type | from_env | to_env | expected_value |
| --- | --- | --- | --- |
| `setup_key` | `windows_desktop` | `android_phone` | `QSTN-7H4K-2M9P` |

(Reverse-direction handoff: copy from the desktop page, paste into the phone authenticator input.)

## Desired final state

```
android_phone.mock_authenticator.enroll_status == "enrolled"
```

## Decoys / ambiguity / source-of-truth

The desktop page shows the **account identifier** `alex@quillstone.io` right beside the
setup key; an agent might enter the account email into the authenticator instead of the
key. Only `QSTN-7H4K-2M9P` enrolls the app. One account, one key — the trap is
account-id-vs-setup-key confusion plus the unusual desktop→phone direction (an agent
biased toward "read phone, type on desktop" may try to push the phone code to the desktop,
which is backwards here).

## Metric rationale

An agent that assumes the usual phone→desktop OTP flow, or enters the account email
instead of the setup key, never lands `QSTN-7H4K-2M9P` in the phone authenticator, so
`enroll_status` stays `unenrolled` and both `handoff_correctness` and `global_success`
fail. Only reading the desktop key and entering it on the phone enrolls the app.

## Verifier sketch

- **handoff_correctness (primary):** `required_handoffs` carries `expected_value=
  "QSTN-7H4K-2M9P"` from `windows_desktop` to `android_phone` — satisfied only by copying
  the desktop key and pasting it into the phone authenticator input.
- **global_success (secondary):** `desired_final_state` checks `mock_authenticator.
  enroll_status == "enrolled"`, set when the entered key matches `expected_setup_key`.
- **routing_accuracy (secondary):** reading pinned to `windows_desktop/twofa_setup`,
  enrolling to `android_phone/mock_authenticator`.
- Config fields set: `desired_final_state`, `required_handoffs`.

## Implementation notes

- **`code_ready: false`.** Today `MockAuthenticatorApp` is view-only (exposes a copyable
  `otp_code`) and cannot accept input, so the desktop→phone enrollment cannot be expressed.
- **New app surface (minimal, modeled on `MockBrowserFormApp`):** extend
  `MockAuthenticatorApp` with an enrollment mode —
  - render fields: `setup_key_field` (input), display `enroll_status`;
  - hidden field: `expected_setup_key`;
  - action: `type setup_key` + `click enroll`;
  - success condition: `enroll_status` flips `"unenrolled" → "enrolled"` when
    `setup_key_field == expected_setup_key`.
  This keeps the phone authenticator's existing OTP role and adds only the input + status
  needed for reverse-direction enrollment. The desktop side reuses `MockBrowserFormApp`
  in a view-only display mode (the setup key is copyable).
- `initial_focus_env="windows_desktop"`, `initial_focus_app="twofa_setup"`.
