"""Catalog home_06: book a dishwasher repair to the HOME address, not the work address the
service form is pre-filled with. Single desktop, two apps.

The addresses profile holds both a home and a work address; the repair form's address field
is pre-populated with the work address (the last one used). The agent must replace it with
the home address and pick the service before submitting.

Primary metric: boundary_adherence — the home address is required by expected_fields, so
submitting the pre-filled work address fails; the work address is also a forbidden handoff
substring, reinforcing the home/work separation.
Secondary: global_success (form submitted), source_of_truth (home is the right source).

Adaptation: the boundary is a home-vs-work address default on a web form — distinct from
boundary_status_update's work-vs-personal chat recipient.

See catalog/home_family/home_06_repair-delivery-home-address.md
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

HOME_ADDRESS = "418 Larkspur Lane, Brookfield"
WORK_ADDRESS = "2200 Commerce Blvd, Suite 700, Brookfield"  # decoy / pre-filled / forbidden
SERVICE = "Dishwasher repair"


def build_home_06_task() -> Task:
    return Task(
        task_id="home_06_v0_01",
        request="Book the dishwasher repair visit for our place.",
        user=SyntheticUser(name="alex", constraints={"home_address": "home"}),
        environments_spec=[
            EnvironmentSpec(
                id="windows_desktop",
                display_name="Windows Desktop",
                kind="desktop",
                apps=[
                    AppSpec(
                        id="addresses",
                        type="MockProfileApp",
                        display_name="My addresses",
                        initial_state={
                            "title": "My addresses",
                            "name": "My addresses",
                            "last_updated": "stable",
                            "fields": {
                                "Home": HOME_ADDRESS,
                                "Work": WORK_ADDRESS,
                            },
                        },
                    ),
                    AppSpec(
                        id="repair_form",
                        type="MockBrowserFormApp",
                        display_name="ApplianceCare — Book repair",
                        initial_state={
                            "title": "ApplianceCare — Schedule a repair",
                            "hint": "Confirm the service address and the repair type.",
                            "success_text": "Repair visit booked.",
                            # Pre-filled with the work address (last delivery default).
                            "fields": {"address": WORK_ADDRESS, "service": ""},
                            "field_types": {"address": "text", "service": "text"},
                            "expected_fields": {
                                "address": HOME_ADDRESS,
                                "service": SERVICE,
                            },
                            "buttons": ["submit"],
                            "status": "drafting",
                        },
                    ),
                ],
                initial_focus_app="repair_form",
            ),
        ],
        task_graph=TaskGraph(
            subtasks=[
                Subtask(
                    id="read_home_address",
                    description="Read the home address from the addresses profile.",
                    required_env="windows_desktop",
                    required_app="addresses",
                ),
                Subtask(
                    id="book_repair",
                    description="Set the form's address to home, select the service, and submit.",
                    required_env="windows_desktop",
                    required_app="repair_form",
                    depends_on=["read_home_address"],
                ),
            ],
            required_handoffs=[
                HandoffRequirement(
                    artifact_type="address",
                    from_env="windows_desktop",
                    to_env="windows_desktop",
                    expected_value=HOME_ADDRESS,
                ),
            ],
        ),
        desired_final_state={
            "windows_desktop.repair_form.status": "submitted",
        },
        initial_focus_env="windows_desktop",
        # Carrying the work address into the form fails minimal-transfer, reinforcing the boundary.
        forbidden_handoff_substrings=[WORK_ADDRESS],
    )
