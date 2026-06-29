---
id: sec_01
title: New-device verification code from phone to desktop "verify this device" page
domain: auth_security
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

# New-device verification code from phone to desktop "verify this device" page

**Request (verbatim, what the agent sees):**
> "Verify this new laptop on my Helios account — it's asking for a code."

## User & constraints

`SyntheticUser(name="alex", constraints={"authenticator_device": "android_phone"})` —
Alex just signed in to the Helios account on a freshly set-up desktop. The web page is
showing a "verify this device" challenge; the matching one-time code is generated only by
the authenticator on the phone. The code lives on the phone, the form lives on the desktop.

## Scenario

Helios flagged a sign-in from an unrecognized device and put up a "Is this you? Verify
this device" page on the desktop browser. The page has a single code field. The
authoritative six-digit code is the current value rotating in the phone authenticator.
The agent must read it on `android_phone` and carry it to the `windows_desktop` form —
a phone-to-desktop OTP handoff into a device-verification portal (not the expense
sign-in portal of `auth_handoff`).

## Environments & apps

| Env | App (`type`) | Seeded state (highlights) |
| --- | --- | --- |
| `android_phone` | `MockAuthenticatorApp` (`mock_authenticator`) | `otp_code="518204"` (copyable) |
| `windows_desktop` | `MockBrowserFormApp` (`verify_device`) | `expected_fields={"device_code":"518204"}`, `field_types={"device_code":"text"}`, `status="drafting"`, title "Helios — Verify this device" |

## Latent task graph (hidden from agent)

| Subtask id | Description | required_env | required_app | depends_on |
| --- | --- | --- | --- | --- |
| `read_code` | Read the rotating verification code on the phone authenticator. | `android_phone` | `mock_authenticator` | — |
| `verify_device` | Enter the code on the desktop "verify this device" form and submit. | `windows_desktop` | `verify_device` | `read_code` |

## Required handoffs

| artifact_type | from_env | to_env | expected_value |
| --- | --- | --- | --- |
| `device_code` | `android_phone` | `windows_desktop` | `518204` |

## Desired final state

```
windows_desktop.verify_device.status == "submitted"
```

## Decoys / ambiguity / source-of-truth

The desktop page header repeats a **device fingerprint id** ("Device ID: HLS-LAP-77")
right above the code field, formatted to look code-like. A naive agent may type that
device id into the code field. Only the phone authenticator's rotating `518204` is
accepted. There is exactly one account and one code, so the trap is fidelity plus
not mistaking the on-screen device id for the verification code.

## Metric rationale

An agent that types the on-screen device id, or hand-types a remembered/guessed six
digits, never produces a real `from_env=android_phone → to_env=windows_desktop` handoff
and fails `expected_fields`, so the form stays `drafting`. Only copying the phone code
and pasting it satisfies `handoff_correctness` and `global_success`.

## Verifier sketch

- **handoff_correctness (primary):** `required_handoffs` carries `expected_value="518204"`
  from `android_phone` to `windows_desktop`; satisfied only when the phone code is copied
  and pasted into the `device_code` input.
- **global_success (secondary):** `desired_final_state` checks `verify_device.status ==
  "submitted"`, set by `MockBrowserFormApp` when `device_code == expected_fields["device_code"]`.
- **routing_accuracy (secondary):** reading pinned to `android_phone/mock_authenticator`,
  submitting to `windows_desktop/verify_device`.
- Config fields set: `desired_final_state`, `required_handoffs`.

## Implementation notes

- **`code_ready: true`.** `MockAuthenticatorApp` with copyable `otp_code="518204"`;
  `MockBrowserFormApp` with one field `device_code`, `expected_fields={"device_code":
  "518204"}`, `status="drafting"`, and a `hint`/`title` containing the decoy
  `Device ID: HLS-LAP-77`. Solvable via `copy_value` on the phone code → `paste_value`
  into `device_code` → `submit`. `desired_final_state` path
  `windows_desktop.verify_device.status` is a real `MockBrowserFormApp` key.
- Differs from `auth_handoff`: that task uses `MockExpensePortalApp` and the framing
  "sign in to the expense portal"; this uses a generic `MockBrowserFormApp` device-
  verification page with a named `device_code` field and an on-screen device-id decoy.
- Set `initial_focus_env="windows_desktop"`, `initial_focus_app="verify_device"` so the
  agent must navigate to the phone for the value.
