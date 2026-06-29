---
id: shop_02
title: Apply the emailed gift-card code at checkout
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

# Apply the emailed gift-card code at checkout

**Request (verbatim, what the agent sees):**
> "Apply my Northport gift card at checkout — the code is in the email they sent."

## User & constraints

`SyntheticUser(name="alex", constraints={})` — Alex was emailed a digital gift card and
wants it applied to the order in the Northport checkout web form. The checkout's redemption
field requires the exact gift-card code; the gift-card number is a different (longer)
identifier and is rejected. Email and checkout are open on the same desktop.

## Scenario

Northport Outfitters emailed a digital gift card with a redemption code. The checkout web
form has a "gift card / promo code" field that finalizes the discount when the correct code
is submitted. The agent must open the email, read the redemption code, and enter it into the
checkout form on the same `windows_desktop`, then submit.

## Environments & apps

| Env | App (`type`) | Seeded state (highlights) |
| --- | --- | --- |
| `windows_desktop` | `MockEmailApp` | thread `np_gift`: sender "Northport Outfitters", subject "Your $50 gift card", body contains `Redemption code: NPGIFT-7K2Q9`, `Card number: 6011-2200-4417-8890`, `Balance: $50.00` |
| `windows_desktop` | `MockBrowserFormApp` | `fields={"promo_code":""}`, `expected_fields={"promo_code":"NPGIFT-7K2Q9"}`, `field_types={"promo_code":"text"}`, `status="drafting"`, page titled "Northport checkout" |

## Latent task graph (hidden from agent)

| Subtask id | Description | required_env | required_app | depends_on |
| --- | --- | --- | --- | --- |
| `read_code` | Open the gift-card email and read the redemption code. | `windows_desktop` | `email` | — |
| `apply_code` | Enter the redemption code in the checkout form and submit. | `windows_desktop` | `checkout_form` | `read_code` |

## Required handoffs

| artifact_type | from_env | to_env | expected_value |
| --- | --- | --- | --- |
| `promo_code` | `windows_desktop` | `windows_desktop` | `NPGIFT-7K2Q9` |

## Desired final state

```
windows_desktop.checkout_form.status == "submitted"
```

## Decoys / ambiguity / source-of-truth

The email body shows both the short **redemption code** `NPGIFT-7K2Q9` (correct, what the
promo field accepts) and a longer **card number** `6011-2200-4417-8890` that looks more like
the "real" card identity. The checkout's `promo_code` field accepts only the redemption
code; an agent that pastes the card-number string fails the `expected_fields` match. The
trap is redemption-code-vs-card-number confusion.

## Metric rationale

A naive agent treats the long card number as "the gift card" and submits it, so the carried
value never equals `NPGIFT-7K2Q9` and the checkout stays in `drafting`. Only carrying the
exact redemption code clears `handoff_correctness` and drives `status == "submitted"`.

## Verifier sketch

- **handoff_correctness (primary):** `required_handoffs` carries `expected_value=
  "NPGIFT-7K2Q9"`, `from_env == to_env == windows_desktop`; satisfied only when the email's
  redemption code is copied and pasted into the `promo_code` input.
- **global_success (secondary):** `desired_final_state` checks `checkout_form.status ==
  "submitted"`, set when `fields["promo_code"] == expected_fields["promo_code"]`.
- **routing_accuracy (secondary):** reading on `email`, submitting on `checkout_form`, both
  `windows_desktop`.
- Config fields set: `desired_final_state`, `required_handoffs`.

## Implementation notes

- **`code_ready: true`.** `MockEmailApp` one thread embedding the redemption code and the
  decoy card number in the same paragraph; `MockBrowserFormApp` with
  `expected_fields={"promo_code":"NPGIFT-7K2Q9"}`, `status="drafting"`. Solvable via
  `tap thread:np_gift`, `copy_value` the redemption code, `paste_value` into `promo_code`,
  `click submit`.
- Set `initial_focus_env="windows_desktop"`, `initial_focus_app="checkout_form"`,
  `opened_thread_id=None`.
