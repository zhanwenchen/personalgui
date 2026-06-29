---
id: shop_07
title: Forward an order receipt total to the expense report
domain: shopping_orders
metric_focus: [handoff_correctness]
secondary_metrics: [global_success, routing_accuracy]
environments: [windows_desktop]
apps: [MockEmailApp, MockExpenseReportApp]
difficulty: 2
code_ready: true
new_apps_needed: []
requires_clarification: false
forbidden_routes: false
forbidden_substrings: false
source_of_truth: false
---

# Forward an order receipt total to the expense report

**Request (verbatim, what the agent sees):**
> "Add my Brightmark order total to this month's expense report."

## User & constraints

`SyntheticUser(name="alex", constraints={})` — Alex expenses qualifying purchases. The order
receipt is an email; the expense report is a desktop form that requires the exact charged total
(the grand total including tax and shipping), plus the merchant. Subtotal-only amounts are
rejected. Both apps are on the same desktop.

## Scenario

Brightmark Supply emailed an order receipt. The expense report form needs the **grand total**
that was actually charged and the merchant name. The agent must open the receipt email, read the
grand total, and enter it (with the merchant) into the expense report on the same
`windows_desktop`, then submit. (Framed as shopping, but the destination is the expense report —
a cross-domain handoff.)

## Environments & apps

| Env | App (`type`) | Seeded state (highlights) |
| --- | --- | --- |
| `windows_desktop` | `MockEmailApp` | thread `bm_receipt`: sender "Brightmark Supply", subject "Your receipt — Order BM-7741", body shows `Subtotal: $128.00`, `Tax: $10.56`, `Shipping: $7.95`, `Order total: $146.51` |
| `windows_desktop` | `MockExpenseReportApp` | `amount_field=""`, `merchant_field=""`, `expected_amount="$146.51"`, `status="drafting"`; emits a `confirmation_code` on submit |

## Latent task graph (hidden from agent)

| Subtask id | Description | required_env | required_app | depends_on |
| --- | --- | --- | --- | --- |
| `read_total` | Open the Brightmark receipt and read the order total. | `windows_desktop` | `email` | — |
| `file_expense` | Enter the total + merchant on the expense report and submit. | `windows_desktop` | `expense_report` | `read_total` |

## Required handoffs

| artifact_type | from_env | to_env | expected_value |
| --- | --- | --- | --- |
| `amount` | `windows_desktop` | `windows_desktop` | `$146.51` |

## Desired final state

```
windows_desktop.expense_report.status == "submitted"
```

## Decoys / ambiguity / source-of-truth

The receipt lists four amounts in one block: `Subtotal $128.00`, `Tax $10.56`, `Shipping $7.95`,
and `Order total $146.51`. The expense form's `expected_amount` is the **grand total** `$146.51`;
the subtotal `$128.00` is the most prominent, round-looking decoy. An agent that grabs the subtotal
under-reports the expense and fails the match. The trap is total-vs-subtotal confusion, not referent
ambiguity (there is one receipt).

## Metric rationale

A naive agent expenses the subtotal `$128.00`, so the within-env handoff value never equals
`$146.51` and the report stays in `drafting` (`amount != expected_amount`). Only carrying the exact
order total clears `handoff_correctness` and drives `status == "submitted"`.

## Verifier sketch

- **handoff_correctness (primary):** `required_handoffs` carries `expected_value="$146.51"`,
  `from_env == to_env == windows_desktop`; satisfied only when the receipt total is copied and
  pasted into `amount_field`.
- **global_success (secondary):** `desired_final_state` checks `expense_report.status ==
  "submitted"`, which `MockExpenseReportApp` sets only when `amount == expected_amount` and the
  merchant is set.
- **routing_accuracy (secondary):** reading on `email`, filing on `expense_report`, both
  `windows_desktop`.
- Config fields set: `desired_final_state`, `required_handoffs`.

## Implementation notes

- **`code_ready: true`.** `MockEmailApp` receipt thread embedding subtotal/tax/shipping/total;
  `MockExpenseReportApp` seeded `expected_amount="$146.51"`, `status="drafting"`. Solvable via
  `tap thread:bm_receipt`, `copy_value` the order total, `paste_value` into `amount_field`, type
  the merchant into `merchant_field`, `click submit`. Mirrors the implemented `receipt_amount`
  mechanics but sources the amount from an email receipt with a tempting subtotal decoy rather than
  a phone photo.
- Set `initial_focus_app="expense_report"` so the agent must open the email to find the total.
