---
id: sch_04
title: Mirror one work meeting to personal calendar, keep the decoy
domain: scheduling_calendar
metric_focus: [routing_accuracy]
secondary_metrics: [handoff_correctness, global_success]
environments: [work_laptop, personal_laptop]
apps: [MockOutlookApp, MockGoogleCalendarApp]
difficulty: 3
code_ready: true
new_apps_needed: []
requires_clarification: false
forbidden_routes: false
forbidden_substrings: false
source_of_truth: false
---

# Mirror one work meeting to personal calendar, keep the decoy

**Request (verbatim, what the agent sees):**
> "Add my Friday client review to my personal calendar so my partner can see I'm busy."

## User & constraints

`SyntheticUser(name="alex", constraints={"work_account": "alex@work.example", "personal_calendar": "google"})` — Outlook (work laptop) requires sign-in; Google Calendar (personal laptop) is the read-write personal target.

## Scenario

Alex wants *one* work meeting — Friday's "Client Review" — copied to the shared personal Google Calendar. The personal calendar already has an unrelated "Client Review prep" entry that Alex added at home; that is **not** the meeting and must be left alone. The agent signs in to Outlook, finds the single real meeting, and adds exactly it. (Distinct from the implemented `work_to_personal_calendar`, which mirrors *all* work events with no personal decoy; here it's a single event plus a same-named decoy already present.)

## Environments & apps

| Env | App (`type`) | Seeded state (highlights) |
| --- | --- | --- |
| `work_laptop` | `MockOutlookApp` (`outlook`) | `status:"signed_out"`, `expected_username/password`, events: `[{title:"Client Review", time:"3:00 PM", date:"2026-07-03"}]` |
| `personal_laptop` | `MockGoogleCalendarApp` (`google_calendar`) | pre-existing `[{title:"Client Review prep", time:"19:00"}, {title:"Yoga", time:"07:00"}]` — **decoy**; `expected_titles:["Client Review"]` |

## Latent task graph (hidden from agent)

| Subtask id | Description | required_env | required_app | depends_on |
| --- | --- | --- | --- | --- |
| `sign_in_outlook` | Sign in to Outlook on the work laptop | `work_laptop` | `outlook` | — |
| `read_meeting` | Read the single "Client Review" event title | `work_laptop` | `outlook` | `sign_in_outlook` |
| `add_to_google` | Add exactly "Client Review" to Google Calendar | `personal_laptop` | `google_calendar` | `read_meeting` |

## Required handoffs

| artifact_type | from_env | to_env | expected_value |
| --- | --- | --- | --- |
| `event_title` | `work_laptop` | `personal_laptop` | `Client Review` |

## Desired final state

```
personal_laptop.google_calendar.sync_status == "synced"
```

(`expected_titles == ["Client Review"]`; do not delete pre-existing personal events.)

## Decoys / ambiguity / source-of-truth

The personal calendar's pre-existing "Client Review prep" is the decoy. An agent that pattern-matches on the word "review" might decide the event is "already there" and do nothing, or might edit the prep entry. The trap: the prep entry is a different event (different title/time) and is **not** what makes `sync_status` flip — only adding the literal "Client Review" does. Routing is the crux: the meeting title is only visible *after* signing in on the work laptop, and the add must happen on the personal laptop.

## Metric rationale

An agent that skips the Outlook sign-in (so never reads the real title), or that conflates the meeting with the personal "prep" decoy, never produces the required handoff to the personal env — failing `routing_accuracy` (subtask handled on the wrong device / not at all) and `global_success`.

## Verifier sketch

- **routing_accuracy:** subtasks pin `read_meeting` to `work_laptop/outlook` and `add_to_google` to `personal_laptop/google_calendar`.
- **handoff_correctness:** the `Client Review` title must cross `work_laptop → personal_laptop`.
- **global_success:** `sync_status == "synced"`.
- Config fields set: `desired_final_state`, `required_handoffs`.

## Implementation notes

- **`code_ready: true`.** `outlook` = `MockOutlookApp` with one event and sign-in credentials; titles copyable only after `sign_in`. `google_calendar` = `MockGoogleCalendarApp` with two pre-existing decoy events and `expected_titles:["Client Review"]`. Solvable with `type username/password` → `sign_in` → `copy_value`(title) → `paste_value`/`type title` → `add_event`.
