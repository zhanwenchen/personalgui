---
id: trv_10
title: Expense the airport-taxi receipt from phone photo to desktop report
domain: travel
metric_focus: [handoff_correctness]
secondary_metrics: [global_success, routing_accuracy]
environments: [android_phone, windows_desktop]
apps: [MockPhotosApp, MockExpenseReportApp]
difficulty: 3
code_ready: true
new_apps_needed: []
requires_clarification: false
forbidden_routes: false
forbidden_substrings: false
source_of_truth: false
---

# Expense the airport-taxi receipt from phone photo to desktop report

**Request (verbatim, what the agent sees):**
> "Expense the cab I took to catch my Aerolux flight."

## User & constraints

`SyntheticUser(name="alex", constraints={"expense_device": "windows_desktop"})` — Alex
photographs trip receipts on the phone but files them on the desktop expense report. This
taxi is a travel expense tied to the Aerolux trip; the amount lives behind a phone photo.

## Scenario

On the way to the airport for the Aerolux flight, Alex took a SkyLine taxi and photographed
the printed receipt on the phone. The travel expense report is a desktop-only app. To file
it, the agent must read the fare off the phone photo and enter it on the desktop form,
crossing from `android_phone` to `windows_desktop`. Framed as a travel expense, distinct
from the standalone finance taxi task by trip context, merchant, and amount.

## Environments & apps

| Env | App (`type`) | Seeded state (highlights) |
| --- | --- | --- |
| `android_phone` | `MockPhotosApp` | `amount="$41.75"`, `merchant="SkyLine Taxi"`, `date="2026-07-09"` (copyable amount, view-only) |
| `windows_desktop` | `MockExpenseReportApp` | `amount_field=""`, `merchant_field=""`, `status="drafting"`, `expected_amount="$41.75"` |

## Latent task graph (hidden from agent)

| Subtask id | Description | required_env | required_app | depends_on |
| --- | --- | --- | --- | --- |
| `read_fare` | Read the fare from the phone receipt photo. | `android_phone` | `phone_photos` | — |
| `file_expense` | Enter the fare + merchant on the desktop form and submit. | `windows_desktop` | `expense_report` | `read_fare` |

## Required handoffs

| artifact_type | from_env | to_env | expected_value |
| --- | --- | --- | --- |
| `amount` | `android_phone` | `windows_desktop` | `$41.75` |

## Desired final state

```
windows_desktop.expense_report.status == "submitted"
```

## Decoys / ambiguity / source-of-truth

The photo also shows a distance line ("9.1 mi") and a separate tip line, and the airport
terminal toll appears as a sub-line — only the fare total `$41.75` is reimbursable here. A
naive agent that adds the toll, rounds the fare, or types a remembered amount never
produces a faithful cross-env handoff and fails the form match. One receipt, no referent
ambiguity — the trap is value fidelity.

## Metric rationale

An agent that hand-types a rough or summed amount into the desktop form never copies the
authoritative value from the phone, so no `from_env=android_phone → to_env=windows_desktop`
handoff is recorded and any digit drift fails `handoff_correctness` and the
`expected_amount` match.

## Verifier sketch

- **handoff_correctness (primary):** `required_handoffs` carries `expected_value="$41.75"`
  from `android_phone` to `windows_desktop`, satisfied only by copy-from-phone /
  paste-into-form.
- **global_success (secondary):** `desired_final_state` checks `expense_report.status ==
  "submitted"`, set when `amount_field == expected_amount` and merchant is non-empty.
- **routing_accuracy (secondary):** reading on `phone_photos`, filing on `expense_report`.
- Config fields set: `desired_final_state`, `required_handoffs`.

## Implementation notes

- **`code_ready: true`.** Same app pair as the implemented `receipt_amount` task but with
  a different merchant ("SkyLine Taxi"), amount ("$41.75"), and travel framing tied to the
  Aerolux trip — distinct seed, not a duplicate. `MockPhotosApp` copyable `amount`;
  `MockExpenseReportApp` seeded `expected_amount="$41.75"`, `status="drafting"`. Solvable
  via `copy_value` the photo amount, `paste_value` into `amount_field`, `type` merchant,
  `click submit`. `desired_final_state` path is a real key.
- Set `initial_focus_env="windows_desktop"`, `initial_focus_app="expense_report"`.
