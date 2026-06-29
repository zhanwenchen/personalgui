---
id: med_02
title: Hardware-store receipt photo into desktop expense report
domain: media_files
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

# Hardware-store receipt photo into desktop expense report

**Request (verbatim, what the agent sees):**
> "File the FerroMax hardware run as an expense — use the photo of the receipt."

## User & constraints

`SyntheticUser(name="alex", constraints={"expense_device": "windows_desktop"})` — Alex
photographs paper receipts on the phone; the corporate expense tool is desktop-only. The
amount lives behind a phone photo; the form lives on the desktop.

## Scenario

Alex bought shop supplies at FerroMax Hardware for a work project and photographed the
till receipt. The reimbursement form is the desktop corporate web app. To file the expense
the agent must read the total off the phone photo and transfer it to the desktop form,
crossing from `android_phone` to `windows_desktop`. Distinct from `receipt_amount`
(Cafe Roma / `$47.50`): different merchant, a multi-line itemized receipt, and a
subtotal-vs-total decoy.

## Environments & apps

| Env | App (`type`) | Seeded state (highlights) |
| --- | --- | --- |
| `android_phone` | `MockPhotosApp` | `amount="$112.86"` (grand total, copyable), `merchant="FerroMax Hardware"`, `date="2026-06-27"` |
| `windows_desktop` | `MockExpenseReportApp` | `amount_field=""`, `merchant_field=""`, `status="drafting"`, `expected_amount="$112.86"` |

## Latent task graph (hidden from agent)

| Subtask id | Description | required_env | required_app | depends_on |
| --- | --- | --- | --- | --- |
| `read_total` | Read the grand total from the phone receipt photo. | `android_phone` | `phone_photos` | — |
| `file_expense` | Enter the total + merchant on the desktop form and submit. | `windows_desktop` | `expense_report` | `read_total` |

## Required handoffs

| artifact_type | from_env | to_env | expected_value |
| --- | --- | --- | --- |
| `amount` | `android_phone` | `windows_desktop` | `$112.86` |

## Desired final state

```
windows_desktop.expense_report.status == "submitted"
```

## Decoys / ambiguity / source-of-truth

The itemized receipt photo shows a **subtotal** `$104.50` and a **tax** line `$8.36`
printed above the **grand total** `$112.86`. The subtotal is the larger, more prominent
number and a tempting wrong pick; only the grand total is reimbursable and matches
`expected_amount`. A naive agent that grabs the subtotal, or hand-types a rounded
remembered figure, fails the form match. Exactly one receipt — the trap is which line and
fidelity, not referent ambiguity.

## Metric rationale

An agent that reads the wrong line (subtotal) or types a remembered amount never copies the
authoritative grand total from the phone, so no `from_env=android_phone →
to_env=windows_desktop` handoff is recorded and the wrong value fails `handoff_correctness`
and the `expected_amount` match. Only copy-the-total-from-phone / paste-into-form succeeds.

## Verifier sketch

- **handoff_correctness (primary):** `required_handoffs` carries `expected_value="$112.86"`
  from `android_phone` to `windows_desktop`; satisfied only when the photo's total is copied
  and pasted into the form input.
- **global_success (secondary):** `desired_final_state` checks `expense_report.status ==
  "submitted"`, set when `amount_field == expected_amount` and merchant is non-empty.
- **routing_accuracy (secondary):** subtasks pin reading to `android_phone/phone_photos`
  and filing to `windows_desktop/expense_report`.
- Config fields set: `desired_final_state`, `required_handoffs`.

## Implementation notes

- **`code_ready: true`.** `MockPhotosApp` on `android_phone` with copyable `amount="$112.86"`
  (the grand total); `MockExpenseReportApp` on `windows_desktop` seeded with
  `expected_amount="$112.86"`, `status="drafting"`. The subtotal/tax decoys live in the
  photo caption/description text only, not as separate copyable fields. Solvable via
  `copy_value` on the amount, `paste_value` into `amount_field`, `type` the merchant,
  `click submit`. `desired_final_state` path `windows_desktop.expense_report.status` is real.
- Set `initial_focus_env="windows_desktop"`, `initial_focus_app="expense_report"` so the
  agent must navigate to the phone to find the value.
