---
id: sch_10
title: Add a calendar event from a phone photo of a paper invite
domain: scheduling_calendar
metric_focus: [handoff_correctness]
secondary_metrics: [routing_accuracy, global_success]
environments: [android_phone, personal_laptop]
apps: [MockPhotosApp, MockGoogleCalendarApp]
difficulty: 3
code_ready: false
new_apps_needed: [MockPhotosApp event fields (event_title/event_date) OR a MockInvitePhotoApp]
requires_clarification: false
forbidden_routes: false
forbidden_substrings: false
source_of_truth: false
---

# Add a calendar event from a phone photo of a paper invite

**Request (verbatim, what the agent sees):**
> "There's a photo of the wedding invite on my phone — put it on my calendar."

## User & constraints

`SyntheticUser(name="alex", constraints={"personal_calendar": "google"})` — the event details live only in a phone photo; the editable calendar is on the personal laptop.

## Scenario

Alex photographed a paper wedding invite. The photo contains the event title ("Priya & Sam's Wedding") and date ("2026-09-12"). The agent must read those off the phone photo and add the event to the personal-laptop Google Calendar. This is a phone→desktop handoff where the source is an image.

## Environments & apps

| Env | App (`type`) | Seeded state (highlights) |
| --- | --- | --- |
| `android_phone` | `MockPhotosApp` (`photos`) | a photo of the invite; needs `event_title:"Priya & Sam's Wedding"`, `event_date:"2026-09-12"` as **copyable** fields |
| `personal_laptop` | `MockGoogleCalendarApp` (`google_calendar`) | editable; `expected_titles:["Priya & Sam's Wedding"]` |

## Latent task graph (hidden from agent)

| Subtask id | Description | required_env | required_app | depends_on |
| --- | --- | --- | --- | --- |
| `read_invite` | Read the title and date off the phone invite photo | `android_phone` | `photos` | — |
| `add_event` | Add the wedding event to Google Calendar | `personal_laptop` | `google_calendar` | `read_invite` |

## Required handoffs

| artifact_type | from_env | to_env | expected_value |
| --- | --- | --- | --- |
| `event_title` | `android_phone` | `personal_laptop` | `Priya & Sam's Wedding` |
| `date` | `android_phone` | `personal_laptop` | `2026-09-12` |

## Desired final state

```
personal_laptop.google_calendar.sync_status == "synced"
```

## Decoys / ambiguity / source-of-truth

Mild decoy: the invite photo also shows an RSVP-by date ("RSVP by 2026-08-01") near the event date. An agent that grabs the wrong date adds the event on the RSVP day. The crux, though, is routing the image-sourced values phone→desktop.

## Metric rationale

An agent that can't move the photo's contents to the desktop (or that adds the RSVP date) fails `handoff_correctness` and `global_success`. Correct play: read the photo's event fields, carry both phone→personal_laptop, add the event.

## Verifier sketch

- **handoff_correctness:** title and date must cross `android_phone → personal_laptop` with exact values.
- **routing_accuracy:** read pinned to `android_phone/photos`, add pinned to `personal_laptop/google_calendar`.
- **global_success:** `sync_status == "synced"`.
- Config fields set: `desired_final_state`, `required_handoffs`.

## Implementation notes

- **`code_ready: false`.** Decision: modeled as **copyable text** rather than true OCR-from-pixels, but the existing `MockPhotosApp` only exposes `amount`/`merchant`/`date` (receipt-shaped). Minimal new surface: add `event_title` and `event_date` **copyable** fields to `MockPhotosApp` (or a thin `MockInvitePhotoApp` clone with `event_title`, `event_date`, and the RSVP-date decoy field, all copyable, view-only). With that, the task is solvable with `copy_value`/`paste_value`/`type`/`add_event` exactly like the receipt-amount handoff. No new verifier needed. (If true photo OCR were required instead, that would be a separate vision capability — out of scope for v0; the copyable-text modeling keeps it close to `MockPhotosApp`.)
