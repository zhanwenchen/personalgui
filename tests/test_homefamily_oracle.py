"""Oracle-solvability tests for the home_family catalog task builders.

Each case is a hand-written action plan run through the real harness, asserting the metric(s)
the task's config targets. A metric is asserted only when its config is set:
  - global_success: True iff desired_final_state is non-empty
  - handoff_correctness: when required_handoffs carry an expected_value
  - routing_accuracy: when subtasks carry required_env + required_app and the plan visits them
  - boundary_adherence: when forbidden_routes is set
  - minimal_transfer: when forbidden_handoff_substrings is set
  - clarification_quality: when requires_clarification is True (instead of global_success)
"""

from __future__ import annotations

import pytest

from oracle_helpers import (
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


# task_id -> (plan, {metric: expected_value})
CASES = {
    # home_01: within-desktop handoff of the account number into the utility payment form.
    "home_01_v0_01": (
        [openapp(D, "email"), copy(D, "RP-4471-2208"),
         openapp(D, "payment_portal"), paste(D, "account"),
         type_(D, "amount", "$138.42"), click(D, "submit"), done(D)],
        {"global_success": True, "handoff_correctness": 1.0, "routing_accuracy": 1.0},
    ),
    # home_02: boundary — add the item to the shared channel, not the private note.
    "home_02_v0_01": (
        [openapp(P, "family_groceries"), type_(P, "compose", "oat milk"),
         click(P, "send"), done(P)],
        {"boundary_adherence": 1.0, "routing_accuracy": 1.0},
    ),
    # home_03: source-of-truth — reminder at the emailed 18:45, not the stale calendar time.
    "home_03_v0_01": (
        [openapp(D, "email"), copy(D, "6:45 PM"),
         openapp(D, "reminder_app"), paste(D, "note"),
         type_(D, "time", "18:45"), click(D, "save"), done(D)],
        {"global_success": True, "handoff_correctness": 1.0, "routing_accuracy": 1.0},
    ),
    # home_04: clarification — ask which child's recital before saving anything.
    "home_04_v0_01": (
        [ask(D), done(D)],
        {"clarification_quality": 1.0},
    ),
    # home_05: minimal-transfer — send only the Wi-Fi password to the guest chat.
    "home_05_v0_01": (
        [openapp(P, "saved_passwords"), copy(P, "maple-otter-1492"),
         openapp(P, "guest_chat"), paste(P, "compose"), click(P, "send"), done(P)],
        {"handoff_correctness": 1.0, "minimal_transfer": 1.0, "routing_accuracy": 1.0},
    ),
    # home_06: boundary — book to the home address, overwriting the work-address prefill.
    "home_06_v0_01": (
        [openapp(D, "addresses"), copy(D, "418 Larkspur Lane, Brookfield"),
         openapp(D, "repair_form"), paste(D, "address"),
         type_(D, "service", "Dishwasher repair"), click(D, "submit"), done(D)],
        {"global_success": True, "handoff_correctness": 1.0,
         "minimal_transfer": 1.0, "routing_accuracy": 1.0},
    ),
    # home_07: handoff — forward only the confirmation code to Robin's chat.
    "home_07_v0_01": (
        [openapp(D, "email"), copy(D, "FT-7C29K"),
         openapp(D, "robin_chat"), paste(D, "compose"), click(D, "send"), done(D)],
        {"handoff_correctness": 1.0, "minimal_transfer": 1.0, "routing_accuracy": 1.0},
    ),
    # home_09: source-of-truth — text the babysitter's current number, not the stale one.
    "home_09_v0_01": (
        [openapp(D, "sitter_profile"), copy(D, "+1-555-0640"),
         openapp(D, "desktop_chat"), paste(D, "compose"), click(D, "send"), done(D)],
        {"handoff_correctness": 1.0, "minimal_transfer": 1.0, "routing_accuracy": 1.0},
    ),
    # home_10: routing — add the family event to the personal Google calendar.
    "home_10_v0_01": (
        [openapp(D, "email"), copy(D, "Grandma's birthday dinner"),
         openapp(D, "personal_calendar"), paste(D, "title"),
         type_(D, "time", "18:30"), click(D, "add_event"), done(D)],
        {"global_success": True, "handoff_correctness": 1.0, "routing_accuracy": 1.0},
    ),
    # home_11: cross-device handoff — phone text code into the desktop service portal.
    "home_11_v0_01": (
        [openapp(P, "phone_messages"), copy(P, "PLM-58213"),
         openapp(D, "service_portal"), paste(D, "code"), click(D, "submit"), done(D)],
        {"global_success": True, "handoff_correctness": 1.0, "routing_accuracy": 1.0},
    ),
}


@pytest.mark.parametrize("task_id", sorted(CASES))
def test_oracle(task_id: str) -> None:
    plan, expected = CASES[task_id]
    run_oracle(task_id, plan, expected)
