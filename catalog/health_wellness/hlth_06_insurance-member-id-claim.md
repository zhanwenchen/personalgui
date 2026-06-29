---
id: hlth_06
title: Copy insurance member ID from card photo into desktop claim form
domain: health_wellness
metric_focus: [handoff_correctness]
secondary_metrics: [global_success, routing_accuracy]
environments: [android_phone, windows_desktop]
apps: [MockPhotosApp, MockBrowserFormApp]
difficulty: 2
code_ready: true
new_apps_needed: []
requires_clarification: false
forbidden_routes: false
forbidden_substrings: false
source_of_truth: false
---

# Copy insurance member ID from card photo into desktop claim form

**Request (verbatim, what the agent sees):**
> "Start my insurance claim — fill in my member ID from the photo of my card."

## User & constraints

`SyntheticUser(name="alex", constraints={"claim_device": "windows_desktop"})` — Alex
photographed the insurance card on the phone; the claim form is a desktop-only web form.
The member ID lives behind the card photo on the phone.

## Scenario

Alex needs to file a claim with BlueRidge Health. The desktop claim form requires the
member ID printed on the insurance card, and the only place that number lives is a photo
of the card on Alex's phone. The agent must read the member ID off the phone photo and
enter it into the desktop claim form — a phone-to-desktop handoff.

## Environments & apps

| Env | App (`type`) | Seeded state (highlights) |
| --- | --- | --- |
| `android_phone` | `MockPhotosApp` (card photo) | `amount="BRH-77A-309148"` (member ID modeled as the copyable value), `merchant="BlueRidge Health"`, `date="2026-06-28"` |
| `windows_desktop` | `MockBrowserFormApp` (claim form) | `fields={"member_id":""}`, `expected_fields={"member_id":"BRH-77A-309148"}`, `field_types={"member_id":"text"}`, `status="drafting"` |

## Latent task graph (hidden from agent)

| Subtask id | Description | required_env | required_app | depends_on |
| --- | --- | --- | --- | --- |
| `read_member_id` | Read the member ID from the card photo. | `android_phone` | `phone_photos` | — |
| `enter_member_id` | Enter the member ID on the claim form and submit. | `windows_desktop` | `claim_form` | `read_member_id` |

## Required handoffs

| artifact_type | from_env | to_env | expected_value |
| --- | --- | --- | --- |
| `member_id` | `android_phone` | `windows_desktop` | `BRH-77A-309148` |

## Desired final state

```
windows_desktop.claim_form.status == "submitted"
```

## Decoys / ambiguity / source-of-truth

The card photo caption also shows a group number ("Group 0042") and a customer-service
phone, both ID-shaped and mis-copyable. Only the member ID `BRH-77A-309148` is required.
There is one card, so the trap is fidelity: transposing a digit or grabbing the group
number fails the exact form match.

## Metric rationale

The claim form reaches `submitted` only when `fields["member_id"] == expected_fields`. An
agent that types a remembered/partial ID, or copies the group number, records no correct
`android_phone → windows_desktop` handoff and fails both `handoff_correctness` and
`global_success`. Only copy-from-photo / paste-into-form passes.

## Verifier sketch

- **handoff_correctness (primary):** `required_handoffs` carries the member ID from
  `android_phone` to `windows_desktop`; satisfied only by copy-then-paste of the photo
  value.
- **global_success (secondary):** `desired_final_state` checks `claim_form.status ==
  "submitted"`, set when the member-id field matches.
- **routing_accuracy (secondary):** reading pinned to the phone photo, entry to the
  desktop form.
- Config fields set: `desired_final_state`, `required_handoffs`.

## Implementation notes

- **`code_ready: true`.** `MockPhotosApp` models the member ID as its copyable `amount`
  slot (the copyable value need not be a currency amount; here it is the alphanumeric
  member ID — a small field-name mismatch only, no new behavior). `MockBrowserFormApp`
  seeded with `expected_fields={"member_id": ...}`, `status="drafting"`. Solvable via
  `copy_value` the photo value, `paste_value` into the `member_id` field, `click submit`.
- If a cleaner mapping is wanted, rename the photo's copyable field to `value` in the
  builder; behavior is identical. Set `initial_focus_env="windows_desktop"`,
  `initial_focus_app="claim_form"`.
