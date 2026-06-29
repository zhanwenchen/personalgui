---
id: fin_04
title: Money transfer needing phone 2FA code on desktop bank form
domain: finance_expenses
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

# Money transfer needing phone 2FA code on desktop bank form

**Request (verbatim, what the agent sees):**
> "Authorize the rent transfer in the bank portal — it needs the code from my authenticator."

## User & constraints

`SyntheticUser(name="alex", constraints={"bank_device": "windows_desktop", "twofa_device": "android_phone"})`
— The bank portal runs on the desktop; the time-based 2FA code only appears in the phone
authenticator app. Completing the transfer requires moving the live code across devices.

## Scenario

Alex initiated a monthly rent transfer in the desktop bank portal, which now sits in an
"awaiting code" state. The required one-time code is shown only in the phone's
authenticator. The agent must read the code on `android_phone` and submit it into the
desktop form to authorize the transfer.

## Environments & apps

| Env | App (`type`) | Seeded state (highlights) |
| --- | --- | --- |
| `android_phone` | `MockAuthenticatorApp` | `otp_code="508134"` (copyable, view-only) |
| `windows_desktop` | `MockExpensePortalApp` | `otp_field=""`, `status="awaiting_otp"`, `expected_code="508134"` |

## Latent task graph (hidden from agent)

| Subtask id | Description | required_env | required_app | depends_on |
| --- | --- | --- | --- | --- |
| `read_code` | Read the 2FA code from the phone authenticator. | `android_phone` | `authenticator` | — |
| `authorize_transfer` | Enter the code into the desktop bank portal and submit. | `windows_desktop` | `bank_portal` | `read_code` |

## Required handoffs

| artifact_type | from_env | to_env | expected_value |
| --- | --- | --- | --- |
| `otp_code` | `android_phone` | `windows_desktop` | `508134` |

## Desired final state

```
windows_desktop.bank_portal.status == "authenticated"
```

## Decoys / ambiguity / source-of-truth

There is one valid code, but it is a 6-digit string that must cross devices verbatim. The
trap is transcription: an agent that paraphrases, drops a leading zero, or "remembers" a
code fails the exact match. The portal only flips to `authenticated` when
`otp_field == expected_code`. (Distinct from `auth_handoff`'s sign-in framing: here the
authorization is a money transfer and the portal is a bank form.)

## Metric rationale

The 2FA code is device-bound; an agent that does not actually copy from the phone and
paste into the desktop produces no cross-env handoff, and any digit error fails
`handoff_correctness` and leaves `status == "awaiting_otp"`.

## Verifier sketch

- **handoff_correctness (primary):** `required_handoffs` carries `508134` from
  `android_phone` to `windows_desktop`; satisfied only by copy-from-phone /
  paste-into-form.
- **global_success (secondary):** `desired_final_state` checks `bank_portal.status ==
  "authenticated"`.
- **routing_accuracy (secondary):** reading pinned to `android_phone/authenticator`,
  authorizing to `windows_desktop/bank_portal`.
- Config fields set: `desired_final_state`, `required_handoffs`.

## Implementation notes

- **`code_ready: true`.** `MockAuthenticatorApp` (`otp_code` copyable) on the phone;
  `MockExpensePortalApp` reused as the bank portal with `expected_code="508134"`,
  `status="awaiting_otp"`. Solvable via `copy_value` the OTP, `paste_value` into
  `otp_field`, `click submit`. Display names can read "Bank Portal" without new app types.
- Set `initial_focus_env="windows_desktop"` so the agent must navigate to the phone for
  the code.
