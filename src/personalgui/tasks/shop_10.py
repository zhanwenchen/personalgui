"""Catalog shop_10: track a package using the carrier tracking number from the shipping email.

The shipping email shows the long carrier tracking number alongside the shorter, friendlier
order number. The carrier's tracking form accepts only the tracking number; the order number is
rejected, and re-typing the long number risks character drift. A within-desktop handoff: copy
the tracking number from the email, paste into the carrier form, submit.

Adaptation: MockEmailApp shipping thread embeds the tracking number beside a decoy order
number; MockBrowserFormApp's `tracking_number` field requires the exact tracking number.

Primary metric: handoff_correctness. Secondary: global_success, routing_accuracy.

See catalog/shopping_orders/shop_10_track_package.md
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

TRACKING_NUMBER = "1Z994AX21205398765"
ORDER_NUMBER = "PG-3320"  # decoy: shorter, friendlier, rejected by the carrier form


def build_shop_10_task(
    tracking_number: str = TRACKING_NUMBER, order_number: str = ORDER_NUMBER
) -> Task:
    email_body = (
        "Good news — your Pinegrove Home order is on its way!\n\n"
        f"  Carrier: Meridian Freight\n"
        f"  Tracking number: {tracking_number}\n"
        f"  Order #: {order_number}\n\n"
        "Enter the tracking number on the carrier's site to see delivery status."
    )
    return Task(
        task_id="shop_10_v0_01",
        request="Track my Pinegrove order — the tracking number is in the shipping email.",
        user=SyntheticUser(name="alex"),
        environments_spec=[
            EnvironmentSpec(
                id="windows_desktop",
                display_name="Windows Desktop",
                kind="desktop",
                apps=[
                    AppSpec(
                        id="tracking_form",
                        type="MockBrowserFormApp",
                        display_name="Meridian Freight — Track",
                        initial_state={
                            "title": "Meridian Freight — Track a package",
                            "hint": "Enter your tracking number.",
                            "success_text": "Tracking found. In transit.",
                            "fields": {"tracking_number": ""},
                            "field_types": {"tracking_number": "text"},
                            "expected_fields": {"tracking_number": tracking_number},
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
                                    "id": "pg_ship",
                                    "sender": "Pinegrove Home",
                                    "subject": "Your order has shipped",
                                    "ts": "today 7:50",
                                    "body": email_body,
                                },
                            ],
                            "opened_thread_id": None,
                        },
                    ),
                ],
                initial_focus_app="tracking_form",
            ),
        ],
        task_graph=TaskGraph(
            subtasks=[
                Subtask(
                    id="read_tracking",
                    description="Open the shipping email and read the tracking number (not the order number).",
                    required_env="windows_desktop",
                    required_app="email",
                ),
                Subtask(
                    id="submit_tracking",
                    description="Paste the tracking number into the carrier form and submit.",
                    required_env="windows_desktop",
                    required_app="tracking_form",
                    depends_on=["read_tracking"],
                ),
            ],
            required_handoffs=[
                HandoffRequirement(
                    artifact_type="tracking_number",
                    from_env="windows_desktop",
                    to_env="windows_desktop",
                    expected_value=tracking_number,
                ),
            ],
        ),
        desired_final_state={
            "windows_desktop.tracking_form.status": "submitted",
        },
        initial_focus_env="windows_desktop",
    )
