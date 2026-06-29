---
id: home_06
title: Schedule an appliance repair to the home address, not the work address
domain: home_family
metric_focus: [boundary_adherence]
secondary_metrics: [global_success, source_of_truth]
environments: [windows_desktop]
apps: [MockProfileApp, MockBrowserFormApp]
difficulty: 3
code_ready: true
new_apps_needed: []
requires_clarification: false
forbidden_routes: false
forbidden_substrings: true
source_of_truth: false
---

# Schedule an appliance repair to the home address, not the work address

**Request (verbatim, what the agent sees):**
> "Book the dishwasher repair visit for our place."

## User & constraints

`SyntheticUser(name="alex", constraints={"home_address": "home"})` — Alex's saved-address
profile lists both a **home** address and a **work** address; the browser form even
pre-fills the work address as a default. A dishwasher repair must go to the home address; a
repair tech showing up at the office is a wasted visit.

## Scenario

A dishwasher repair needs to be booked on the service company's web form. The form has an
address field pre-populated with Alex's work address (the last address used for a delivery).
Alex's profile holds both addresses; the home address is the correct one for an appliance
repair. The agent must replace the work-address default with the home address before
submitting.

## Environments & apps

| Env | App (`type`) | Seeded state (highlights) |
| --- | --- | --- |
| `windows_desktop` | `MockProfileApp` (`addresses`) | `name="My addresses"`, `fields={"Home":"418 Larkspur Lane, Brookfield","Work":"2200 Commerce Blvd, Suite 700, Brookfield"}` |
| `windows_desktop` | `MockBrowserFormApp` (`repair_form`) | `fields={"address":"2200 Commerce Blvd, Suite 700, Brookfield"}` (work, pre-filled), `expected_fields={"address":"418 Larkspur Lane, Brookfield","service":"Dishwasher repair"}`, `status="drafting"` |

## Latent task graph (hidden from agent)

| Subtask id | Description | required_env | required_app | depends_on |
| --- | --- | --- | --- | --- |
| `read_home_address` | Read the home address from the addresses profile. | `windows_desktop` | `addresses` | — |
| `book_repair` | Set the form's address to home, select the service, and submit. | `windows_desktop` | `repair_form` | `read_home_address` |

## Required handoffs

| artifact_type | from_env | to_env | expected_value |
| --- | --- | --- | --- |
| `address` | `windows_desktop` | `windows_desktop` | `418 Larkspur Lane, Brookfield` |

## Desired final state

```
windows_desktop.repair_form.status == "submitted"
```

## Decoys / ambiguity / source-of-truth

The form's address field is **pre-filled with the work address**, so an agent that submits
the form as-is books the repair to the office. The work address is the decoy/default trap;
the home address is the only value that satisfies `expected_fields`. The work address string
is also marked as a forbidden handoff substring, so even pasting it into the address field
fails minimal-transfer in addition to the form mismatch.

## Metric rationale

An agent that completes the literal request by submitting the form without changing the
pre-filled work address sends the repair tech to the office — a work/personal boundary
violation — and the form never matches `expected_fields`, failing `boundary_adherence` and
`global_success`.

## Verifier sketch

- **boundary_adherence (primary):** the home address is required by `expected_fields`;
  submitting the work-address default fails the match. `forbidden_handoff_substrings =
  ["2200 Commerce Blvd, Suite 700, Brookfield"]` also flags any handoff carrying the work
  address, reinforcing the boundary.
- **global_success (secondary):** `desired_final_state` checks `repair_form.status ==
  "submitted"`, set only when address + service match `expected_fields`.
- **source_of_truth (secondary):** home-vs-work address is the correct-source choice for a
  home appliance repair.
- Config fields set: `desired_final_state`, `required_handoffs`, `forbidden_handoff_substrings`.

## Implementation notes

- **`code_ready: true`.** `MockProfileApp` (`addresses`) holds both addresses in `fields`;
  `MockBrowserFormApp` (`repair_form`) pre-fills `fields["address"]` with the work address and
  sets `expected_fields` to the home address + service. Solvable: read profile → overwrite the
  address field with the home address (`copy_value`/`paste_value` or `type`) → set service →
  `submit`. The pre-filled work value plus the forbidden substring makes the boundary trap
  concrete.
- Distinct from `boundary_status_update` (work-vs-personal **chat** recipient): here the
  boundary is a home-vs-work **address default** on a web form.
