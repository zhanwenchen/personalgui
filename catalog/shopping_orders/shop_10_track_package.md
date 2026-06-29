---
id: shop_10
title: Track a package using the tracking number from email
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

# Track a package using the tracking number from email

**Request (verbatim, what the agent sees):**
> "Track my Pinegrove order — the tracking number is in the shipping email."

## User & constraints

`SyntheticUser(name="alex", constraints={})` — Alex tracks shipments on the carrier's website by
entering the tracking number. The shipping email contains the carrier tracking number; the carrier's
tracking web form is a separate browser app on the same desktop. The order number is not a valid
tracking number and is rejected by the carrier form.

## Scenario

Pinegrove Home shipped an order and emailed a shipping notice with the carrier tracking number. The
carrier's tracking page is a web form that returns delivery status when the tracking number is
entered. The agent must open the shipping email, read the tracking number, and enter it into the
carrier's tracking form on the same `windows_desktop`, then submit.

## Environments & apps

| Env | App (`type`) | Seeded state (highlights) |
| --- | --- | --- |
| `windows_desktop` | `MockEmailApp` | thread `pg_ship`: sender "Pinegrove Home", subject "Your order has shipped", body: `Tracking number: 1Z994AX21205398765` (carrier "Meridian Freight"), `Order #: PG-3320` |
| `windows_desktop` | `MockBrowserFormApp` | `fields={"tracking_number":""}`, `expected_fields={"tracking_number":"1Z994AX21205398765"}`, `field_types={"tracking_number":"text"}`, `status="drafting"`, page titled "Meridian Freight — Track a package" |

## Latent task graph (hidden from agent)

| Subtask id | Description | required_env | required_app | depends_on |
| --- | --- | --- | --- | --- |
| `read_tracking` | Open the shipping email and read the tracking number. | `windows_desktop` | `email` | — |
| `submit_tracking` | Paste the tracking number into the carrier form and submit. | `windows_desktop` | `tracking_form` | `read_tracking` |

## Required handoffs

| artifact_type | from_env | to_env | expected_value |
| --- | --- | --- | --- |
| `tracking_number` | `windows_desktop` | `windows_desktop` | `1Z994AX21205398765` |

## Desired final state

```
windows_desktop.tracking_form.status == "submitted"
```

## Decoys / ambiguity / source-of-truth

The email body shows the **tracking number** `1Z994AX21205398765` (correct) alongside the **order
number** `PG-3320`. The carrier form accepts only the tracking number; an agent that submits the
order number fails the `expected_fields` match. The tracking number is long, so any character drift
from re-typing also fails. There is one shipping email, so the trap is tracking-vs-order-number
confusion and code fidelity, not referent ambiguity.

## Metric rationale

A naive agent enters the shorter, friendlier order number `PG-3320`, or re-types the long tracking
number and drops a character, so the within-env handoff never equals `1Z994AX21205398765` and the
form stays in `drafting`. Only copy-from-email / paste-into-form both records the handoff and matches.

## Verifier sketch

- **handoff_correctness (primary):** `required_handoffs` carries `expected_value=
  "1Z994AX21205398765"`, `from_env == to_env == windows_desktop`; satisfied only when the tracking
  number is copied and pasted into the form input.
- **global_success (secondary):** `desired_final_state` checks `tracking_form.status == "submitted"`,
  set when `tracking_number == expected_fields["tracking_number"]`.
- **routing_accuracy (secondary):** reading on `email`, submitting on `tracking_form`, both
  `windows_desktop`.
- Config fields set: `desired_final_state`, `required_handoffs`.

## Implementation notes

- **`code_ready: true`.** `MockEmailApp` shipping thread embedding the tracking number and the order
  number; `MockBrowserFormApp` with `expected_fields={"tracking_number":"1Z994AX21205398765"}`,
  `status="drafting"`. Solvable via `tap thread:pg_ship`, `copy_value` the tracking number,
  `paste_value` into `tracking_number`, `click submit`.
- Set `initial_focus_env="windows_desktop"`, `initial_focus_app="tracking_form"`,
  `opened_thread_id=None` so the agent must open the email to find the number.
