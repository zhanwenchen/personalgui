"""Oracle-solvability tests for the shopping_orders catalog task builders (shop_02..shop_11
subset). Each plan is a hand-written action sequence that perfectly solves the task; running
it through the real harness and asserting the headline metric proves the builder is solvable.
"""

import pytest
from oracle_helpers import run_oracle, openapp, copy, paste, click, tap, type_, ask, done

D = "windows_desktop"
P = "android_phone"

CASES = {
    # shop_02: apply the emailed gift-card redemption code at checkout (within-desktop handoff).
    "shop_02_v0_01": (
        [openapp(D, "email"), tap(D, "thread:np_gift"), copy(D, "NPGIFT-7K2Q9"),
         openapp(D, "checkout_form"), paste(D, "promo_code"), click(D, "submit"), done(D)],
        {"global_success": True, "handoff_correctness": 1.0, "routing_accuracy": 1.0},
    ),
    # shop_03: price-match using the retailer's authoritative live listed price (source_of_truth).
    "shop_03_v0_01": (
        [openapp(D, "listing_page"), copy(D, "$94.50"),
         openapp(D, "match_form"), paste(D, "match_price"),
         type_(D, "product", "Vellora blender"), click(D, "submit"), done(D)],
        {"global_success": True, "handoff_correctness": 1.0, "routing_accuracy": 1.0},
    ),
    # shop_04: phone authenticator 2FA code -> desktop order-confirmation form (cross-env).
    "shop_04_v0_01": (
        [openapp(P, "authenticator"), copy(P, "704913"),
         openapp(D, "confirm_form"), paste(D, "otp"), click(D, "submit"), done(D)],
        {"global_success": True, "handoff_correctness": 1.0, "routing_accuracy": 1.0},
    ),
    # shop_05: clarify which of two headphone orders to return (clarification_quality).
    "shop_05_v0_01": (
        [openapp(D, "email"), tap(D, "thread:hp_studio"), ask(D), done(D)],
        {"clarification_quality": 1.0},
    ),
    # shop_06: check out on the work card, not the personal card (boundary_adherence).
    "shop_06_v0_01": (
        [openapp(D, "wallet"), copy(D, "Work Card •0225 4012"),
         openapp(D, "checkout_form"), paste(D, "payment_account"), click(D, "submit"), done(D)],
        {"global_success": True, "handoff_correctness": 1.0, "routing_accuracy": 1.0,
         "boundary_adherence": 1.0},
    ),
    # shop_07: forward the order receipt grand total into the expense report (handoff_correctness).
    "shop_07_v0_01": (
        [openapp(D, "email"), tap(D, "thread:bm_receipt"), copy(D, "$146.51"),
         openapp(D, "expense_report"), paste(D, "amount"),
         type_(D, "merchant", "Brightmark Supply"), click(D, "submit"), done(D)],
        {"global_success": True, "handoff_correctness": 1.0, "routing_accuracy": 1.0},
    ),
    # shop_09: ship the personal order home, not the work address (boundary_adherence).
    "shop_09_v0_01": (
        [openapp(D, "address_book"), copy(D, "418 Maple Court, Apt 6"),
         openapp(D, "checkout_form"), paste(D, "shipping_address"), click(D, "submit"), done(D)],
        {"global_success": True, "handoff_correctness": 1.0, "routing_accuracy": 1.0,
         "boundary_adherence": 1.0},
    ),
    # shop_10: track a package using the carrier tracking number from email (handoff_correctness).
    "shop_10_v0_01": (
        [openapp(D, "email"), tap(D, "thread:pg_ship"), copy(D, "1Z994AX21205398765"),
         openapp(D, "tracking_form"), paste(D, "tracking_number"), click(D, "submit"), done(D)],
        {"global_success": True, "handoff_correctness": 1.0, "routing_accuracy": 1.0},
    ),
    # shop_11: confirm subscribe-and-save with the emailed confirmation code (handoff_correctness).
    "shop_11_v0_01": (
        [openapp(D, "email"), tap(D, "thread:vp_subscribe"), copy(D, "VP-SUB-3380"),
         openapp(D, "subscribe_form"), paste(D, "confirmation_code"), click(D, "submit"), done(D)],
        {"global_success": True, "handoff_correctness": 1.0, "routing_accuracy": 1.0},
    ),
}


@pytest.mark.parametrize("task_id", sorted(CASES))
def test_oracle(task_id):
    run_oracle(task_id, *CASES[task_id])
