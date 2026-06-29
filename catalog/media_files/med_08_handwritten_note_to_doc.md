---
id: med_08
title: Copy handwritten-note text from a photo into a saved document
domain: media_files
metric_focus: [handoff_correctness]
secondary_metrics: [global_success, routing_accuracy]
environments: [android_phone, windows_desktop]
apps: [MockPhotosApp, MockDocumentEditorApp]
difficulty: 2
code_ready: true
new_apps_needed: []
requires_clarification: false
forbidden_routes: false
forbidden_substrings: false
source_of_truth: false
---

# Copy handwritten-note text from a photo into a saved document

**Request (verbatim, what the agent sees):**
> "Type up the Wi-Fi note I photographed into my Home Info doc and save it."

## User & constraints

`SyntheticUser(name="alex", constraints={"notes_device": "windows_desktop"})` — Alex keeps a
"Home Info" document on the desktop and photographed a handwritten Wi-Fi note stuck to the
router. The note text lives behind a phone photo; the document lives on the desktop.

## Scenario

A relative wrote the guest Wi-Fi password on a sticky note; Alex photographed it. To save it
properly, the agent must read the handwritten text off the phone photo and transcribe it into
the desktop Home Info document, then save — crossing from `android_phone` to `windows_desktop`.

## Environments & apps

| Env | App (`type`) | Seeded state (highlights) |
| --- | --- | --- |
| `android_phone` | `MockPhotosApp` | `amount="Guest WiFi: maple-river-88"` (the copyable note text), `merchant="Handwritten note"`, `date="2026-06-28"` |
| `windows_desktop` | `MockDocumentEditorApp` | `body_field=""`, `required_substrings=["Guest WiFi: maple-river-88"]`, `status="drafting"` |

## Latent task graph (hidden from agent)

| Subtask id | Description | required_env | required_app | depends_on |
| --- | --- | --- | --- | --- |
| `read_note` | Read the handwritten note text from the phone photo. | `android_phone` | `phone_photos` | — |
| `save_note` | Paste the note text into the Home Info doc and save. | `windows_desktop` | `doc_editor` | `read_note` |

## Required handoffs

| artifact_type | from_env | to_env | expected_value |
| --- | --- | --- | --- |
| `note_text` | `android_phone` | `windows_desktop` | `Guest WiFi: maple-river-88` |

## Desired final state

```
windows_desktop.doc_editor.status == "saved"
```

## Decoys / ambiguity / source-of-truth

The photo caption shows a second scribble — a router serial "SN: 4471-AA" jotted in the
corner — that an agent might transcribe instead of or alongside the password. Only the exact
note text `Guest WiFi: maple-river-88` satisfies `required_substrings`. A naive agent that
mis-reads the handwriting (e.g., `maple_river_88` or `maple-river-8`) or transcribes the
serial fails the save condition. One note photo — the trap is fidelity of the handwritten
text.

## Metric rationale

An agent that eyeballs the handwriting and hand-types an approximation never copies the
authoritative note value from the phone, so no `from_env=android_phone →
to_env=windows_desktop` handoff is recorded and any character drift fails both
`handoff_correctness` and the document's `required_substrings`. Only copy-from-phone /
paste-into-doc / save succeeds.

## Verifier sketch

- **handoff_correctness (primary):** `required_handoffs` carries
  `expected_value="Guest WiFi: maple-river-88"` from `android_phone` to `windows_desktop`;
  satisfied only when the photo's note text is copied and pasted into the doc body.
- **global_success (secondary):** `desired_final_state` checks `doc_editor.status == "saved"`,
  set when all `required_substrings` are present in the body.
- **routing_accuracy (secondary):** reading pinned to `android_phone/phone_photos`, saving to
  `windows_desktop/doc_editor`.
- Config fields set: `desired_final_state`, `required_handoffs`.

## Implementation notes

- **`code_ready: true`.** `MockPhotosApp` carries the visible handwritten text in its copyable
  `amount` field (modeled as copyable text per README) with the serial decoy in the caption;
  `MockDocumentEditorApp` seeded with `required_substrings=["Guest WiFi: maple-river-88"]`,
  `status="drafting"`. Solvable via `copy_value` on the note text, `paste_value` into
  `body_field`, `click save`. `desired_final_state` path `windows_desktop.doc_editor.status`
  is a real state key.
- Set `initial_focus_env="windows_desktop"`, `initial_focus_app="doc_editor"` so the agent
  must navigate to the phone to read the note.
