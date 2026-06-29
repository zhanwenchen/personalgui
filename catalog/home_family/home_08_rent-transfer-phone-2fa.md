---
id: home_08
title: Pay rent via a transfer needing a 2FA code from the phone authenticator
domain: home_family
metric_focus: [handoff_correctness]
secondary_metrics: [global_success, routing_accuracy]
environments: [android_phone, windows_desktop]
apps: [MockAuthenticatorApp, MockExpensePortalApp]
difficulty: 3
code_ready: true
new_apps_needed: []
requires_clarification: false
forbidden_routes: false
forbidden_substrings: false
source_of_truth: false
---

# Pay rent via a transfer needing a 2FA code from the phone authenticator

**Request (verbatim, what the agent sees):**
> "Confirm the rent payment in the bank portal — it wants the code from my authenticator app."

## User & constraints

`SyntheticUser(name="alex", constraints={"bank_device": "windows_desktop", "twofa_device": "android_phone"})`
— the bank portal runs on the desktop; the time-based 2FA code only appears in the phone
authenticator. Completing the rent transfer requires moving the live code across devices.

## Scenario

Alex started this month's rent transfer in the desktop bank portal, which now sits in an
"awaiting code" state. The required one-time code is shown only in the phone's authenticator,
which currently lists codes for several accounts. The agent must read the **bank** code on
`android_phone` and submit it into the desktop portal to confirm the rent payment.

## Environments & apps

| Env | App (`type`) | Seeded state (highlights) |
| --- | --- | --- |
| `android_phone` | `MockAuthenticatorApp` (`authenticator`) | `otp_code="730596"` (the bank account's current code; copyable, view-only) |
| `windows_desktop` | `MockExpensePortalApp` (`bank_portal`) | `otp_field=""`, `status="awaiting_otp"`, `expected_code="730596"` |

## Latent task graph (hidden from agent)

| Subtask id | Description | required_env | required_app | depends_on |
| --- | --- | --- | --- | --- |
| `read_code` | Read the 2FA code from the phone authenticator. | `android_phone` | `authenticator` | — |
| `confirm_rent` | Enter the code into the desktop bank portal and submit. | `windows_desktop` | `bank_portal` | `read_code` |

## Required handoffs

| artifact_type | from_env | to_env | expected_value |
| --- | --- | --- | --- |
| `otp_code` | `android_phone` | `windows_desktop` | `730596` |

## Desired final state

```
windows_desktop.bank_portal.status == "authenticated"
```

## Decoys / ambiguity / source-of-truth

There is one valid code, but it is a 6-digit string that must cross devices verbatim. The
trap is transcription: an agent that paraphrases, drops a leading digit, or "remembers" a
code fails the exact match. The portal only flips to `authenticated` when `otp_field ==
expected_code`. The scenario is rent (a household transfer), distinguishing it from the
finance/expense framings.

## Metric rationale

The 2FA code is device-bound; an agent that does not actually copy from the phone and paste
into the desktop produces no cross-env handoff, and any digit error fails `handoff_correctness`
and leaves `status == "awaiting_otp"`.

## Verifier sketch

- **handoff_correctness (primary):** `required_handoffs` carries `730596` from `android_phone`
  to `windows_desktop`; satisfied only by copy-from-phone / paste-into-form.
- **global_success (secondary):** `desired_final_state` checks `bank_portal.status ==
  "authenticated"`.
- **routing_accuracy (secondary):** reading pinned to `android_phone/authenticator`, confirming
  to `windows_desktop/bank_portal`.
- Config fields set: `desired_final_state`, `required_handoffs`.

## Implementation notes

- **`code_ready: true`.** `MockAuthenticatorApp` (`otp_code` copyable) on the phone;
  `MockExpensePortalApp` reused as the bank portal with `expected_code="730596"`,
  `status="awaiting_otp"`. Solvable via `copy_value` the OTP, `paste_value` into `otp_field`,
  `click submit`. Display names can read "Bank Portal" / "Rent payment" without new app types.
- Set `initial_focus_env="windows_desktop"` so the agent must navigate to the phone for the
  code. Distinct from `auth_handoff` (sign-in) and `fin_04` (generic rent transfer framing):
  here it is explicitly the household rent due, same app surface.
