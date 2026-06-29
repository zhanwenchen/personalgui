---
id: fin_10
title: File converted-currency amount from email, not foreign receipt
domain: finance_expenses
metric_focus: [source_of_truth]
secondary_metrics: [handoff_correctness, global_success]
environments: [android_phone, windows_desktop]
apps: [MockPhotosApp, MockEmailApp, MockExpenseReportApp]
difficulty: 4
code_ready: true
new_apps_needed: []
requires_clarification: false
forbidden_routes: false
forbidden_substrings: false
source_of_truth: true
---

# File converted-currency amount from email, not foreign receipt

**Request (verbatim, what the agent sees):**
> "Expense the Tokyo hotel — claim the converted USD amount finance confirmed, not the yen."

## User & constraints

`SyntheticUser(name="alex", constraints={"reimburse_currency": "USD", "authoritative_conversion": "finance_email"})`
— The expense system reimburses in USD. Finance's emailed converted figure is
authoritative; the yen amount on the receipt photo is the foreign-currency decoy.

## Scenario

Alex's hotel receipt photo on the phone shows a yen amount. Finance emailed the agreed
USD conversion to use for the claim. The desktop expense form must carry the **USD**
figure from the email, not the yen number from the photo. The email and form are on the
desktop; the receipt photo is on the phone.

## Environments & apps

| Env | App (`type`) | Seeded state (highlights) |
| --- | --- | --- |
| `android_phone` | `MockPhotosApp` | `amount="¥48,900"`, `merchant="Sakura Hotel Tokyo"`, `date="2026-06-20"` (foreign-currency decoy) |
| `windows_desktop` | `MockEmailApp` | thread `finance_fx`: body `Approved conversion for the Tokyo hotel: claim $327.85 USD (rate locked 2026-06-21).` (authoritative) |
| `windows_desktop` | `MockExpenseReportApp` | `amount_field=""`, `merchant_field=""`, `status="drafting"`, `expected_amount="$327.85"` |

## Latent task graph (hidden from agent)

| Subtask id | Description | required_env | required_app | depends_on |
| --- | --- | --- | --- | --- |
| `see_receipt` | Note the foreign-currency receipt on the phone. | `android_phone` | `phone_photos` | — |
| `read_usd` | Read the approved USD amount from finance's email. | `windows_desktop` | `email` | — |
| `file_usd` | Enter the USD amount + merchant and submit. | `windows_desktop` | `expense_report` | `read_usd` |

## Required handoffs

| artifact_type | from_env | to_env | expected_value |
| --- | --- | --- | --- |
| `amount` | `windows_desktop` | `windows_desktop` | `$327.85` |

## Desired final state

```
windows_desktop.expense_report.status == "submitted"
```

## Decoys / ambiguity / source-of-truth

The same expense has two amounts: the **yen receipt** `¥48,900` (the salient "hotel"
number, a decoy in the wrong currency) and the **approved USD conversion** `$327.85`
(authoritative). The form's `expected_amount` is the USD figure. An agent that copies the
phone's yen amount — or self-converts — fails. The finance email is the source of truth.

## Metric rationale

The reimbursable amount is duplicated across currencies; only finance's emailed USD figure
is authoritative. An agent that transfers the yen amount (or its own conversion) submits a
value that never equals `expected_amount`, failing `global_success`.

## Verifier sketch

- **source_of_truth (primary):** authoritative `$327.85` is what `expected_amount` /
  `desired_final_state` require; `¥48,900` is the decoy that fails the form match.
- **handoff_correctness (secondary):** within-desktop handoff carries `$327.85` from the
  email into the form.
- **global_success (secondary):** `expense_report.status == "submitted"`.
- Config fields set: `desired_final_state`, `required_handoffs`.

## Implementation notes

- **`code_ready: true`.** `MockPhotosApp` (yen decoy) on phone; `MockEmailApp` with the
  finance FX thread and `MockExpenseReportApp` (`expected_amount="$327.85"`) on desktop.
  Solvable by reading finance's email, copy/paste the USD amount into `amount_field`,
  `type` merchant, `submit`. The phone is present to create the cross-currency trap but
  the canonical handoff is within the desktop.
- Seed `opened_thread_id=None` so the email must be opened.
