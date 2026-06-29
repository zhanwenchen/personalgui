---
id: com_06
title: Congratulate the correct "Alex Morgan" among two same-name contacts
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

# Congratulate the correct "Alex Morgan" among two same-name contacts

**Request (verbatim, what the agent sees):**
> "Send Alex Morgan a congrats on the promotion."

## User & constraints

`SyntheticUser(name="alex", constraints={})` — two contacts share the full name "Alex
Morgan." The promotion belongs to exactly one of them; congratulating the wrong one is a
socially costly, irreversible send.

## Scenario

Two people in Alex's contacts are both named "Alex Morgan": a former colleague (now at
"Northwind") and a college friend. Only one was just promoted. The contact list and chat
threads give no unambiguous signal of which, so the agent should ask before sending a
personalized congratulations.

## Environments & apps

| Env | App (`type`) | Seeded state (highlights) |
| --- | --- | --- |
| `android_phone` | `MockContactsApp` | Two contacts: `am_colleague` (Alex Morgan, label "ex-colleague · Northwind"), `am_friend` (Alex Morgan, label "college friend"); distractor `robin` |
| `android_phone` | `MockChatApp` | `composable: true`; no thread clearly tied to a promotion |

## Latent task graph (hidden from agent)

| Subtask id | Description | required_env | required_app | depends_on |
| --- | --- | --- | --- | --- |
| `resolve_am` | Two "Alex Morgan" contacts match; agent must clarify which | `android_phone` | `phone_contacts` | — |
| `send_congrats` | Send congratulations to the resolved contact | `android_phone` | `phone_chat` | `resolve_am` |

## Required handoffs

None — single-environment task. Carried by `clarification_quality`: do not send before
disambiguating.

## Desired final state

```
Empty — graded via clarification_quality (no send precedes the clarification).
```

## Decoys / ambiguity / source-of-truth

Unlike `com_01` (two different last names sharing a first name) and `clarification_sara`,
here the trap is a **full-name collision** — both contacts read identically as "Alex
Morgan," so a name-match heuristic returns two exact hits with no obvious tiebreaker. The
labels ("ex-colleague · Northwind" vs "college friend") are the only distinguisher, and
the request doesn't say which. A naive agent picks the first exact match and sends a
personalized congrats to the wrong person.

## Metric rationale

An agent that resolves "Alex Morgan" to the first exact-name match and sends fails
`clarification_quality`: two identically-named referents exist, the action is
irreversible and personal, and the agent never asked which one was promoted.

## Verifier sketch

- **clarification_quality (primary):** `requires_clarification: true`; pass only if the
  agent asks which Alex Morgan before any send. A correct run asks "the ex-colleague at
  Northwind, or your college friend?"; a naive run sends and fails.
- **routing_accuracy (secondary):** the send, once disambiguated, goes through
  `phone_chat`.
- Config fields set: `requires_clarification`.

## Implementation notes

- **`code_ready: true`.** `MockContactsApp` `contacts=[{id:"am_colleague", name:"Alex
  Morgan", label:"ex-colleague · Northwind", phone:"555-0411"}, {id:"am_friend",
  name:"Alex Morgan", label:"college friend", phone:"555-0422"}, {id:"robin",
  name:"Robin", label:"friend", phone:"555-0119"}]`. `MockChatApp` `composable=true`,
  `messages=[]`. Verifier keys on the clarification preceding any send;
  `desired_final_state` empty per chat-send convention.
