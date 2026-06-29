---
id: home_04
title: Clarify which child's recital before setting the reminder
domain: home_family
metric_focus: [clarification_quality]
secondary_metrics: [routing_accuracy]
environments: [windows_desktop]
apps: [MockCalendarApp, MockReminderApp]
difficulty: 2
code_ready: true
new_apps_needed: []
requires_clarification: true
forbidden_routes: false
forbidden_substrings: false
source_of_truth: false
---

# Clarify which child's recital before setting the reminder

**Request (verbatim, what the agent sees):**
> "Remind me about the recital."

## User & constraints

`SyntheticUser(name="alex", constraints={})` — no preferred-channel constraint; the
difficulty is purely referent ambiguity. Both children have a recital on the **same day**,
at different times, so "the recital" does not resolve to one event.

## Scenario

Alex says "remind me about the recital," but two of Alex's children have a recital today:
Mia's piano recital at **4:00 PM** and Leo's choir recital at **7:00 PM**. Both are on the
family calendar today; neither is more obviously "the" recital. Setting a reminder for the
wrong child's time means Alex misses the intended one, so the agent must ask which child's
recital before saving anything.

## Environments & apps

| Env | App (`type`) | Seeded state (highlights) |
| --- | --- | --- |
| `windows_desktop` | `MockCalendarApp` (`family_calendar`) | two events today: `{title:"Mia — piano recital", time:"4:00 PM"}`, `{title:"Leo — choir recital", time:"7:00 PM"}`; a distractor `{title:"Trash pickup", time:"8:00 AM"}` |
| `windows_desktop` | `MockReminderApp` (`reminder_app`) | `expected_time=null` (no single correct time until clarified), pre-existing unrelated reminders |

## Latent task graph (hidden from agent)

| Subtask id | Description | required_env | required_app | depends_on |
| --- | --- | --- | --- | --- |
| `resolve_recital` | Two recitals today (Mia 4:00 PM, Leo 7:00 PM) match; agent must clarify which child. | `windows_desktop` | `family_calendar` | — |
| `set_reminder` | After clarifying, save a reminder for the chosen recital's time. | `windows_desktop` | `reminder_app` | `resolve_recital` |

## Required handoffs

None — single-environment task. The carrying metric is `clarification_quality`: the agent
must not commit to a time before asking which child's recital.

## Desired final state

```
Empty — graded via clarification_quality (and that no reminder is saved before the clarification).
```

## Decoys / ambiguity / source-of-truth

The trap is two **equally valid** recitals on the same day with no tiebreaker: Mia's piano
recital at 4:00 PM and Leo's choir recital at 7:00 PM. Neither is more recent, sooner-is-not
a tiebreaker the user stated, and both literally are "the recital." A naive agent picks the
earlier event (or the first row) and saves a reminder. Distinct from `clarification_sara` and
`com_01`: the ambiguity here is two **calendar events for two children on one day**, and the
downstream action is saving a reminder, not sending a message.

## Metric rationale

An agent that completes the literal request ("remind me about the recital") without asking
will set a reminder for one of two equally plausible events and fail `clarification_quality`,
because the ambiguity is material and the user would miss the intended recital.

## Verifier sketch

- **clarification_quality (primary):** `requires_clarification: true`; verifier returns pass
  only if the agent calls `ask_clarification` before any `save` action. A correct run asks
  "which recital — Mia's piano at 4 PM or Leo's choir at 7 PM?"; a naive run saves a reminder
  and fails.
- **routing_accuracy (secondary):** once disambiguated, the reminder must be saved in
  `reminder_app`; satisfied trivially.
- Config fields set: `requires_clarification`.

## Implementation notes

- **`code_ready: true`.** `MockCalendarApp` seeded with two same-day recital events plus a
  distractor; `MockReminderApp` with no single `expected_time` (the correct time depends on the
  clarification answer, so grading keys on the clarification preceding any save). Solvable with
  read calendar → `ask_clarification` → `type time`/`note` → `save`. `desired_final_state`
  empty, consistent with clarification tasks.
