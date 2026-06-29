---
id: med_03
title: Transfer boarding-pass file from phone to desktop editor
domain: media_files
metric_focus: [handoff_correctness]
secondary_metrics: [global_success, routing_accuracy]
environments: [android_phone, windows_desktop]
apps: [MockFileHandoffApp, MockDocumentEditorApp]
difficulty: 3
code_ready: false
new_apps_needed: [MockFileHandoffApp]
requires_clarification: false
forbidden_routes: false
forbidden_substrings: false
source_of_truth: false
---

# Transfer boarding-pass file from phone to desktop editor

**Request (verbatim, what the agent sees):**
> "Send my boarding-pass PDF from my phone to the desktop and open it in the editor."

## User & constraints

`SyntheticUser(name="alex", constraints={"editing_device": "windows_desktop"})` — Alex
received the airline boarding pass as a file on the phone but wants it on the desktop to
annotate seat preferences before printing. The file originates on the phone; the editor
is desktop-only.

## Scenario

Alex's airline sent a boarding-pass PDF that downloaded to the phone's Files area. To mark
it up, the agent must move the actual file from the phone to the desktop and open it in the
document editor — a genuine *file* handoff (not a copied text value) crossing from
`android_phone` to `windows_desktop`.

## Environments & apps

| Env | App (`type`) | Seeded state (highlights) |
| --- | --- | --- |
| `android_phone` | `MockFileHandoffApp` | `files=[{id:"bp1", name:"boardingpass_AX482.pdf", kind:"pdf", date:"2026-06-28", transferable:true}, {id:"img9", name:"vacation_dunes.jpg", kind:"image", transferable:true}]`, `selected_file_id=null` |
| `windows_desktop` | `MockDocumentEditorApp` | `body_field=""`, `required_substrings=["boardingpass_AX482.pdf"]`, `status="drafting"` |

## Latent task graph (hidden from agent)

| Subtask id | Description | required_env | required_app | depends_on |
| --- | --- | --- | --- | --- |
| `select_file` | Select the boarding-pass PDF on the phone and send it. | `android_phone` | `phone_files` | — |
| `open_in_editor` | Receive the file on the desktop and open it in the editor. | `windows_desktop` | `doc_editor` | `select_file` |

## Required handoffs

| artifact_type | from_env | to_env | expected_value |
| --- | --- | --- | --- |
| `file` | `android_phone` | `windows_desktop` | `boardingpass_AX482.pdf` |

## Desired final state

```
windows_desktop.doc_editor.status == "saved"
```

(The editor records `saved` once the transferred file's name is present in the document body —
i.e., the file was opened into the editor.)

## Decoys / ambiguity / source-of-truth

The phone's Files surface also holds a recently-downloaded vacation image
`vacation_dunes.jpg`, the most recent and visually prominent item. An agent that grabs the
"latest file" or the photo sends the wrong artifact; only `boardingpass_AX482.pdf` is the
boarding pass and matches the editor's `required_substrings`. One correct file, one
tempting decoy — the trap is selecting the right file, then preserving its identity across
the handoff.

## Metric rationale

An agent that transcribes a remembered filename, or sends the wrong (latest) file, never
records a faithful `file` handoff of `boardingpass_AX482.pdf` from `android_phone` to
`windows_desktop`, so `handoff_correctness` fails. Opening the wrong file also leaves the
editor's `required_substrings` unmet, failing `global_success`.

## Verifier sketch

- **handoff_correctness (primary):** `required_handoffs` carries `expected_value=
  "boardingpass_AX482.pdf"` as a `file` artifact from `android_phone` to `windows_desktop`;
  satisfied only when the correct file is selected/sent and received on the desktop.
- **global_success (secondary):** `desired_final_state` checks `doc_editor.status == "saved"`,
  set when the file name appears in `required_substrings`.
- **routing_accuracy (secondary):** selecting pinned to `android_phone/phone_files`, opening
  to `windows_desktop/doc_editor`.
- Config fields set: `desired_final_state`, `required_handoffs`.

## Implementation notes

- **`code_ready: false`.** Needs a minimal new **`MockFileHandoffApp`** (a thin files
  surface, close to `MockPhotosApp`): render `files: [{id, name, kind, date, transferable}]`
  and `selected_file_id`; actions `select_file:<id>` (focuses a file) and `send_file`
  (places the selected file's identity on the clipboard / handoff channel and records its
  origin env, mirroring `copy_value`). On the desktop side the existing
  `MockDocumentEditorApp` receives the file via `paste_value` of the file name (recording the
  cross-env handoff) and `save`. Keep the file artifact mechanics identical to copy/paste so
  no new verifier is needed — only the new render+select surface is added.
- Set `initial_focus_env="windows_desktop"`, `initial_focus_app="doc_editor"` so the agent
  must navigate to the phone to fetch the file.
