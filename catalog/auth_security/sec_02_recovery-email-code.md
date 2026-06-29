---
id: sec_02
title: Recovery-email reset code into the desktop account-recovery form
domain: auth_security
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

# Recovery-email reset code into the desktop account-recovery form

**Request (verbatim, what the agent sees):**
> "I locked myself out of Nimbus Drive — finish the account recovery, the code's in my email."

## User & constraints

`SyntheticUser(name="alex", constraints={})` — Alex started a Nimbus Drive account
recovery, which sent a recovery code to the inbox. Both the email and the recovery web
form are open on the same desktop, so this is a within-desktop, cross-app handoff (no
phone involved).

## Scenario

Nimbus Drive's "Recover your account" page is waiting on the desktop with a single
recovery-code field. The provider just emailed a six-character recovery code to Alex's
inbox. The agent must open the email, read the code, and carry it into the browser
recovery form on the same `windows_desktop`.

## Environments & apps

| Env | App (`type`) | Seeded state (highlights) |
| --- | --- | --- |
| `windows_desktop` | `MockEmailApp` (`email`) | thread `nimbus_recovery` body: `Your recovery code is R7K2Q9`, also mentions `ticket #48120` and `expires in 15 minutes`; `opened_thread_id=None` |
| `windows_desktop` | `MockBrowserFormApp` (`recovery_form`) | `expected_fields={"recovery_code":"R7K2Q9"}`, `field_types={"recovery_code":"text"}`, `status="drafting"`, title "Nimbus Drive — Recover your account" |

## Latent task graph (hidden from agent)

| Subtask id | Description | required_env | required_app | depends_on |
| --- | --- | --- | --- | --- |
| `read_recovery_code` | Open the Nimbus recovery email; read `R7K2Q9`. | `windows_desktop` | `email` | — |
| `submit_recovery` | Enter the recovery code on the desktop recovery form and submit. | `windows_desktop` | `recovery_form` | `read_recovery_code` |

## Required handoffs

| artifact_type | from_env | to_env | expected_value |
| --- | --- | --- | --- |
| `recovery_code` | `windows_desktop` | `windows_desktop` | `R7K2Q9` |

(Within-env handoff: copy the code out of Email, paste into the recovery form on the same desktop.)

## Desired final state

```
windows_desktop.recovery_form.status == "submitted"
```

## Decoys / ambiguity / source-of-truth

The email body places the **recovery code** `R7K2Q9` in the same paragraph as a
**support ticket number** `ticket #48120`. The ticket number is more "official-looking"
and numeric; an agent that grabs it fails the form match. Only `R7K2Q9` is the recovery
code. One account, one code — the trap is code-vs-ticket confusion.

## Metric rationale

A naive agent skims the email and submits the ticket number `48120`, so the within-env
handoff value never equals `R7K2Q9` and the form stays `drafting`. Only carrying the
exact recovery code clears `handoff_correctness` and `global_success`.

## Verifier sketch

- **handoff_correctness (primary):** `required_handoffs` with `from_env == to_env ==
  windows_desktop` and `expected_value="R7K2Q9"`; satisfied only by copying the code from
  Email and pasting it into the form.
- **global_success (secondary):** `desired_final_state` checks `recovery_form.status ==
  "submitted"`, set when `recovery_code == expected_fields["recovery_code"]`.
- **routing_accuracy (secondary):** reading pinned to `email`, submitting to
  `recovery_form`, both on `windows_desktop`.
- Config fields set: `desired_final_state`, `required_handoffs`.

## Implementation notes

- **`code_ready: true`.** `MockEmailApp` with one thread whose body embeds the recovery
  code and the decoy ticket number; `MockBrowserFormApp` with one field `recovery_code`,
  `expected_fields={"recovery_code":"R7K2Q9"}`, `status="drafting"`. Solvable via
  `tap thread:nimbus_recovery` → `copy_value` the code → `paste_value` into
  `recovery_code` → `submit`. `desired_final_state` path references a real
  `MockBrowserFormApp` key.
- Differs from `sec_01` (within-desktop email→form vs phone→desktop authenticator) and
  from `bank_password_reset` (single code, no 2FA, no new password, different service).
- Seed `opened_thread_id=None` so the agent must open the email first; set
  `initial_focus_env="windows_desktop"`, `initial_focus_app="recovery_form"`.
