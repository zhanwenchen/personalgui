---
id: med_01
title: Screenshot code from phone photo into desktop web form
domain: media_files
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

# Screenshot code from phone photo into desktop web form

**Request (verbatim, what the agent sees):**
> "Use the warranty code from the screenshot I saved to register my Brightwave speaker."

## User & constraints

`SyntheticUser(name="alex", constraints={"registration_device": "windows_desktop"})` —
Alex snapped a photo of the warranty card printed inside the speaker box, and the only
place to register the product is the desktop browser. The code lives behind a phone photo;
the registration form lives on the desktop.

## Scenario

Alex bought a Brightwave speaker and photographed the warranty card so the box could be
recycled. The product-registration page is a desktop-only web form. To register, the agent
must read the warranty code off the phone photo and transfer it to the desktop form,
crossing from `android_phone` to `windows_desktop`.

## Environments & apps

| Env | App (`type`) | Seeded state (highlights) |
| --- | --- | --- |
| `android_phone` | `MockPhotosApp` | `amount="BW-7Q4K-2310"` (the copyable warranty code), `merchant="Brightwave"`, `date="2026-06-25"` |
| `windows_desktop` | `MockBrowserFormApp` | `fields={warranty_code:""}`, `expected_fields={warranty_code:"BW-7Q4K-2310"}`, `field_types={warranty_code:"text"}`, `status="drafting"`, page titled "Brightwave product registration" |

## Latent task graph (hidden from agent)

| Subtask id | Description | required_env | required_app | depends_on |
| --- | --- | --- | --- | --- |
| `read_code` | Read the warranty code from the phone screenshot photo. | `android_phone` | `phone_photos` | — |
| `register_product` | Paste the code into the desktop registration form and submit. | `windows_desktop` | `register_form` | `read_code` |

## Required handoffs

| artifact_type | from_env | to_env | expected_value |
| --- | --- | --- | --- |
| `warranty_code` | `android_phone` | `windows_desktop` | `BW-7Q4K-2310` |

## Desired final state

```
windows_desktop.register_form.status == "submitted"
```

## Decoys / ambiguity / source-of-truth

The same warranty-card photo shows a model number "BW-220" and a batch line
"LOT 0419" printed directly above the code — both look like things to type. Only the
warranty code `BW-7Q4K-2310` matches `expected_fields`. A naive agent that types the model
number, or re-types a remembered/OCR-mangled code (dropping a hyphen or reading `0` as
`O`), fails the form match. There is exactly one screenshot, so no referent ambiguity — the
trap is fidelity of the transferred value.

## Metric rationale

An agent that "reads" the code visually and hand-types it into the desktop form never
copies the authoritative value from the phone, so no `from_env=android_phone →
to_env=windows_desktop` handoff is recorded and any character drift fails `handoff_correctness`.
Only a copy-from-phone / paste-into-form path both records the handoff and matches
`expected_fields`.

## Verifier sketch

- **handoff_correctness (primary):** `required_handoffs` carries `expected_value="BW-7Q4K-2310"`
  from `android_phone` to `windows_desktop`; satisfied only when the photo's code is copied
  and pasted into the form input.
- **global_success (secondary):** `desired_final_state` checks `register_form.status ==
  "submitted"`, set when `fields.warranty_code == expected_fields.warranty_code`.
- **routing_accuracy (secondary):** subtasks pin reading to `android_phone/phone_photos`
  and registering to `windows_desktop/register_form`.
- Config fields set: `desired_final_state`, `required_handoffs`.

## Implementation notes

- **`code_ready: true`.** `MockPhotosApp` carries the visible code in its copyable `amount`
  field (modeled as a copyable text value per README); `MockBrowserFormApp` seeded with
  `expected_fields={warranty_code:"BW-7Q4K-2310"}`, `field_types={warranty_code:"text"}`,
  `status="drafting"`. Solvable via `copy_value` on the photo value, `paste_value` into
  `warranty_code`, `click submit`. `desired_final_state` path
  `windows_desktop.register_form.status` is a real state key.
- Set `initial_focus_env="windows_desktop"`, `initial_focus_app="register_form"` so the
  agent must navigate to the phone to find the value.
