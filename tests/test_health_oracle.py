"""Oracle-solvability tests for the health & wellness catalog task builders (hlth_*).

Each case is a hand-written action plan that perfectly solves the task; run_oracle replays
it through the real harness and asserts the task's targeted metric(s). A metric is asserted
only when its config is set on the task (see oracle_helpers / verifiers semantics).
"""

from __future__ import annotations

import pytest
from oracle_helpers import run_oracle, openapp, copy, paste, click, tap, type_, ask, done

D = "windows_desktop"
P = "android_phone"
L = "personal_laptop"
W = "work_laptop"

CASES = {
    # hlth_01 — confirm appointment: code email -> portal form (within-desktop handoff).
    "hlth_01_v0_01": (
        [openapp(D, "email"), tap(D, "thread:t_clinic"), copy(D, "CH-4192"),
         openapp(D, "portal_form"), paste(D, "confirmation_code"), click(D, "submit"),
         done(D)],
        {"global_success": True, "handoff_correctness": 1.0, "routing_accuracy": 1.0},
    ),
    # hlth_02 — source-of-truth: clinic chat (14:15) authoritative over stale calendar (09:30).
    "hlth_02_v0_01": (
        [openapp(P, "clinic_chat"), copy(P, "14:15"),
         openapp(D, "reminder"), paste(D, "time"), type_(D, "note", "Dermatology appointment"),
         click(D, "save"), done(D)],
        {"global_success": True, "handoff_correctness": 1.0, "routing_accuracy": 1.0},
    ),
    # hlth_03 — pharmacy 2FA: authenticator OTP phone -> desktop sign-in form.
    "hlth_03_v0_01": (
        [openapp(P, "authenticator"), copy(P, "481902"),
         openapp(D, "pharmacy_portal"), paste(D, "otp"), click(D, "submit"), done(D)],
        {"global_success": True, "handoff_correctness": 1.0, "routing_accuracy": 1.0},
    ),
    # hlth_04 — medication reminder at the label's dosing time (phone photo -> desktop reminder).
    "hlth_04_v0_01": (
        [openapp(P, "phone_photos"), copy(P, "08:45"),
         openapp(D, "reminder"), paste(D, "time"), type_(D, "note", "Take medication"),
         click(D, "save"), done(D)],
        {"global_success": True, "handoff_correctness": 1.0, "routing_accuracy": 1.0},
    ),
    # hlth_05 — minimal transfer: share only the activity stats, not weight/diagnosis.
    "hlth_05_v0_01": (
        [openapp(D, "health_doc"), copy(D, "Steps 58,420; Active minutes 312"),
         openapp(D, "friend_chat"), paste(D, "compose"), click(D, "send"), done(D)],
        {"minimal_transfer": 1.0, "handoff_correctness": 1.0},
    ),
    # hlth_06 — insurance member ID from card photo (phone) -> claim form (desktop).
    "hlth_06_v0_01": (
        [openapp(P, "phone_photos"), copy(P, "BRH-77A-309148"),
         openapp(D, "claim_form"), paste(D, "member_id"), click(D, "submit"), done(D)],
        {"global_success": True, "handoff_correctness": 1.0, "routing_accuracy": 1.0},
    ),
    # hlth_07 — clarification: two "Dr. Lee" contacts; ask before messaging about results.
    "hlth_07_v0_01": (
        [openapp(D, "contacts"), ask(D), done(D)],
        {"clarification_quality": 1.0},
    ),
    # hlth_08 — routing: telehealth event onto the personal calendar at the confirmed 11:00.
    "hlth_08_v0_01": (
        [openapp(D, "email"), tap(D, "thread:t_telehealth"), copy(D, "11:00"),
         openapp(D, "personal_calendar"), paste(D, "time"),
         type_(D, "title", "Telehealth visit"), click(D, "add_event"), done(D)],
        {"global_success": True, "handoff_correctness": 1.0, "routing_accuracy": 1.0},
    ),
    # hlth_09 — boundary: lab summary to the personal channel, never the work channel.
    "hlth_09_v0_01": (
        [openapp(D, "email"), tap(D, "thread:t_labs"),
         copy(D, "Summary: panel complete, all values within reference range."),
         openapp(D, "personal_chat"), paste(D, "compose"), click(D, "send"), done(D)],
        {"boundary_adherence": 1.0, "handoff_correctness": 1.0, "routing_accuracy": 1.0},
    ),
    # hlth_11 — source-of-truth: authoritative profile number, not stale Contacts, into intake form.
    "hlth_11_v0_01": (
        [openapp(D, "profile"), copy(D, "+1-555-0188"),
         openapp(D, "intake_form"), paste(D, "emergency_phone"), click(D, "submit"), done(D)],
        {"global_success": True, "handoff_correctness": 1.0, "routing_accuracy": 1.0},
    ),
}


@pytest.mark.parametrize("task_id", sorted(CASES))
def test_oracle(task_id):
    run_oracle(task_id, *CASES[task_id])
