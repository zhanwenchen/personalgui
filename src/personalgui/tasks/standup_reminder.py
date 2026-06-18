"""v0 task #3: source-of-truth resolution.

The user's phone Calendar still says the standup is at 10:00 AM (old invite).
The desktop Work Chat has a more recent message from the manager: "moving standup
to 11:00 AM starting tomorrow". The agent must set a reminder for 11:00 AM —
trusting the chat (newer/authoritative), not the calendar (stale).

A naive agent that reads only the calendar will type 10:00 AM and fail. A correct
agent reads the chat, recognizes it's newer, and sets 11:00 AM.

Structurally different from the other v0 tasks:
- No cross-environment handoff is required (the authoritative value lives entirely on the desktop).
- Tests source-of-truth selection: visiting work_chat is the required subtask, not phone_calendar.
- phone_calendar is a distractor, not a forbidden source — visiting it is allowed; trusting it is the failure mode.
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

# Stored form value is the 24-hour HH:MM string that <input type="time"> emits.
# The chat message uses the human-readable form so the agent must translate.
AUTHORITATIVE_TIME_FORM = "11:00"
AUTHORITATIVE_TIME_HUMAN = "11:00 AM"
STALE_TIME_HUMAN = "10:00 AM"


def build_standup_reminder_task(
    authoritative_form: str = AUTHORITATIVE_TIME_FORM,
    authoritative_human: str = AUTHORITATIVE_TIME_HUMAN,
    stale_human: str = STALE_TIME_HUMAN,
) -> Task:
    return Task(
        task_id="standup_reminder_v0_01",
        request="Set a reminder for tomorrow's standup.",
        user=SyntheticUser(name="alex"),
        environments_spec=[
            EnvironmentSpec(
                id="windows_desktop",
                display_name="Windows Desktop",
                kind="desktop",
                apps=[
                    AppSpec(
                        id="work_chat",
                        type="MockChatApp",
                        display_name="Work Chat",
                        initial_state={
                            "title": "Work Chat",
                            "channel": "#team",
                            "messages": [
                                {
                                    "sender": "Manager",
                                    "ts": "yesterday 5:42 PM",
                                    "text": (
                                        f"Heads up: moving standup to {authoritative_human} starting tomorrow. "
                                        "Please update your calendars when you get a chance."
                                    ),
                                },
                                {
                                    "sender": "you",
                                    "ts": "yesterday 5:50 PM",
                                    "text": "Got it, thanks!",
                                },
                            ],
                        },
                    ),
                    AppSpec(
                        id="reminder_app",
                        type="MockReminderApp",
                        display_name="Reminders",
                        initial_state={
                            # Pre-existing reminders so the agent's addition appears as a third entry.
                            # The Initial-vs-Now split surfaces the list growing by one.
                            "reminders": [
                                {"time": "07:30", "note": "Morning gym"},
                                {"time": "17:30", "note": "Pick up laundry"},
                            ],
                            "time_field": "",
                            "note_field": "",
                            "status": "drafting",
                            "expected_time": authoritative_form,
                        },
                    ),
                ],
                initial_focus_app="reminder_app",
            ),
            EnvironmentSpec(
                id="android_phone",
                display_name="Android Phone",
                kind="mobile",
                apps=[
                    AppSpec(
                        id="phone_calendar",
                        type="MockCalendarApp",
                        display_name="Personal Calendar",
                        initial_state={
                            "title": "Tomorrow",
                            # Each event carries a "last_updated" timestamp so the agent can
                            # see which is newer when comparing against the chat. The standup
                            # entry pre-dates the manager's chat message; the lunch entry is
                            # recent and unaffected.
                            "events": [
                                {"title": "Standup", "time": stale_human, "last_updated": "3 weeks ago"},
                                {"title": "Lunch with Sara", "time": "12:30 PM", "last_updated": "yesterday"},
                            ],
                        },
                    ),
                    # Second phone app demonstrates multi-app switching. Personal chat is a
                    # boundary distractor — unrelated to the standup, never the authoritative
                    # source for work events.
                    AppSpec(
                        id="phone_chat",
                        type="MockChatApp",
                        display_name="Messages",
                        initial_state={
                            "title": "Messages",
                            "channel": "Sara",
                            "messages": [
                                {"sender": "Sara", "ts": "yesterday 8:12 PM", "text": "still on for lunch tomorrow?"},
                                {"sender": "you", "ts": "yesterday 8:30 PM", "text": "yes! 12:30 at the new place"},
                            ],
                        },
                    ),
                ],
                initial_focus_app="phone_calendar",
            ),
        ],
        task_graph=TaskGraph(
            subtasks=[
                Subtask(
                    id="find_authoritative_time",
                    description="Find the current standup time. The authoritative source is the latest message in Work Chat (the calendar is stale).",
                    required_env="windows_desktop",
                    required_app="work_chat",
                ),
                Subtask(
                    id="set_reminder",
                    description="Set a reminder in the Reminders app for the authoritative time.",
                    required_env="windows_desktop",
                    required_app="reminder_app",
                    depends_on=["find_authoritative_time"],
                ),
            ],
            required_handoffs=[],
        ),
        desired_final_state={
            "windows_desktop.reminder_app.status": "saved",
            "windows_desktop.reminder_app.time_field": authoritative_form,
        },
        initial_focus_env="windows_desktop",
    )
