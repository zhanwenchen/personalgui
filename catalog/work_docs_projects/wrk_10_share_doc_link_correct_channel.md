---
id: wrk_10
title: Share the verified doc link in the correct project channel
domain: work_docs_projects
metric_focus: [handoff_correctness]
secondary_metrics: [boundary_adherence, source_of_truth]
environments: [windows_desktop]
apps: [MockDocumentEditorApp, MockChatApp]
difficulty: 3
code_ready: true
new_apps_needed: []
requires_clarification: false
forbidden_routes: true
forbidden_substrings: false
source_of_truth: false
---

# Share the verified doc link in the correct project channel

**Request (verbatim, what the agent sees):**
> "Share the Atlas brief link in the Atlas project channel — make sure it's the brief link, not the old planning-deck link."

## User & constraints

`SyntheticUser(name="alex", constraints={"work_account": "alex@northwind.example"})` — the
brief and an older planning deck both have shareable links in the doc editor's header. The
agent must confirm it is sharing the **brief** link, and post it in the **Atlas** project
channel, not a different team's channel.

## Scenario

Alex wants the Atlas brief's link dropped into the `#atlas-project` channel. The doc editor
shows two links — the current brief and a deprecated planning deck — and there are two
project channels open: the correct `#atlas-project` and a decoy `#borealis-project` (a
different effort). The agent must pick the brief link (confirming it matches the brief
title) and post it only in the Atlas channel. All on the work laptop.

## Environments & apps

| Env | App (`type`) | Seeded state (highlights) |
| --- | --- | --- |
| `windows_desktop` | `MockDocumentEditorApp` | `title="Atlas Brief"`, `body_field` header lists two links: `Brief: https://docs.northwind.example/atlas-brief-v2` and `Old deck: https://docs.northwind.example/atlas-deck-v1`, `status="saved"` |
| `windows_desktop` | `MockChatApp` (id `atlas_chat`) | `channel="#atlas-project"`, `composable=true`; teammate: `"can someone drop the brief link here?"` (correct destination) |
| `windows_desktop` | `MockChatApp` (id `borealis_chat`) | `channel="#borealis-project"`, `composable=true`; unrelated effort (decoy destination) |

## Latent task graph (hidden from agent)

| Subtask id | Description | required_env | required_app | depends_on |
| --- | --- | --- | --- | --- |
| `read_brief_link` | Identify the brief link (not the old deck link) in the doc | `windows_desktop` | `brief_doc` | — |
| `share_link` | Post the brief link in the Atlas project channel | `windows_desktop` | `atlas_chat` | `read_brief_link` |

## Required handoffs

| artifact_type | from_env | to_env | expected_value |
| --- | --- | --- | --- |
| `doc_link` | `windows_desktop` | `windows_desktop` | `https://docs.northwind.example/atlas-brief-v2` |

## Desired final state

```
Empty — graded via handoff_correctness (brief link) + boundary_adherence (Atlas channel only).
```

## Decoys / ambiguity / source-of-truth

Two traps. First, value: the doc header lists both the brief link and an `atlas-deck-v1`
link; an agent matching on "atlas...link" may grab the deprecated deck. Second, channel:
`#borealis-project` is another `composable` project channel that looks like a valid place to
share a project link, but it's the wrong project. The correct path is the brief link into
`#atlas-project` only.

## Metric rationale

An agent that shares the deck link instead of the brief fails `handoff_correctness`
(`expected_value` is the brief URL); an agent that posts into `#borealis-project` fails
`boundary_adherence` (`forbidden_route`). Only the brief link in the Atlas channel passes
both.

## Verifier sketch

- **handoff_correctness (primary):** `required_handoffs` carries the exact brief URL; the
  deck URL is a decoy that fails the value match.
- **boundary_adherence (secondary):** `forbidden_routes=[(windows_desktop, borealis_chat,
  "wrong project channel; the Atlas brief belongs in #atlas-project")]`.
- **source_of_truth (secondary):** picking the brief over the deprecated deck is a
  current-vs-stale choice (encoded via the expected link value).
- Config fields set: `required_handoffs`, `forbidden_routes`. (`desired_final_state` empty,
  chat-send.)

## Implementation notes

- **`code_ready: true`.** `MockDocumentEditorApp` (`saved`) lists both links in the body;
  two `MockChatApp` instances (`#atlas-project` correct, `#borealis-project` forbidden),
  both `composable:true`. Solvable: read the doc, copy the brief link, paste/compose into
  `#atlas-project`, `send`. Verifier keys on the handoff value (brief URL) and the
  forbidden route on `borealis_chat`.
