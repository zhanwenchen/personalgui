"""Guards that the whole catalog is runnable.

- No task module fails to import or build (DISCOVERY_ERRORS empty).
- Every catalog/<domain>/*.md task has a registered builder.

The 12 first-batch + 5 new-app builders use semantic task_ids (mapped below); every other
catalog id <id> maps to task_id "<id>_v0_01".
"""

from __future__ import annotations

import re
from pathlib import Path

from personalgui.tasks import DISCOVERY_ERRORS, TASK_REGISTRY

CATALOG = Path(__file__).resolve().parents[1] / "catalog"

# catalog id -> task_id for the builders that use a semantic (non-"<id>_v0_01") task_id
SEMANTIC = {
    "fin_07": "subscription_cancel_code_v0_01",
    "fin_08": "reimbursement_work_chat_only_v0_01",
    "fin_09": "which_lunch_expense_v0_01",
    "sch_02": "ooo_from_approval_v0_01",
    "sec_03": "new_account_two_codes_v0_01",
    "sec_07": "authenticator_vs_sms_v0_01",
    "com_04": "relay_code_to_support_chat_v0_01",
    "wrk_01": "reviewer_comment_into_doc_v0_01",
    "shop_01": "return_rma_code_v0_01",
    "shop_08": "coupon_not_card_number_v0_01",
    "hlth_10": "copay_reference_number_v0_01",
    "home_08": "rent_transfer_2fa_v0_01",
    "sch_10": "invite_photo_to_calendar_v0_01",
    "trv_11": "boarding_pass_print_v0_01",
    "sec_11": "enroll_authenticator_v0_01",
    "med_03": "boarding_pass_to_editor_v0_01",
    "med_11": "profile_photo_latest_v0_01",
}


def _catalog_ids() -> list[str]:
    ids: list[str] = []
    for p in sorted(CATALOG.glob("*/*.md")):
        m = re.match(r"^---\n(.*?)\n---", p.read_text(encoding="utf-8"), re.S)
        if not m:
            continue
        for line in m.group(1).splitlines():
            if line.startswith("id:"):
                ids.append(line.split(":", 1)[1].strip())
                break
    return ids


def test_no_discovery_errors() -> None:
    assert DISCOVERY_ERRORS == [], f"task discovery problems: {DISCOVERY_ERRORS}"


def test_every_catalog_task_has_a_registered_builder() -> None:
    catalog_ids = _catalog_ids()
    assert len(catalog_ids) >= 110, f"expected >=110 catalog tasks, found {len(catalog_ids)}"
    missing = [
        cid for cid in catalog_ids
        if SEMANTIC.get(cid, f"{cid}_v0_01") not in TASK_REGISTRY
    ]
    assert not missing, f"catalog ids with no registered/runnable builder: {missing}"
