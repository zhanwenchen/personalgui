---
id: com_04
title: Relay phone authenticator code into desktop support chat
domain: comms_messaging
metric_focus: [handoff_correctness]
secondary_metrics: [routing_accuracy]
environments: [android_phone, windows_desktop]
apps: [MockAuthenticatorApp, MockChatApp]
difficulty: 3
code_ready: true
new_apps_needed: []
requires_clarification: false
forbidden_routes: false
forbidden_substrings: false
source_of_truth: false
---

# Relay phone authenticator code into desktop support chat

**Request (verbatim, what the agent sees):**
> "The support agent needs the verification code from my authenticator — give it to them in the chat."

## User & constraints

`SyntheticUser(name="alex", constraints={})` — the verification code lives only on the
phone authenticator; the support conversation is open on the desktop. The code must
cross devices intact.

## Scenario

Alex is in a live support chat on the desktop to recover account access. The support
agent asks Alex to confirm identity by sending the current verification code, which is
shown only in the phone authenticator app. The agent must read the code on the phone and
paste exactly that code into the desktop support chat.

## Environments & apps

| Env | App (`type`) | Seeded state (highlights) |
| --- | --- | --- |
| `android_phone` | `MockAuthenticatorApp` | `otp_code: "830-194"` (copyable, view-only) |
| `windows_desktop` | `MockChatApp` | `channel: "Support — Account Recovery"`, `composable: true`, agent message "Please send your current verification code to confirm it's you." |

## Latent task graph (hidden from agent)

| Subtask id | Description | required_env | required_app | depends_on |
| --- | --- | --- | --- | --- |
| `read_code` | Read the verification code from the phone authenticator | `android_phone` | `mock_authenticator` | — |
| `send_code` | Paste the code into the desktop support chat and send | `windows_desktop` | `support_chat` | `read_code` |

## Required handoffs

| artifact_type | from_env | to_env | expected_value |
| --- | --- | --- | --- |
| `verification_code` | `android_phone` | `windows_desktop` | `830-194` |

## Desired final state

```
Empty — graded via handoff_correctness (code crosses android_phone→windows_desktop intact).
```

## Decoys / ambiguity / source-of-truth

The trap is corruption, not routing: codes are easy to transpose or truncate. The hyphen
in `830-194` invites an agent to drop or re-format it. There is no second code to confuse
it with; the metric is purely fidelity of the cross-device handoff. (No `expected_code`
form here — the support agent is a chat recipient, so the code lands in `messages`, and
the handoff record carries the grade.)

## Metric rationale

An agent that "sends the code" but transposes a digit, drops the hyphen, or paraphrases
fails `handoff_correctness`, because the `expected_value` "830-194" never crosses
`android_phone → windows_desktop` exactly.

## Verifier sketch

- **handoff_correctness (primary):** `HandoffRequirement(verification_code,
  android_phone→windows_desktop, "830-194")` is satisfied only when the agent copies the
  authenticator value on the phone and pastes that exact string into the support chat.
- **routing_accuracy (secondary):** read must occur on `android_phone`, send on
  `windows_desktop`.
- Config fields set: `required_handoffs`.

## Implementation notes

- **`code_ready: true`.** `MockAuthenticatorApp` `initial_state={"otp_code":"830-194"}`
  (copyable). `MockChatApp` `channel="Support — Account Recovery"`, `composable=true`,
  `messages=[{sender:"Support", text:"Please send your current verification code to
  confirm it's you."}]`. Solvable with `copy_value` on the phone authenticator and
  `paste_value` into the desktop chat composer, then `send`. The paste records the
  cross-env handoff; `desired_final_state` empty per chat-send convention. (code_ready
  value to relay: yes — a concrete code "830-194".)
