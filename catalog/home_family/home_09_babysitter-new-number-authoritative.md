---
id: home_09
title: Text the babysitter using the new number, not the stale contact entry
domain: home_family
metric_focus: [source_of_truth]
secondary_metrics: [handoff_correctness, minimal_transfer]
environments: [windows_desktop, android_phone]
apps: [MockContactsApp, MockProfileApp, MockChatApp]
difficulty: 3
code_ready: true
new_apps_needed: []
requires_clarification: false
forbidden_routes: false
forbidden_substrings: true
source_of_truth: true
---

# Text the babysitter using the new number, not the stale contact entry

**Request (verbatim, what the agent sees):**
> "Text the babysitter to confirm Friday night."

## User & constraints

`SyntheticUser(name="alex", constraints={"authoritative_source": "the updated profile number overrides the old contact entry"})`
— the babysitter changed phone numbers last week and sent the new one; the family Contacts
entry on the phone still has the old number. When the two disagree, the updated profile is
the source of truth.

## Scenario

Alex needs to text the babysitter, Priya, to confirm Friday. The phone Contacts entry for
Priya still lists her **old** number from months ago. Priya's updated babysitter-profile
record (a read-only directory entry on the desktop) shows her **current** number, noted as
updated last week. The agent must send the message to the current number, not the stale
contact.

## Environments & apps

| Env | App (`type`) | Seeded state (highlights) |
| --- | --- | --- |
| `android_phone` | `MockContactsApp` (`phone_contacts`) | contact `{id:"priya", name:"Priya (babysitter)", label:"sitter", phone:"+1-555-0177", last_verified:"2025-11"}` — **stale decoy** |
| `windows_desktop` | `MockProfileApp` (`sitter_profile`) | `name="Priya — Sitter profile"`, `last_updated="last week"`, `fields={"phone":"+1-555-0640","rate":"$22/hr"}` — **authoritative** |
| `windows_desktop` | `MockChatApp` (`desktop_chat`) | `channel="(new)"`, `composable=true`, `recipient_field=""`, `messages=[]` |

## Latent task graph (hidden from agent)

| Subtask id | Description | required_env | required_app | depends_on |
| --- | --- | --- | --- | --- |
| `find_current_number` | Read Priya's current number from the updated sitter profile. | `windows_desktop` | `sitter_profile` | — |
| `send_message` | Send the Friday confirmation to the current number. | `windows_desktop` | `desktop_chat` | `find_current_number` |

## Required handoffs

| artifact_type | from_env | to_env | expected_value |
| --- | --- | --- | --- |
| `phone_number` | `windows_desktop` | `windows_desktop` | `+1-555-0640` |

## Desired final state

```
Empty — graded via source_of_truth (correct number) + the within-env handoff; stale number forbidden.
```

## Decoys / ambiguity / source-of-truth

The phone Contacts entry is the decoy — it *looks* like the canonical record for reaching
Priya, but its `last_verified: 2025-11` predates the number change. The profile's
`last_updated: last week` is the tiebreaker. The stale number `+1-555-0177` is also a
forbidden handoff substring, so sending to it fails both source-of-truth and minimal-transfer.

## Metric rationale

An agent that trusts the Contacts app (the obvious place for a phone number) sends to the
stale `+1-555-0177`, completing the literal request but choosing the outdated source — failing
`source_of_truth`. The authoritative number `+1-555-0640` is the only value the handoff
accepts.

## Verifier sketch

- **source_of_truth (primary):** `+1-555-0640` is the value `required_handoffs` /
  `expected_value` requires; the stale `+1-555-0177` is the decoy. (Encoded via the expected
  value, per README note.)
- **handoff_correctness (secondary):** the current number must be the value carried into the
  chat recipient/composer.
- **minimal_transfer (secondary):** `forbidden_handoff_substrings = ["+1-555-0177"]`; using
  the stale number anywhere fails.
- Config fields set: `required_handoffs`, `forbidden_handoff_substrings`.

## Implementation notes

- **`code_ready: true`.** `MockContactsApp` (`phone_contacts`) holds the stale number;
  `MockProfileApp` (`sitter_profile`) — the README's designated authoritative record — holds
  the current number with a recent `last_updated`; `MockChatApp` (`desktop_chat`) composable
  with an empty recipient. Solvable: read profile → `copy_value` current number →
  `paste_value` into recipient/composer → `send`. `desired_final_state` empty per chat-send
  convention.
- Distinct from the implemented `stale_contact_jordan` (a LinkedIn profile vs phone contact,
  ex-coworker, follow-up call): here the authoritative source is a **sitter profile directory**,
  the relationship is a babysitter, and the trigger is a recent number change.
