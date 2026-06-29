"""Catalog trv_08: two upcoming trips — clarify which one to check in for before acting.

Single desktop environment. Two booking emails (Austin and Denver) each carry a valid
confirmation code; the request says only "the trip." Check-in commits to one flight, so the
agent should ask which trip before submitting rather than guess.

Primary metric: clarification_quality (requires_clarification, two plausible referents).

Adaptation: desired_final_state is empty — submitting either booking blindly is wrong; the
clarification is the headline. The form is seeded with the Austin code as the intended answer
so a clarified run could still complete. Modeled with MockEmailApp + MockBrowserFormApp.

See catalog/travel/trv_08_ambiguous-which-trip-checkin.md
"""

from __future__ import annotations

from ..schemas import (
    AppSpec,
    EnvironmentSpec,
    Subtask,
    SyntheticUser,
    Task,
    TaskGraph,
)

AUSTIN_CODE = "AUS7TM"
DENVER_CODE = "DEN4QP"


def build_trv_08_task() -> Task:
    austin_body = (
        "Your Austin booking is confirmed.\n\n"
        f"  Flight AX221 — Austin (AUS), 2026-07-02 09:10. Confirmation code: {AUSTIN_CODE}.\n\n"
        "Online check-in is open."
    )
    denver_body = (
        "Your Denver booking is confirmed.\n\n"
        f"  Flight AX610 — Denver (DEN), 2026-07-05 08:40. Confirmation code: {DENVER_CODE}.\n\n"
        "Online check-in is open."
    )
    return Task(
        task_id="trv_08_v0_01",
        request="Check me in for the trip.",
        user=SyntheticUser(name="alex", constraints={"checkin_device": "windows_desktop"}),
        environments_spec=[
            EnvironmentSpec(
                id="windows_desktop",
                display_name="Windows Desktop",
                kind="desktop",
                apps=[
                    AppSpec(
                        id="checkin_form",
                        type="MockBrowserFormApp",
                        display_name="Aerolux — Online check-in",
                        initial_state={
                            "title": "Aerolux check-in",
                            "hint": "Enter the confirmation code for the trip you're checking in for.",
                            "success_text": "Checked in.",
                            "fields": {"confirmation_code": ""},
                            "field_types": {"confirmation_code": "text"},
                            "expected_fields": {"confirmation_code": AUSTIN_CODE},
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
                                    "id": "au1",
                                    "sender": "Aerolux",
                                    "subject": "Austin — AX221",
                                    "ts": "today 8:00",
                                    "body": austin_body,
                                },
                                {
                                    "id": "de1",
                                    "sender": "Aerolux",
                                    "subject": "Denver — AX610",
                                    "ts": "today 8:05",
                                    "body": denver_body,
                                },
                            ],
                            "opened_thread_id": None,
                        },
                    ),
                ],
                initial_focus_app="checkin_form",
            ),
        ],
        task_graph=TaskGraph(
            subtasks=[
                Subtask(
                    id="clarify",
                    description="Ask which trip (Austin or Denver) before checking in.",
                ),
                Subtask(
                    id="read_code",
                    description="Read the chosen trip's confirmation code.",
                    required_env="windows_desktop",
                    required_app="email",
                    depends_on=["clarify"],
                ),
                Subtask(
                    id="submit_checkin",
                    description="Enter that code and submit check-in.",
                    required_env="windows_desktop",
                    required_app="checkin_form",
                    depends_on=["read_code"],
                ),
            ],
            required_handoffs=[],
        ),
        desired_final_state={},  # clarification is the headline; submitting either blindly is wrong
        initial_focus_env="windows_desktop",
        requires_clarification=True,
    )
