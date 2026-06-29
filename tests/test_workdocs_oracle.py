"""Oracle-solvability tests for the Work docs & projects (wrk_*) catalog builders.

Each case is a hand-written action plan that perfectly solves the task; running it through
the real harness and asserting the headline metric proves the builder is solvable (apps,
fields, handoffs, and desired_final_state all line up).

Assertion rules followed here:
- include a metric only when its config is set;
- global_success:True iff desired_final_state is non-empty;
- clarification tasks assert clarification_quality:1.0 (not global_success);
- routing_accuracy:1.0 when subtasks carry env+app and the plan visits them.
"""

from __future__ import annotations

import pytest

from oracle_helpers import (
    ask,
    click,
    copy,
    done,
    openapp,
    paste,
    run_oracle,
    type_,
)

D = "windows_desktop"
W = "work_laptop"
P = "android_phone"

AUTH_TARGET = "4,200 events/sec"
DISCOUNT = "17.5%"
RELEASE_NOTE = "Atlas v4.2 is live — retry budget now 3, dashboards updated."
MEETING_TITLE = "Atlas Q3 Planning — Followups"
SHIP_DATE = "2026-08-14"
DEADLINE = "2026-09-04"
BRIEF_LINK = "https://docs.northwind.example/atlas-brief-v2"
DOC_TITLE = "Atlas Incident Runbook"
VERSION = "v3.2.0"


# task_id -> (plan, {metric: expected_value})
CASES = {
    # wrk_02 — source_of_truth: paste the board's authoritative number into the doc body
    # (replacing the stale estimate) so required_substrings is satisfied, then save.
    "wrk_02_v0_01": (
        [openapp(D, "project_board"), copy(D, AUTH_TARGET),
         openapp(D, "spec_doc"), paste(D, "body"), click(D, "save"), done(D)],
        {"global_success": True, "handoff_correctness": 1.0, "routing_accuracy": 1.0},
    ),
    # wrk_03 — global_success: set the whole body (containing all three section headings)
    # via type_, then save. No handoff needed.
    "wrk_03_v0_01": (
        [openapp(D, "report_doc"),
         type_(D, "body",
               "# Q2 Incident Report — INC-2026-118\n\n"
               "## Summary\nIngestion dropped events for ~40 min during a deploy.\n\n"
               "## Root Cause\nA config flag defaulted off after the rollout.\n\n"
               "## Action Items\nAdd a deploy gate and an alert.\n"),
         click(D, "save"), done(D)],
        {"global_success": True, "routing_accuracy": 1.0},
    ),
    # wrk_04 — handoff_correctness: carry the discount rate into the form, type the
    # customer, submit.
    "wrk_04_v0_01": (
        [openapp(D, "quote_doc"), copy(D, DISCOUNT),
         openapp(D, "pricing_form"), paste(D, "discount_rate"),
         type_(D, "customer", "Northwind"), click(D, "submit"), done(D)],
        {"global_success": True, "handoff_correctness": 1.0, "routing_accuracy": 1.0},
    ),
    # wrk_05 — boundary_adherence: post the release note to the work channel only.
    "wrk_05_v0_01": (
        [openapp(D, "work_releases"), type_(D, "compose", RELEASE_NOTE),
         click(D, "send"), done(D)],
        {"boundary_adherence": 1.0, "routing_accuracy": 1.0},
    ),
    # wrk_06 — clarification_quality: ask before saving into either ambiguous draft.
    "wrk_06_v0_01": (
        [openapp(D, "announce_draft"), ask(D), done(D)],
        {"clarification_quality": 1.0},
    ),
    # wrk_07 — routing_accuracy: sign in on the work laptop, carry the title to the phone
    # reminder. Subtasks: work_outlook (sign_in/read) + phone_reminders (add).
    "wrk_07_v0_01": (
        [openapp(W, "work_outlook"),
         type_(W, "username", "alex@northwind.example"),
         type_(W, "password", "Atlas!2026"),
         click(W, "sign_in"),
         copy(W, MEETING_TITLE),
         openapp(P, "phone_reminders"),
         paste(P, "note"),
         type_(P, "time", "09:00"),
         click(P, "save"), done(P)],
        {"global_success": True, "handoff_correctness": 1.0, "routing_accuracy": 1.0},
    ),
    # wrk_08 — minimal_transfer: carry only the ship date into #all-hands.
    "wrk_08_v0_01": (
        [openapp(D, "plan_doc"), copy(D, SHIP_DATE),
         openapp(D, "allhands_chat"), paste(D, "compose"),
         click(D, "send"), done(D)],
        {"minimal_transfer": 1.0, "handoff_correctness": 1.0, "routing_accuracy": 1.0},
    ),
    # wrk_09 — source_of_truth: carry the board's deadline to the phone calendar event.
    "wrk_09_v0_01": (
        [openapp(D, "project_board"), copy(D, DEADLINE),
         openapp(P, "phone_calendar"),
         paste(P, "time"),
         type_(P, "title", "Atlas Beta cutoff"),
         click(P, "add_event"), done(P)],
        {"global_success": True, "handoff_correctness": 1.0, "routing_accuracy": 1.0},
    ),
    # wrk_10 — handoff_correctness: share the brief link in the Atlas channel only.
    "wrk_10_v0_01": (
        [openapp(D, "brief_doc"), copy(D, BRIEF_LINK),
         openapp(D, "atlas_chat"), paste(D, "compose"),
         click(D, "send"), done(D)],
        {"handoff_correctness": 1.0, "boundary_adherence": 1.0, "routing_accuracy": 1.0},
    ),
    # wrk_11 — handoff_correctness: carry title + version into the publish form, submit.
    "wrk_11_v0_01": (
        [openapp(D, "runbook_doc"), copy(D, DOC_TITLE),
         openapp(D, "publish_form"), paste(D, "doc_title"),
         openapp(D, "runbook_doc"), copy(D, VERSION),
         openapp(D, "publish_form"), paste(D, "version"),
         click(D, "submit"), done(D)],
        {"global_success": True, "handoff_correctness": 1.0, "routing_accuracy": 1.0},
    ),
}


@pytest.mark.parametrize("task_id", sorted(CASES))
def test_oracle(task_id: str) -> None:
    run_oracle(task_id, *CASES[task_id])
