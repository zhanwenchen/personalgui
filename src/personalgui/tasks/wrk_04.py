"""Catalog wrk_04: copy the negotiated discount RATE (a percentage) from a signed renewal
quote into a pricing-approval web form and submit. A dollar list price and per-seat price
sit in the same block as a tempting wrong value.

Primary metric: handoff_correctness — the exact rate "17.5%" must cross the quote doc into
the form's discount_rate field.
Secondary: global_success (form status flips to submitted when every expected field
matches), routing_accuracy (both subtasks on the work laptop).

Distinct from contract_price_update: web form vs doc body, a percentage vs a flat fee,
different field name.

See catalog/work_docs_projects/wrk_04_quote_into_pricing_form.md
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

DISCOUNT_RATE = "17.5%"
CUSTOMER = "Northwind"

QUOTE_BODY = (
    "Northwind Renewal — Signed Quote\n\n"
    "List price: $48,000/yr\n"
    "Per-seat price: $240\n"
    "Negotiated discount: 17.5% off list (applies to all seats)\n\n"
    "Countersigned 2026-06-20.\n"
)


def build_wrk_04_task(discount_rate: str = DISCOUNT_RATE, customer: str = CUSTOMER) -> Task:
    return Task(
        task_id="wrk_04_v0_01",
        request=(
            "The renewal quote lists the discount we offered — enter that discount rate "
            "into the pricing approval form and submit."
        ),
        user=SyntheticUser(
            name="alex",
            constraints={"work_account": "alex@northwind.example"},
        ),
        environments_spec=[
            EnvironmentSpec(
                id="windows_desktop",
                display_name="Work Laptop",
                kind="desktop",
                apps=[
                    AppSpec(
                        id="quote_doc",
                        type="MockDocumentEditorApp",
                        display_name="Northwind Renewal — Signed Quote",
                        initial_state={
                            "title": "Northwind Renewal — Signed Quote",
                            "body_field": QUOTE_BODY,
                            "status": "saved",
                        },
                    ),
                    AppSpec(
                        id="pricing_form",
                        type="MockBrowserFormApp",
                        display_name="Pricing Approval",
                        initial_state={
                            "title": "Pricing Approval",
                            "hint": "Enter the negotiated discount rate and customer.",
                            "success_text": "Pricing approval submitted.",
                            "fields": {"discount_rate": "", "customer": ""},
                            "field_types": {"discount_rate": "text", "customer": "text"},
                            "expected_fields": {
                                "discount_rate": discount_rate,
                                "customer": customer,
                            },
                            "buttons": ["submit"],
                            "status": "drafting",
                        },
                    ),
                ],
                initial_focus_app="quote_doc",
            ),
        ],
        task_graph=TaskGraph(
            subtasks=[
                Subtask(
                    id="read_discount",
                    description="Find the negotiated discount rate in the quote doc.",
                    required_env="windows_desktop",
                    required_app="quote_doc",
                ),
                Subtask(
                    id="submit_form",
                    description="Enter the rate (and customer) in the approval form and submit.",
                    required_env="windows_desktop",
                    required_app="pricing_form",
                    depends_on=["read_discount"],
                ),
            ],
            required_handoffs=[
                HandoffRequirement(
                    artifact_type="discount_rate",
                    from_env="windows_desktop",
                    to_env="windows_desktop",
                    expected_value=discount_rate,
                ),
            ],
        ),
        desired_final_state={
            "windows_desktop.pricing_form.status": "submitted",
        },
        initial_focus_env="windows_desktop",
    )
