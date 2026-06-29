---
id: wrk_04
title: Copy the discount rate from a quote into the renewal pricing form
domain: work_docs_projects
metric_focus: [handoff_correctness]
secondary_metrics: [global_success, routing_accuracy]
environments: [windows_desktop]
apps: [MockDocumentEditorApp, MockBrowserFormApp]
difficulty: 2
code_ready: true
new_apps_needed: []
requires_clarification: false
forbidden_routes: false
forbidden_substrings: false
source_of_truth: false
---

# Copy the discount rate from a quote into the renewal pricing form

**Request (verbatim, what the agent sees):**
> "The renewal quote lists the discount we offered — enter that discount rate into the pricing approval form and submit."

## User & constraints

`SyntheticUser(name="alex", constraints={"work_account": "alex@northwind.example"})` — the
approval form expects the negotiated **discount rate** (a percentage), distinct from the
total contract price. The figure must be carried exactly as written in the quote.

## Scenario

Alex negotiated a renewal and the signed quote document records the agreed discount rate.
A separate web "pricing approval" form needs that rate entered before finance signs off.
Both the quote doc and the form live on the work laptop. This is a same-desktop figure
handoff — deliberately a *different field and value* than the existing `contract_price_update`
task: here the artifact is a discount **percentage** entered into a web form's
`discount_rate` field, not a flat fee written into a contract body.

## Environments & apps

| Env | App (`type`) | Seeded state (highlights) |
| --- | --- | --- |
| `windows_desktop` | `MockDocumentEditorApp` | `title="Northwind Renewal — Signed Quote"`, `body_field` includes line items and the line `"Negotiated discount: 17.5% off list (applies to all seats)"`, `status="saved"` (read-only source) |
| `windows_desktop` | `MockBrowserFormApp` | `title="Pricing Approval"`, `expected_fields={"discount_rate":"17.5%","customer":"Northwind"}`, `field_types={"discount_rate":"text","customer":"text"}`, `status="drafting"` |

## Latent task graph (hidden from agent)

| Subtask id | Description | required_env | required_app | depends_on |
| --- | --- | --- | --- | --- |
| `read_discount` | Find the negotiated discount rate in the quote doc | `windows_desktop` | `quote_doc` | — |
| `submit_form` | Enter the rate (and customer) in the approval form and submit | `windows_desktop` | `pricing_form` | `read_discount` |

## Required handoffs

| artifact_type | from_env | to_env | expected_value |
| --- | --- | --- | --- |
| `discount_rate` | `windows_desktop` | `windows_desktop` | `17.5%` |

## Desired final state

```
windows_desktop.pricing_form.status == "submitted"
```

## Decoys / ambiguity / source-of-truth

The quote body also lists a **list price** (`$48,000`) and a **per-seat price** (`$240`) in
the same block as the discount line. An agent that grabs the most prominent dollar figure
enters a price instead of the rate, and the form's `expected_fields` (which wants `17.5%`)
rejects it. The trap is multiple numbers in one paragraph where only the percentage is the
target field.

## Metric rationale

An agent that completes "enter the discount" by transferring a dollar amount, or that
rounds `17.5%` to `18%`, submits a value the form does not accept; it stays in `drafting`
and `handoff_correctness` + `global_success` fail. Only the exact `17.5%` carried into the
`discount_rate` field passes.

## Verifier sketch

- **handoff_correctness (primary):** `required_handoffs` carries `17.5%` from `quote_doc`
  into `pricing_form` (same env). Pass only if the exact rate was transferred.
- **global_success (secondary):** `pricing_form.status == "submitted"`, reached only when
  every `expected_fields` entry matches.
- **routing_accuracy (secondary):** both subtasks on `windows_desktop`; fails only if a
  route is invented.
- Config fields set: `desired_final_state`, `required_handoffs`.

## Implementation notes

- **`code_ready: true`.** `MockDocumentEditorApp` (already `saved`) holds the quote with the
  discount line plus dollar-amount decoys; `MockBrowserFormApp` enforces
  `expected_fields={"discount_rate":"17.5%","customer":"Northwind"}`. Solvable via reading
  the quote, copy/paste `17.5%` into `discount_rate`, type `Northwind`, then `submit`.
  Distinct from `contract_price_update`: different app surface (web form vs doc body),
  different artifact (percentage vs flat fee), different field name.
