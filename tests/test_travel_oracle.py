"""Oracle-solvability tests for the travel-domain task builders (trv_01..trv_10).

Each case is a hand-written action plan that perfectly solves the task; running it through
the real harness and asserting the task's metric(s) proves the builder is solvable.
"""

from __future__ import annotations

import pytest

from oracle_helpers import run_oracle, openapp, copy, paste, click, tap, type_, ask, done

D = "windows_desktop"
P = "android_phone"
L = "personal_laptop"
W = "work_laptop"

# task_id -> (plan, {metric: expected_value})
CASES = {
    # trv_01: confirmation code from email -> check-in form (within-desktop handoff).
    "trv_01_v0_01": (
        [openapp(D, "email"), tap(D, "thread:bk1"), copy(D, "QPZ4K9"),
         openapp(D, "checkin_form"), paste(D, "confirmation_code"),
         click(D, "submit"), done(D)],
        {"global_success": True, "handoff_correctness": 1.0, "routing_accuracy": 1.0},
    ),
    # trv_02: itinerary email -> three calendar events; sync flips when all titles present.
    "trv_02_v0_01": (
        [openapp(D, "email"), tap(D, "thread:it1"),
         openapp(D, "gcal"),
         type_(D, "title", "Aerolux AX610 to Denver"),
         copy(D, "2026-07-10 08:40"), paste(D, "time"), click(D, "add_event"),
         type_(D, "title", "Aerolux AX617 home"),
         copy(D, "2026-07-13 18:05"), paste(D, "time"), click(D, "add_event"),
         type_(D, "title", "Cascade Suites check-in"),
         copy(D, "2026-07-10"), paste(D, "time"), click(D, "add_event"),
         done(D)],
        {"global_success": True, "handoff_correctness": 1.0, "routing_accuracy": 1.0},
    ),
    # trv_03: source-of-truth — use the new (schedule-change) time, not the stale one.
    "trv_03_v0_01": (
        [openapp(D, "email"), tap(D, "thread:bk1"), tap(D, "thread:sc1"),
         openapp(D, "gcal"),
         type_(D, "title", "Aerolux AX482 departure"),
         copy(D, "2026-07-09 10:50"), paste(D, "time"), click(D, "add_event"),
         done(D)],
        {"global_success": True, "handoff_correctness": 1.0, "routing_accuracy": 1.0},
    ),
    # trv_04: airline 2FA — phone authenticator OTP -> desktop sign-in.
    "trv_04_v0_01": (
        [openapp(P, "authenticator"), copy(P, "704218"),
         openapp(D, "signin"), paste(D, "otp"), click(D, "submit"), done(D)],
        {"global_success": True, "handoff_correctness": 1.0, "routing_accuracy": 1.0},
    ),
    # trv_05: minimal transfer — post only the date range to the work channel.
    "trv_05_v0_01": (
        [openapp(D, "email"), tap(D, "thread:tr1"),
         copy(D, "2026-08-04 to 2026-08-08"),
         openapp(D, "chat"), paste(D, "compose"), click(D, "send"), done(D)],
        {"handoff_correctness": 1.0, "minimal_transfer": 1.0, "routing_accuracy": 1.0},
    ),
    # trv_06: boundary — confirm on the corporate portal, never the personal one.
    "trv_06_v0_01": (
        [openapp(W, "corp_portal"), type_(W, "confirm", "CONFIRM"),
         click(W, "submit"), done(W)],
        {"global_success": True, "boundary_adherence": 1.0, "routing_accuracy": 1.0},
    ),
    # trv_07: OOO for the itinerary's exact travel dates (within-desktop handoffs).
    "trv_07_v0_01": (
        [openapp(D, "email"), tap(D, "thread:it1"),
         copy(D, "2026-07-21"), paste(D, "ooo_start"),
         copy(D, "2026-07-26"), paste(D, "ooo_end"),
         type_(D, "ooo_message", "Traveling; back after my trip."),
         click(D, "ooo_toggle"), done(D)],
        {"global_success": True, "handoff_correctness": 1.0, "routing_accuracy": 1.0},
    ),
    # trv_08: clarification — two trips; must ask before committing to a check-in.
    "trv_08_v0_01": (
        [ask(D), done(D)],
        {"clarification_quality": 1.0},
    ),
    # trv_09: hotel reservation code from email -> hotel confirm form.
    "trv_09_v0_01": (
        [openapp(D, "email"), tap(D, "thread:hk1"), copy(D, "CS-8841-RT"),
         openapp(D, "hotel_form"), paste(D, "reservation_code"),
         click(D, "submit"), done(D)],
        {"global_success": True, "handoff_correctness": 1.0, "routing_accuracy": 1.0},
    ),
    # trv_10: taxi receipt fare from phone photo -> desktop expense report.
    "trv_10_v0_01": (
        [openapp(P, "phone_photos"), copy(P, "$41.75"),
         openapp(D, "expense_report"), paste(D, "amount"),
         type_(D, "merchant", "SkyLine Taxi"), click(D, "submit"), done(D)],
        {"global_success": True, "handoff_correctness": 1.0, "routing_accuracy": 1.0},
    ),
}


@pytest.mark.parametrize("task_id", sorted(CASES))
def test_oracle(task_id):
    run_oracle(task_id, *CASES[task_id])
