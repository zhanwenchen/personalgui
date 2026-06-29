---
id: wrk_07
title: Sign in to Outlook, then add meeting action items to the personal task list
domain: work_docs_projects
metric_focus: [routing_accuracy]
secondary_metrics: [handoff_correctness, global_success]
environments: [work_laptop, android_phone]
apps: [MockOutlookApp, MockReminderApp]
difficulty: 3
code_ready: true
new_apps_needed: []
requires_clarification: false
forbidden_routes: false
forbidden_substrings: false
source_of_truth: false
---

# Sign in to Outlook, then add meeting action items to the personal task list

**Request (verbatim, what the agent sees):**
> "Sign in to my work Outlook, find the title of this morning's planning meeting, and add it as a reminder on my personal task list."

## User & constraints

`SyntheticUser(name="alex", constraints={"work_account": "alex@northwind.example", "personal_account": "alex@gmail"})` —
the meeting title lives behind a work Outlook sign-in on the work laptop; the personal task
list is the Reminders app on the phone. The work info is read-only until sign-in succeeds.

## Scenario

Alex wants a personal reminder to follow up on the morning planning meeting, but the only
record of the exact meeting title is in work Outlook, which requires signing in first. The
flow crosses a work device (sign in, read the title) to a personal device (add the
reminder). The agent must authenticate before the event title becomes copyable, then carry
the title across to the phone's task list.

## Environments & apps

| Env | App (`type`) | Seeded state (highlights) |
| --- | --- | --- |
| `work_laptop` | `MockOutlookApp` | `expected_username="alex@northwind.example"`, `expected_password="Atlas!2026"`, `status="signed_out"`, `events=[{title:"Atlas Q3 Planning — Followups", time:"09:00"}, {title:"1:1 with Maya", time:"11:00"}]` (titles copyable only after sign-in) |
| `android_phone` | `MockReminderApp` | `reminders=[{time:"08:00", note:"Standup"}]`, `time_field=""`, `note_field=""`, `status="drafting"`, `expected_time="09:00"` (reminder note must carry the meeting title) |

## Latent task graph (hidden from agent)

| Subtask id | Description | required_env | required_app | depends_on |
| --- | --- | --- | --- | --- |
| `sign_in` | Sign in to work Outlook with the work credentials | `work_laptop` | `work_outlook` | — |
| `read_title` | Read the morning planning meeting's title | `work_laptop` | `work_outlook` | `sign_in` |
| `add_reminder` | Add a reminder on the personal task list with that title | `android_phone` | `phone_reminders` | `read_title` |

## Required handoffs

| artifact_type | from_env | to_env | expected_value |
| --- | --- | --- | --- |
| `meeting_title` | `work_laptop` | `android_phone` | `Atlas Q3 Planning — Followups` |

## Desired final state

```
android_phone.phone_reminders.status == "saved"
android_phone.phone_reminders.time_field == "09:00"
```

## Decoys / ambiguity / source-of-truth

Two decoys: the `1:1 with Maya` event is also a morning Outlook event but isn't the
planning meeting (wrong title); and the titles are not copyable until sign-in, so an agent
that tries to read before authenticating gets nothing. The "this morning's planning
meeting" qualifier disambiguates to the `09:00` event — an agent that grabs the first or
nearest event may pick the 1:1.

## Metric rationale

An agent that skips the sign-in routes the read against a locked Outlook and fails to
obtain the title, or one that adds the reminder on the work device instead of the personal
phone fails `routing_accuracy`; the planning-meeting title must cross work_laptop ->
android_phone intact for `handoff_correctness` and the reminder to save.

## Verifier sketch

- **routing_accuracy (primary):** `sign_in`/`read_title` must run on `work_laptop`
  (`work_outlook`), `add_reminder` on `android_phone` (`phone_reminders`). Wrong-device
  placement fails.
- **handoff_correctness (secondary):** carries `Atlas Q3 Planning — Followups` from work
  laptop to phone.
- **global_success (secondary):** `phone_reminders.status == "saved"` with `time_field ==
  "09:00"`.
- Config fields set: `desired_final_state`, `required_handoffs`.

## Implementation notes

- **`code_ready: true`.** `MockOutlookApp` gates copyable titles on sign-in
  (`type username`/`password`, `click sign_in`); `MockReminderApp` appends when
  `time == expected_time` and a note is set. Solvable: sign in, copy the planning title,
  paste into the reminder's note field, type `09:00`, `save`. `desired_final_state`
  references real keys (`status`, `time_field`).
