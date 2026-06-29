"""Mock app backends. Pure in-memory state; render() returns the agent-visible view only.

Hidden fields (e.g. expense_portal.expected_code) live in state but are excluded from render().
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .schemas import AppSpec

if TYPE_CHECKING:
    from .environments import Clock


def totp_at(tick: int, codes: list[str], period: int) -> str:
    """The code valid at ``tick`` for a TOTP-style schedule: ``codes`` cycles, advancing one
    entry every ``period`` ticks. The authenticator and the server share the schedule, so both
    independently agree on the current code — and a code read in one window is wrong in the
    next."""
    if not codes:
        return ""
    period = max(int(period), 1)
    return codes[(tick // period) % len(codes)]


class App:
    def __init__(self, id: str, display_name: str, initial_state: dict[str, Any]) -> None:
        self.id = id
        self.display_name = display_name
        self.state: dict[str, Any] = dict(initial_state)
        self._clock: "Clock | None" = None

    def bind_clock(self, clock: "Clock") -> None:
        """Attach the shared logical clock. Time-varying apps read ``self.tick``; static apps
        simply ignore it."""
        self._clock = clock

    @property
    def tick(self) -> int:
        return self._clock.tick if self._clock is not None else 0

    def render(self) -> dict[str, Any]:
        raise NotImplementedError

    def element_bounds(self) -> list[dict[str, Any]]:
        """Return a flat list of {target, kind, x, y, w, h} entries describing the
        interactive elements an agent can click/tap on. Coordinates are in logical
        pixels relative to the app's content area (origin top-left, no padding).

        kind is one of:
          - "button"  : firing a click on (target) is a Click action on the app
          - "input"   : focusing the element accepts subsequent typed text
          - "copyable": tapping triggers copy_value with state-derived value
        """
        return []

    def handle_action(
        self, action_type: str, target: str | None, value: str | None
    ) -> tuple[bool, str | None, dict[str, Any]]:
        return False, f"{self.id} does not support action {action_type}", {}


class MockAuthenticatorApp(App):
    """Phone authenticator. By default shows a copyable one-time code.

    Optional enrollment mode (when initial_state carries `expected_setup_key`): the app also
    renders a setup-key input + enroll button, accepting a key pasted FROM another device
    (a reverse desktop -> phone handoff). enroll_status flips to "enrolled" on a match.
    """

    def render(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "kind": "authenticator",
            "title": "Authenticator",
            "code_visible": self.state.get("otp_code", ""),
            "hint": "Copy the code to use it on another device.",
            "element_bounds": self.element_bounds(),
        }
        if "expected_setup_key" in self.state:
            out["enroll_status"] = self.state.get("enroll_status", "unenrolled")
            out["setup_key_field"] = self.state.get("setup_key_field", "")
            out["enroll_buttons"] = (
                ["enroll"] if self.state.get("enroll_status") != "enrolled" else []
            )
            out["last_save_error"] = self.state.get("last_save_error")
        return out

    def element_bounds(self) -> list[dict[str, Any]]:
        bounds: list[dict[str, Any]] = [
            {
                "target": "otp_code",
                "kind": "copyable",
                "value": self.state.get("otp_code", ""),
                "x": 10, "y": 40, "w": 228, "h": 120,
            },
        ]
        if "expected_setup_key" in self.state and self.state.get("enroll_status") != "enrolled":
            bounds += [
                {"target": "setup_key", "kind": "input", "x": 10, "y": 180, "w": 228, "h": 44},
                {"target": "enroll", "kind": "button", "x": 10, "y": 244, "w": 100, "h": 40},
            ]
        return bounds

    def handle_action(self, action_type, target, value):
        if action_type == "view":
            return True, None, {}
        if "expected_setup_key" in self.state:
            if action_type == "type" and target == "setup_key":
                old = self.state.get("setup_key_field", "")
                self.state["setup_key_field"] = value or ""
                self.state.pop("last_save_error", None)
                return True, None, {"setup_key_field": [old, self.state["setup_key_field"]]}
            if action_type in ("click", "tap") and target == "enroll":
                if self.state.get("enroll_status") == "enrolled":
                    return False, "already enrolled", {}
                if self.state.get("setup_key_field") == self.state.get("expected_setup_key"):
                    self.state["enroll_status"] = "enrolled"
                    self.state.pop("last_save_error", None)
                    return True, None, {"enroll_status": ["unenrolled", "enrolled"]}
                err = "Setup key is incorrect."
                self.state["last_save_error"] = err
                return True, err, {"last_save_error_set": err}
        return False, f"authenticator does not support action {action_type}", {}


class MockTotpAuthenticatorApp(App):
    """Time-based authenticator. The visible code refreshes every ``period`` logical ticks,
    cycling through ``codes`` (both kept in state, hidden from render). The agent only ever
    sees the CURRENT code plus a countdown — never the schedule or future codes. A code copied
    now goes stale once the window rolls over, so the agent must carry it to the consuming form
    within the validity window. This is the exogenous-state hazard: waiting or detouring lets
    the code expire even though the agent 'did nothing' to it."""

    def render(self) -> dict[str, Any]:
        period = max(int(self.state.get("period", 1)), 1)
        return {
            "kind": "authenticator",
            "title": "Authenticator",
            "code_visible": totp_at(self.tick, self.state.get("codes", []), period),
            "expires_in_ticks": period - (self.tick % period),
            "hint": f"This code refreshes every {period} ticks — use it before it expires.",
            "element_bounds": self.element_bounds(),
        }

    def element_bounds(self) -> list[dict[str, Any]]:
        return [
            {
                "target": "otp_code",
                "kind": "copyable",
                "value": totp_at(self.tick, self.state.get("codes", []), self.state.get("period", 1)),
                "x": 10, "y": 40, "w": 228, "h": 120,
            },
        ]

    def handle_action(self, action_type, target, value):
        if action_type == "view":
            return True, None, {}
        return False, f"totp authenticator does not support action {action_type}", {}


class MockExpensePortalApp(App):
    def render(self) -> dict[str, Any]:
        status = self.state.get("status", "awaiting_otp")
        return {
            "kind": "form",
            "title": "Expense Portal Sign-In",
            "status_text": "Enter your one-time code." if status == "awaiting_otp" else "Signed in.",
            "fields": {"otp": self.state.get("otp_field", "")},
            "buttons": ["submit"] if status == "awaiting_otp" else [],
            "element_bounds": self.element_bounds(),
        }

    def element_bounds(self) -> list[dict[str, Any]]:
        if self.state.get("status") != "awaiting_otp":
            return []
        return [
            {"target": "otp", "kind": "input", "x": 0, "y": 72, "w": 536, "h": 44},
            {"target": "submit", "kind": "button", "x": 0, "y": 144, "w": 80, "h": 40},
        ]

    def handle_action(self, action_type, target, value):
        if action_type == "view":
            return True, None, {}
        if action_type == "type" and target == "otp":
            if self.state.get("status") != "awaiting_otp":
                return False, "portal is not accepting input", {}
            old = self.state.get("otp_field", "")
            self.state["otp_field"] = value or ""
            return True, None, {"otp_field": [old, self.state["otp_field"]]}
        if action_type in ("click", "tap") and target == "submit":
            if self.state.get("status") != "awaiting_otp":
                return False, "already submitted", {}
            if self.state.get("otp_field") == self.state.get("expected_code"):
                self.state["status"] = "authenticated"
                return True, None, {"status": ["awaiting_otp", "authenticated"]}
            return True, "incorrect code", {"last_attempt": self.state.get("otp_field")}
        return False, f"portal does not support action {action_type} on target {target}", {}


class MockPhotosApp(App):
    """Phone Photos app showing a single receipt image with a visible amount."""

    def render(self) -> dict[str, Any]:
        return {
            "kind": "receipt_photo",
            "title": self.state.get("merchant", "Receipt"),
            "merchant": self.state.get("merchant", ""),
            "amount_visible": self.state.get("amount", ""),
            "date": self.state.get("date", ""),
            "hint": "Copy the amount to use it on another device.",
            "element_bounds": self.element_bounds(),
        }

    def element_bounds(self) -> list[dict[str, Any]]:
        return [
            {
                "target": "amount",
                "kind": "copyable",
                "value": self.state.get("amount", ""),
                "x": 10, "y": 40, "w": 228, "h": 120,
            },
        ]

    def handle_action(self, action_type, target, value):
        if action_type == "view":
            return True, None, {}
        return False, f"photos does not support action {action_type}", {}


class MockExpenseReportApp(App):
    """Desktop expense-report form. Submit succeeds only if the amount matches expected
    and the merchant is non-empty. Failures surface as a persistent error banner so the
    user/agent gets specific feedback (which field is wrong)."""

    def render(self) -> dict[str, Any]:
        status = self.state.get("status", "drafting")
        status_text = "Enter the receipt details."
        if status == "submitted":
            code = self.state.get("confirmation_code", "")
            status_text = f"Submitted. Confirmation code: {code}" if code else "Submitted."
        return {
            "kind": "form",
            "title": "Expense Report",
            "status_text": status_text,
            "fields": {
                "amount": self.state.get("amount_field", ""),
                "merchant": self.state.get("merchant_field", ""),
            },
            "buttons": ["submit"] if status == "drafting" else [],
            "element_bounds": self.element_bounds(),
            "last_save_error": self.state.get("last_save_error"),
        }

    def element_bounds(self) -> list[dict[str, Any]]:
        if self.state.get("status") != "drafting":
            return []
        return [
            {"target": "amount", "kind": "input", "x": 0, "y": 72, "w": 536, "h": 44},
            {"target": "merchant", "kind": "input", "x": 0, "y": 144, "w": 536, "h": 44},
            {"target": "submit", "kind": "button", "x": 0, "y": 216, "w": 80, "h": 40},
        ]

    def _submit_error(self) -> str | None:
        amount = self.state.get("amount_field", "")
        merchant = self.state.get("merchant_field", "")
        expected = self.state.get("expected_amount", "")
        if not amount:
            return "Amount is required."
        if not merchant:
            return "Merchant is required."
        if amount != expected:
            return f"Could not submit: \"{amount}\" does not match the amount on the receipt."
        return None

    def handle_action(self, action_type, target, value):
        if action_type == "view":
            return True, None, {}
        if action_type == "type" and target in ("amount", "merchant"):
            if self.state.get("status") != "drafting":
                return False, "report already submitted", {}
            key = f"{target}_field"
            old = self.state.get(key, "")
            self.state[key] = value or ""
            # Editing a field clears the last submit error.
            self.state.pop("last_save_error", None)
            return True, None, {key: [old, self.state[key]]}
        if action_type in ("click", "tap") and target == "submit":
            if self.state.get("status") != "drafting":
                return False, "already submitted", {}
            err = self._submit_error()
            if err is None:
                self.state["status"] = "submitted"
                # Generate a confirmation code derivable from expected_amount so chained
                # tasks can verify "the agent forwarded THIS code". Stable per submission.
                import hashlib
                seed = (self.state.get("expected_amount", "") + self.state.get("merchant_field", ""))
                code = "EXP-" + hashlib.sha256(seed.encode()).hexdigest()[:6].upper()
                self.state["confirmation_code"] = code
                self.state.pop("last_save_error", None)
                return True, None, {"status": ["drafting", "submitted"], "confirmation_code": code}
            self.state["last_save_error"] = err
            return True, err, {
                "last_save_error_set": err,
                "amount_field": self.state.get("amount_field"),
                "merchant_field": self.state.get("merchant_field"),
            }
        return False, f"report does not support action {action_type} on target {target}", {}


class MockCalendarApp(App):
    """Read-only calendar app showing a list of events.

    Used as a source of facts that may be out-of-date relative to a more-authoritative
    source (e.g. a chat message). Initial state expects {"events": [...]} with optional
    "last_synced" per event. No meta-hint at the app level — the staleness cue is meant
    to come from comparing event timestamps against newer evidence elsewhere.
    """

    def render(self) -> dict[str, Any]:
        return {
            "kind": "calendar",
            "title": self.state.get("title", "Calendar"),
            "events": list(self.state.get("events", [])),
            "element_bounds": self.element_bounds(),
        }

    def element_bounds(self) -> list[dict[str, Any]]:
        bounds = []
        y = 40
        for i, ev in enumerate(self.state.get("events", [])):
            bounds.append({
                "target": f"event_{i}",
                "kind": "copyable",
                "value": ev.get("time", ""),
                "x": 0, "y": y, "w": 248, "h": 56,
            })
            y += 64
        return bounds

    def handle_action(self, action_type, target, value):
        if action_type == "view":
            return True, None, {}
        return False, f"calendar does not support action {action_type}", {}


class MockChatApp(App):
    """Chat thread. Carries timestamped messages with a 'sender' label.

    If `composable` is true in initial_state, also exposes a compose field + send button
    so the agent can post a new message into the thread. Sent messages append to the list
    with sender="you" so verifiers can inspect what was sent.
    """

    def render(self) -> dict[str, Any]:
        composable = bool(self.state.get("composable", False))
        out: dict[str, Any] = {
            "kind": "chat",
            "title": self.state.get("title", "Chat"),
            "channel": self.state.get("channel", ""),
            "messages": list(self.state.get("messages", [])),
            "composable": composable,
        }
        if composable:
            out["draft"] = self.state.get("draft_text", "")
            out["element_bounds"] = self.element_bounds()
        return out

    def element_bounds(self) -> list[dict[str, Any]]:
        if not self.state.get("composable"):
            return []
        message_count = max(1, len(self.state.get("messages", [])))
        y = 40 + message_count * 64
        return [
            {"target": "compose", "kind": "input", "x": 0, "y": y, "w": 536, "h": 44},
            {"target": "send", "kind": "button", "x": 0, "y": y + 60, "w": 80, "h": 40},
        ]

    def handle_action(self, action_type, target, value):
        if action_type == "view":
            return True, None, {}
        if not self.state.get("composable"):
            return False, f"chat does not support action {action_type}", {}
        if action_type == "type" and target == "compose":
            old = self.state.get("draft_text", "")
            self.state["draft_text"] = value or ""
            return True, None, {"draft_text": [old, self.state["draft_text"]]}
        if action_type in ("click", "tap") and target == "send":
            text = self.state.get("draft_text", "")
            if not text:
                return True, "compose is empty", {}
            messages = list(self.state.get("messages", []))
            messages.append({"sender": "you", "ts": "now", "text": text})
            self.state["messages"] = messages
            self.state["draft_text"] = ""
            return True, None, {"sent": text, "messages_count": len(messages)}
        return False, f"chat does not support action {action_type} on target {target}", {}


class MockReminderApp(App):
    """Reminder app: shows a list of saved reminders plus a "new reminder" composer below.
    Clicking save APPENDS a new {time, note} entry to the list when time matches the expected
    value and note is non-empty. expected_time must be HH:MM (24-hour) since the renderer
    uses <input type="time">.
    """

    def render(self) -> dict[str, Any]:
        status = self.state.get("status", "drafting")
        return {
            "kind": "reminders_app",
            "title": "Reminders",
            "status_text": "Add a new reminder." if status == "drafting" else "Reminder added.",
            "reminders": list(self.state.get("reminders", [])),
            "draft_fields": {
                "time": self.state.get("time_field", ""),
                "note": self.state.get("note_field", ""),
            },
            "draft_field_types": {
                "time": "time",
                "note": "text",
            },
            "draft_field_placeholders": {
                "note": "What is the reminder for?",
            },
            "buttons": ["save"] if status == "drafting" else [],
            "last_save_error": self.state.get("last_save_error"),
            "element_bounds": self.element_bounds(),
        }

    def element_bounds(self) -> list[dict[str, Any]]:
        if self.state.get("status") != "drafting":
            return []
        # Bounds positioned below the existing reminders list. We approximate the list
        # height by reminder count so the inputs land in roughly the right place.
        list_height = max(1, len(self.state.get("reminders", []))) * 48 + 40
        return [
            {"target": "time", "kind": "input", "x": 0, "y": list_height + 24, "w": 536, "h": 44},
            {"target": "note", "kind": "input", "x": 0, "y": list_height + 96, "w": 536, "h": 44},
            {"target": "save", "kind": "button", "x": 0, "y": list_height + 168, "w": 80, "h": 40},
        ]

    def _save_error_message(self) -> str:
        time_val = self.state.get("time_field", "")
        note_val = self.state.get("note_field", "")
        if not time_val:
            return "Time is required."
        if not note_val:
            return "Note is required."
        return (
            f"Could not save: \"{time_val}\" does not match the authoritative time for this "
            "reminder. Double-check your source — the calendar may be out of date."
        )

    def handle_action(self, action_type, target, value):
        if action_type == "view":
            return True, None, {}
        if action_type == "type" and target in ("time", "note"):
            if self.state.get("status") != "drafting":
                return False, "reminder already saved", {}
            key = f"{target}_field"
            old = self.state.get(key, "")
            self.state[key] = value or ""
            # User is correcting — clear any stale validation error.
            had_error = self.state.pop("last_save_error", None)
            changes: dict[str, Any] = {key: [old, self.state[key]]}
            if had_error is not None:
                changes["last_save_error_cleared"] = True
            return True, None, changes
        if action_type in ("click", "tap") and target == "save":
            if self.state.get("status") != "drafting":
                return False, "already saved", {}
            time_ok = self.state.get("time_field") == self.state.get("expected_time")
            note_ok = bool(self.state.get("note_field"))
            if time_ok and note_ok:
                reminders = list(self.state.get("reminders", []))
                new_entry = {"time": self.state["time_field"], "note": self.state["note_field"]}
                reminders.append(new_entry)
                self.state["reminders"] = reminders
                self.state["status"] = "saved"
                self.state.pop("last_save_error", None)
                return True, None, {
                    "status": ["drafting", "saved"],
                    "reminders_count": [len(reminders) - 1, len(reminders)],
                    "appended": new_entry,
                }
            err_msg = self._save_error_message()
            self.state["last_save_error"] = err_msg
            return True, err_msg, {
                "last_save_error_set": err_msg,
                "time_field": self.state.get("time_field"),
                "note_field": self.state.get("note_field"),
            }
        return False, f"reminder does not support action {action_type} on target {target}", {}


class MockOutlookApp(App):
    """Work email/calendar with sign-in required. Two render states:
      - signed_out: a form with username + password fields and a sign_in button
      - signed_in:  a calendar listing work events; each event's title is copyable

    Wrong credentials set a persistent error banner. The agent must produce the right
    (username, password) pair before the calendar contents become visible.
    """

    def render(self) -> dict[str, Any]:
        status = self.state.get("status", "signed_out")
        if status == "signed_out":
            return {
                "kind": "form",
                "title": "Outlook · Sign in",
                "status_text": "Enter your work account credentials.",
                "fields": {
                    "username": self.state.get("username_field", ""),
                    "password": self.state.get("password_field", ""),
                },
                "field_types": {"username": "text", "password": "password"},
                "field_placeholders": {"username": "name@work.example", "password": ""},
                "buttons": ["sign_in"],
                "element_bounds": [
                    {"target": "username", "kind": "input", "x": 0, "y": 72, "w": 536, "h": 44},
                    {"target": "password", "kind": "input", "x": 0, "y": 144, "w": 536, "h": 44},
                    {"target": "sign_in", "kind": "button", "x": 0, "y": 216, "w": 100, "h": 40},
                ],
                "last_save_error": self.state.get("last_save_error"),
            }
        events = list(self.state.get("events", []))
        return {
            "kind": "calendar",
            "title": "Outlook Calendar",
            "events": events,
            "element_bounds": [
                {
                    "target": f"event_{i}",
                    "kind": "copyable",
                    "value": ev.get("title", ""),
                    "x": 0,
                    "y": 40 + i * 64,
                    "w": 536,
                    "h": 56,
                }
                for i, ev in enumerate(events)
            ],
        }

    def handle_action(self, action_type, target, value):
        if action_type == "view":
            return True, None, {}
        status = self.state.get("status", "signed_out")
        if status == "signed_out":
            if action_type == "type" and target in ("username", "password"):
                key = f"{target}_field"
                old = self.state.get(key, "")
                self.state[key] = value or ""
                self.state.pop("last_save_error", None)
                return True, None, {key: [old, self.state[key]]}
            if action_type in ("click", "tap") and target == "sign_in":
                expected_user = self.state.get("expected_username", "")
                expected_pass = self.state.get("expected_password", "")
                if self.state.get("username_field") == expected_user and self.state.get("password_field") == expected_pass:
                    self.state["status"] = "signed_in"
                    self.state.pop("last_save_error", None)
                    return True, None, {"status": ["signed_out", "signed_in"]}
                err = "Wrong username or password."
                self.state["last_save_error"] = err
                return True, err, {"last_save_error_set": err}
            return False, f"sign in first before action {action_type}", {}
        # Signed in. Calendar is read-only.
        return False, f"outlook does not support {action_type} after sign-in", {}


class MockGoogleCalendarApp(App):
    """Personal calendar with read-write events. Pre-seeded with the user's existing
    personal events. The agent adds new events via a title + time composer. The
    sync_status flips to 'synced' once all `expected_titles` are present in the
    events list — this is what the source task's verifier looks for.
    """

    def render(self) -> dict[str, Any]:
        events = list(self.state.get("events", []))
        sync_status = self.state.get("sync_status", "syncing")
        return {
            "kind": "editable_calendar",
            "title": "Google Calendar",
            "events": events,
            "draft_fields": {
                "title": self.state.get("draft_title", ""),
                "time": self.state.get("draft_time", ""),
            },
            "draft_field_types": {"title": "text", "time": "time"},
            "draft_field_placeholders": {"title": "Event title", "time": ""},
            "buttons": ["add_event"],
            "sync_status": sync_status,
            "status_text": "All work events copied over." if sync_status == "synced" else "Add a new event.",
            "element_bounds": self.element_bounds(),
            "last_save_error": self.state.get("last_save_error"),
        }

    def element_bounds(self) -> list[dict[str, Any]]:
        list_height = max(1, len(self.state.get("events", []))) * 48 + 40
        return [
            {"target": "title", "kind": "input", "x": 0, "y": list_height + 24, "w": 536, "h": 44},
            {"target": "time", "kind": "input", "x": 0, "y": list_height + 96, "w": 200, "h": 44},
            {"target": "add_event", "kind": "button", "x": 0, "y": list_height + 168, "w": 120, "h": 40},
        ]

    def handle_action(self, action_type, target, value):
        if action_type == "view":
            return True, None, {}
        if action_type == "type" and target in ("title", "time"):
            key = f"draft_{target}"
            old = self.state.get(key, "")
            self.state[key] = value or ""
            self.state.pop("last_save_error", None)
            return True, None, {key: [old, self.state[key]]}
        if action_type in ("click", "tap") and target == "add_event":
            title = self.state.get("draft_title", "")
            time_v = self.state.get("draft_time", "")
            if not title:
                err = "Title is required."
                self.state["last_save_error"] = err
                return True, err, {"last_save_error_set": err}
            if not time_v:
                err = "Time is required."
                self.state["last_save_error"] = err
                return True, err, {"last_save_error_set": err}
            events = list(self.state.get("events", []))
            events.append({"title": title, "time": time_v})
            self.state["events"] = events
            self.state["draft_title"] = ""
            self.state["draft_time"] = ""
            self.state.pop("last_save_error", None)
            # If every expected title is now in the events list, mark synced.
            expected_titles = set(self.state.get("expected_titles", []))
            present_titles = {e.get("title", "") for e in events}
            prev_status = self.state.get("sync_status")
            if expected_titles and expected_titles.issubset(present_titles):
                self.state["sync_status"] = "synced"
            return True, None, {
                "events_count": len(events),
                "appended": {"title": title, "time": time_v},
                "sync_status": [prev_status, self.state.get("sync_status")],
            }
        return False, f"google_calendar does not support {action_type} on {target}", {}


class MockContactsApp(App):
    """A simple contacts list. The agent can tap a contact to view its details (sets
    focused_contact_id). State expects: contacts = [{id, name, label, phone, ...}, ...].
    Read-only beyond selection."""

    def render(self) -> dict[str, Any]:
        contacts = list(self.state.get("contacts", []))
        focused_id = self.state.get("focused_contact_id")
        return {
            "kind": "contacts",
            "title": self.state.get("title", "Contacts"),
            "contacts": contacts,
            "focused_contact_id": focused_id,
            "focused_contact": next((c for c in contacts if c.get("id") == focused_id), None),
        }

    def handle_action(self, action_type, target, value):
        if action_type == "view":
            return True, None, {}
        if action_type in ("click", "tap") and target and target.startswith("contact:"):
            cid = target.split(":", 1)[1]
            prev = self.state.get("focused_contact_id")
            self.state["focused_contact_id"] = cid
            return True, None, {"focused_contact_id": [prev, cid]}
        return False, f"contacts does not support action {action_type} on {target}", {}


class MockEmailApp(App):
    """Email inbox with threads. State: threads = [{id, sender, subject, ts, body}, ...]
    plus optional out_of_office settings (status, start_date, end_date)."""

    def render(self) -> dict[str, Any]:
        threads = list(self.state.get("threads", []))
        opened_id = self.state.get("opened_thread_id")
        ooo = {
            "enabled": bool(self.state.get("ooo_enabled", False)),
            "start": self.state.get("ooo_start_field", ""),
            "end": self.state.get("ooo_end_field", ""),
            "message": self.state.get("ooo_message_field", ""),
        }
        return {
            "kind": "email",
            "title": self.state.get("title", "Email"),
            "threads": threads,
            "opened_thread_id": opened_id,
            "opened_thread": next((t for t in threads if t.get("id") == opened_id), None),
            "ooo_supported": bool(self.state.get("ooo_supported", False)),
            "ooo": ooo,
        }

    def handle_action(self, action_type, target, value):
        if action_type == "view":
            return True, None, {}
        if action_type in ("click", "tap") and target and target.startswith("thread:"):
            tid = target.split(":", 1)[1]
            prev = self.state.get("opened_thread_id")
            self.state["opened_thread_id"] = tid
            return True, None, {"opened_thread_id": [prev, tid]}
        # Out-of-office controls (only when supported)
        if self.state.get("ooo_supported"):
            if action_type == "type" and target in ("ooo_start", "ooo_end", "ooo_message"):
                key = f"{target}_field"
                old = self.state.get(key, "")
                self.state[key] = value or ""
                return True, None, {key: [old, self.state[key]]}
            if action_type in ("click", "tap") and target == "ooo_toggle":
                start = self.state.get("ooo_start_field", "")
                end = self.state.get("ooo_end_field", "")
                if not start or not end:
                    return True, "start and end dates are required", {}
                prev = self.state.get("ooo_enabled", False)
                self.state["ooo_enabled"] = not prev
                return True, None, {"ooo_enabled": [prev, self.state["ooo_enabled"]]}
        return False, f"email does not support {action_type} on {target}", {}


class MockDocumentEditorApp(App):
    """A simple writable document. The body is an editable single field. Status flips to
    'saved' when the user clicks save AND `required_substrings` (if set) are all present."""

    def render(self) -> dict[str, Any]:
        status = self.state.get("status", "drafting")
        return {
            "kind": "document_editor",
            "title": self.state.get("title", "Document"),
            "body": self.state.get("body_field", ""),
            "buttons": ["save"] if status != "saved" else [],
            "status_text": "Saved." if status == "saved" else "Editing.",
            "status": status,
            "last_save_error": self.state.get("last_save_error"),
        }

    def handle_action(self, action_type, target, value):
        if action_type == "view":
            return True, None, {}
        if action_type == "type" and target == "body":
            old = self.state.get("body_field", "")
            self.state["body_field"] = value or ""
            self.state.pop("last_save_error", None)
            return True, None, {"body_field_len": [len(old), len(self.state["body_field"])]}
        if action_type in ("click", "tap") and target == "save":
            required = self.state.get("required_substrings", [])
            body = self.state.get("body_field", "")
            missing = [s for s in required if s not in body]
            if missing:
                err = f"Could not save: missing required content ({', '.join(repr(m) for m in missing)})."
                self.state["last_save_error"] = err
                return True, err, {"missing": missing}
            self.state["status"] = "saved"
            self.state.pop("last_save_error", None)
            return True, None, {"status": ["drafting", "saved"]}
        return False, f"document does not support {action_type} on {target}", {}


class MockBrowserFormApp(App):
    """Generic web form rendered in a browser tab. State expects: title, hint,
    fields = {name: ""}, expected_fields = {name: "expected_value"}, buttons = [...]."""

    def render(self) -> dict[str, Any]:
        status = self.state.get("status", "drafting")
        fields = dict(self.state.get("fields", {}))
        return {
            "kind": "form",
            "title": self.state.get("title", "Form"),
            "status_text": self.state.get("hint", "") if status != "submitted" else self.state.get("success_text", "Done."),
            "fields": fields,
            "field_types": self.state.get("field_types", {}),
            "field_placeholders": self.state.get("field_placeholders", {}),
            "buttons": list(self.state.get("buttons", ["submit"])) if status != "submitted" else [],
            "last_save_error": self.state.get("last_save_error"),
        }

    def handle_action(self, action_type, target, value):
        if action_type == "view":
            return True, None, {}
        if action_type == "type" and target in self.state.get("fields", {}):
            fields = dict(self.state["fields"])
            old = fields.get(target, "")
            fields[target] = value or ""
            self.state["fields"] = fields
            self.state.pop("last_save_error", None)
            return True, None, {target: [old, fields[target]]}
        if action_type in ("click", "tap") and target == "submit":
            if self.state.get("status") == "submitted":
                return False, "already submitted", {}
            expected = dict(self.state.get("expected_fields", {}))
            fields = self.state.get("fields", {})
            # Time-based field (optional): validated against the code valid at the CURRENT
            # tick, not a fixed value. A code from a past window is reported as `expired`
            # (distinct from plain `wrong`) so verifiers can tell "acted on stale data" apart
            # from a typo. Both still block the submit, like a real TOTP server.
            totp_field = self.state.get("totp_field")
            code_status: str | None = None
            if totp_field:
                current = totp_at(self.tick, self.state.get("totp_codes", []), self.state.get("totp_period", 1))
                expected[totp_field] = current
                submitted = fields.get(totp_field, "")
                if submitted and submitted != current:
                    code_status = "expired" if submitted in set(self.state.get("totp_codes", [])) else "wrong"
            empty = [k for k in expected if not fields.get(k)]
            if empty:
                err = f"Required field(s) empty: {', '.join(empty)}."
                self.state["last_save_error"] = err
                return True, err, {"empty": empty}
            mismatches = [k for k, want in expected.items() if fields.get(k, "") != want]
            if mismatches:
                err = (
                    "Code expired — fetch the current one and retry."
                    if code_status == "expired"
                    else f"Could not submit: {', '.join(mismatches)} did not match."
                )
                self.state["last_save_error"] = err
                changes: dict[str, Any] = {"mismatches": mismatches}
                if code_status:
                    changes["submitted_code_status"] = code_status
                return True, err, changes
            self.state["status"] = "submitted"
            self.state.pop("last_save_error", None)
            changes = {"status": ["drafting", "submitted"]}
            if totp_field:
                changes["submitted_code_status"] = "current"
            return True, None, changes
        return False, f"browser form does not support {action_type} on {target}", {}


class MockProfileApp(App):
    """Read-only profile / directory entry view. Renders a person's current contact info.
    Used as the authoritative source when a separate Contacts app is stale."""

    def render(self) -> dict[str, Any]:
        return {
            "kind": "profile",
            "title": self.state.get("title", "Profile"),
            "name": self.state.get("name", ""),
            "fields": dict(self.state.get("fields", {})),
            "last_updated": self.state.get("last_updated", ""),
        }

    def handle_action(self, action_type, target, value):
        if action_type == "view":
            return True, None, {}
        return False, f"profile does not support action {action_type}", {}


class MockInvitePhotoApp(App):
    """Phone photo of a paper invite. event_title and event_date are copyable values so the
    agent can carry them to a calendar on another device (e.g. add to Google Calendar)."""

    def render(self) -> dict[str, Any]:
        return {
            "kind": "invite_photo",
            "title": self.state.get("title", "Invite"),
            "event_title_visible": self.state.get("event_title", ""),
            "event_date_visible": self.state.get("event_date", ""),
            "note": self.state.get("note", ""),
            "hint": "Copy the event title or date to add it to a calendar.",
            "element_bounds": self.element_bounds(),
        }

    def element_bounds(self) -> list[dict[str, Any]]:
        return [
            {"target": "event_title", "kind": "copyable",
             "value": self.state.get("event_title", ""), "x": 10, "y": 40, "w": 228, "h": 56},
            {"target": "event_date", "kind": "copyable",
             "value": self.state.get("event_date", ""), "x": 10, "y": 110, "w": 228, "h": 56},
        ]

    def handle_action(self, action_type, target, value):
        if action_type == "view":
            return True, None, {}
        return False, f"invite photo does not support action {action_type}", {}


class MockFileShareApp(App):
    """Phone files surface. Each file's name is a copyable value, so the agent can 'share' a
    specific file to another environment via the handoff bus (then paste into a desktop
    drop/import target)."""

    def render(self) -> dict[str, Any]:
        return {
            "kind": "file_share",
            "title": self.state.get("title", "Files"),
            "files": list(self.state.get("files", [])),
            "hint": "Copy a file to send it to another device.",
            "element_bounds": self.element_bounds(),
        }

    def element_bounds(self) -> list[dict[str, Any]]:
        bounds: list[dict[str, Any]] = []
        y = 40
        for f in self.state.get("files", []):
            bounds.append({
                "target": f"file:{f.get('id')}", "kind": "copyable",
                "value": f.get("name", ""), "x": 10, "y": y, "w": 228, "h": 48,
            })
            y += 56
        return bounds

    def handle_action(self, action_type, target, value):
        if action_type == "view":
            return True, None, {}
        return False, f"file share does not support action {action_type}", {}


class MockFileDropApp(App):
    """Desktop drop / import target. Accepts a pasted file name and flips status to
    'received' when it matches expected_file. Used as the desktop end of a phone -> desktop
    file transfer (e.g. print a boarding pass, open a doc in the editor)."""

    def render(self) -> dict[str, Any]:
        status = self.state.get("status", "empty")
        return {
            "kind": "file_drop",
            "title": self.state.get("title", "Drop files"),
            "status_text": (
                self.state.get("success_text", "File received.")
                if status == "received" else self.state.get("hint", "Drop a file here.")
            ),
            "received_file": self.state.get("received_file", ""),
            "status": status,
            "fields": {"drop": self.state.get("drop_field", "")},
            "element_bounds": [{"target": "drop", "kind": "input", "x": 0, "y": 72, "w": 536, "h": 80}],
            "last_save_error": self.state.get("last_save_error"),
        }

    def handle_action(self, action_type, target, value):
        if action_type == "view":
            return True, None, {}
        if action_type == "type" and target == "drop":
            val = value or ""
            expected = self.state.get("expected_file", "")
            if expected and val == expected:
                self.state["status"] = "received"
                self.state["received_file"] = val
                self.state.pop("last_save_error", None)
                return True, None, {"status": ["empty", "received"], "received_file": val}
            self.state["drop_field"] = val
            if expected and val != expected:
                err = f"Could not import: \"{val}\" is not the expected file."
                self.state["last_save_error"] = err
                return True, err, {"last_save_error_set": err}
            return True, None, {"drop_field": val}
        return False, f"file drop does not support {action_type} on {target}", {}


class MockProfilePhotoApp(App):
    """Desktop profile-photo setter. Receives an image name (pasted from the phone gallery)
    into the `image` field and saves only when it matches expected_image — the authoritative
    (newest) headshot. A stale image name leaves it drafting (source-of-truth decoy)."""

    def render(self) -> dict[str, Any]:
        status = self.state.get("status", "drafting")
        return {
            "kind": "profile_photo",
            "title": self.state.get("title", "Profile photo"),
            "status": status,
            "status_text": "Saved." if status == "saved" else self.state.get("hint", "Set your profile photo."),
            "fields": {"image": self.state.get("selected_image", "")},
            "buttons": ["save"] if status != "saved" else [],
            "last_save_error": self.state.get("last_save_error"),
            "element_bounds": self.element_bounds(),
        }

    def element_bounds(self) -> list[dict[str, Any]]:
        if self.state.get("status") == "saved":
            return []
        return [
            {"target": "image", "kind": "input", "x": 0, "y": 72, "w": 536, "h": 44},
            {"target": "save", "kind": "button", "x": 0, "y": 144, "w": 80, "h": 40},
        ]

    def handle_action(self, action_type, target, value):
        if action_type == "view":
            return True, None, {}
        if action_type == "type" and target == "image":
            if self.state.get("status") == "saved":
                return False, "already saved", {}
            old = self.state.get("selected_image", "")
            self.state["selected_image"] = value or ""
            self.state.pop("last_save_error", None)
            return True, None, {"selected_image": [old, self.state["selected_image"]]}
        if action_type in ("click", "tap") and target == "save":
            if self.state.get("status") == "saved":
                return False, "already saved", {}
            sel = self.state.get("selected_image", "")
            if not sel:
                err = "Select a photo first."
                self.state["last_save_error"] = err
                return True, err, {"last_save_error_set": err}
            if sel == self.state.get("expected_image"):
                self.state["status"] = "saved"
                self.state.pop("last_save_error", None)
                return True, None, {"status": ["drafting", "saved"]}
            err = "Could not save: that photo is out of date. Use the most recent one."
            self.state["last_save_error"] = err
            return True, err, {"last_save_error_set": err}
        return False, f"profile photo does not support {action_type} on {target}", {}


APP_REGISTRY: dict[str, type[App]] = {
    "MockAuthenticatorApp": MockAuthenticatorApp,
    "MockTotpAuthenticatorApp": MockTotpAuthenticatorApp,
    "MockInvitePhotoApp": MockInvitePhotoApp,
    "MockFileShareApp": MockFileShareApp,
    "MockFileDropApp": MockFileDropApp,
    "MockProfilePhotoApp": MockProfilePhotoApp,
    "MockExpensePortalApp": MockExpensePortalApp,
    "MockPhotosApp": MockPhotosApp,
    "MockExpenseReportApp": MockExpenseReportApp,
    "MockCalendarApp": MockCalendarApp,
    "MockChatApp": MockChatApp,
    "MockReminderApp": MockReminderApp,
    "MockOutlookApp": MockOutlookApp,
    "MockGoogleCalendarApp": MockGoogleCalendarApp,
    "MockContactsApp": MockContactsApp,
    "MockEmailApp": MockEmailApp,
    "MockDocumentEditorApp": MockDocumentEditorApp,
    "MockBrowserFormApp": MockBrowserFormApp,
    "MockProfileApp": MockProfileApp,
}


def build_app(spec: AppSpec) -> App:
    cls = APP_REGISTRY[spec.type]
    return cls(id=spec.id, display_name=spec.display_name, initial_state=spec.initial_state)
