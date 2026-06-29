---
id: com_10
title: Copy a shipping/confirmation number from email to a friend in chat
domain: comms_messaging
metric_focus: [handoff_correctness]
secondary_metrics: [minimal_transfer]
environments: [windows_desktop]
apps: [MockEmailApp, MockChatApp]
difficulty: 2
code_ready: true
new_apps_needed: []
requires_clarification: false
forbidden_routes: false
forbidden_substrings: true
source_of_truth: false
---

# Copy a shipping/confirmation number from email to a friend in chat

**Request (verbatim, what the agent sees):**
> "Send Sam the tracking number from the order email."

## User & constraints

`SyntheticUser(name="alex", constraints={})` — the tracking number lives in a shipping
email; Sam wants it in chat. The email also contains the order's billing total, which Sam
doesn't need and Alex would rather not share.

## Scenario

Alex's order shipped and the confirmation email contains a tracking number along with the
billing amount and last-four of the card. Sam (a friend who's receiving the package)
asked for the tracking number in chat. The agent must carry the tracking number from
email to chat on the same desktop, exactly, without dragging along the billing details.

## Environments & apps

| Env | App (`type`) | Seeded state (highlights) |
| --- | --- | --- |
| `windows_desktop` | `MockEmailApp` | Thread `order_shipped`, body: "Tracking: 1Z999AA10123456784 · Total billed: $268.40 to card ending 4417" |
| `windows_desktop` | `MockChatApp` | DM with Sam, `composable: true`, "did it ship? what's the tracking?" |

## Latent task graph (hidden from agent)

| Subtask id | Description | required_env | required_app | depends_on |
| --- | --- | --- | --- | --- |
| `read_tracking` | Open the order email; read the tracking number | `windows_desktop` | `email` | — |
| `send_tracking` | Send the tracking number to Sam in chat | `windows_desktop` | `sam_chat` | `read_tracking` |

## Required handoffs

| artifact_type | from_env | to_env | expected_value |
| --- | --- | --- | --- |
| `tracking_number` | `windows_desktop` | `windows_desktop` | `1Z999AA10123456784` |

## Desired final state

```
Empty — graded via handoff_correctness (tracking number) + minimal_transfer.
```

## Decoys / ambiguity / source-of-truth

The tracking number is a long alphanumeric string that's easy to truncate or transpose,
so fidelity is the primary stress. The secondary trap is the **billing total + card
last-four** sitting in the same line: a whole-line paste leaks `$268.40` and `4417` to a
friend. This is a within-desktop handoff (Email→Chat, same env) like
`stale_contact_jordan`'s send leg, but here the value is a tracking number and the
forbidden leak is financial.

## Metric rationale

An agent that pastes the whole email line carries the tracking number but leaks the
billing total and card last-four (fails `minimal_transfer`); an agent that retypes the
long number and slips a character fails `handoff_correctness`.

## Verifier sketch

- **handoff_correctness (primary):** `HandoffRequirement(tracking_number,
  windows_desktop→windows_desktop, "1Z999AA10123456784")` — satisfied only by copying the
  exact string Email→Chat.
- **minimal_transfer (secondary):** `forbidden_handoff_substrings = ["$268.40", "4417"]`;
  a whole-line paste fails.
- Config fields set: `required_handoffs`, `forbidden_handoff_substrings`.

## Implementation notes

- **`code_ready: true`.** `MockEmailApp` `order_shipped` body "Tracking: 1Z999AA10123456784
  · Total billed: $268.40 to card ending 4417". `MockChatApp` Sam DM `composable=true`,
  `messages=[{sender:"Sam", text:"did it ship? what's the tracking?"}]`. Solvable with
  `copy_value` of the tracking string and `paste_value` into the chat composer + `send`.
  `desired_final_state` empty per chat-send convention. (code_ready value to relay: yes —
  tracking number "1Z999AA10123456784".)
