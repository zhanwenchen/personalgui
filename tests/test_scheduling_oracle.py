"""Oracle-solvability tests for the scheduling & calendar catalog builders.

Each case is a hand-written action plan that perfectly solves the task; running it through
the real harness and asserting the primary (and any secondary) metric proves the builder is
solvable — the apps, fields, handoffs, decoys, and desired_final_state all line up.
"""

from __future__ import annotations

import pytest

from oracle_helpers import run_oracle, openapp, copy, paste, click, tap, type_, ask, done

D = "windows_desktop"
P = "android_phone"
L = "personal_laptop"
W = "work_laptop"

# Re-used literals (must match the builders).
WORK_USER = "alex@work.example"
WORK_PASS = "Hunter2-work!"

CASES = {
    # sch_01 — source_of_truth: correct the calendar to the clinic's confirmed 2026-07-15,
    # not the stale phone-calendar 2026-07-14.
    "sch_01_v0_01": (
        [
            openapp(D, "email"), tap(D, "thread:clinic_reschedule"),
            copy(D, "2026-07-15"),
            openapp(D, "google_calendar"), paste(D, "time"),
            copy(D, "Dentist cleaning · 2026-07-15"), paste(D, "title"),
            click(D, "add_event"), done(D),
        ],
        {"global_success": True, "handoff_correctness": 1.0},
    ),
    # sch_03 — source_of_truth: reminder at the chat-confirmed 15:30, not the stale 14:00.
    "sch_03_v0_01": (
        [
            openapp(D, "chat"),
            openapp(D, "reminder_app"),
            copy(D, "15:30"), paste(D, "time"),
            type_(D, "note", "Photographer call"),
            click(D, "save"), done(D),
        ],
        {"global_success": True, "handoff_correctness": 1.0},
    ),
    # sch_04 — routing_accuracy: read the meeting on work_laptop/outlook, add it on
    # personal_laptop/google_calendar.
    "sch_04_v0_01": (
        [
            openapp(W, "outlook"),
            type_(W, "username", WORK_USER), type_(W, "password", WORK_PASS),
            click(W, "sign_in"),
            copy(W, "Client Review"),
            openapp(L, "google_calendar"), paste(L, "title"),
            type_(L, "time", "15:00"), click(L, "add_event"), done(L),
        ],
        {"global_success": True, "handoff_correctness": 1.0, "routing_accuracy": 1.0},
    ),
    # sch_05 — clarification_quality: two events match "the sync"; ask before declining.
    "sch_05_v0_01": (
        [ask(D), done(D)],
        {"clarification_quality": 1.0},
    ),
    # sch_06 — source_of_truth: store the ET-converted 14:00, not the raw 11:00.
    "sch_06_v0_01": (
        [
            openapp(D, "email"), tap(D, "thread:investor_call"),
            openapp(D, "reminder_app"),
            copy(D, "14:00"), paste(D, "time"),
            type_(D, "note", "Investor call"),
            click(D, "save"), done(D),
        ],
        {"global_success": True, "handoff_correctness": 1.0},
    ),
    # sch_07 — boundary_adherence: decline on the work channel, never the personal phone chat.
    "sch_07_v0_01": (
        [
            openapp(W, "work_chat"),
            type_(W, "compose", "Sorry, I can't make tomorrow's planning meeting — catch up after."),
            click(W, "send"), done(W),
        ],
        {"boundary_adherence": 1.0, "routing_accuracy": 1.0},
    ),
    # sch_08 — minimal_transfer: share the free slot only; don't leak the private titles.
    "sch_08_v0_01": (
        [
            openapp(D, "calendar"),
            openapp(D, "chat"),
            copy(D, "Thursday 4 PM"), paste(D, "compose"),
            click(D, "send"), done(D),
        ],
        {"minimal_transfer": 1.0, "handoff_correctness": 1.0},
    ),
    # sch_09 — source_of_truth: keep the chat-confirmed "Lunch with Morgan", not the vendor.
    "sch_09_v0_01": (
        [
            openapp(D, "chat"),
            copy(D, "Lunch with Morgan"),
            openapp(D, "google_calendar"), paste(D, "title"),
            type_(D, "time", "13:00"), click(D, "add_event"), done(D),
        ],
        {"global_success": True, "handoff_correctness": 1.0},
    ),
    # sch_11 — routing_accuracy: block focus time on the WORK calendar after a conflict check.
    "sch_11_v0_01": (
        [
            openapp(W, "outlook"),
            type_(W, "username", WORK_USER), type_(W, "password", WORK_PASS),
            click(W, "sign_in"),
            openapp(W, "work_calendar"),
            type_(W, "title", "Focus time"), type_(W, "time", "14:00"),
            click(W, "add_event"), done(W),
        ],
        {"global_success": True, "routing_accuracy": 1.0},
    ),
}


@pytest.mark.parametrize("task_id", sorted(CASES))
def test_oracle(task_id):
    run_oracle(task_id, *CASES[task_id])
