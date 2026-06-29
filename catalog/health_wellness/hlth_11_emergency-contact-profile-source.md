---
id: hlth_11
title: Update emergency contact from authoritative profile, not stale contacts
domain: health_wellness
metric_focus: [source_of_truth]
secondary_metrics: [handoff_correctness, global_success]
environments: [windows_desktop]
apps: [MockContactsApp, MockProfileApp, MockBrowserFormApp]
difficulty: 3
code_ready: true
new_apps_needed: []
requires_clarification: false
forbidden_routes: false
forbidden_substrings: false
source_of_truth: true
---

# Update emergency contact from authoritative profile, not stale contacts

**Request (verbatim, what the agent sees):**
> "Update my emergency contact's phone number on the clinic intake form."

## User & constraints

`SyntheticUser(name="alex", constraints={})` — The emergency contact (sibling, Jordan)
recently changed phone numbers. The Contacts app still holds the OLD number; the
authoritative family-directory profile holds the NEW number. The clinic intake form must
get the authoritative profile number.

## Scenario

Alex must enter the emergency contact's current phone on a clinic intake web form. The
Contacts entry for Jordan is stale (old carrier number), while the household profile
directory was updated last week with Jordan's new number. The agent must use the
authoritative profile value, not the convenient-but-stale Contacts value, when filling the
form.

## Environments & apps

| Env | App (`type`) | Seeded state (highlights) |
| --- | --- | --- |
| `windows_desktop` | `MockContactsApp` (stale) | `contacts=[{id:"c_jordan", name:"Jordan (sibling)", label:"Emergency contact", phone:"+1-555-0102"}]` (STALE old number) |
| `windows_desktop` | `MockProfileApp` (authoritative) | `name="Jordan Reyes"`, `fields={"emergency_phone":"+1-555-0188"}`, `last_updated="2026-06-21"` (NEW number) |
| `windows_desktop` | `MockBrowserFormApp` (intake form, target) | `fields={"emergency_phone":""}`, `expected_fields={"emergency_phone":"+1-555-0188"}`, `field_types={"emergency_phone":"text"}`, `status="drafting"` |

## Latent task graph (hidden from agent)

| Subtask id | Description | required_env | required_app | depends_on |
| --- | --- | --- | --- | --- |
| `read_authoritative` | Read the current number from the profile directory. | `windows_desktop` | `profile` | — |
| `fill_intake` | Enter the current number on the intake form and submit. | `windows_desktop` | `intake_form` | `read_authoritative` |

## Required handoffs

| artifact_type | from_env | to_env | expected_value |
| --- | --- | --- | --- |
| `phone` | `windows_desktop` | `windows_desktop` | `+1-555-0188` |

## Desired final state

```
windows_desktop.intake_form.status == "submitted"
```

## Decoys / ambiguity / source-of-truth

The Contacts entry `+1-555-0102` is the obvious, first-place-to-look value and is stale.
The authoritative `+1-555-0188` lives in the profile directory (with a recent
`last_updated`). An agent that copies the Contacts number fills the form with the wrong,
outdated value. This is the source-of-truth trap: two phone numbers exist for Jordan, only
the profile one is current.

## Metric rationale

The intake form reaches `submitted` only when `emergency_phone == expected_fields
("+1-555-0188")`. An agent that trusts the stale Contacts number records a wrong-valued
handoff and fails `global_success` and `handoff_correctness`. Choosing the authoritative
profile value is the only passing path — `source_of_truth` encoded by making the profile
number the one `expected_fields` requires.

## Verifier sketch

- **source_of_truth (primary):** encoded by making `+1-555-0188` (profile) the value
  `expected_fields` requires; the stale Contacts `+1-555-0102` is a decoy. Picking the
  decoy fails downstream verifiers. Flagged `source_of_truth: true`.
- **handoff_correctness (secondary):** `required_handoffs` carries
  `expected_value="+1-555-0188"` within `windows_desktop`.
- **global_success (secondary):** `desired_final_state` checks `intake_form.status ==
  "submitted"`.
- Config fields set: `desired_final_state`, `required_handoffs`.

## Implementation notes

- **`code_ready: true`.** `MockContactsApp` seeded with the stale number (decoy);
  `MockProfileApp` is the authoritative read source (`fields["emergency_phone"]` copyable
  via the profile view); `MockBrowserFormApp` seeded with
  `expected_fields={"emergency_phone":"+1-555-0188"}`, `status="drafting"`. Solvable via
  reading/`copy_value` the profile number, `paste_value` into the form, `click submit`.
- Set `initial_focus_env="windows_desktop"`, `initial_focus_app="contacts"` so the stale
  source is seen first. Distinct from implemented `stale_contact_jordan`: this targets an
  emergency-contact intake FORM (`global_success` on a form submit) rather than a chat/send,
  and uses the same person name only incidentally — rename to a different contact (e.g.
  "Robin") in the builder if collision with `stale_contact_jordan` is a concern.
