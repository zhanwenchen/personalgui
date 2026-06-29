---
id: hlth_10
title: Pay copay on billing portal using reference number from bill email
domain: health_wellness
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

# Pay copay on billing portal using reference number from bill email

**Request (verbatim, what the agent sees):**
> "Pay my clinic copay — use the reference number from the bill they emailed."

## User & constraints

`SyntheticUser(name="alex", constraints={})` — The billing portal looks up the copay by a
reference (account) number printed in the bill email. The agent must carry that exact
reference into the portal's payment form on the same desktop.

## Scenario

Cedar Hollow Billing emailed a statement: "Copay due $35.00. Reference number:
INV-2026-55831. Pay online at the patient billing portal." The desktop billing portal's
payment form requires the reference number to locate and settle the copay. The agent must
read the reference from the email and enter it into the portal form — a within-desktop
carry from inbox to web form.

## Environments & apps

| Env | App (`type`) | Seeded state (highlights) |
| --- | --- | --- |
| `windows_desktop` | `MockEmailApp` (inbox) | thread `t_bill`: sender "Cedar Hollow Billing", body "Copay due $35.00. Reference number: INV-2026-55831." |
| `windows_desktop` | `MockBrowserFormApp` (billing portal) | `fields={"reference":"","amount":""}`, `expected_fields={"reference":"INV-2026-55831","amount":"$35.00"}`, `field_types={"reference":"text","amount":"text"}`, `status="drafting"` |

## Latent task graph (hidden from agent)

| Subtask id | Description | required_env | required_app | depends_on |
| --- | --- | --- | --- | --- |
| `read_ref` | Read the reference number (and amount) from the bill email. | `windows_desktop` | `email` | — |
| `pay_copay` | Enter reference + amount in the portal and submit payment. | `windows_desktop` | `billing_portal` | `read_ref` |

## Required handoffs

| artifact_type | from_env | to_env | expected_value |
| --- | --- | --- | --- |
| `reference` | `windows_desktop` | `windows_desktop` | `INV-2026-55831` |

## Desired final state

```
windows_desktop.billing_portal.status == "submitted"
```

## Decoys / ambiguity / source-of-truth

The email footer also lists a clinic phone and a prior statement number
("Prev: INV-2026-41020"), both reference-shaped. Only the current `INV-2026-55831` settles
this copay. The trap is grabbing the previous statement's number or transposing a digit,
which fails the exact form match.

## Metric rationale

The portal reaches `submitted` only when both `reference` and `amount` match
`expected_fields`. An agent that types a remembered/previous reference records no correct
within-desktop handoff for `INV-2026-55831` and fails `handoff_correctness` and
`global_success`. Only copy-from-email / paste-into-form passes.

## Verifier sketch

- **handoff_correctness (primary):** `required_handoffs` carries
  `expected_value="INV-2026-55831"` within `windows_desktop`; satisfied only by
  copy-then-paste of the email reference.
- **global_success (secondary):** `desired_final_state` checks `billing_portal.status ==
  "submitted"`, set when every field matches `expected_fields`.
- **routing_accuracy (secondary):** reading pinned to `email`, payment to `billing_portal`.
- Config fields set: `desired_final_state`, `required_handoffs`.

## Implementation notes

- **`code_ready: true`.** `MockEmailApp` holds the reference + amount. `MockBrowserFormApp`
  seeded with `expected_fields={"reference":"INV-2026-55831","amount":"$35.00"}`,
  `status="drafting"`. Solvable via `copy_value`/`paste_value` of the reference, `type` the
  amount, `click submit`.
- Set `initial_focus_env="windows_desktop"`, `initial_focus_app="billing_portal"` so the
  agent must navigate to the inbox to find the reference.
