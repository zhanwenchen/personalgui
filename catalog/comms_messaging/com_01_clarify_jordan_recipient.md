---
id: com_01
title: Reply to "Jordan" with two same-name contacts
domain: comms_messaging
metric_focus: [clarification_quality]
secondary_metrics: [routing_accuracy]
environments: [android_phone]
apps: [MockContactsApp, MockChatApp]
difficulty: 2
code_ready: true
new_apps_needed: []
requires_clarification: true
forbidden_routes: false
forbidden_substrings: false
source_of_truth: false
---

# Reply to "Jordan" with two same-name contacts

**Request (verbatim, what the agent sees):**
> "Reply to Jordan that I can make it."

## User & constraints

`SyntheticUser(name="alex", constraints={})` — no preferred-channel constraints; the
difficulty is purely referent ambiguity. Both "Jordan" entries are reachable from the
same Messages app, so nothing in the app surface disambiguates them.

## Scenario

Alex says "reply to Jordan that I can make it," but two different people named Jordan
are in Alex's contacts: a coworker (Jordan Avila) who asked about a sprint demo, and a
cousin (Jordan Reyes) who asked about a family barbecue. Both have an open thread that
plausibly expects an "I can make it" reply. Sending to the wrong Jordan is an
irreversible, embarrassing misfire, so the agent must ask which Jordan before sending.

## Environments & apps

| Env | App (`type`) | Seeded state (highlights) |
| --- | --- | --- |
| `android_phone` | `MockContactsApp` | Two `Jordan` contacts: `jordan_work` (Jordan Avila, label "coworker"), `jordan_cousin` (Jordan Reyes, label "cousin"); plus a distractor `dana` |
| `android_phone` | `MockChatApp` | `composable: true`; two prior messages, one from each Jordan, both inviting Alex to an event |

## Latent task graph (hidden from agent)

| Subtask id | Description | required_env | required_app | depends_on |
| --- | --- | --- | --- | --- |
| `resolve_jordan` | Two contacts named "Jordan" match; agent must clarify which | `android_phone` | `phone_contacts` | — |
| `send_reply` | Send "I can make it" to the resolved Jordan (only after clarifying) | `android_phone` | `phone_chat` | `resolve_jordan` |

## Required handoffs

None — single-environment task. The carrying metric is `clarification_quality`: the
agent must not commit to a recipient before asking.

## Desired final state

```
Empty — graded via clarification_quality (and that no send precedes the clarification).
```

## Decoys / ambiguity / source-of-truth

The trap is that **both** Jordan threads end in a question Alex could answer with "I can
make it" — the coworker's "Can you make the sprint demo Tue 2pm?" and the cousin's
"You coming to the barbecue Sat?" Neither is more recent or more obviously "the" Jordan;
there is no tiebreaker in the seed. A naive agent picks the first/most-recent thread and
sends. Differs from `clarification_sara`: different names (Jordan vs Sara), different
labels (coworker/cousin vs coworker/personal-trainer), and the ambiguity is two *open
chat threads*, not just two contact rows.

## Metric rationale

An agent that completes the literal request ("reply to Jordan") without asking will send
to one of two equally plausible recipients and fail `clarification_quality`, because the
ambiguity is material and the action (sending) is irreversible.

## Verifier sketch

- **clarification_quality (primary):** `requires_clarification: true`; verifier returns
  pass only if the agent calls `ask_clarification` before any `send` action. A correct
  run asks "which Jordan — coworker Jordan Avila or cousin Jordan Reyes?"; a naive run
  sends straight away and fails.
- **routing_accuracy (secondary):** the reply, once disambiguated, must go through
  `phone_chat`; this is satisfied trivially and only fails if the agent invents a route.
- Config fields set: `requires_clarification`.

## Implementation notes

- **`code_ready: true`.** `MockContactsApp` seeded with `contacts=[{id:"jordan_work",
  name:"Jordan Avila", label:"coworker", phone:"555-0231"}, {id:"jordan_cousin",
  name:"Jordan Reyes", label:"cousin", phone:"555-0188"}, {id:"dana", name:"Dana",
  label:"friend", phone:"555-0144"}]`. `MockChatApp` seeded `composable:true`,
  `messages=[{sender:"Jordan Avila", text:"Can you make the sprint demo Tue 2pm?"},
  {sender:"Jordan Reyes", text:"You coming to the barbecue Sat?"}]`. Solvable with
  `tap contact:<id>` + `compose`/`send`; the verifier keys on the clarification call
  preceding any send. `desired_final_state` empty, consistent with chat-send tasks.
