"""Oracle solvability for the 5 catalog tasks that required new mock apps
(MockInvitePhotoApp, MockFileShareApp, MockFileDropApp, MockProfilePhotoApp, and the
enrollment extension to MockAuthenticatorApp)."""

from __future__ import annotations

import pytest

from oracle_helpers import run_oracle, openapp, copy, paste, click, type_, done

D = "windows_desktop"
P = "android_phone"
L = "personal_laptop"

CASES = {
    "invite_photo_to_calendar_v0_01": (
        [openapp(P, "photos"), copy(P, "Priya & Sam's Wedding"),
         openapp(L, "google_calendar"), paste(L, "title"),
         copy(P, "2026-09-12"), paste(L, "time"),
         click(L, "add_event"), done(L)],
        {"global_success": True, "handoff_correctness": 1.0, "routing_accuracy": 1.0},
    ),
    "boarding_pass_print_v0_01": (
        [openapp(P, "fileshare"), copy(P, "boarding_pass_AX482.png"),
         openapp(D, "print_queue"), paste(D, "drop"), done(D)],
        {"global_success": True, "handoff_correctness": 1.0, "routing_accuracy": 1.0},
    ),
    "boarding_pass_to_editor_v0_01": (
        [openapp(P, "phone_files"), copy(P, "boardingpass_AX482.pdf"),
         openapp(D, "doc_editor"), paste(D, "body"), click(D, "save"), done(D)],
        {"global_success": True, "handoff_correctness": 1.0, "routing_accuracy": 1.0},
    ),
    "enroll_authenticator_v0_01": (
        [openapp(D, "twofa_setup"), copy(D, "QSTN-7H4K-2M9P"),
         openapp(P, "mock_authenticator"), paste(P, "setup_key"), click(P, "enroll"), done(P)],
        {"global_success": True, "handoff_correctness": 1.0, "routing_accuracy": 1.0},
    ),
    "profile_photo_latest_v0_01": (
        [openapp(P, "phone_photos"), copy(P, "headshot_2026.jpg"),
         openapp(D, "profile_photo"), paste(D, "image"), click(D, "save"), done(D)],
        {"global_success": True, "handoff_correctness": 1.0, "routing_accuracy": 1.0},
    ),
}


@pytest.mark.parametrize("task_id", sorted(CASES))
def test_oracle_solves_newapp_task(task_id: str) -> None:
    run_oracle(task_id, *CASES[task_id])


def test_profile_photo_stale_image_fails() -> None:
    """Picking the older headshot leaves the profile unsaved (source-of-truth failure)."""
    metrics = {}
    from oracle_helpers import FixedPlanAgent
    from personalgui.harness import evaluate_task
    from personalgui.tasks import build_task
    from personalgui.verifiers import DEFAULT_VERIFIERS

    plan = [openapp(P, "phone_photos"), copy(P, "headshot_2024.jpg"),
            openapp(D, "profile_photo"), paste(D, "image"), click(D, "save"), done(D)]
    metrics, _ = evaluate_task(build_task("profile_photo_latest_v0_01"),
                               FixedPlanAgent(plan), DEFAULT_VERIFIERS)
    assert metrics["global_success"] is False
    assert metrics["handoff_correctness"] == 0.0
