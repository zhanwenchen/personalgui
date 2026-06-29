---
id: hlth_04
title: Medication reminder at authoritative label time, not a guessed time
domain: health_wellness
metric_focus: [handoff_correctness]
secondary_metrics: [global_success, source_of_truth]
environments: [android_phone, windows_desktop]
apps: [MockPhotosApp, MockReminderApp]
difficulty: 2
code_ready: true
new_apps_needed: []
requires_clarification: false
forbidden_routes: false
forbidden_substrings: false
source_of_truth: true
---

# Medication reminder at authoritative label time, not a guessed time

**Request (verbatim, what the agent sees):**
> "Set a daily reminder to take my medication at the time on the prescription label."

## User & constraints

`SyntheticUser(name="alex", constraints={})` — The dosing time is printed on the
prescription-label photo on Alex's phone. The reminder must use that exact printed time,
not a rounded or "typical" dosing time the agent might assume.

## Scenario

Alex photographed the prescription label, which reads "Take one tablet daily at 08:45."
The agent must read the printed dosing time off the phone photo and save a daily reminder
at exactly 08:45 on the desktop reminder app — a phone-to-desktop handoff where the
authoritative time is the one on the label, not a convenient round number.

## Environments & apps

| Env | App (`type`) | Seeded state (highlights) |
| --- | --- | --- |
| `android_phone` | `MockPhotosApp` (label photo) | `amount="08:45"` (modeled as the copyable value), `merchant="Aurora Pharmacy"`, `date="2026-06-28"`; caption text "Take one tablet daily at 08:45" |
| `windows_desktop` | `MockReminderApp` (target) | `time_field=""`, `note_field=""`, `expected_time="08:45"`, `status="idle"` |

## Latent task graph (hidden from agent)

| Subtask id | Description | required_env | required_app | depends_on |
| --- | --- | --- | --- | --- |
| `read_dose_time` | Read the printed dosing time from the label photo. | `android_phone` | `phone_photos` | — |
| `set_reminder` | Save a daily medication reminder at that time. | `windows_desktop` | `reminder` | `read_dose_time` |

## Required handoffs

| artifact_type | from_env | to_env | expected_value |
| --- | --- | --- | --- |
| `time` | `android_phone` | `windows_desktop` | `08:45` |

## Desired final state

```
windows_desktop.reminder.status == "saved"
```

## Decoys / ambiguity / source-of-truth

The trap is the temptation to "round" to a tidy dosing time (08:00, 09:00) or to use a
remembered default rather than the printed `08:45`. Only the label value is authoritative.
There is one label, so no referent ambiguity — the failure mode is substituting a guessed
time for the source-of-truth value on the photo.

## Metric rationale

The reminder reaches `saved` only when `time_field == expected_time ("08:45")` and a note
is set. An agent that guesses `08:00`/`09:00` instead of copying the label time records a
wrong-valued (or no) handoff and fails both `handoff_correctness` and `global_success`.
The authoritative label time is the only passing value — encoding `source_of_truth`.

## Verifier sketch

- **handoff_correctness (primary):** `required_handoffs` carries `expected_value="08:45"`
  from `android_phone` to `windows_desktop`; satisfied only by copy-from-photo /
  paste-into-reminder.
- **source_of_truth (secondary):** authoritative label time is what `expected_time`
  requires; any guessed time is a decoy. Flagged `source_of_truth: true`.
- **global_success (secondary):** `desired_final_state` checks `reminder.status == "saved"`.
- Config fields set: `desired_final_state`, `required_handoffs`.

## Implementation notes

- **`code_ready: true`.** `MockPhotosApp` models the printed dosing time as its copyable
  `amount` value `"08:45"` (a small reuse of the copyable slot for a time string; no new
  field). `MockReminderApp` seeded with `expected_time="08:45"`, `status="idle"`. Solvable
  via `copy_value` the photo value, `paste_value` into `time_field`, `type` a note (e.g.
  "Take medication"), `click save`.
- Set `initial_focus_env="windows_desktop"`, `initial_focus_app="reminder"` so the agent
  must navigate to the phone for the authoritative time.
