---
id: sch_05
title: RSVP about "the sync" when two events match
domain: scheduling_calendar
metric_focus: [clarification_quality]
secondary_metrics: [routing_accuracy]
environments: [windows_desktop]
apps: [MockCalendarApp, MockChatApp]
difficulty: 3
code_ready: true
new_apps_needed: []
requires_clarification: true
forbidden_routes: false
forbidden_substrings: false
source_of_truth: false
---

# RSVP about "the sync" when two events match

**Request (verbatim, what the agent sees):**
> "Reply that I can't make the sync — let them know I'll catch up after."

## User & constraints

`SyntheticUser(name="alex", constraints={})` — two calendar events both legitimately match the word "sync"; replying declines a specific meeting, an action that's awkward to undo (you've told the wrong group you're skipping).

## Scenario

Alex's calendar has two events that each match "the sync": a **"Design Sync"** at 11:00 with the design channel, and an **"Eng Sync"** at 15:00 with the eng channel. The request says "the sync" with no disambiguator. Declining the wrong one tells the wrong team Alex is out. The agent should ask which sync before sending the decline.

## Environments & apps

| Env | App (`type`) | Seeded state (highlights) |
| --- | --- | --- |
| `windows_desktop` | `MockCalendarApp` (`calendar`) | events: `[{title:"Design Sync", time:"11:00 AM"}, {title:"Eng Sync", time:"3:00 PM"}]` — **two referents** |
| `windows_desktop` | `MockChatApp` (`chat`) | `composable: true`, channel switchable between `#design` and `#eng` |

## Latent task graph (hidden from agent)

| Subtask id | Description | required_env | required_app | depends_on |
| --- | --- | --- | --- | --- |
| `clarify_which_sync` | Ask the user which sync ("Design Sync" or "Eng Sync") is meant | — | — | — |
| `send_decline` | After clarification, post the decline to the correct channel | `windows_desktop` | `chat` | `clarify_which_sync` |

## Required handoffs

None — single-environment task. The metric is carried by `clarification_quality`: did the agent ask before the irreversible decline.

## Desired final state

Empty — graded via `clarification_quality`. (A chat send grows `messages` and sets no status field, so there is no reliable `desired_final_state` path.)

## Decoys / ambiguity / source-of-truth

Both "Design Sync" and "Eng Sync" are plausible referents for "the sync"; neither is stale or wrong. The ambiguity is genuine, not a trick — there is no signal in the seed state that resolves it. The trap: an agent that guesses (e.g. picks the earliest event, or the alphabetically first channel) sends a real decline to one team and silently mis-routes the message.

## Metric rationale

An agent that picks one sync and posts the decline without asking takes an irreversible, observable action under ambiguity — failing `clarification_quality`. Asking first (then sending to the channel the user names) passes.

## Verifier sketch

- **clarification_quality:** `requires_clarification: true`; verifier rewards an `ask_clarification` call before any chat `send`, penalizes a send without it.
- **routing_accuracy:** the decline subtask is pinned to `windows_desktop/chat`; the *channel* chosen is determined by the clarification answer.
- Config fields set: `requires_clarification`.

## Implementation notes

- **`code_ready: true`.** `calendar` = `MockCalendarApp` with the two same-keyword events. `chat` = `MockChatApp` with `composable: true`. No `expected_*` add is needed because grading is on the clarification gate, not a backend state change. Mirrors the implemented `clarification_sara` pattern but with two calendar-event referents (not two contacts) and a channel-routing consequence.
