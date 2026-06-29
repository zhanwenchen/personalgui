---
id: med_11
title: Set profile photo using the most recent image, not the stale one
domain: media_files
metric_focus: [source_of_truth]
secondary_metrics: [handoff_correctness, global_success]
environments: [android_phone, windows_desktop]
apps: [MockPhotosApp, MockProfilePhotoApp]
difficulty: 3
code_ready: false
new_apps_needed: [MockProfilePhotoApp]
requires_clarification: false
forbidden_routes: false
forbidden_substrings: false
source_of_truth: true
---

# Set profile photo using the most recent image, not the stale one

**Request (verbatim, what the agent sees):**
> "Update my work profile picture to my current headshot from my phone."

## User & constraints

`SyntheticUser(name="alex", constraints={"authoritative_source": "newest_headshot"})` — Alex
has two headshots in the phone gallery; the **most recent** one is the current look and the one
to use. The crux is choosing the authoritative (newest) image when two candidates exist.

## Scenario

Alex's phone gallery holds two headshot photos: an older `headshot_2024.jpg` and a newer
`headshot_2026.jpg` taken last week after a haircut. The work directory's profile-photo page is
on the desktop. The agent must pick the current (newest) headshot from the phone and set it as
the desktop profile photo — crossing from `android_phone` to `windows_desktop` and resisting the
stale image.

## Environments & apps

| Env | App (`type`) | Seeded state (highlights) |
| --- | --- | --- |
| `android_phone` | `MockPhotosApp` | two headshots: `{id:"hs_old", name:"headshot_2024.jpg", date:"2024-03-11", kind:"image"}` and `{id:"hs_new", name:"headshot_2026.jpg", date:"2026-06-21", kind:"image"}`; each `name` is copyable |
| `windows_desktop` | `MockProfilePhotoApp` | `selected_image=""`, `expected_image="headshot_2026.jpg"`, `status="drafting"` |

## Latent task graph (hidden from agent)

| Subtask id | Description | required_env | required_app | depends_on |
| --- | --- | --- | --- | --- |
| `pick_headshot` | Identify the most recent headshot in the phone gallery by date. | `android_phone` | `phone_photos` | — |
| `set_profile` | Set that image as the desktop work profile photo and save. | `windows_desktop` | `profile_photo` | `pick_headshot` |

## Required handoffs

| artifact_type | from_env | to_env | expected_value |
| --- | --- | --- | --- |
| `image` | `android_phone` | `windows_desktop` | `headshot_2026.jpg` |

## Desired final state

```
windows_desktop.profile_photo.status == "saved"
```

(The profile page records `saved` once `selected_image == expected_image`.)

## Decoys / ambiguity / source-of-truth

Two headshots exist; the **older** `headshot_2024.jpg` (date 2024-03-11) is a plausible "profile
picture" and may sort first in the gallery, making it the obvious-but-stale pick. The **newer**
`headshot_2026.jpg` (date 2026-06-21) is the current look and authoritative. An agent that grabs
the first headshot or any image named "headshot" without checking the date sets the stale photo.
The date is the only tiebreaker; the trap is trusting the name/order over recency.

## Metric rationale

The fact "my current headshot" is duplicated across two images with one stale. An agent that
picks the older `headshot_2024.jpg` carries the wrong value, so the required handoff
`expected_value="headshot_2026.jpg"` is not satisfied and `profile_photo.status` never reaches
`saved`. Choosing by date is the only path that matches (encoded via `expected_image`, per
README's source-of-truth note).

## Verifier sketch

- **source_of_truth (primary):** the authoritative newest image `headshot_2026.jpg` is what
  `expected_image` / `desired_final_state` require; the older `headshot_2024.jpg` is a decoy that
  fails the match.
- **handoff_correctness (secondary):** `required_handoffs` carries `headshot_2026.jpg` as an
  `image` artifact from `android_phone` to `windows_desktop`; only the newest image passes.
- **global_success (secondary):** `desired_final_state` checks `profile_photo.status == "saved"`.
- Config fields set: `desired_final_state`, `required_handoffs`.

## Implementation notes

- **`code_ready: false`.** Needs a minimal new **`MockProfilePhotoApp`** (close to
  `MockBrowserFormApp` / `MockDocumentEditorApp`): render `selected_image` and a hidden
  `expected_image`; action `paste_value` sets `selected_image` to the pasted image name and,
  when `selected_image == expected_image`, flips `status` `drafting`→`saved`. Reuse the existing
  copy/paste handoff mechanics — the phone image `name` is the copyable value — so no new
  verifier is required, only the new set-and-check surface. The phone side can use
  `MockPhotosApp` with two image entries carrying copyable `name` + `date`.
- Set `initial_focus_env="windows_desktop"`, `initial_focus_app="profile_photo"` so the agent
  must navigate to the phone and choose by date.
