"""Catalog shop_03: submit a price-match request using the retailer's CURRENT listed price.

A stale shopping note saved last week shows a lower price ($89.99); the retailer's live
product listing now shows the authoritative current price ($94.50). The price-match form
requires the current listed price. Picking the convenient stale note fails the form match.

Adaptation: the live listing is a read-context MockBrowserFormApp exposing the current
price; a saved MockDocumentEditorApp holds the stale decoy note; the price-match
MockBrowserFormApp enforces the authoritative price + product name.

Primary metric: source_of_truth (encoded via expected_fields = authoritative live price).
Secondary: handoff_correctness, global_success.

See catalog/shopping_orders/shop_03_price_match_authoritative.md
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

LISTED_PRICE = "$94.50"  # authoritative current listing
STALE_PRICE = "$89.99"   # decoy: saved in a note last week
PRODUCT = "Vellora blender"


def build_shop_03_task(
    listed_price: str = LISTED_PRICE, stale_price: str = STALE_PRICE, product: str = PRODUCT
) -> Task:
    return Task(
        task_id="shop_03_v0_01",
        request="Submit a price-match request for the Vellora blender at the price it's listed at now.",
        user=SyntheticUser(
            name="alex",
            constraints={"authoritative_source": "live_listing"},
        ),
        environments_spec=[
            EnvironmentSpec(
                id="windows_desktop",
                display_name="Windows Desktop",
                kind="desktop",
                apps=[
                    AppSpec(
                        id="shopping_note",
                        type="MockDocumentEditorApp",
                        display_name="Shopping Note",
                        initial_state={
                            "title": "Shopping Note",
                            # Stale decoy: the lower, more appealing price saved last week.
                            "body_field": f"Shopping note: {product} {stale_price} (saw it last week)",
                            "status": "saved",
                        },
                    ),
                    AppSpec(
                        id="listing_page",
                        type="MockBrowserFormApp",
                        display_name="Vellora — Product page",
                        initial_state={
                            # Read-context page: shows the current listed price. View-only;
                            # the agent copies the authoritative price from here.
                            "title": f"{product} — product page",
                            "hint": f"Current price: {listed_price}",
                            "fields": {"listed_price": listed_price},
                            "field_types": {"listed_price": "text"},
                            "expected_fields": {},
                            "buttons": [],
                            "status": "drafting",
                        },
                    ),
                    AppSpec(
                        id="match_form",
                        type="MockBrowserFormApp",
                        display_name="Price-match request",
                        initial_state={
                            "title": "Price-match request",
                            "hint": "Enter the product and its currently listed price.",
                            "success_text": "Price-match request submitted.",
                            "fields": {"match_price": "", "product": ""},
                            "field_types": {"match_price": "text", "product": "text"},
                            "expected_fields": {"match_price": listed_price, "product": product},
                            "buttons": ["submit"],
                            "status": "drafting",
                        },
                    ),
                ],
                # Focus the stale note first, so the convenient (wrong) price is seen first.
                initial_focus_app="shopping_note",
            ),
        ],
        task_graph=TaskGraph(
            subtasks=[
                Subtask(
                    id="read_listed",
                    description="Read the current listed price from the live product page (not the stale note).",
                    required_env="windows_desktop",
                    required_app="listing_page",
                ),
                Subtask(
                    id="submit_match",
                    description="Enter the listed price + product on the price-match form and submit.",
                    required_env="windows_desktop",
                    required_app="match_form",
                    depends_on=["read_listed"],
                ),
            ],
            required_handoffs=[
                HandoffRequirement(
                    artifact_type="price",
                    from_env="windows_desktop",
                    to_env="windows_desktop",
                    expected_value=listed_price,
                ),
            ],
        ),
        desired_final_state={
            "windows_desktop.match_form.status": "submitted",
        },
        initial_focus_env="windows_desktop",
    )
