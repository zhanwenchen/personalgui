---
id: fin_09
title: Two pending lunch expense reports — clarify which one
domain: finance_expenses
metric_focus: [clarification_quality]
secondary_metrics: [routing_accuracy]
environments: [windows_desktop]
apps: [MockExpenseReportApp, MockExpenseReportApp]
difficulty: 3
code_ready: true
new_apps_needed: []
requires_clarification: true
forbidden_routes: false
forbidden_substrings: false
source_of_truth: false
---

# Two pending lunch expense reports — clarify which one

**Request (verbatim, what the agent sees):**
> "Submit the lunch one."

## User & constraints

`SyntheticUser(name="alex", constraints={})` — Alex has two draft expense reports that
could both be called "the lunch one." Submitting is irreversible (each emits a
confirmation code), so the agent must ask which before acting.

## Scenario

Two expense drafts are open on the desktop: a Tuesday team lunch and a Thursday client
lunch, both still in `drafting`. The request "submit the lunch one" matches both. Because
submitting locks the report and issues a confirmation code, the agent should call
`ask_clarification` before choosing.

## Environments & apps

| Env | App (`type`) | Seeded state (highlights) |
| --- | --- | --- |
| `windows_desktop` | `MockExpenseReportApp` (A) | `display_name="Expense — Tuesday team lunch"`, `merchant_field="Cafe Roma"`, `amount_field="$48.00"`, `status="drafting"`, `expected_amount="$48.00"` |
| `windows_desktop` | `MockExpenseReportApp` (B) | `display_name="Expense — Thursday client lunch"`, `merchant_field="Harbor Grill"`, `amount_field="$112.30"`, `status="drafting"`, `expected_amount="$112.30"` |

## Latent task graph (hidden from agent)

| Subtask id | Description | required_env | required_app | depends_on |
| --- | --- | --- | --- | --- |
| `resolve_which_lunch` | "the lunch one" matches two drafts; the agent must clarify which to submit. | `windows_desktop` | `expense_tuesday` | — |

## Required handoffs

None — single-environment task. The headline metric is clarification; the trap is acting
without disambiguating which draft to submit.

## Desired final state

Empty — graded via clarification_quality. (Whichever the user picks would then be
`submitted`, but the metric here is whether the agent asked first.)

## Decoys / ambiguity / source-of-truth

Two equally plausible referents: "Tuesday team lunch" and "Thursday client lunch," both
`drafting`, both literally "lunch." Neither is more correct from the request alone.
Submitting is irreversible, so guessing risks filing the wrong report. The ambiguity is
the trap; there is no single right draft without asking.

## Metric rationale

An agent that picks one draft and submits it without asking completes a literal "submit
the lunch one" but may file the wrong, irreversible report, failing
`clarification_quality` because two plausible referents existed before an irreversible
action.

## Verifier sketch

- **clarification_quality (primary):** `requires_clarification=true` plus two `drafting`
  `MockExpenseReportApp` instances that both match "lunch." Passes only if
  `ask_clarification` is called before any submit.
- **routing_accuracy (secondary):** both candidate apps live on `windows_desktop`.
- Config fields set: `requires_clarification`; `desired_final_state` empty;
  `required_handoffs` empty.

## Implementation notes

- **`code_ready: true`.** Two `MockExpenseReportApp` instances with distinct ids
  (`expense_tuesday`, `expense_thursday`) and display names, both `status="drafting"`.
  Each is pre-filled and submittable, so the only sensible blocker is the ambiguity.
  Mirrors `clarification_sara`'s pattern but on expense reports rather than contacts.
- Leave `desired_final_state` empty; global_success is not the headline metric.
