"""Catalog shop_02: apply the emailed gift-card redemption code at checkout.

The gift-card email shows both a short redemption code (what the promo field accepts) and a
longer card number that looks more like the "real" gift card. A within-desktop handoff:
copy the redemption code from the email, paste it into the checkout promo field, submit.

Adaptation: MockEmailApp thread embeds the redemption code next to a decoy card number;
MockBrowserFormApp's `promo_code` field requires the exact redemption code.

Primary metric: handoff_correctness. Secondary: global_success, routing_accuracy.

See catalog/shopping_orders/shop_02_giftcard_promo_checkout.md
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

REDEMPTION_CODE = "NPGIFT-7K2Q9"
CARD_NUMBER = "6011-2200-4417-8890"  # decoy: looks like the "real" gift card


def build_shop_02_task(
    redemption_code: str = REDEMPTION_CODE, card_number: str = CARD_NUMBER
) -> Task:
    email_body = (
        "Thanks for your gift! Here are your $50 Northport gift card details:\n\n"
        f"  Redemption code: {redemption_code}\n"
        f"  Card number: {card_number}\n"
        "  Balance: $50.00\n\n"
        "Enter the redemption code in the gift card / promo field at checkout."
    )
    return Task(
        task_id="shop_02_v0_01",
        request="Apply my Northport gift card at checkout — the code is in the email they sent.",
        user=SyntheticUser(name="alex"),
        environments_spec=[
            EnvironmentSpec(
                id="windows_desktop",
                display_name="Windows Desktop",
                kind="desktop",
                apps=[
                    AppSpec(
                        id="checkout_form",
                        type="MockBrowserFormApp",
                        display_name="Northport — Checkout",
                        initial_state={
                            "title": "Northport checkout",
                            "hint": "Enter your gift card / promo code.",
                            "success_text": "Gift card applied. $50.00 off.",
                            "fields": {"promo_code": ""},
                            "field_types": {"promo_code": "text"},
                            "expected_fields": {"promo_code": redemption_code},
                            "buttons": ["submit"],
                            "status": "drafting",
                        },
                    ),
                    AppSpec(
                        id="email",
                        type="MockEmailApp",
                        display_name="Email",
                        initial_state={
                            "title": "Email",
                            "threads": [
                                {
                                    "id": "np_gift",
                                    "sender": "Northport Outfitters",
                                    "subject": "Your $50 gift card",
                                    "ts": "today 10:15",
                                    "body": email_body,
                                },
                            ],
                            "opened_thread_id": None,
                        },
                    ),
                ],
                initial_focus_app="checkout_form",
            ),
        ],
        task_graph=TaskGraph(
            subtasks=[
                Subtask(
                    id="read_code",
                    description="Open the gift-card email and read the redemption code (not the card number).",
                    required_env="windows_desktop",
                    required_app="email",
                ),
                Subtask(
                    id="apply_code",
                    description="Enter the redemption code in the checkout form and submit.",
                    required_env="windows_desktop",
                    required_app="checkout_form",
                    depends_on=["read_code"],
                ),
            ],
            required_handoffs=[
                HandoffRequirement(
                    artifact_type="promo_code",
                    from_env="windows_desktop",
                    to_env="windows_desktop",
                    expected_value=redemption_code,
                ),
            ],
        ),
        desired_final_state={
            "windows_desktop.checkout_form.status": "submitted",
        },
        initial_focus_env="windows_desktop",
    )
