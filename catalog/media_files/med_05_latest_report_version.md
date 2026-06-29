---
id: med_05
title: Attach the latest report version, not the stale one
domain: media_files
metric_focus: [source_of_truth]
secondary_metrics: [handoff_correctness, routing_accuracy]
environments: [windows_desktop]
apps: [MockEmailApp, MockChatApp]
difficulty: 3
code_ready: true
new_apps_needed: []
requires_clarification: false
forbidden_routes: false
forbidden_substrings: false
source_of_truth: true
---

# Attach the latest report version, not the stale one

**Request (verbatim, what the agent sees):**
> "Send Priya the final Q2 report file from the email thread."

## User & constraints

`SyntheticUser(name="alex", constraints={"authoritative_source": "newest_attachment"})` —
the same report exists as two attachments with confusing names; the newest revision is the
one to send. The crux is picking the authoritative (latest) version.

## Scenario

A long email thread about the Q2 report has two attachments: an earlier `Q2_report_final.pdf`
and a later `Q2_report_final_v2.pdf` sent a day afterward with a correction. The name
"final" on the older file is a trap; the timestamp shows `v2` is newer and authoritative. The
agent must identify the latest version from the thread and send that file's name to Priya's
chat — all on the desktop. Modeled via `MockEmailApp` attachments/threads with timestamps
(no files app needed).

## Environments & apps

| Env | App (`type`) | Seeded state (highlights) |
| --- | --- | --- |
| `windows_desktop` | `MockEmailApp` | thread `q2rep` with two attachments: `{name:"Q2_report_final.pdf", ts:"2026-06-24 16:02"}` (older) and `{name:"Q2_report_final_v2.pdf", ts:"2026-06-25 11:40"}` (newer, body says "v2 fixes the revenue table"); `opened_thread_id=null` |
| `windows_desktop` | `MockChatApp` | `channel="Priya Nandakumar"`, `composable=true`, prior message "can you send me the final Q2 report?" |

## Latent task graph (hidden from agent)

| Subtask id | Description | required_env | required_app | depends_on |
| --- | --- | --- | --- | --- |
| `find_latest` | Open the thread; identify the newest report attachment by timestamp. | `windows_desktop` | `email` | — |
| `send_latest` | Send the latest version's file name to Priya's chat. | `windows_desktop` | `chat` | `find_latest` |

## Required handoffs

| artifact_type | from_env | to_env | expected_value |
| --- | --- | --- | --- |
| `file` | `windows_desktop` | `windows_desktop` | `Q2_report_final_v2.pdf` |

(Within-env handoff: `from_env == to_env`, carrying the chosen file name from email to chat.)

## Desired final state

```
Empty — graded via source_of_truth / handoff_correctness (the v2 file name carried into chat).
```

## Decoys / ambiguity / source-of-truth

Two attachments name the same report; the **older** `Q2_report_final.pdf` literally contains
the word "final" and appears earlier in the thread, making it the obvious-but-stale pick. The
**newer** `Q2_report_final_v2.pdf` (later timestamp, body note "v2 fixes the revenue table")
is authoritative. An agent matching on the word "final" or grabbing the first attachment
sends the stale revision. The timestamp is the only tiebreaker; the trap is trusting the
filename over recency.

## Metric rationale

The fact "the final report file" is duplicated with one stale version. An agent that picks the
filename-matching but older `Q2_report_final.pdf` carries the wrong value, so the required
handoff `expected_value="Q2_report_final_v2.pdf"` is not satisfied. Choosing by timestamp is
the only path that matches (encoded via `expected_value`, per README's source-of-truth note).

## Verifier sketch

- **source_of_truth (primary):** the authoritative latest name `Q2_report_final_v2.pdf` is the
  required `expected_value`; the older `..._final.pdf` is a decoy that fails the handoff match.
- **handoff_correctness (secondary):** within-env handoff carries the chosen file name into the
  chat compose input; only the v2 name passes.
- **routing_accuracy (secondary):** finding pinned to `email`, sending to `chat`.
- Config fields set: `required_handoffs`; `desired_final_state` empty per chat-send convention.

## Implementation notes

- **`code_ready: true`** — modeled via `MockEmailApp` attachments/threads with timestamps
  rather than a files app. Seed one thread whose body references two attachments with distinct
  `ts` values; the newer attachment's name is the copyable/handoff value. `MockChatApp`
  (`composable=true`) receives the send. Solvable via `tap thread:q2rep`, identify the latest
  by timestamp, `copy_value`/`compose` the v2 file name, `send`.
- Decision noted: kept `code_ready: true` by encoding the duplicate-version contrast in email
  attachment metadata (timestamps) — no new files-browser app required.
