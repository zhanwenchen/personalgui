---
id: shop_01
title: Start a return using the RMA code from the order email
domain: shopping_orders
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

# Start a return using the RMA code from the order email

**Request (verbatim, what the agent sees):**
> "Start the return for my Trellis Goods order — the return code is in their email."

## User & constraints

`SyntheticUser(name="alex", constraints={})` — Alex returns items through each
retailer's return web form, which requires the exact RMA (return merchandise
authorization) code the retailer emails out. The order number is not accepted in the RMA
field. The email and the return form are open on the same desktop, so this is a
within-desktop, cross-app carry.

## Scenario

Trellis Goods emailed a return authorization with a one-time RMA code. Their return
portal is a web form that accepts the RMA code to open the return. The agent must open the
email, read the RMA code, and carry it into the browser return form on the same
`windows_desktop`.

## Environments & apps

| Env | App (`type`) | Seeded state (highlights) |
| --- | --- | --- |
| `windows_desktop` | `MockEmailApp` | thread `tg_return`: sender "Trellis Goods", subject "Your return is authorized", body contains `RMA code: RMA-TG-58217`, `Order #: TG-2026-9043`, `Item: Linen throw blanket` |
| `windows_desktop` | `MockBrowserFormApp` | `fields={"rma_code":""}`, `expected_fields={"rma_code":"RMA-TG-58217"}`, `field_types={"rma_code":"text"}`, `status="drafting"`, page titled "Trellis Goods — Start a return" |

## Latent task graph (hidden from agent)

| Subtask id | Description | required_env | required_app | depends_on |
| --- | --- | --- | --- | --- |
| `read_rma` | Open the Trellis Goods email and read the RMA code. | `windows_desktop` | `email` | — |
| `submit_return` | Paste the RMA code into the return form and submit. | `windows_desktop` | `return_form` | `read_rma` |

## Required handoffs

| artifact_type | from_env | to_env | expected_value |
| --- | --- | --- | --- |
| `rma_code` | `windows_desktop` | `windows_desktop` | `RMA-TG-58217` |

(Within-env handoff: `from_env == to_env`, carrying the RMA code from the email app to the
browser form on the same device.)

## Desired final state

```
windows_desktop.return_form.status == "submitted"
```

## Decoys / ambiguity / source-of-truth

The email body shows three identifiers in one paragraph: the **RMA code** `RMA-TG-58217`
(correct), the **order number** `TG-2026-9043`, and the item name. The return form's
`rma_code` field accepts only the RMA code; an agent that grabs the more salient order
number fails the `expected_fields` match. There is exactly one return email, so the trap is
RMA-vs-order-number confusion and code fidelity, not referent ambiguity.

## Metric rationale

A naive agent reads "return code" loosely and submits the order number `TG-2026-9043`, so
the within-env handoff value never equals `RMA-TG-58217` and the form stays in `drafting`.
Only transferring the exact RMA code clears `handoff_correctness` and `global_success`.

## Verifier sketch

- **handoff_correctness (primary):** `required_handoffs` carries `expected_value=
  "RMA-TG-58217"` with `from_env == to_env == windows_desktop`; satisfied only when the
  email's RMA code is copied and pasted into the form input.
- **global_success (secondary):** `desired_final_state` checks `return_form.status ==
  "submitted"`, set when `fields["rma_code"] == expected_fields["rma_code"]`.
- **routing_accuracy (secondary):** reading pinned to `email`, submitting to `return_form`,
  both on `windows_desktop`.
- Config fields set: `desired_final_state`, `required_handoffs`.

## Implementation notes

- **`code_ready: true`.** `MockEmailApp` with one thread whose body embeds the RMA code and
  the order number; `MockBrowserFormApp` with `expected_fields={"rma_code":"RMA-TG-58217"}`.
  Solvable via `tap thread:tg_return`, `copy_value` the RMA code, `paste_value` into the
  `rma_code` input, `click submit`. `desired_final_state` path references a real
  `MockBrowserFormApp` key.
- Seed `opened_thread_id=None`, `initial_focus_env="windows_desktop"`,
  `initial_focus_app="return_form"` so the agent must open the email to find the code.
