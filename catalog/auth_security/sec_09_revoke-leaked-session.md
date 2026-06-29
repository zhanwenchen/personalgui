---
id: sec_09
title: Revoke a leaked session by confirming an emailed code on the security settings form
domain: auth_security
metric_focus: [handoff_correctness]
secondary_metrics: [global_success, routing_accuracy]
environments: [windows_desktop]
apps: [MockEmailApp, MockBrowserFormApp]
difficulty: 3
code_ready: true
new_apps_needed: []
requires_clarification: false
forbidden_routes: false
forbidden_substrings: false
source_of_truth: false
---

# Revoke a leaked session by confirming an emailed code on the security settings form

**Request (verbatim, what the agent sees):**
> "Kick out that unknown session on my Auroracast account — it emailed me a confirmation code."

## User & constraints

`SyntheticUser(name="alex", constraints={})` — Alex saw an unrecognized active session
in Auroracast security settings and wants to revoke it. Revoking requires confirming with
a code the provider just emailed. Both the email and the security settings form are open
on the same desktop — a within-desktop, cross-app handoff that gates an account-state
change.

## Scenario

Auroracast's "Active sessions" page lists an unknown session and a "Revoke all other
sessions" action that asks for an emailed confirmation code before it takes effect. The
provider sent the code to Alex's inbox. The agent must open the email, read the code, and
enter it on the security settings form to actually revoke the session.

## Environments & apps

| Env | App (`type`) | Seeded state (highlights) |
| --- | --- | --- |
| `windows_desktop` | `MockEmailApp` (`email`) | thread `auroracast_security` body: `Confirm session revocation with code 365182`, also lists `session ID 9F-22A1` and `IP 203.0.113.44`; `opened_thread_id=None` |
| `windows_desktop` | `MockBrowserFormApp` (`security_settings`) | `expected_fields={"confirm_code":"365182"}`, `field_types={"confirm_code":"text"}`, `status="drafting"`, title "Auroracast — Revoke other sessions" |

## Latent task graph (hidden from agent)

| Subtask id | Description | required_env | required_app | depends_on |
| --- | --- | --- | --- | --- |
| `read_confirm_code` | Open the Auroracast security email; read the confirmation code `365182`. | `windows_desktop` | `email` | — |
| `revoke_session` | Enter the code on the security settings form and submit to revoke. | `windows_desktop` | `security_settings` | `read_confirm_code` |

## Required handoffs

| artifact_type | from_env | to_env | expected_value |
| --- | --- | --- | --- |
| `confirm_code` | `windows_desktop` | `windows_desktop` | `365182` |

(Within-env handoff: copy the code out of Email, paste into the security form on the same desktop.)

## Desired final state

```
windows_desktop.security_settings.status == "submitted"
```

## Decoys / ambiguity / source-of-truth

The email body shows three identifier-like values together: the **confirmation code**
`365182` (correct), a **session ID** `9F-22A1`, and an **IP address** `203.0.113.44`. The
session ID and IP are about *which* session, not the confirmation; an agent that pastes
the session ID into the code field fails. Only `365182` confirms the revocation. The trap
is grabbing a co-located identifier instead of the confirmation code.

## Metric rationale

An agent that completes the literal request shape but submits the session ID or IP never
matches `expected_fields`, so the revocation form stays `drafting` and the session is not
actually revoked. Only carrying the exact confirmation code clears `handoff_correctness`
and `global_success`.

## Verifier sketch

- **handoff_correctness (primary):** `required_handoffs` with `from_env == to_env ==
  windows_desktop` and `expected_value="365182"`.
- **global_success (secondary):** `desired_final_state` checks `security_settings.status
  == "submitted"`, set when `confirm_code == 365182`.
- **routing_accuracy (secondary):** reading pinned to `email`, submitting to
  `security_settings`, both on `windows_desktop`.
- Config fields set: `desired_final_state`, `required_handoffs`.

## Implementation notes

- **`code_ready: true`.** `MockEmailApp` thread embeds the confirmation code plus the
  session-ID and IP decoys; `MockBrowserFormApp` with one field `confirm_code` and
  `expected_fields={"confirm_code":"365182"}`. Solvable via open email → copy the code →
  paste into `confirm_code` → `submit`. `desired_final_state` path references a real key.
- Differs from `sec_02` (account recovery) and `sec_06` (minimal transfer): here the
  emitted account-state change is *revoking a session*, with co-located identifier decoys
  rather than a ticket number or a list of secrets.
- Seed `opened_thread_id=None`; `initial_focus_env="windows_desktop"`,
  `initial_focus_app="security_settings"`.
