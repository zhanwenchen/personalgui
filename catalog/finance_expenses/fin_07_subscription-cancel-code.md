---
id: fin_07
title: Subscription cancellation confirmation code from email to web form
domain: finance_expenses
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

# Subscription cancellation confirmation code from email to web form

**Request (verbatim, what the agent sees):**
> "Cancel my StreamHaus subscription — they emailed a confirmation code for the cancel page."

## User & constraints

`SyntheticUser(name="alex", constraints={})` — To cancel, StreamHaus emails a one-time
cancellation confirmation code that must be entered on their cancellation web form. Both
the email and the form are on the same desktop, so this is a within-desktop cross-app
handoff.

## Scenario

Alex requested cancellation; StreamHaus replied with a code to paste into their
"Confirm cancellation" web form. The agent must open the email, read the code, and enter
it into the browser form to finalize the cancellation on `windows_desktop`.

## Environments & apps

| Env | App (`type`) | Seeded state (highlights) |
| --- | --- | --- |
| `windows_desktop` | `MockEmailApp` | thread `streamhaus`: body contains `Your cancellation confirmation code: CXL-9F32K` and an unrelated `Account ID: 4471-220` |
| `windows_desktop` | `MockBrowserFormApp` | `expected_fields={"confirmation_code":"CXL-9F32K"}`, `field_types={"confirmation_code":"text"}`, `status="drafting"` |

## Latent task graph (hidden from agent)

| Subtask id | Description | required_env | required_app | depends_on |
| --- | --- | --- | --- | --- |
| `read_code` | Open the StreamHaus email and read the cancellation code. | `windows_desktop` | `email` | — |
| `submit_cancel` | Enter the code on the cancellation form and submit. | `windows_desktop` | `cancel_form` | `read_code` |

## Required handoffs

| artifact_type | from_env | to_env | expected_value |
| --- | --- | --- | --- |
| `confirmation_code` | `windows_desktop` | `windows_desktop` | `CXL-9F32K` |

## Desired final state

```
windows_desktop.cancel_form.status == "submitted"
```

## Decoys / ambiguity / source-of-truth

The email body contains two codes: the **cancellation confirmation code** `CXL-9F32K`
(correct) and an unrelated **Account ID** `4471-220`. The form accepts only the
confirmation code. An agent that grabs the account id fails the `expected_fields` match.
The trap is picking the wrong code from a body with multiple identifiers.

## Metric rationale

A naive agent that scans for "code" and transfers the account id never satisfies the
`expected_value="CXL-9F32K"` handoff, so the cancel form stays in `drafting`. Only the
correct confirmation code clears both metrics.

## Verifier sketch

- **handoff_correctness (primary):** `required_handoffs` with `from_env == to_env ==
  windows_desktop` and `expected_value="CXL-9F32K"`.
- **global_success (secondary):** `desired_final_state` checks `cancel_form.status ==
  "submitted"`.
- **routing_accuracy (secondary):** reading pinned to `email`, submitting to
  `cancel_form`.
- Config fields set: `desired_final_state`, `required_handoffs`.

## Implementation notes

- **`code_ready: true`.** `MockEmailApp` thread embeds both identifiers;
  `MockBrowserFormApp` with a single `confirmation_code` field in `expected_fields`.
  Solvable via `tap thread:streamhaus`, `copy_value` the code, `paste_value` into the
  field, `submit`. `desired_final_state` path references a real `MockBrowserFormApp` key.
- Seed `opened_thread_id=None`.
