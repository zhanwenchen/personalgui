---
id: trv_11
title: Transfer the boarding-pass file from phone to desktop to print
domain: travel
metric_focus: [handoff_correctness]
secondary_metrics: [global_success, routing_accuracy]
environments: [android_phone, windows_desktop]
apps: [MockFileShareApp, MockPrintQueueApp]
difficulty: 3
code_ready: false
new_apps_needed: [MockFileShareApp, MockPrintQueueApp]
requires_clarification: false
forbidden_routes: false
forbidden_substrings: false
source_of_truth: false
---

# Transfer the boarding-pass file from phone to desktop to print

**Request (verbatim, what the agent sees):**
> "Print my boarding pass — it's the screenshot on my phone."

## User & constraints

`SyntheticUser(name="alex", constraints={"printer": "windows_desktop"})` — Alex saved the
boarding pass as a screenshot on the phone but the only printer is on the desktop. The
artifact to move is a **file**, not a copyable text value, so this needs a file-handoff
surface.

## Scenario

Alex's boarding pass arrived as an image and lives in the phone's saved files. The printer
is attached to the desktop. The agent must move the specific boarding-pass file from the
phone to the desktop print queue and print it — a phone-to-desktop **file** handoff, where
the handoff artifact is an attachment/file identity rather than a typed string.

## Environments & apps

| Env | App (`type`) | Seeded state (highlights) |
| --- | --- | --- |
| `android_phone` | `MockFileShareApp` | `files=[{id:"f_bp", name:"boarding_pass_AX482.png", kind:"image"}, {id:"f_rcpt", name:"hotel_receipt.png"}, {id:"f_map", name:"trip_map.png"}]`, selected file shareable to a target env |
| `windows_desktop` | `MockPrintQueueApp` | `queue=[]`, `expected_file_id="f_bp"`, `status="idle"` |

## Latent task graph (hidden from agent)

| Subtask id | Description | required_env | required_app | depends_on |
| --- | --- | --- | --- | --- |
| `select_file` | Select the boarding-pass image on the phone. | `android_phone` | `fileshare` | — |
| `send_to_desktop` | Share the selected file to the desktop print queue. | `windows_desktop` | `print_queue` | `select_file` |
| `print` | Print the received file. | `windows_desktop` | `print_queue` | `send_to_desktop` |

## Required handoffs

| artifact_type | from_env | to_env | expected_value |
| --- | --- | --- | --- |
| `file` | `android_phone` | `windows_desktop` | `f_bp` (boarding_pass_AX482.png) |

(File handoff: the artifact is the file id/identity, not a typed string. A correct run
moves `f_bp` specifically, not a sibling image.)

## Desired final state

```
windows_desktop.print_queue.status == "printed"
```

## Decoys / ambiguity / source-of-truth

The phone holds two sibling images — `hotel_receipt.png` and `trip_map.png` — next to the
boarding pass. An agent that sends the wrong image (or "all photos") prints the wrong file:
`expected_file_id` is `f_bp`, so any other file leaves the queue mismatched and unprinted.
The trap is selecting the right file before sending.

## Metric rationale

An agent that grabs a sibling image, or that "describes" the boarding pass instead of
moving the actual file, never records a `from_env=android_phone → to_env=windows_desktop`
file handoff carrying `f_bp`, so the print queue never receives the expected file and
`global_success` fails. Only selecting and sending the correct file satisfies both.

## Verifier sketch

- **handoff_correctness (primary):** `required_handoffs` carries a `file` artifact with
  `expected_value="f_bp"` from `android_phone` to `windows_desktop`; satisfied only when
  that specific file is shared into the print queue.
- **global_success (secondary):** `desired_final_state` checks `print_queue.status ==
  "printed"`, reached when the received file id equals `expected_file_id` and print is
  triggered.
- **routing_accuracy (secondary):** selection on the phone, printing on the desktop.
- Config fields set: `desired_final_state`, `required_handoffs`.

## Implementation notes

- **`code_ready: false`.** The 14 existing apps move *text values* over the clipboard; no
  app moves a **file/image** as the handoff artifact. Two minimal new app surfaces, each
  kept close to existing patterns:
  - **`MockFileShareApp`** (phone, mirrors `MockPhotosApp`/`MockContacts` selection):
    render fields `files: [{id, name, kind}]`, `selected_file_id`. Actions: `tap
    file:<id>` to select; `share_to:<env_id>` to dispatch the selected file to a target
    env — this is the file analog of `copy_value`/`paste_value` and records a `file`
    handoff `from_env → to_env` with the file id as the handoff value.
  - **`MockPrintQueueApp`** (desktop, mirrors `MockExpenseReportApp` submit/status):
    render fields `queue: [file_id...]`, `expected_file_id`, `status` (`idle` →
    `queued` → `printed`). Actions: receiving a shared file appends to `queue`; `click
    print` sets `status="printed"` iff the queued file id equals `expected_file_id`.
  - **Verifier reuse:** `handoff_correctness` needs the handoff value to be a file id
    rather than a text string — a small extension to the existing `paste_value`/handoff
    recording so `artifact_type="file"` carries the id. `global_success` uses the existing
    status-equality check on `print_queue.status`.
- Set `initial_focus_env="windows_desktop"`, `initial_focus_app="print_queue"` so the
  agent must navigate to the phone to find and select the file.
