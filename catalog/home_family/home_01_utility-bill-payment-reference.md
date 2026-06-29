---
id: home_01
title: Pay a utility bill using the emailed account/reference number
domain: home_family
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

# Pay a utility bill using the emailed account/reference number

**Request (verbatim, what the agent sees):**
> "Pay the Riverside Power bill on their site — the account number is in their email."

## User & constraints

`SyntheticUser(name="alex", constraints={})` — Alex pays the household electric bill on
the utility's own web portal, which requires the exact account/reference number printed in
the billing email. Typing the meter number or the customer-service phone number instead is
rejected. The email and the portal are both open on the same desktop, so this is a
within-desktop, cross-app handoff.

## Scenario

Riverside Power emailed this month's statement. The household payment portal is a web form
that accepts the account number plus a confirming amount due. The agent must open the
email, read the account number, and carry it into the browser form on the same
`windows_desktop`.

## Environments & apps

| Env | App (`type`) | Seeded state (highlights) |
| --- | --- | --- |
| `windows_desktop` | `MockEmailApp` | thread `riverside`: body contains `Account number: RP-4471-2208`, `Meter #: M-90871`, `Customer service: 1-800-555-0117`, `Amount due: $138.42` |
| `windows_desktop` | `MockBrowserFormApp` | `expected_fields={"account":"RP-4471-2208","amount":"$138.42"}`, `field_types={"account":"text","amount":"text"}`, `status="drafting"` |

## Latent task graph (hidden from agent)

| Subtask id | Description | required_env | required_app | depends_on |
| --- | --- | --- | --- | --- |
| `read_account` | Open Riverside Power's email and read the account number. | `windows_desktop` | `email` | — |
| `submit_payment` | Enter account number + amount on the portal form and submit. | `windows_desktop` | `payment_portal` | `read_account` |

## Required handoffs

| artifact_type | from_env | to_env | expected_value |
| --- | --- | --- | --- |
| `account_number` | `windows_desktop` | `windows_desktop` | `RP-4471-2208` |

## Desired final state

```
windows_desktop.payment_portal.status == "submitted"
```

## Decoys / ambiguity / source-of-truth

The email body lists four numbers in close proximity: the **account number**
`RP-4471-2208` (correct), the **meter number** `M-90871`, the **customer-service phone**
`1-800-555-0117`, and the **amount due** `$138.42`. The portal's `account` field accepts
only the account number; an agent that grabs the meter number or the phone number fails the
form's `expected_fields` match. The amount must also be carried, but the core trap is
account-vs-meter confusion.

## Metric rationale

A naive agent reads "account number is in their email" loosely and submits the meter number
`M-90871`, so the within-env handoff value never equals `RP-4471-2208` and the browser form
stays in `drafting`. Only transferring the exact account number clears `handoff_correctness`
and `global_success`.

## Verifier sketch

- **handoff_correctness (primary):** `required_handoffs` with `from_env == to_env ==
  windows_desktop` and `expected_value="RP-4471-2208"`.
- **global_success (secondary):** `desired_final_state` checks `payment_portal.status ==
  "submitted"`, which `MockBrowserFormApp` sets only when every field equals
  `expected_fields`.
- **routing_accuracy (secondary):** reading pinned to `email`, submitting to
  `payment_portal`, both on `windows_desktop`.
- Config fields set: `desired_final_state`, `required_handoffs`.

## Implementation notes

- **`code_ready: true`.** `MockEmailApp` with a single thread whose body embeds all four
  numbers; `MockBrowserFormApp` with `expected_fields` for `account` and `amount`. Solvable
  via `tap thread:riverside` to open, `copy_value` the account number, `paste_value` into
  the `account` input, then enter the amount and `submit`. All `desired_final_state` paths
  reference real `MockBrowserFormApp` keys.
- Seed `opened_thread_id=None` so the agent must open the email first.
- Distinct from `fin_02`: this is a household utility (account number vs meter/phone), not a
  vendor invoice (payment reference vs invoice number).
