"""Available v0 tasks, keyed by task_id."""

from typing import Callable

from ..schemas import Task
from .authenticator_handoff import build_authenticator_handoff_task
from .bank_password_reset import build_bank_password_reset_task
from .boundary_status_update import build_boundary_status_update_task
from .clarification_sara import build_clarification_sara_task
from .contract_price_update import build_contract_price_update_task
from .expense_then_notify import build_expense_then_notify_task
from .minimal_transfer import build_minimal_transfer_task
from .ooo_setup import build_ooo_setup_task
from .receipt_amount import build_receipt_amount_task
from .stale_contact_jordan import build_stale_contact_jordan_task
from .standup_reminder import build_standup_reminder_task
from .work_to_personal_calendar import build_work_to_personal_calendar_task


TASK_REGISTRY: dict[str, Callable[[], Task]] = {
    "auth_handoff_v0_01": build_authenticator_handoff_task,
    "receipt_amount_v0_01": build_receipt_amount_task,
    "standup_reminder_v0_01": build_standup_reminder_task,
    "work_to_personal_calendar_v0_01": build_work_to_personal_calendar_task,
    "expense_then_notify_v0_01": build_expense_then_notify_task,
    "clarification_sara_v0_01": build_clarification_sara_task,
    "boundary_status_update_v0_01": build_boundary_status_update_task,
    "minimal_transfer_v0_01": build_minimal_transfer_task,
    "bank_password_reset_v0_01": build_bank_password_reset_task,
    "contract_price_update_v0_01": build_contract_price_update_task,
    "stale_contact_jordan_v0_01": build_stale_contact_jordan_task,
    "ooo_setup_v0_01": build_ooo_setup_task,
}


def list_tasks() -> list[dict[str, str]]:
    """Lightweight catalog for the task picker."""
    out = []
    for builder in TASK_REGISTRY.values():
        t = builder()
        out.append({"task_id": t.task_id, "request": t.request})
    return out


def build_task(task_id: str) -> Task:
    if task_id not in TASK_REGISTRY:
        raise KeyError(f"unknown task_id: {task_id}; valid: {list(TASK_REGISTRY)}")
    return TASK_REGISTRY[task_id]()


__all__ = [
    "TASK_REGISTRY",
    "list_tasks",
    "build_task",
    "build_authenticator_handoff_task",
    "build_receipt_amount_task",
    "build_standup_reminder_task",
    "build_work_to_personal_calendar_task",
]
