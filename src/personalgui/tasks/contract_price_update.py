"""Task F: contract price update — document editing with external context.

The contract draft is a writable document on the desktop. The agreed price is in an
email thread (also on the desktop). The agent must read the email, find the price, and
edit the contract document to include it.

Tests cross-app read+write and the document_editor app's required_substrings save check.
"""

from __future__ import annotations

from ..schemas import (
    AppSpec,
    EnvironmentSpec,
    SyntheticUser,
    Subtask,
    Task,
    TaskGraph,
)

AGREED_PRICE = "$12,500"
CONTRACT_TEMPLATE = (
    "MASTER SERVICES AGREEMENT — DRAFT\n"
    "\n"
    "Between Cafe Roma LLC (\"Client\") and Alex Consulting (\"Provider\").\n"
    "\n"
    "1. Scope: …\n"
    "2. Term: 12 months starting on the Effective Date.\n"
    "3. Fees: The Client shall pay the Provider a flat fee of [PRICE_TBD] payable on signing.\n"
    "4. Termination: Either party may terminate with 30 days notice.\n"
    "\n"
    "Signed:\n"
    "________________________  ________________________\n"
    "Provider                  Client\n"
)


def build_contract_price_update_task(agreed_price: str = AGREED_PRICE) -> Task:
    email_body = (
        "Hi Alex,\n\n"
        f"After our call this morning we landed on {agreed_price} for the full engagement. "
        "Please update the contract draft and send it over for signing.\n\n"
        "—Pat"
    )
    return Task(
        task_id="contract_price_update_v0_01",
        request="Update the contract draft with the price we agreed on in last week's email and save it.",
        user=SyntheticUser(name="alex"),
        environments_spec=[
            EnvironmentSpec(
                id="windows_desktop",
                display_name="Windows Desktop",
                kind="desktop",
                apps=[
                    AppSpec(
                        id="document_editor",
                        type="MockDocumentEditorApp",
                        display_name="Document",
                        initial_state={
                            "title": "MSA — Cafe Roma — DRAFT",
                            "body_field": CONTRACT_TEMPLATE,
                            "status": "drafting",
                            # Save succeeds only if the body contains the agreed price.
                            "required_substrings": [agreed_price],
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
                                    "id": "pat_contract",
                                    "sender": "Pat (Cafe Roma)",
                                    "subject": "RE: engagement price",
                                    "ts": "last Thursday",
                                    "body": email_body,
                                },
                            ],
                            "opened_thread_id": None,
                        },
                    ),
                ],
                initial_focus_app="document_editor",
            ),
        ],
        task_graph=TaskGraph(
            subtasks=[
                Subtask(
                    id="read_price_from_email",
                    description="Find the agreed price in Pat's email.",
                    required_env="windows_desktop",
                    required_app="email",
                ),
                Subtask(
                    id="update_contract",
                    description="Replace the placeholder in the contract with the price and save.",
                    required_env="windows_desktop",
                    required_app="document_editor",
                    depends_on=["read_price_from_email"],
                ),
            ],
            # No required_handoff: the price is entered into a free-form document body
            # (textarea-style), so clipboard-mediated transfer is not the canonical path.
            # The required_substrings check on the document's save guarantees the
            # agreed price actually made it into the file.
            required_handoffs=[],
        ),
        desired_final_state={
            "windows_desktop.document_editor.status": "saved",
        },
        initial_focus_env="windows_desktop",
    )
