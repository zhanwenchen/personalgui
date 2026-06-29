---
id: fin_02
title: Pay invoice using emailed payment reference
domain: finance_expenses
metric_focus: [handoff_correctness]
secondary_metrics: [global_success, routing_accuracy]
environments: [windows_desktop]
apps: [MockEmailApp, MockBrowserFormApp]
difficulty: 3
code_ready: true
new_apps_needed: []
requires_clarification: false
forbidden_routes: false
forbidden_substrings: false
source_of_truth: false
---

# Pay invoice using emailed payment reference

**Request (verbatim, what the agent sees):**
> "Pay the Brightleaf Supplies invoice on their portal — the reference is in their email."

## User & constraints

`SyntheticUser(name="alex", constraints={})` — Alex pays vendor invoices through each
vendor's web portal. The portal requires the exact payment reference code that the
vendor emails out; typing the invoice number instead is rejected. Both the email and the
portal are open on the same desktop, so this is a within-desktop, cross-app handoff.

## Scenario

Brightleaf Supplies emailed a payment notice with a one-time payment reference code. The
vendor's payment portal is a web form that accepts the reference and a confirming amount.
The agent must open the email, read the reference, and carry it into the browser form on
the same `windows_desktop`.

## Environments & apps

| Env | App (`type`) | Seeded state (highlights) |
| --- | --- | --- |
| `windows_desktop` | `MockEmailApp` | thread `brightleaf`: body contains `Payment reference: BLF-2026-77413` and `Invoice #: INV-3092`, `Amount due: $1,240.00` |
| `windows_desktop` | `MockBrowserFormApp` | `expected_fields={"reference":"BLF-2026-77413","amount":"$1,240.00"}`, `field_types={"reference":"text","amount":"text"}`, `status="drafting"` |

## Latent task graph (hidden from agent)

| Subtask id | Description | required_env | required_app | depends_on |
| --- | --- | --- | --- | --- |
| `read_reference` | Open Brightleaf's email and read the payment reference. | `windows_desktop` | `email` | — |
| `submit_payment` | Enter reference + amount on the portal form and submit. | `windows_desktop` | `payment_portal` | `read_reference` |

## Required handoffs

| artifact_type | from_env | to_env | expected_value |
| --- | --- | --- | --- |
| `payment_reference` | `windows_desktop` | `windows_desktop` | `BLF-2026-77413` |

## Desired final state

```
windows_desktop.payment_portal.status == "submitted"
```

## Decoys / ambiguity / source-of-truth

The email body shows three numbers in the same paragraph: the **payment reference**
`BLF-2026-77413` (correct), the **invoice number** `INV-3092`, and the **amount**
`$1,240.00`. The portal's `reference` field accepts only the payment reference; an agent
that grabs the more salient invoice number fails the form's `expected_fields` match. The
amount must also be carried, but the trap is reference-vs-invoice confusion.

## Metric rationale

A naive agent reads "reference" loosely and submits the invoice number `INV-3092`, so
the within-env handoff value never equals `BLF-2026-77413` and the browser form stays in
`drafting`. Only transferring the exact payment reference clears `handoff_correctness`
and `global_success`.

## Verifier sketch

- **handoff_correctness (primary):** `required_handoffs` with `from_env == to_env ==
  windows_desktop` and `expected_value="BLF-2026-77413"`.
- **global_success (secondary):** `desired_final_state` checks `payment_portal.status ==
  "submitted"`, which `MockBrowserFormApp` sets only when every field equals
  `expected_fields`.
- **routing_accuracy (secondary):** reading pinned to `email`, submitting to
  `payment_portal`, both on `windows_desktop`.
- Config fields set: `desired_final_state`, `required_handoffs`.

## Implementation notes

- **`code_ready: true`.** `MockEmailApp` with a single thread whose body embeds all three
  numbers; `MockBrowserFormApp` with `expected_fields` for `reference` and `amount`.
  Solvable via `tap thread:brightleaf` to open, `copy_value` the reference, `paste_value`
  into the `reference` input, then enter the amount and `submit`. All
  `desired_final_state` paths reference real `MockBrowserFormApp` keys.
- Seed `opened_thread_id=None` so the agent must open the email first.
