---
id: fin_11
title: Enter receipt total, not subtotal, into expense form
domain: finance_expenses
metric_focus: [source_of_truth]
secondary_metrics: [handoff_correctness, global_success]
environments: [android_phone, windows_desktop]
apps: [MockPhotosApp, MockExpenseReportApp]
difficulty: 3
code_ready: true
new_apps_needed: []
requires_clarification: false
forbidden_routes: false
forbidden_substrings: false
source_of_truth: true
---

# Enter receipt total, not subtotal, into expense form

**Request (verbatim, what the agent sees):**
> "Expense the Bluebird Diner receipt — file the full total including tip."

## User & constraints

`SyntheticUser(name="alex", constraints={"claim_basis": "grand_total"})` — Reimbursement
is on the grand total (incl. tip), not the pre-tip subtotal. The receipt photo shows both,
and the subtotal is the more prominent figure.

## Scenario

Alex's diner receipt photo on the phone shows a **subtotal** and a **grand total** that
includes the tip. The expense form must carry the grand total. The agent must read the
right line off the phone and transfer it to the desktop form, crossing from
`android_phone` to `windows_desktop`.

## Environments & apps

| Env | App (`type`) | Seeded state (highlights) |
| --- | --- | --- |
| `android_phone` | `MockPhotosApp` | `amount="$58.10"` (grand total, copyable), `merchant="Bluebird Diner"`, `date="2026-06-25"`; caption shows `Subtotal $48.00 · Tip $10.10 · TOTAL $58.10` |
| `windows_desktop` | `MockExpenseReportApp` | `amount_field=""`, `merchant_field=""`, `status="drafting"`, `expected_amount="$58.10"` |

## Latent task graph (hidden from agent)

| Subtask id | Description | required_env | required_app | depends_on |
| --- | --- | --- | --- | --- |
| `read_total` | Read the grand total (incl. tip) from the receipt photo. | `android_phone` | `phone_photos` | — |
| `file_total` | Enter the grand total + merchant on the desktop form and submit. | `windows_desktop` | `expense_report` | `read_total` |

## Required handoffs

| artifact_type | from_env | to_env | expected_value |
| --- | --- | --- | --- |
| `amount` | `android_phone` | `windows_desktop` | `$58.10` |

## Desired final state

```
windows_desktop.expense_report.status == "submitted"
```

## Decoys / ambiguity / source-of-truth

The receipt exposes two amounts: the **subtotal** `$48.00` (a prominent, round, tempting
decoy) and the **grand total** `$58.10` (the reimbursable figure). The form's
`expected_amount` is the grand total. An agent that grabs the round subtotal under-claims
and fails the form match. The copyable `amount` field is set to the total; the subtotal
lives only in the caption text as the trap.

## Metric rationale

The "amount" is duplicated as subtotal vs total; only the tip-inclusive total is
authoritative for reimbursement. An agent that reads the salient subtotal `$48.00`
produces a handoff value that never equals `expected_amount`, failing `handoff_correctness`
and leaving the form in `drafting`.

## Verifier sketch

- **source_of_truth (primary):** authoritative grand total `$58.10` is what
  `expected_amount` / `desired_final_state` require; subtotal `$48.00` is the caption
  decoy that fails the form match.
- **handoff_correctness (secondary):** cross-env handoff carries `$58.10` from
  `android_phone` to `windows_desktop`.
- **global_success (secondary):** `expense_report.status == "submitted"`.
- Config fields set: `desired_final_state`, `required_handoffs`.

## Implementation notes

- **`code_ready: true`.** `MockPhotosApp` with the copyable `amount` set to the grand
  total and the subtotal embedded only in the caption; `MockExpenseReportApp` with
  `expected_amount="$58.10"`. An agent that `copy_value`s the clean `amount` passes; one
  that reads the subtotal out of the caption and types it fails. Solvable via copy/paste +
  `type` merchant + `submit`.
- Set `initial_focus_env="windows_desktop"` so the phone must be visited to read the total.
