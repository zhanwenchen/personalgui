---
id: sec_12
title: Submit the authenticator code before it refreshes
domain: auth_security
metric_focus: [validity_window]
secondary_metrics: [global_success, handoff_correctness, routing_accuracy]
environments: [android_phone, windows_desktop]
apps: [MockTotpAuthenticatorApp, MockBrowserFormApp]
difficulty: 4
code_ready: true
new_apps_needed: []
requires_clarification: false
forbidden_routes: false
forbidden_substrings: false
source_of_truth: false
---

# Submit the authenticator code before it refreshes

**Request (verbatim, what the agent sees):**
> "Confirm the security check on the Vault portal — it needs my authenticator code. Heads up: that code changes every few seconds."

## User & constraints

`SyntheticUser(name="alex", constraints={"freshness": "the authenticator code is only valid until it refreshes"})` —
the phone's authenticator code is time-based: it cycles to a new value every `period` logical
ticks. The Vault portal accepts only the code that is current at the moment of submission.

## Scenario

This is a **live exogenous-state** task: the environment's clock advances one tick per agent
action (including an explicit `wait`), so the authenticator code moves on its own whether or
not the agent does anything. The agent reads the code on the phone, carries it to the desktop
portal, and submits — but a code copied in one window is rejected once the window rolls over.
A direct read→submit path stays inside one window and succeeds; wasted steps (detours,
re-checking, waiting) let the code expire. "Doing nothing" is therefore a consequential
action, and the failure mode "acted on stale data" is distinct from a wrong value.

## Environments & apps

| Env | App (`type`) | Seeded state (highlights) |
| --- | --- | --- |
| `android_phone` | `MockTotpAuthenticatorApp` (`mock_authenticator`) | `codes=[730164, 118402, 550973, 884201]`, `period=5`; render shows only the **current** code + `expires_in_ticks` |
| `windows_desktop` | `MockBrowserFormApp` (`vault_portal`) | `totp_field="auth_code"`, `totp_codes=…`, `totp_period=5`, `status="drafting"`; validates the submitted code against the code valid at the submit tick |

The schedule lives in both apps' harness-side state and is never rendered — the agent sees one
six-digit code at a time, not the list or future codes.

## Latent task graph (hidden from agent)

| Subtask id | Description | required_env | required_app | depends_on |
| --- | --- | --- | --- | --- |
| `read_code` | Read the current authenticator code on the phone. | `android_phone` | `mock_authenticator` | — |
| `submit_code` | Enter the code on the desktop Vault portal and submit before it expires. | `windows_desktop` | `vault_portal` | `read_code` |

Required handoff: `auth_code` from `android_phone` → `windows_desktop` (no fixed
`expected_value` — the value is time-varying, so any phone→desktop transfer of the code
counts).

## Success & metrics

- **Desired final state:** `windows_desktop.vault_portal.status == "submitted"`.
- **validity_window** (primary): `1.0` if the agent submitted a code that was current at
  submit time and never submitted an expired one; `0.5` if it eventually succeeded after at
  least one expired attempt; `0.0` if it submitted code(s) but never a current one.
- The form rejects an expired (past-window) code with "Code expired — fetch the current one"
  and tags the event `submitted_code_status` ∈ {`current`, `expired`, `wrong`}, which is what
  the verifier reads.

## Oracle sketch

Open authenticator → copy current code → open Vault portal → paste → submit, all within one
refresh window (≤ `period` ticks from read to submit).
