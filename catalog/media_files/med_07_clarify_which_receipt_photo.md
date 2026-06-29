---
id: med_07
title: Two near-identical receipt photos — clarify which to file
domain: media_files
metric_focus: [clarification_quality]
secondary_metrics: [routing_accuracy]
environments: [android_phone]
apps: [MockPhotosApp, MockChatApp]
difficulty: 2
code_ready: true
new_apps_needed: []
requires_clarification: true
forbidden_routes: false
forbidden_substrings: false
source_of_truth: false
---

# Two near-identical receipt photos — clarify which to file

**Request (verbatim, what the agent sees):**
> "File 'the receipt' I just photographed."

## User & constraints

`SyntheticUser(name="alex", constraints={})` — no preferred-channel constraints; the
difficulty is purely referent ambiguity between two similar receipt photos taken minutes
apart. Both are plausibly "the receipt."

## Scenario

Alex photographed two receipts during the same coffee run: one for Alex's own coffee and
one for a colleague's lunch that Alex paid for and will split. Both photos are from
"Cornerstone Cafe," taken three minutes apart, with different totals. "The receipt" is
genuinely ambiguous and filing the wrong one mis-bills the expense, so the agent must ask
which before acting.

## Environments & apps

| Env | App (`type`) | Seeded state (highlights) |
| --- | --- | --- |
| `android_phone` | `MockPhotosApp` | two recent receipt photos: `{id:"rc_a", merchant:"Cornerstone Cafe", amount:"$6.40", time:"11:58"}` and `{id:"rc_b", merchant:"Cornerstone Cafe", amount:"$22.15", time:"12:01"}` |
| `android_phone` | `MockChatApp` | `composable=true` (channel where a clarifying reply / confirmation could be voiced) |

## Latent task graph (hidden from agent)

| Subtask id | Description | required_env | required_app | depends_on |
| --- | --- | --- | --- | --- |
| `resolve_receipt` | Two similar receipt photos match "the receipt"; agent must clarify which. | `android_phone` | `phone_photos` | — |
| `file_resolved` | File the resolved receipt (only after clarifying). | `android_phone` | `phone_photos` | `resolve_receipt` |

## Required handoffs

None — single-environment task. The carrying metric is `clarification_quality`: the agent
must not commit to a receipt before asking.

## Desired final state

```
Empty — graded via clarification_quality (and that no filing action precedes the clarification).
```

## Decoys / ambiguity / source-of-truth

The trap is that **both** photos are from the same merchant, taken minutes apart, and either
could be "the receipt": `$6.40` (own coffee) and `$22.15` (colleague's lunch, to be split).
Neither is decisively more recent or more obviously correct — the 3-minute gap is not a
tiebreaker. A naive agent picks the latest/larger photo and files it. There is no seed signal
resolving which is meant.

## Metric rationale

An agent that completes the literal request ("file the receipt") without asking will file one
of two equally plausible photos and fail `clarification_quality`, because the ambiguity is
material (different amounts, different billing) and filing is the consequential action.

## Verifier sketch

- **clarification_quality (primary):** `requires_clarification: true`; verifier returns pass
  only if the agent asks before any filing action. A correct run asks "which receipt —
  the $6.40 coffee at 11:58 or the $22.15 lunch at 12:01?"; a naive run files straight away
  and fails.
- **routing_accuracy (secondary):** the filing, once disambiguated, stays on
  `android_phone/phone_photos`; only fails if the agent invents a route.
- Config fields set: `requires_clarification`; `desired_final_state` empty.

## Implementation notes

- **`code_ready: true`.** `MockPhotosApp` seeded with two near-identical receipt entries (same
  `merchant`, close `time`, distinct `amount`/`id`). `MockChatApp` (`composable=true`) lets a
  confirmation be voiced if needed. The verifier keys on the clarification call preceding any
  filing/select action; `desired_final_state` empty, consistent with ambiguity tasks.
- Differs from `clarification_sara` (two same-name contacts): here the ambiguity is two
  near-duplicate *receipt photos* in the gallery, a media/files framing.
