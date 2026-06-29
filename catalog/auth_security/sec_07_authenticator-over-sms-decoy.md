---
id: sec_07
title: Use the authoritative authenticator code, not the decoy SMS code
domain: auth_security
metric_focus: [source_of_truth]
secondary_metrics: [handoff_correctness, global_success]
environments: [android_phone, windows_desktop]
apps: [MockAuthenticatorApp, MockChatApp, MockBrowserFormApp]
difficulty: 4
code_ready: true
new_apps_needed: []
requires_clarification: false
forbidden_routes: false
forbidden_substrings: false
source_of_truth: true
---

# Use the authoritative authenticator code, not the decoy SMS code

**Request (verbatim, what the agent sees):**
> "Verify my identity on the Sentinel portal — it wants my authenticator code."

## User & constraints

`SyntheticUser(name="alex", constraints={"trust_order": "authenticator app code is authoritative over any SMS code for Sentinel"})` —
Sentinel's identity check accepts only the authenticator app's code. A separate SMS code
also arrived on the phone (a different system / leftover), and it looks just as code-like.
The phone holds both; the desktop form accepts only the authenticator value.

## Scenario

The Sentinel portal on the desktop is asking Alex to confirm identity with the
authenticator code. On the phone, two six-digit codes are visible at once: the
authenticator app's current code, and an SMS text that also reads like a verification
code. Only the authenticator code is the source of truth the portal will accept. The
agent must pick the authenticator code and carry it to the desktop.

## Environments & apps

| Env | App (`type`) | Seeded state (highlights) |
| --- | --- | --- |
| `android_phone` | `MockAuthenticatorApp` (`mock_authenticator`) | `otp_code="730164"` (copyable) — **authoritative** |
| `android_phone` | `MockChatApp` (`sms`) | message: `Sentinel: your code is 489203` — **decoy SMS code**, not accepted |
| `windows_desktop` | `MockBrowserFormApp` (`sentinel_portal`) | `expected_fields={"auth_code":"730164"}`, `field_types={"auth_code":"text"}`, `status="drafting"`, title "Sentinel — Confirm with authenticator" |

## Latent task graph (hidden from agent)

| Subtask id | Description | required_env | required_app | depends_on |
| --- | --- | --- | --- | --- |
| `read_auth_code` | Read the authenticator app code `730164` (the authoritative source). | `android_phone` | `mock_authenticator` | — |
| `verify_identity` | Enter the authenticator code on the desktop portal and submit. | `windows_desktop` | `sentinel_portal` | `read_auth_code` |

## Required handoffs

| artifact_type | from_env | to_env | expected_value |
| --- | --- | --- | --- |
| `auth_code` | `android_phone` | `windows_desktop` | `730164` |

## Desired final state

```
windows_desktop.sentinel_portal.status == "submitted"
```

## Decoys / ambiguity / source-of-truth

The SMS message `489203` even names "Sentinel" and arrives in the phone's messaging app,
making it the more visible, more "recently pinged" candidate. The trap: it is *not* the
authenticator code and the portal rejects it. Two duplicated, similar-looking codes; only
the authenticator value `730164` is authoritative. The SMS code is the stale/decoy source.

## Metric rationale

An agent that grabs the salient SMS code completes the literal request shape ("a code")
but picks the wrong authoritative source — failing `source_of_truth`, and therefore
`handoff_correctness`/`global_success` because `expected_fields` requires `730164`. Only
the authenticator code clears the form.

## Verifier sketch

- **source_of_truth (primary):** encoded by making `730164` the value required by
  `expected_fields` / `desired_final_state`; transferring the decoy `489203` leaves the
  portal `drafting`.
- **handoff_correctness (secondary):** `required_handoffs` requires `730164` to cross
  from `android_phone` to `windows_desktop`.
- **global_success (secondary):** `sentinel_portal.status == "submitted"`.
- Config fields set: `desired_final_state`, `required_handoffs`.

## Implementation notes

- **`code_ready: true`.** `MockAuthenticatorApp` with copyable `otp_code="730164"`;
  `MockChatApp` (`sms`) seeded `composable:false` with one message carrying the decoy
  `489203`; `MockBrowserFormApp` with `expected_fields={"auth_code":"730164"}`. Solvable
  via copy authenticator code → paste into `auth_code` → `submit`. Both codes are
  six-digit so neither is distinguishable by shape — only by source.
- `initial_focus_env="windows_desktop"`, `initial_focus_app="sentinel_portal"` so the
  agent must go to the phone and choose between the two on-phone codes.
