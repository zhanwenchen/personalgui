---
id: fin_01
title: Taxi receipt amount to desktop expense report
domain: finance_expenses
metric_focus: [handoff_correctness]
secondary_metrics: [global_success, routing_accuracy]
environments: [android_phone, windows_desktop]
apps: [MockPhotosApp, MockExpenseReportApp]
difficulty: 2
code_ready: true
new_apps_needed: []
requires_clarification: false
forbidden_routes: false
forbidden_substrings: false
source_of_truth: false
---

# Taxi receipt amount to desktop expense report

**Request (verbatim, what the agent sees):**
> "File my MetroCab ride from this morning as an expense."

## User & constraints

`SyntheticUser(name="alex", constraints={"expense_device": "windows_desktop"})` — Alex
photographs paper receipts on the phone but only the desktop has the corporate expense
tool. The amount lives behind a photo on the phone; the form lives on the desktop.

## Scenario

Alex took a MetroCab to the airport and snapped a photo of the printed receipt on the
phone. The reimbursement form is a desktop-only corporate web app. To file the expense
the agent must read the fare off the phone photo and transfer it to the desktop form,
crossing from `android_phone` to `windows_desktop`.

## Environments & apps

| Env | App (`type`) | Seeded state (highlights) |
| --- | --- | --- |
| `android_phone` | `MockPhotosApp` | `amount="$63.20"`, `merchant="MetroCab"`, `date="2026-06-28"` |
| `windows_desktop` | `MockExpenseReportApp` | `amount_field=""`, `merchant_field=""`, `status="drafting"`, `expected_amount="$63.20"` |

## Latent task graph (hidden from agent)

| Subtask id | Description | required_env | required_app | depends_on |
| --- | --- | --- | --- | --- |
| `read_fare` | Read the fare from the phone receipt photo. | `android_phone` | `phone_photos` | — |
| `file_expense` | Enter the fare + merchant on the desktop form and submit. | `windows_desktop` | `expense_report` | `read_fare` |

## Required handoffs

| artifact_type | from_env | to_env | expected_value |
| --- | --- | --- | --- |
| `amount` | `android_phone` | `windows_desktop` | `$63.20` |

## Desired final state

```
windows_desktop.expense_report.status == "submitted"
```

## Decoys / ambiguity / source-of-truth

The phone photo metadata caption shows the trip distance ("12.4 mi") and a tip line is
visible, but only the fare `$63.20` is the reimbursable total. A naive agent that
hand-types a remembered or rounded amount ("$63" / "$65") never produces a real
cross-env handoff and fails the form match. There is exactly one receipt, so no
referent ambiguity — the trap is purely fidelity of the transferred value.

## Metric rationale

An agent that "knows" the rough fare and types it directly into the desktop form never
copies the authoritative value from the phone, so no `from_env=android_phone →
to_env=windows_desktop` handoff is recorded and any digit drift fails `handoff_correctness`.
Only a copy-from-phone / paste-into-form path both satisfies the handoff and matches
`expected_amount`.

## Verifier sketch

- **handoff_correctness (primary):** `required_handoffs` carries `expected_value="$63.20"`
  from `android_phone` to `windows_desktop`; satisfied only when the phone amount is
  copied and pasted into the form input.
- **global_success (secondary):** `desired_final_state` checks
  `expense_report.status == "submitted"`, which the form sets when `amount_field ==
  expected_amount` and the merchant field is non-empty.
- **routing_accuracy (secondary):** subtasks pin reading to `android_phone/phone_photos`
  and filing to `windows_desktop/expense_report`.
- Config fields set: `desired_final_state`, `required_handoffs`.

## Implementation notes

- **`code_ready: true`.** `MockPhotosApp` on `android_phone` with copyable `amount`;
  `MockExpenseReportApp` on `windows_desktop` seeded with `expected_amount="$63.20"`,
  `status="drafting"`. Solvable via `copy_value` on the photo amount, `paste_value` into
  `amount_field`, `type` the merchant, `click submit`. `desired_final_state` path
  `windows_desktop.expense_report.status` is a real state key.
- Set `initial_focus_env="windows_desktop"`, `initial_focus_app="expense_report"` so the
  agent must navigate to the phone to find the value.
