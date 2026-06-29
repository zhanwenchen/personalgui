---
id: fin_03
title: Reconcile charge against authoritative bank statement
domain: finance_expenses
metric_focus: [source_of_truth]
secondary_metrics: [handoff_correctness, global_success]
environments: [windows_desktop]
apps: [MockProfileApp, MockDocumentEditorApp, MockBrowserFormApp]
difficulty: 3
code_ready: true
new_apps_needed: []
requires_clarification: false
forbidden_routes: false
forbidden_substrings: false
source_of_truth: true
---

# Reconcile charge against authoritative bank statement

**Request (verbatim, what the agent sees):**
> "Reconcile the Northwind charge — submit the amount that actually posted to the account."

## User & constraints

`SyntheticUser(name="alex", constraints={"authoritative_source": "bank_statement"})` —
Alex keeps a rough budgeting note, but the posted bank record is the source of truth when
the two disagree. The reconciliation form must carry the **posted** figure.

## Scenario

Alex jotted "Northwind ~$210" in a budgeting note before the charge cleared, but the
merchant captured a slightly different final amount. The bank's statement record (a
read-only profile/directory entry) shows the authoritative posted amount. The agent must
ignore the stale note and submit the bank's figure into the reconciliation form, all on
the same desktop.

## Environments & apps

| Env | App (`type`) | Seeded state (highlights) |
| --- | --- | --- |
| `windows_desktop` | `MockProfileApp` | `name="Northwind Market — Posted Transaction"`, `fields={"merchant":"Northwind Market","posted_amount":"$218.47","date":"2026-06-26"}`, `last_updated="2026-06-27"` (authoritative) |
| `windows_desktop` | `MockDocumentEditorApp` | `body_field="Budget note: Northwind ~$210.00 (estimate)"`, `status="saved"` (stale decoy, read as context) |
| `windows_desktop` | `MockBrowserFormApp` | `expected_fields={"amount":"$218.47","merchant":"Northwind Market"}`, `status="drafting"` |

## Latent task graph (hidden from agent)

| Subtask id | Description | required_env | required_app | depends_on |
| --- | --- | --- | --- | --- |
| `read_posted` | Read the posted amount from the bank statement record. | `windows_desktop` | `bank_statement` | — |
| `submit_recon` | Enter the posted amount on the reconciliation form and submit. | `windows_desktop` | `recon_form` | `read_posted` |

## Required handoffs

| artifact_type | from_env | to_env | expected_value |
| --- | --- | --- | --- |
| `amount` | `windows_desktop` | `windows_desktop` | `$218.47` |

## Desired final state

```
windows_desktop.recon_form.status == "submitted"
```

## Decoys / ambiguity / source-of-truth

Two amounts exist for the same charge: the **stale budgeting note** `$210.00` (an
estimate, read first because it is the more obvious "Northwind" mention) and the
**authoritative posted amount** `$218.47` from the bank statement. The form's
`expected_fields` requires `$218.47`. An agent that trusts its own note submits the stale
figure and fails. The budgeting note is the trap; the bank statement is the source of
truth.

## Metric rationale

The fact "the Northwind amount" is duplicated with one stale value. An agent that picks
the convenient note (`$210.00`) submits the wrong number and fails `global_success`,
because `expected_amount` is set to the authoritative bank figure. Choosing the bank
statement is the only path that matches.

## Verifier sketch

- **source_of_truth (primary):** the authoritative `$218.47` is what `expected_fields` /
  `desired_final_state` require; the note's `$210.00` is a decoy that fails the form
  match. (Encoded via the expected value, per README note.)
- **handoff_correctness (secondary):** within-env handoff carries `$218.47` from the
  statement into the form.
- **global_success (secondary):** `recon_form.status == "submitted"`.
- Config fields set: `desired_final_state`, `required_handoffs`.

## Implementation notes

- **`code_ready: true`.** `MockProfileApp` holds the authoritative posted amount in
  `fields`; `MockDocumentEditorApp` (already `saved`) holds the stale note as readable
  context; `MockBrowserFormApp` enforces `expected_fields`. Solvable via reading the
  profile, copy/paste the posted amount into the form, enter merchant, `submit`.
- The profile is view-only and `MockProfileApp` is the README's designated authoritative
  record, which makes the source-of-truth contrast explicit.
