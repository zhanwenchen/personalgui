"""Oracle-solvability tests for the finance_expenses catalog task builders (fin_01..fin_11
subset). Each plan is a hand-written action sequence that perfectly solves the task; running
it through the real harness and asserting the headline metric proves the builder is solvable.
"""

import pytest
from oracle_helpers import run_oracle, openapp, copy, paste, click, tap, type_, ask, done

D = "windows_desktop"
P = "android_phone"
L = "personal_laptop"
W = "work_laptop"

CASES = {
    # fin_01: read taxi fare on phone, file on desktop expense report.
    "fin_01_v0_01": (
        [openapp(P, "phone_photos"), copy(P, "$63.20"),
         openapp(D, "expense_report"), paste(D, "amount"),
         type_(D, "merchant", "MetroCab"), click(D, "submit"), done(D)],
        {"global_success": True, "handoff_correctness": 1.0, "routing_accuracy": 1.0},
    ),
    # fin_02: read payment reference from email, pay on portal (within-desktop handoff).
    "fin_02_v0_01": (
        [openapp(D, "email"), tap(D, "thread:brightleaf"), copy(D, "BLF-2026-77413"),
         openapp(D, "payment_portal"), paste(D, "reference"),
         type_(D, "amount", "$1,240.00"), click(D, "submit"), done(D)],
        {"global_success": True, "handoff_correctness": 1.0, "routing_accuracy": 1.0},
    ),
    # fin_03: reconcile against authoritative posted bank amount (source_of_truth).
    "fin_03_v0_01": (
        [openapp(D, "bank_statement"), copy(D, "$218.47"),
         openapp(D, "recon_form"), paste(D, "amount"),
         type_(D, "merchant", "Northwind Market"), click(D, "submit"), done(D)],
        {"global_success": True, "handoff_correctness": 1.0, "routing_accuracy": 1.0},
    ),
    # fin_04: phone 2FA code -> desktop bank portal.
    "fin_04_v0_01": (
        [openapp(P, "authenticator"), copy(P, "508134"),
         openapp(D, "bank_portal"), paste(D, "otp"), click(D, "submit"), done(D)],
        {"global_success": True, "handoff_correctness": 1.0, "routing_accuracy": 1.0},
    ),
    # fin_05: split bill — send only the total to Dana (minimal_transfer).
    "fin_05_v0_01": (
        [openapp(P, "phone_photos"), copy(P, "$96.40"),
         openapp(P, "phone_chat"), paste(P, "compose"), click(P, "send"), done(P)],
        {"handoff_correctness": 1.0, "minimal_transfer": 1.0, "routing_accuracy": 1.0},
    ),
    # fin_06: claim the per-meal cap from the policy page, not the receipt total.
    "fin_06_v0_01": (
        [openapp(D, "policy_page"), copy(D, "$75.00"),
         openapp(D, "expense_report"), paste(D, "amount"),
         type_(D, "merchant", "Harbor Grill"), click(D, "submit"), done(D)],
        {"global_success": True, "handoff_correctness": 1.0, "routing_accuracy": 1.0},
    ),
    # fin_10: claim the approved USD amount from email, not the yen receipt.
    "fin_10_v0_01": (
        [openapp(P, "phone_photos"),
         openapp(D, "email"), tap(D, "thread:finance_fx"), copy(D, "$327.85"),
         openapp(D, "expense_report"), paste(D, "amount"),
         type_(D, "merchant", "Sakura Hotel Tokyo"), click(D, "submit"), done(D)],
        {"global_success": True, "handoff_correctness": 1.0, "routing_accuracy": 1.0},
    ),
    # fin_11: claim the grand total (incl. tip), not the subtotal.
    "fin_11_v0_01": (
        [openapp(P, "phone_photos"), copy(P, "$58.10"),
         openapp(D, "expense_report"), paste(D, "amount"),
         type_(D, "merchant", "Bluebird Diner"), click(D, "submit"), done(D)],
        {"global_success": True, "handoff_correctness": 1.0, "routing_accuracy": 1.0},
    ),
}


@pytest.mark.parametrize("task_id", sorted(CASES))
def test_oracle(task_id):
    run_oracle(task_id, *CASES[task_id])
