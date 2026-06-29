---
id: wrk_11
title: Fill the publish-request form with the doc title and version
domain: work_docs_projects
metric_focus: [handoff_correctness]
secondary_metrics: [global_success, routing_accuracy]
environments: [windows_desktop]
apps: [MockDocumentEditorApp, MockBrowserFormApp]
difficulty: 3
code_ready: true
new_apps_needed: []
requires_clarification: false
forbidden_routes: false
forbidden_substrings: false
source_of_truth: false
---

# Fill the publish-request form with the doc title and version

**Request (verbatim, what the agent sees):**
> "Submit the publish request for the runbook — use the doc's exact title and version from the editor."

## User & constraints

`SyntheticUser(name="alex", constraints={"work_account": "alex@northwind.example"})` — the
publishing workflow's web form requires the document's **exact** title and version string;
a mismatch with the editor's metadata rejects the request. Two values must cross, both
verbatim.

## Scenario

Alex finished a runbook in the doc editor and now has to file a "publish request" through a
web form so docs-ops can publish it. The form needs the document's exact title and its
version string, both shown in the editor's header. This is a two-value, same-desktop
handoff from the editor into a browser form, where exactness matters: the form validates
against the editor's metadata.

## Environments & apps

| Env | App (`type`) | Seeded state (highlights) |
| --- | --- | --- |
| `windows_desktop` | `MockDocumentEditorApp` | `title="Atlas Incident Runbook"`, `body_field` header shows `"Version: v3.2.0"` (and a changelog line mentioning an older `v3.1.4`), `status="saved"` (read-only source) |
| `windows_desktop` | `MockBrowserFormApp` | `title="Publish Request"`, `expected_fields={"doc_title":"Atlas Incident Runbook","version":"v3.2.0"}`, `field_types={"doc_title":"text","version":"text"}`, `status="drafting"` |

## Latent task graph (hidden from agent)

| Subtask id | Description | required_env | required_app | depends_on |
| --- | --- | --- | --- | --- |
| `read_title_version` | Read the exact title and current version from the editor header | `windows_desktop` | `runbook_doc` | — |
| `submit_request` | Enter both into the publish-request form and submit | `windows_desktop` | `publish_form` | `read_title_version` |

## Required handoffs

| artifact_type | from_env | to_env | expected_value |
| --- | --- | --- | --- |
| `doc_title` | `windows_desktop` | `windows_desktop` | `Atlas Incident Runbook` |
| `version` | `windows_desktop` | `windows_desktop` | `v3.2.0` |

## Desired final state

```
windows_desktop.publish_form.status == "submitted"
```

## Decoys / ambiguity / source-of-truth

The editor body also contains a changelog line mentioning the prior version `v3.1.4`. An
agent that scans for any "v3.x" string may carry the older version; the form's
`expected_fields` only accepts the current `v3.2.0`. The title is a single, unambiguous
string, but the version requires distinguishing "current version" (header) from "previous
version" (changelog). The old version is the trap.

## Metric rationale

An agent that transfers `v3.1.4` from the changelog, or paraphrases the title (e.g. drops
"Incident"), submits values the form rejects; it stays in `drafting` and both
`handoff_correctness` and `global_success` fail. Only both exact strings — title and
`v3.2.0` — let the form submit.

## Verifier sketch

- **handoff_correctness (primary):** two `required_handoffs` carry the exact title and
  current version from `runbook_doc` into `publish_form` (same env). The changelog version
  is a decoy that fails the value match.
- **global_success (secondary):** `publish_form.status == "submitted"`, reached only when
  both `expected_fields` match.
- **routing_accuracy (secondary):** both subtasks on `windows_desktop`; fails only if a
  route is invented.
- Config fields set: `desired_final_state`, `required_handoffs`.

## Implementation notes

- **`code_ready: true`.** `MockDocumentEditorApp` (`saved`) exposes the title and header
  version (plus a changelog decoy version); `MockBrowserFormApp` enforces
  `expected_fields={"doc_title":"Atlas Incident Runbook","version":"v3.2.0"}`. Solvable by
  reading the editor, copy/paste the title into `doc_title`, copy/paste `v3.2.0` into
  `version`, then `submit`. Two-value within-desktop handoff; `desired_final_state`
  references the real `status` key.
