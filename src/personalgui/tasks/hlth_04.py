"""Catalog hlth_04: save a daily medication reminder at the exact dosing time printed on
the prescription-label photo (phone), not a rounded/guessed time. Phone -> desktop handoff.

Source-of-truth: the label photo's printed time (08:45) is authoritative; a tidy round
time (08:00/09:00) is the tempting wrong substitute. The reminder app only saves when
time_field == "08:45".

Primary metric: handoff_correctness (the time must cross phone -> desktop).
Secondary: global_success (reminder saved), source_of_truth.
Adaptation: dosing time modeled as the photo's copyable `amount` value; agent sets a
Reminder at that authoritative time (expected_time HH:MM). Reuses MockPhotosApp +
MockReminderApp.

See catalog/health_wellness/hlth_04_medication-reminder-label-time.md
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

DOSE_TIME = "08:45"


def build_hlth_04_task(dose_time: str = DOSE_TIME) -> Task:
    return Task(
        task_id="hlth_04_v0_01",
        request="Set a daily reminder to take my medication at the time on the prescription label.",
        user=SyntheticUser(name="alex"),
        environments_spec=[
            EnvironmentSpec(
                id="android_phone",
                display_name="Android Phone",
                kind="mobile",
                apps=[
                    AppSpec(
                        id="phone_photos",
                        type="MockPhotosApp",
                        display_name="Photos — Prescription label",
                        initial_state={
                            # The label's printed dosing time, modeled as the copyable value.
                            "amount": dose_time,
                            "merchant": "Aurora Pharmacy",
                            "date": "2026-06-28",
                        },
                    ),
                ],
                initial_focus_app="phone_photos",
            ),
            EnvironmentSpec(
                id="windows_desktop",
                display_name="Windows Desktop",
                kind="desktop",
                apps=[
                    AppSpec(
                        id="reminder",
                        type="MockReminderApp",
                        display_name="Reminders",
                        initial_state={
                            "reminders": [],
                            "time_field": "",
                            "note_field": "",
                            "expected_time": dose_time,
                            "status": "drafting",
                        },
                    ),
                ],
                initial_focus_app="reminder",
            ),
        ],
        task_graph=TaskGraph(
            subtasks=[
                Subtask(
                    id="read_dose_time",
                    description="Read the printed dosing time from the label photo.",
                    required_env="android_phone",
                    required_app="phone_photos",
                ),
                Subtask(
                    id="set_reminder",
                    description="Save a daily medication reminder at that time.",
                    required_env="windows_desktop",
                    required_app="reminder",
                    depends_on=["read_dose_time"],
                ),
            ],
            required_handoffs=[
                HandoffRequirement(
                    artifact_type="time",
                    from_env="android_phone",
                    to_env="windows_desktop",
                    expected_value=dose_time,
                ),
            ],
        ),
        desired_final_state={
            "windows_desktop.reminder.status": "saved",
        },
        initial_focus_env="windows_desktop",
    )
