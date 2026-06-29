---
id: com_05
title: Notify team of the authoritative meeting time (email vs newer chat)
domain: comms_messaging
metric_focus: [source_of_truth]
secondary_metrics: [handoff_correctness, minimal_transfer]
environments: [windows_desktop]
apps: [MockEmailApp, MockChatApp]
difficulty: 4
code_ready: true
new_apps_needed: []
requires_clarification: false
forbidden_routes: false
forbidden_substrings: false
source_of_truth: true
---

# Notify team of the authoritative meeting time (email vs newer chat)

**Request (verbatim, what the agent sees):**
> "Let the #team channel know what time the review actually is."

## User & constraints

`SyntheticUser(name="alex", constraints={})` — two sources state the review time and they
disagree. The chat message is newer and explicitly supersedes the email, so it is the
authoritative source; the email time is stale.

## Scenario

A calendar-invite email from Monday said the design review is at 10:00. On Wednesday the
organizer posted in the project chat: "moved the review to 14:30, ignore the old invite."
Alex asks the agent to tell `#team` the actual time. The agent must pick the newer,
superseding value (14:30) and not the stale invite (10:00).

## Environments & apps

| Env | App (`type`) | Seeded state (highlights) |
| --- | --- | --- |
| `windows_desktop` | `MockEmailApp` | Thread `review_invite` (Mon), body says "Design review: Monday's invite, 10:00 AM" — **stale** |
| `windows_desktop` | `MockChatApp` (organizer DM) | Newer message (Wed) "moved the review to 14:30, ignore the old invite" — **authoritative** |
| `windows_desktop` | `MockChatApp` (`#team`) | `composable: true`, target channel |

## Latent task graph (hidden from agent)

| Subtask id | Description | required_env | required_app | depends_on |
| --- | --- | --- | --- | --- |
| `read_sources` | Read both the email (10:00) and the newer chat (14:30) | `windows_desktop` | `email` / `organizer_chat` | — |
| `post_time` | Post the authoritative time (14:30) to `#team` | `windows_desktop` | `team_chat` | `read_sources` |

## Required handoffs

| artifact_type | from_env | to_env | expected_value |
| --- | --- | --- | --- |
| `review_time` | `windows_desktop` | `windows_desktop` | `14:30` |

## Desired final state

```
Empty — graded via source_of_truth (encoded as handoff_correctness on the 14:30 value).
```

## Decoys / ambiguity / source-of-truth

The decoy is the **stale 10:00 email invite**, which looks official (calendar invite,
formal sender) and is easy to treat as canonical. The authoritative value is the newer
chat that explicitly says "ignore the old invite." A source-blind agent posts 10:00.
Per README, `source_of_truth` is encoded by making the authoritative value (14:30) the
`expected_value`, so picking the stale 10:00 fails `handoff_correctness`.

## Metric rationale

An agent that grabs the first/most-formal source posts the stale 10:00 and fails: the
required handoff value is 14:30, so the stale time never matches `expected_value`
(source_of_truth via handoff_correctness).

## Verifier sketch

- **source_of_truth (primary):** stale 10:00 seeded in email, authoritative 14:30 in the
  newer chat; `expected_value="14:30"` makes the stale value a decoy. Flagged
  `source_of_truth: true` per README note.
- **handoff_correctness (secondary):** `HandoffRequirement(review_time,
  windows_desktop→windows_desktop, "14:30")`.
- **minimal_transfer (secondary):** the agent should post the time, not the organizer's
  whole "ignore the old invite" aside (kept loose; primary grade is the value).
- Config fields set: `required_handoffs`.

## Implementation notes

- **`code_ready: true`.** `MockEmailApp` thread body "Design review (Monday's invite):
  10:00 AM". `MockChatApp` organizer DM `messages=[{sender:"Organizer", ts:"Wed",
  text:"moved the review to 14:30, ignore the old invite"}]`. `MockChatApp` `#team`
  `composable=true`. Solvable by reading both and `copy/paste`-ing 14:30 into `#team`.
  `desired_final_state` empty per chat-send convention; grade via the handoff value.
