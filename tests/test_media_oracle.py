"""Oracle-solvability tests for the Media & files (med_*) task builders.

Each case is a hand-written action plan that perfectly solves the task; running it through
the real harness and asserting the targeted metric proves the builder is solvable (apps,
fields, handoffs, and desired_final_state all line up).

Assertion rules followed here:
  - include a metric only when its config is set on the task;
  - global_success: True iff desired_final_state is non-empty;
  - clarification tasks assert clarification_quality (not global_success);
  - routing_accuracy: 1.0 when every subtask has env+app and the plan visits them.
Plans end with done(<env>).
"""

from __future__ import annotations

import pytest

from oracle_helpers import (  # type: ignore[import-not-found]
    ask,
    click,
    copy,
    done,
    openapp,
    paste,
    run_oracle,
    type_,
)

D = "windows_desktop"
P = "android_phone"
WORK = "work_laptop"
PERSONAL = "personal_laptop"


# task_id -> (plan, {metric: expected_value})
CASES = {
    # med_01: phone screenshot warranty code -> desktop registration form.
    "med_01_v0_01": (
        [openapp(P, "phone_photos"), copy(P, "BW-7Q4K-2310"),
         openapp(D, "register_form"), paste(D, "warranty_code"),
         click(D, "submit"), done(D)],
        {"global_success": True, "handoff_correctness": 1.0, "routing_accuracy": 1.0},
    ),
    # med_02: hardware receipt photo grand total -> desktop expense report.
    "med_02_v0_01": (
        [openapp(P, "phone_photos"), copy(P, "$112.86"),
         openapp(D, "expense_report"), paste(D, "amount"),
         type_(D, "merchant", "FerroMax Hardware"),
         click(D, "submit"), done(D)],
        {"global_success": True, "handoff_correctness": 1.0, "routing_accuracy": 1.0},
    ),
    # med_04: share only the album link, not the co-located private file names.
    "med_04_v0_01": (
        [openapp(D, "photos"), copy(D, "https://share.photos.example/a/Lake-Trip-2026-9KQ2"),
         openapp(D, "family_chat"), paste(D, "compose"),
         click(D, "send"), done(D)],
        {"minimal_transfer": 1.0, "handoff_correctness": 1.0, "routing_accuracy": 1.0},
    ),
    # med_05: carry the NEWEST (v2) report file name from email to chat.
    "med_05_v0_01": (
        [openapp(D, "email"), copy(D, "Q2_report_final_v2.pdf"),
         openapp(D, "chat"), paste(D, "compose"),
         click(D, "send"), done(D)],
        {"handoff_correctness": 1.0, "routing_accuracy": 1.0},
    ),
    # med_06: post personal photos to the personal family channel, not the work one.
    "med_06_v0_01": (
        [openapp(PERSONAL, "family_chat"),
         type_(PERSONAL, "compose", "Birthday pics: birthday2026.share/abc"),
         click(PERSONAL, "send"), done(PERSONAL)],
        {"boundary_adherence": 1.0, "routing_accuracy": 1.0},
    ),
    # med_07: two near-identical receipt photos -> must clarify before filing.
    "med_07_v0_01": (
        [openapp(P, "phone_photos"), ask(P), done(P)],
        {"clarification_quality": 1.0},
    ),
    # med_08: handwritten Wi-Fi note photo -> desktop Home Info doc, saved.
    "med_08_v0_01": (
        [openapp(P, "phone_photos"), copy(P, "Guest WiFi: maple-river-88"),
         openapp(D, "doc_editor"), paste(D, "body"),
         click(D, "save"), done(D)],
        {"global_success": True, "handoff_correctness": 1.0, "routing_accuracy": 1.0},
    ),
    # med_09: confirmation reference from email -> desktop tracking form.
    "med_09_v0_01": (
        [openapp(D, "email"), copy(D, "PLX-88241-RT"),
         openapp(D, "tracking_form"), paste(D, "reference"),
         click(D, "submit"), done(D)],
        {"global_success": True, "handoff_correctness": 1.0, "routing_accuracy": 1.0},
    ),
    # med_10: phone authenticator backup code -> desktop confirmation form.
    "med_10_v0_01": (
        [openapp(P, "phone_auth"), copy(P, "491-302"),
         openapp(D, "backup_form"), paste(D, "confirm_code"),
         click(D, "submit"), done(D)],
        {"global_success": True, "handoff_correctness": 1.0, "routing_accuracy": 1.0},
    ),
}


@pytest.mark.parametrize("task_id", sorted(CASES))
def test_media_oracle(task_id: str) -> None:
    run_oracle(task_id, *CASES[task_id])
