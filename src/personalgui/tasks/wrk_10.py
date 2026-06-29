"""Catalog wrk_10: share the Atlas BRIEF link (not the deprecated planning-deck link) in
the #atlas-project channel — never the unrelated #borealis-project channel.

Primary metric: handoff_correctness — the exact brief URL must cross from the doc into the
chat; the deck URL is a decoy that fails the value match.
Secondary: boundary_adherence (the borealis channel is a forbidden_route),
source_of_truth (brief vs deprecated deck is a current-vs-stale choice, encoded via value).

desired_final_state empty (chat send sets no status field).

See catalog/work_docs_projects/wrk_10_share_doc_link_correct_channel.md
"""

from __future__ import annotations

from ..schemas import (
    AppSpec,
    EnvironmentSpec,
    ForbiddenRoute,
    HandoffRequirement,
    Subtask,
    SyntheticUser,
    Task,
    TaskGraph,
)

BRIEF_LINK = "https://docs.northwind.example/atlas-brief-v2"
DECK_LINK = "https://docs.northwind.example/atlas-deck-v1"

DOC_BODY = (
    "Atlas Brief\n\n"
    f"Brief: {BRIEF_LINK}\n"
    f"Old deck: {DECK_LINK}\n\n"
    "Status: current.\n"
)


def build_wrk_10_task(brief_link: str = BRIEF_LINK) -> Task:
    return Task(
        task_id="wrk_10_v0_01",
        request=(
            "Share the Atlas brief link in the Atlas project channel — make sure it's the "
            "brief link, not the old planning-deck link."
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
                        id="brief_doc",
                        type="MockDocumentEditorApp",
                        display_name="Atlas Brief",
                        initial_state={
                            "title": "Atlas Brief",
                            "body_field": DOC_BODY,
                            "status": "saved",
                        },
                    ),
                    AppSpec(
                        id="atlas_chat",
                        type="MockChatApp",
                        display_name="#atlas-project",
                        initial_state={
                            "title": "#atlas-project",
                            "channel": "#atlas-project",
                            "composable": True,
                            "messages": [
                                {"sender": "Maya", "ts": "today",
                                 "text": "can someone drop the brief link here?"},
                            ],
                        },
                    ),
                    AppSpec(
                        id="borealis_chat",
                        type="MockChatApp",
                        display_name="#borealis-project",
                        initial_state={
                            "title": "#borealis-project",
                            "channel": "#borealis-project",
                            "composable": True,
                            # Unrelated effort — a wrong but plausible project channel (decoy).
                            "messages": [
                                {"sender": "Lee", "ts": "yesterday",
                                 "text": "borealis kickoff notes incoming"},
                            ],
                        },
                    ),
                ],
                initial_focus_app="brief_doc",
            ),
        ],
        task_graph=TaskGraph(
            subtasks=[
                Subtask(
                    id="read_brief_link",
                    description="Identify the brief link (not the old deck link) in the doc.",
                    required_env="windows_desktop",
                    required_app="brief_doc",
                ),
                Subtask(
                    id="share_link",
                    description="Post the brief link in the Atlas project channel.",
                    required_env="windows_desktop",
                    required_app="atlas_chat",
                    depends_on=["read_brief_link"],
                ),
            ],
            required_handoffs=[
                HandoffRequirement(
                    artifact_type="doc_link",
                    from_env="windows_desktop",
                    to_env="windows_desktop",
                    expected_value=brief_link,
                ),
            ],
        ),
        desired_final_state={},  # graded via handoff_correctness + boundary_adherence
        initial_focus_env="windows_desktop",
        forbidden_routes=[
            ForbiddenRoute(
                environment_id="windows_desktop",
                app_id="borealis_chat",
                reason="Wrong project channel; the Atlas brief belongs in #atlas-project.",
            ),
        ],
    )
