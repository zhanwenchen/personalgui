---
id: sec_03
title: New account needing both an email verification code and a phone 2FA code
domain: auth_security
metric_focus: [handoff_correctness]
secondary_metrics: [global_success, routing_accuracy]
environments: [android_phone, windows_desktop]
apps: [MockEmailApp, MockAuthenticatorApp, MockBrowserFormApp]
difficulty: 4
code_ready: true
new_apps_needed: []
requires_clarification: false
forbidden_routes: false
forbidden_substrings: false
source_of_truth: false
---

# New account needing both an email verification code and a phone 2FA code

**Request (verbatim, what the agent sees):**
> "Finish creating my Larkspur Cloud account — the signup page needs a couple of codes."

## User & constraints

`SyntheticUser(name="alex", constraints={"authenticator_device": "android_phone"})` —
Alex is mid-signup for a brand-new Larkspur Cloud account. The final "Confirm your
account" form needs two codes at once: an email verification code (in the inbox) and a
2FA enrollment code (in the phone authenticator). One code is on the desktop email; the
other is on the phone. Both must land in the right fields of one form.

## Scenario

Larkspur Cloud's account-creation flow ends on a single "Confirm your account" page with
two fields: an email code and an authenticator code. The provider emailed the email code
to Alex's inbox, and the authenticator app on the phone shows the 2FA enrollment code.
The agent must gather both — one within-desktop, one phone-to-desktop — and submit them
together to finish creating the account.

## Environments & apps

| Env | App (`type`) | Seeded state (highlights) |
| --- | --- | --- |
| `windows_desktop` | `MockEmailApp` (`email`) | thread `larkspur_signup` body: `Email verification code: 902451` plus `welcome offer code SAVE20`; `opened_thread_id=None` |
| `windows_desktop` | `MockBrowserFormApp` (`signup_form`) | `expected_fields={"email_code":"902451","auth_code":"663507"}`, `field_types={"email_code":"text","auth_code":"text"}`, `status="drafting"`, title "Larkspur Cloud — Confirm your account" |
| `android_phone` | `MockAuthenticatorApp` (`mock_authenticator`) | `otp_code="663507"` (copyable) |

## Latent task graph (hidden from agent)

| Subtask id | Description | required_env | required_app | depends_on |
| --- | --- | --- | --- | --- |
| `read_email_code` | Open the signup email; read the email verification code `902451`. | `windows_desktop` | `email` | — |
| `read_auth_code` | Read the 2FA enrollment code `663507` on the phone authenticator. | `android_phone` | `mock_authenticator` | — |
| `submit_signup` | Enter both codes on the desktop confirmation form and submit. | `windows_desktop` | `signup_form` | `read_email_code, read_auth_code` |

## Required handoffs

| artifact_type | from_env | to_env | expected_value |
| --- | --- | --- | --- |
| `email_code` | `windows_desktop` | `windows_desktop` | `902451` |
| `auth_code` | `android_phone` | `windows_desktop` | `663507` |

## Desired final state

```
windows_desktop.signup_form.status == "submitted"
```

## Decoys / ambiguity / source-of-truth

The signup email puts a **welcome-offer promo code** `SAVE20` in the same body as the
email verification code `902451`. A skimming agent might paste the promo code into the
`email_code` field. The two real codes also belong in *different* fields: putting the
authenticator code in `email_code` (or vice versa) fails the match even though both
codes are correct. The trap is field-routing plus promo-vs-verification confusion.

## Metric rationale

An agent that completes the literal request but mixes up the two codes, or grabs the
`SAVE20` promo code, sends handoff values that don't match `expected_fields`, leaving the
form `drafting`. Only the email code into `email_code` and the authenticator code into
`auth_code` satisfy both handoffs and `global_success`.

## Verifier sketch

- **handoff_correctness (primary):** two `required_handoffs` — `email_code` within
  `windows_desktop` (`902451`) and `auth_code` from `android_phone` to `windows_desktop`
  (`663507`). Each is value-checked independently.
- **global_success (secondary):** `desired_final_state` checks `signup_form.status ==
  "submitted"`, set only when every field equals `expected_fields`.
- **routing_accuracy (secondary):** email-code reading pinned to `email`, auth-code
  reading to `android_phone/mock_authenticator`, submit to `signup_form`.
- Config fields set: `desired_final_state`, `required_handoffs`.

## Implementation notes

- **`code_ready: true`.** `MockEmailApp` thread embeds `902451` and the `SAVE20` decoy;
  `MockBrowserFormApp` with two fields and `expected_fields={"email_code":"902451",
  "auth_code":"663507"}`; `MockAuthenticatorApp` with `otp_code="663507"`. Solvable via
  open email → copy/paste email code, then copy phone code → paste into `auth_code` →
  `submit`. All `desired_final_state` paths are real `MockBrowserFormApp` keys.
- Differs from `bank_password_reset`: that is a *password reset* (verification_code +
  totp + new_password) for Apex Bank; this is a *new-account creation* for Larkspur Cloud
  with two code fields (`email_code`, `auth_code`), no password, and a promo-code decoy.
- Seed `opened_thread_id=None`; `initial_focus_env="windows_desktop"`,
  `initial_focus_app="signup_form"`.
