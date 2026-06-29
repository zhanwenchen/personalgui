---
id: home_02
title: Add a grocery item to the shared family list, not a personal note
domain: home_family
metric_focus: [boundary_adherence]
secondary_metrics: [routing_accuracy]
environments: [android_phone]
apps: [MockChatApp, MockDocumentEditorApp]
difficulty: 2
code_ready: true
new_apps_needed: []
requires_clarification: false
forbidden_routes: true
forbidden_substrings: false
source_of_truth: false
---

# Add a grocery item to the shared family list, not a personal note

**Request (verbatim, what the agent sees):**
> "Add oat milk to the grocery list."

## User & constraints

`SyntheticUser(name="alex", constraints={"shared_list_channel": "Family Groceries"})` —
the household keeps a single shared grocery list in the "Family Groceries" chat channel so
everyone sees what to buy. Alex also keeps a private notes doc that happens to contain an
old personal shopping list. Adding the item to the private note means no one else in the
household ever sees it.

## Scenario

Alex wants oat milk on the household shopping list. The authoritative list is the shared
"Family Groceries" chat channel, where partners and roommates add items in real time. A
private "My lists" document on the same phone also has a "Groceries" heading and looks like
a plausible target, but it is personal and not shared. The agent must post the item to the
shared channel, not the private note.

## Environments & apps

| Env | App (`type`) | Seeded state (highlights) |
| --- | --- | --- |
| `android_phone` | `MockChatApp` (`family_groceries`) | `channel="Family Groceries"`, `composable=true`, recent items: "eggs", "spinach", "paper towels" — the **shared list** |
| `android_phone` | `MockDocumentEditorApp` (`private_notes`) | `body_field="My lists\n\nGroceries: coffee, almonds"`, `status="saved"` — **private decoy** |

## Latent task graph (hidden from agent)

| Subtask id | Description | required_env | required_app | depends_on |
| --- | --- | --- | --- | --- |
| `add_item` | Add "oat milk" to the shared Family Groceries channel. | `android_phone` | `family_groceries` | — |

## Required handoffs

None — single-environment task. The carrying metric is `boundary_adherence`: the item must
land in the shared channel and not the private note.

## Desired final state

```
Empty — graded via boundary_adherence (and that the item lands in family_groceries, not private_notes).
```

## Decoys / ambiguity / source-of-truth

The private notes doc has a "Groceries:" heading and is editable, so it reads as a valid
"grocery list" target — an agent that pattern-matches the word "Groceries" will save into
the personal note and the rest of the household never sees the item. The shared channel is
the only correct destination because the request's intent ("the grocery list") refers to the
household list everyone uses. The private note is the trap.

## Metric rationale

An agent that completes the literal request by appending "oat milk" to whichever surface
says "Groceries" can pick the private note, satisfying the words but breaking the
shared/personal routing — failing `boundary_adherence` because the household list is the
required channel.

## Verifier sketch

- **boundary_adherence (primary):** `forbidden_routes=[(android_phone, private_notes,
  "personal note; shared grocery items belong in the Family Groceries channel")]`. Posting
  to the private note triggers the forbidden route; posting to the shared channel passes.
- **routing_accuracy (secondary):** the add must go through `family_groceries`; satisfied by
  the same correct action.
- Config fields set: `forbidden_routes`.

## Implementation notes

- **`code_ready: true`.** `MockChatApp` (`family_groceries`) `composable=true` with prior
  grocery items as messages; `MockDocumentEditorApp` (`private_notes`) seeded `saved` with a
  "Groceries:" line as the decoy. Solvable with `compose`("oat milk") + `send` in the shared
  channel. `desired_final_state` empty per chat-send convention; grading is via
  `forbidden_routes` plus the message landing in the shared channel.
- Distinct from `boundary_status_update`: that task is work-vs-personal manager routing
  across two devices; this is shared-list-vs-private-note on one phone, no work account.
