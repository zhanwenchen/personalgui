---
id: wrk_09
title: Mirror the board's authoritative deadline into a calendar reminder
domain: work_docs_projects
metric_focus: [source_of_truth]
secondary_metrics: [handoff_correctness, routing_accuracy]
environments: [windows_desktop, android_phone]
apps: [MockProfileApp, MockChatApp, MockGoogleCalendarApp]
difficulty: 4
code_ready: true
new_apps_needed: []
requires_clarification: false
forbidden_routes: false
forbidden_substrings: false
source_of_truth: true
---

# Mirror the board's authoritative deadline into a calendar reminder

**Request (verbatim, what the agent sees):**
> "Put the Atlas milestone deadline on my personal calendar as an event so I don't miss it."

## User & constraints

`SyntheticUser(name="alex", constraints={"authoritative_source": "project_board"})` — the
project board is the system of record for milestone dates. A teammate's earlier chat
mentioned a different, since-revised date. When they disagree, the board's date wins, and
it goes on the personal calendar.

## Scenario

Alex wants the Atlas milestone deadline mirrored onto the personal Google Calendar. The
authoritative date lives on the project board (read-only directory) on the work laptop; an
older `#atlas-eng` chat message on the same laptop names an earlier, now-stale date. The
agent must pick the board's date and create the calendar event on the phone — a
source-of-truth choice plus a work-laptop -> phone handoff.

## Environments & apps

| Env | App (`type`) | Seeded state (highlights) |
| --- | --- | --- |
| `windows_desktop` | `MockProfileApp` | `name="Atlas — Project Board (Milestones)"`, `fields={"milestone":"Beta cutoff","deadline":"2026-09-04","status":"locked"}`, `last_updated="2026-06-25"` (authoritative) |
| `windows_desktop` | `MockChatApp` | `channel="#atlas-eng"`, `composable=false`; older message `"target beta cutoff is Aug 21"` (stale decoy date `2026-08-21`) |
| `android_phone` | `MockGoogleCalendarApp` | `events=[{title:"Dentist", time:"2026-07-02 10:00"}]`, `draft_title=""`, `draft_time=""`, `expected_titles=["Atlas Beta cutoff"]`, `sync_status="pending"` |

## Latent task graph (hidden from agent)

| Subtask id | Description | required_env | required_app | depends_on |
| --- | --- | --- | --- | --- |
| `read_deadline` | Read the locked milestone deadline from the project board | `windows_desktop` | `project_board` | — |
| `add_event` | Create the milestone event on the personal calendar at the board's date | `android_phone` | `phone_calendar` | `read_deadline` |

## Required handoffs

| artifact_type | from_env | to_env | expected_value |
| --- | --- | --- | --- |
| `deadline` | `windows_desktop` | `android_phone` | `2026-09-04` |

## Desired final state

```
android_phone.phone_calendar.sync_status == "synced"
```

## Decoys / ambiguity / source-of-truth

The same milestone has two dates: the board's locked `2026-09-04` and the chat's stale
`Aug 21` (`2026-08-21`). The chat is more conversational and easier to read at a glance,
which is the trap. An agent that trusts the chat creates the event on the wrong date; the
calendar's `expected_titles` requires the `Atlas Beta cutoff` event, and the
source-of-truth crux is the date carried into it being the board's, not the chat's.

## Metric rationale

The deadline is duplicated with one stale copy. An agent that picks the convenient chat
date schedules the milestone on `2026-08-21` and fails `source_of_truth` (encoded via the
required value); only the board's `2026-09-04` is authoritative, and it must cross to the
phone intact for the event to be correct.

## Verifier sketch

- **source_of_truth (primary):** the board's `2026-09-04` is the value the handoff /
  expected event require; the chat's `2026-08-21` is a decoy. (Encoded via expected value,
  per README note.)
- **handoff_correctness (secondary):** carries `2026-09-04` from work laptop to phone.
- **routing_accuracy (secondary):** read on `windows_desktop`, write on `android_phone`;
  wrong-device placement fails.
- Config fields set: `desired_final_state`, `required_handoffs`.

## Implementation notes

- **`code_ready: true`.** `MockProfileApp` (authoritative board) holds the locked deadline;
  `MockChatApp` (`composable:false`) seeds the stale-date decoy; `MockGoogleCalendarApp`
  reaches `sync_status="synced"` when `expected_titles=["Atlas Beta cutoff"]` is present
  (don't delete the pre-existing Dentist event). Solvable: read the board, copy the
  deadline, `type title`/`time` and `add_event` on the phone calendar. `desired_final_state`
  references the real `sync_status` key.
