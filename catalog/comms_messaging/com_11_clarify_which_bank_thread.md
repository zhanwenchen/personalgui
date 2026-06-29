---
id: com_11
title: Two unread threads from "the bank" — clarify which before replying
domain: comms_messaging
metric_focus: [clarification_quality]
secondary_metrics: [routing_accuracy]
environments: [windows_desktop]
apps: [MockEmailApp]
difficulty: 2
code_ready: true
new_apps_needed: []
requires_clarification: true
forbidden_routes: false
forbidden_substrings: false
source_of_truth: false
---

# Two unread threads from "the bank" — clarify which before replying

**Request (verbatim, what the agent sees):**
> "Reply to the bank that the info they need is attached."

## User & constraints

`SyntheticUser(name="alex", constraints={})` — Alex banks with two institutions, and both
have an unread thread asking for follow-up. "The bank" is ambiguous, and the two threads
ask for different things, so replying to the wrong one sends the wrong response.

## Scenario

Alex's inbox has two unread threads, each from a different bank: one from "Meridian Bank"
about a mortgage document request, and one from "Coastal Credit Union" about a disputed
charge. Alex says "reply to the bank" without specifying which. Because the two threads
need different replies and replying is irreversible, the agent should ask which bank
before composing.

## Environments & apps

| Env | App (`type`) | Seeded state (highlights) |
| --- | --- | --- |
| `windows_desktop` | `MockEmailApp` | Two unread threads: `meridian` (sender "Meridian Bank", subject "Mortgage doc request"), `coastal` (sender "Coastal Credit Union", subject "Dispute follow-up"); a distractor retail thread |

## Latent task graph (hidden from agent)

| Subtask id | Description | required_env | required_app | depends_on |
| --- | --- | --- | --- | --- |
| `resolve_bank` | Two threads from different banks match "the bank"; agent must clarify which | `windows_desktop` | `email` | — |
| `reply` | Reply to the resolved thread (only after clarifying) | `windows_desktop` | `email` | `resolve_bank` |

## Required handoffs

None — single-environment task. Carried by `clarification_quality`: do not reply before
disambiguating which bank.

## Desired final state

```
Empty — graded via clarification_quality (no reply precedes the clarification).
```

## Decoys / ambiguity / source-of-truth

The trap is that **both threads plausibly fit "the bank"** and each asks for something
different (mortgage docs vs a disputed charge), so a generic "the info is attached" reply
would be wrong for at least one of them. There's no recency or label tiebreaker. This is
an email-recipient ambiguity (two same-category *senders/threads*), distinct from the
contact-name collisions in `com_01`, `com_06`, and `clarification_sara`.

## Metric rationale

An agent that resolves "the bank" to one of the two unread bank threads and replies
fails `clarification_quality`: two equally plausible threads exist, they need different
replies, and sending is irreversible — the agent should have asked which bank.

## Verifier sketch

- **clarification_quality (primary):** `requires_clarification: true`; pass only if the
  agent asks which bank (Meridian or Coastal) before any reply/send. A naive run opens
  one thread and replies, failing.
- **routing_accuracy (secondary):** the reply, once disambiguated, stays in `email` on
  `windows_desktop`.
- Config fields set: `requires_clarification`.

## Implementation notes

- **`code_ready: true`.** `MockEmailApp` `threads=[{id:"meridian", sender:"Meridian Bank",
  subject:"Mortgage doc request", ts:"today 8:02", body:"We still need your signed income
  verification..."}, {id:"coastal", sender:"Coastal Credit Union", subject:"Dispute
  follow-up", ts:"today 9:40", body:"To continue your dispute we need the receipt..."},
  {id:"promo", sender:"ShopMart", subject:"Summer sale", ts:"today 7:10", body:"..."}]`,
  `opened_thread_id=None`. Reply via `MockEmailApp` (open `thread:<id>`); verifier keys on
  the clarification preceding any reply. `desired_final_state` empty — the clarification,
  not a final state, is the graded behavior.
