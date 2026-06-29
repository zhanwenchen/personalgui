---
id: shop_11
title: Confirm a subscribe-and-save recurring order with the emailed code
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

# Confirm a subscribe-and-save recurring order with the emailed code

**Request (verbatim, what the agent sees):**
> "Confirm my Verdant Pantry subscribe-and-save — use the confirmation code they emailed."

## User & constraints

`SyntheticUser(name="alex", constraints={})` — Alex set up a recurring (subscribe-and-save) order
and the retailer emailed a confirmation code to activate the subscription. The retailer's
confirmation web form requires that exact code to switch the subscription from pending to active;
the subscription/plan ID is a different identifier and is rejected. Email and form are on the same
desktop.

## Scenario

Verdant Pantry emailed a confirmation code to activate Alex's subscribe-and-save plan. The
retailer's web form finalizes the recurring order once the confirmation code is entered. The agent
must open the email, read the confirmation code, and enter it into the confirmation form on the
same `windows_desktop`, then submit to activate the recurring order.

## Environments & apps

| Env | App (`type`) | Seeded state (highlights) |
| --- | --- | --- |
| `windows_desktop` | `MockEmailApp` | thread `vp_subscribe`: sender "Verdant Pantry", subject "Confirm your subscribe-and-save", body: `Confirmation code: VP-SUB-3380`, `Plan ID: PLAN-90217`, `Ships every 4 weeks` |
| `windows_desktop` | `MockBrowserFormApp` | `fields={"confirmation_code":""}`, `expected_fields={"confirmation_code":"VP-SUB-3380"}`, `field_types={"confirmation_code":"text"}`, `status="drafting"`, page titled "Verdant Pantry — Confirm subscription" |

## Latent task graph (hidden from agent)

| Subtask id | Description | required_env | required_app | depends_on |
| --- | --- | --- | --- | --- |
| `read_code` | Open the subscribe-and-save email and read the confirmation code. | `windows_desktop` | `email` | — |
| `confirm_sub` | Enter the confirmation code in the form and submit to activate. | `windows_desktop` | `subscribe_form` | `read_code` |

## Required handoffs

| artifact_type | from_env | to_env | expected_value |
| --- | --- | --- | --- |
| `confirmation_code` | `windows_desktop` | `windows_desktop` | `VP-SUB-3380` |

## Desired final state

```
windows_desktop.subscribe_form.status == "submitted"
```

## Decoys / ambiguity / source-of-truth

The email body shows both the **confirmation code** `VP-SUB-3380` (correct) and the **plan ID**
`PLAN-90217`, which looks like the natural identifier for "the subscription." The form's
`confirmation_code` field accepts only the confirmation code; an agent that submits the plan ID fails
the `expected_fields` match. There is one subscription email, so the trap is code-vs-plan-ID confusion
and fidelity, not referent ambiguity.

## Metric rationale

A naive agent treats the plan ID `PLAN-90217` as "the subscription code" and submits it, so the
within-env handoff never equals `VP-SUB-3380` and the form stays in `drafting`. Only carrying the
exact confirmation code clears `handoff_correctness` and drives `status == "submitted"` (subscription
active).

## Verifier sketch

- **handoff_correctness (primary):** `required_handoffs` carries `expected_value="VP-SUB-3380"`,
  `from_env == to_env == windows_desktop`; satisfied only when the confirmation code is copied and
  pasted into the form input.
- **global_success (secondary):** `desired_final_state` checks `subscribe_form.status ==
  "submitted"`, set when `confirmation_code == expected_fields["confirmation_code"]`.
- **routing_accuracy (secondary):** reading on `email`, confirming on `subscribe_form`, both
  `windows_desktop`.
- Config fields set: `desired_final_state`, `required_handoffs`.

## Implementation notes

- **`code_ready: true`.** `MockEmailApp` thread embedding the confirmation code and the decoy plan
  ID; `MockBrowserFormApp` with `expected_fields={"confirmation_code":"VP-SUB-3380"}`,
  `status="drafting"`. Solvable via `tap thread:vp_subscribe`, `copy_value` the confirmation code,
  `paste_value` into `confirmation_code`, `click submit`.
- Set `initial_focus_env="windows_desktop"`, `initial_focus_app="subscribe_form"`,
  `opened_thread_id=None` so the agent must open the email to find the code.
