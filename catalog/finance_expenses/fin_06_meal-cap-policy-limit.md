---
id: fin_06
title: Expense within per-meal policy cap from browser policy page
domain: finance_expenses
metric_focus: [source_of_truth]
secondary_metrics: [handoff_correctness, global_success]
environments: [windows_desktop]
apps: [MockBrowserFormApp, MockProfileApp, MockExpenseReportApp]
difficulty: 3
code_ready: true
new_apps_needed: []
requires_clarification: false
forbidden_routes: false
forbidden_substrings: false
source_of_truth: true
---

# Expense within per-meal policy cap from browser policy page

**Request (verbatim, what the agent sees):**
> "File the client dinner, but only claim up to the per-meal cap in our travel policy."

## User & constraints

`SyntheticUser(name="alex", constraints={"reimburse_rule": "per_meal_cap"})` — Alex's
employer reimburses meals only up to a per-meal cap stated on the internal policy page.
The dinner exceeded the cap, so the claimed amount must be the cap, not the receipt total.

## Scenario

Alex's client dinner cost more than the company's per-meal limit. The authoritative cap
is published on the internal travel-policy page (a read-only profile/directory). The
expense form must carry the **cap** amount, not the higher receipt total that is the
obvious "dinner" number. Everything is on the desktop.

## Environments & apps

| Env | App (`type`) | Seeded state (highlights) |
| --- | --- | --- |
| `windows_desktop` | `MockProfileApp` | `name="Travel & Expense Policy"`, `fields={"per_meal_cap":"$75.00","mileage_rate":"$0.67/mi"}` (authoritative) |
| `windows_desktop` | `MockDocumentEditorApp` | `body_field="Client dinner — Harbor Grill — receipt total $112.30"`, `status="saved"` (decoy higher amount) |
| `windows_desktop` | `MockExpenseReportApp` | `amount_field=""`, `merchant_field=""`, `status="drafting"`, `expected_amount="$75.00"` |

## Latent task graph (hidden from agent)

| Subtask id | Description | required_env | required_app | depends_on |
| --- | --- | --- | --- | --- |
| `read_cap` | Read the per-meal cap from the policy page. | `windows_desktop` | `policy_page` | — |
| `file_capped` | Enter the capped amount + merchant and submit. | `windows_desktop` | `expense_report` | `read_cap` |

## Required handoffs

| artifact_type | from_env | to_env | expected_value |
| --- | --- | --- | --- |
| `amount` | `windows_desktop` | `windows_desktop` | `$75.00` |

## Desired final state

```
windows_desktop.expense_report.status == "submitted"
```

## Decoys / ambiguity / source-of-truth

Two amounts compete: the **receipt total** `$112.30` (the salient "dinner" number, a
decoy) and the **policy cap** `$75.00` (authoritative). The expense form's
`expected_amount` is the cap. An agent that claims the full receipt total submits the
wrong figure. The policy page is the source of truth; the receipt is the higher decoy.

## Metric rationale

The reimbursable amount is duplicated against a more obvious wrong value. An agent that
files the receipt total ignores the policy constraint and fails `global_success` because
`expected_amount` is the cap. Reading the policy page and claiming the cap is the only
matching path.

## Verifier sketch

- **source_of_truth (primary):** authoritative `$75.00` is what `expected_amount` /
  `desired_final_state` require; receipt `$112.30` is the decoy that fails the form match.
- **handoff_correctness (secondary):** within-env handoff carries `$75.00` from the
  policy page into the form.
- **global_success (secondary):** `expense_report.status == "submitted"`.
- Config fields set: `desired_final_state`, `required_handoffs`.

## Implementation notes

- **`code_ready: true`.** `MockProfileApp` holds the cap in `fields`;
  `MockDocumentEditorApp` (already `saved`) holds the higher receipt total as readable
  context; `MockExpenseReportApp` enforces `expected_amount="$75.00"`. Solvable via
  reading the policy, copy/paste cap into `amount_field`, `type` merchant, `submit`.
- Merchant ("Harbor Grill") is available from the document body so the form's merchant
  requirement is satisfiable without ambiguity.
