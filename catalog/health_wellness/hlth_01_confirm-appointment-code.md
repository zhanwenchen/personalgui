---
id: hlth_01
title: Confirm clinic appointment with code from email into patient portal
domain: health_wellness
metric_focus: [handoff_correctness]
secondary_metrics: [global_success, routing_accuracy]
environments: [windows_desktop]
apps: [MockEmailApp, MockBrowserFormApp]
difficulty: 2
code_ready: true
new_apps_needed: []
requires_clarification: false
forbidden_routes: false
forbidden_substrings: false
source_of_truth: false
---

# Confirm clinic appointment with code from email into patient portal

**Request (verbatim, what the agent sees):**
> "Confirm my Cedar Hollow checkup using the code they emailed me."

## User & constraints

`SyntheticUser(name="alex", constraints={})` — Alex received a confirmation email from
the clinic with a one-time confirmation code and needs to type it into the clinic's
patient-portal web form to lock in the appointment. Both apps live on the same desktop,
so this is a within-desktop carry from inbox to web form.

## Scenario

Cedar Hollow Family Medicine sent a "Please confirm your appointment" email containing a
confirmation code. The patient portal will not finalize the booking until that code is
entered into its web form. The agent must open the email, read the authoritative code,
and enter it into the portal form — a copy-from-email / paste-into-form handoff that
stays on `windows_desktop` (`from_env == to_env`).

## Environments & apps

| Env | App (`type`) | Seeded state (highlights) |
| --- | --- | --- |
| `windows_desktop` | `MockEmailApp` (inbox) | thread `t_clinic`: sender "Cedar Hollow Family Medicine", subject "Confirm your 2026-07-06 visit", body contains `Confirmation code: CH-4192`. Decoy thread `t_news` is a clinic newsletter with no code. |
| `windows_desktop` | `MockBrowserFormApp` (portal) | `fields={"confirmation_code":""}`, `expected_fields={"confirmation_code":"CH-4192"}`, `field_types={"confirmation_code":"text"}`, `status="drafting"` |

## Latent task graph (hidden from agent)

| Subtask id | Description | required_env | required_app | depends_on |
| --- | --- | --- | --- | --- |
| `read_code` | Open the clinic email and read the confirmation code. | `windows_desktop` | `email` | — |
| `enter_code` | Enter the code in the portal form and submit. | `windows_desktop` | `portal_form` | `read_code` |

## Required handoffs

| artifact_type | from_env | to_env | expected_value |
| --- | --- | --- | --- |
| `code` | `windows_desktop` | `windows_desktop` | `CH-4192` |

## Desired final state

```
windows_desktop.portal_form.status == "submitted"
```

## Decoys / ambiguity / source-of-truth

The newsletter thread `t_news` mentions a generic "member ID CH-0001" in its footer and a
phone number, both of which look code-shaped and could be mis-copied. Only the
`Confirmation code: CH-4192` line in the appointment email is authoritative. There is
exactly one confirmation code, so the trap is fidelity, not referent ambiguity: an agent
that grabs the newsletter's `CH-0001` or types a remembered/rounded value fails the form
match.

## Metric rationale

An agent that hand-types a plausible-looking code (or the newsletter's `CH-0001`) without
copying the real value from the appointment email never records the correct within-desktop
handoff and fails the form's exact match, so `handoff_correctness` and `global_success`
both fail. Only copy-from-email / paste-into-form satisfies both.

## Verifier sketch

- **handoff_correctness (primary):** `required_handoffs` carries `expected_value="CH-4192"`
  with `from_env == to_env == windows_desktop`; satisfied only when the email code is
  copied and pasted into the form input.
- **global_success (secondary):** `desired_final_state` checks `portal_form.status ==
  "submitted"`, set when `fields["confirmation_code"] == "CH-4192"`.
- **routing_accuracy (secondary):** subtasks pin reading to `email` and entry to
  `portal_form`, both on `windows_desktop`.
- Config fields set: `desired_final_state`, `required_handoffs`.

## Implementation notes

- **`code_ready: true`.** `MockEmailApp` thread body holds `Confirmation code: CH-4192`;
  tap `thread:t_clinic` to open, then `copy_value` the code. `MockBrowserFormApp` seeded
  with `expected_fields={"confirmation_code":"CH-4192"}`, `status="drafting"`. Solvable via
  `paste_value` into the `confirmation_code` field, `click submit`.
- Set `initial_focus_env="windows_desktop"`, `initial_focus_app="portal_form"` so the agent
  must navigate to the inbox to find the code.
