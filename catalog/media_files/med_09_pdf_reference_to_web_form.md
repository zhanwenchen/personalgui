---
id: med_09
title: Move a confirmation PDF reference number into a web form
domain: media_files
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

# Move a confirmation PDF reference number into a web form

**Request (verbatim, what the agent sees):**
> "Track my Parcelink delivery — enter the reference from the confirmation PDF."

## User & constraints

`SyntheticUser(name="alex", constraints={"tracking_device": "windows_desktop"})` — Alex
downloaded a shipping-confirmation PDF that arrived by email; the carrier's tracking page is a
separate browser app on the same desktop. The reference lives in the email/PDF; the form lives
in the browser.

## Scenario

Parcelink emailed a delivery confirmation with the tracking reference printed in the body (the
downloaded PDF mirrors it). To track the parcel, the agent must read the reference number out
of the email and type it into the tracking web form — a handoff *within* the desktop, from the
email app to the browser form.

## Environments & apps

| Env | App (`type`) | Seeded state (highlights) |
| --- | --- | --- |
| `windows_desktop` | `MockEmailApp` | thread `plk1` from `Parcelink`, subject "Shipment confirmed — PL-2026", body: "Tracking reference: PLX-88241-RT. Order #774-9920, est. delivery 2026-07-01." |
| `windows_desktop` | `MockBrowserFormApp` | `fields={reference:""}`, `expected_fields={reference:"PLX-88241-RT"}`, `field_types={reference:"text"}`, `status="drafting"`, page titled "Parcelink tracking" |

## Latent task graph (hidden from agent)

| Subtask id | Description | required_env | required_app | depends_on |
| --- | --- | --- | --- | --- |
| `read_reference` | Open the confirmation email and read the tracking reference. | `windows_desktop` | `email` | — |
| `submit_tracking` | Paste the reference into the tracking form and submit. | `windows_desktop` | `tracking_form` | `read_reference` |

## Required handoffs

| artifact_type | from_env | to_env | expected_value |
| --- | --- | --- | --- |
| `reference` | `windows_desktop` | `windows_desktop` | `PLX-88241-RT` |

(Within-env handoff: `from_env == to_env`, carrying the reference from the email app to the
browser form on the same device.)

## Desired final state

```
windows_desktop.tracking_form.status == "submitted"
```

## Decoys / ambiguity / source-of-truth

The same email body shows an **order number** `#774-9920` printed right beside the tracking
reference — both look like identifiers to enter. Only the tracking reference `PLX-88241-RT`
matches `expected_fields`. A naive agent that enters the order number, or re-types a
remembered/mis-read reference (dropping a digit or confusing `RT`/`R7`), fails the form match.
One email — the trap is picking the right identifier and preserving it exactly.

## Metric rationale

An agent that enters the order number, or hand-types a remembered reference, never copies the
authoritative value from the email, so no within-env handoff is recorded and any drift fails
the form's `expected_fields` check. Only copy-from-email / paste-into-form both records the
handoff and matches the expected reference.

## Verifier sketch

- **handoff_correctness (primary):** `required_handoffs` carries `expected_value="PLX-88241-RT"`
  with `from_env == to_env == windows_desktop`; satisfied only when the email reference is
  copied and pasted into the form input.
- **global_success (secondary):** `desired_final_state` checks `tracking_form.status ==
  "submitted"`, set when `fields.reference == expected_fields.reference`.
- **routing_accuracy (secondary):** both subtasks pinned to `windows_desktop`.
- Config fields set: `desired_final_state`, `required_handoffs`.

## Implementation notes

- **`code_ready: true`.** `MockEmailApp` thread body holds the reference as readable/copyable
  text (the PDF is modeled as the same value in the email body, copyable per README);
  `MockBrowserFormApp` seeded with `expected_fields={reference:"PLX-88241-RT"}`,
  `field_types={reference:"text"}`, `status="drafting"`. Solvable via `tap thread:plk1`,
  `copy_value` on the reference, `paste_value` into `reference`, `click submit`.
  `desired_final_state` path `windows_desktop.tracking_form.status` is a real key.
- Set `initial_focus_env="windows_desktop"`, `initial_focus_app="tracking_form"` so the agent
  must navigate to the email to find the reference.
