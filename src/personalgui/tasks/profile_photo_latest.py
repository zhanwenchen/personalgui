"""Catalog med_11: set the work profile photo using the most recent headshot, not the stale
one. Two headshots in the phone gallery (one older, one newer); only the newest is
authoritative. Source-of-truth selection, then a phone -> desktop image-name handoff.

Primary metric: source_of_truth (encoded by making the newest image the one
expected_image / desired_final_state requires). Secondary: handoff_correctness,
global_success.

Modeling note: the phone gallery uses MockFileShareApp (two image entries with copyable
name + date); the desktop profile page is MockProfilePhotoApp.

See catalog/media_files/med_11_profile_photo_latest_image.md
"""

from __future__ import annotations

from ..schemas import (
    AppSpec,
    EnvironmentSpec,
    HandoffRequirement,
    Subtask,
    SyntheticUser,
    Task,
    TaskGraph,
)

NEW_HEADSHOT = "headshot_2026.jpg"   # authoritative (newest)
OLD_HEADSHOT = "headshot_2024.jpg"   # stale decoy


def build_profile_photo_latest_task(newest: str = NEW_HEADSHOT) -> Task:
    return Task(
        task_id="profile_photo_latest_v0_01",
        request="Update my work profile picture to my current headshot from my phone.",
        user=SyntheticUser(name="alex", constraints={"authoritative_source": "newest_headshot"}),
        environments_spec=[
            EnvironmentSpec(
                id="windows_desktop",
                display_name="Windows Desktop",
                kind="desktop",
                apps=[
                    AppSpec(
                        id="profile_photo",
                        type="MockProfilePhotoApp",
                        display_name="Work Directory — Profile photo",
                        initial_state={
                            "title": "Work Directory — Profile photo",
                            "hint": "Set your profile photo from your phone gallery.",
                            "selected_image": "",
                            "expected_image": newest,
                            "status": "drafting",
                        },
                    ),
                ],
                initial_focus_app="profile_photo",
            ),
            EnvironmentSpec(
                id="android_phone",
                display_name="Android Phone",
                kind="mobile",
                apps=[
                    AppSpec(
                        id="phone_photos",
                        type="MockFileShareApp",
                        display_name="Gallery",
                        initial_state={
                            "title": "Gallery",
                            "files": [
                                {"id": "hs_old", "name": OLD_HEADSHOT, "kind": "image", "date": "2024-03-11"},
                                {"id": "hs_new", "name": newest, "kind": "image", "date": "2026-06-21"},
                            ],
                        },
                    ),
                ],
                initial_focus_app="phone_photos",
            ),
        ],
        task_graph=TaskGraph(
            subtasks=[
                Subtask(
                    id="pick_headshot",
                    description="Identify the most recent headshot in the phone gallery by date.",
                    required_env="android_phone",
                    required_app="phone_photos",
                ),
                Subtask(
                    id="set_profile",
                    description="Set that image as the desktop work profile photo and save.",
                    required_env="windows_desktop",
                    required_app="profile_photo",
                    depends_on=["pick_headshot"],
                ),
            ],
            required_handoffs=[
                HandoffRequirement(
                    artifact_type="image",
                    from_env="android_phone",
                    to_env="windows_desktop",
                    expected_value=newest,
                ),
            ],
        ),
        desired_final_state={
            "windows_desktop.profile_photo.status": "saved",
        },
        initial_focus_env="windows_desktop",
    )
