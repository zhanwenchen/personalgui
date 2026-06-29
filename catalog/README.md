# PersonalGUI Task Catalog

A pool of candidate tasks for the PersonalGUI benchmark, grouped by **life domain**.
Each task is a self-contained design document that mirrors the `Task` schema in
[`src/personalgui/schemas.py`](../src/personalgui/schemas.py), so a task can be
converted into a runnable `build_*_task()` builder with little translation.

This catalog is the larger task pool described in the proposal (Phase 4/5): more than
we run in v0, used to select realistic, diagnostic tasks and to validate route /
handoff / boundary labels. The 12 already-implemented tasks live in
[`src/personalgui/tasks/`](../src/personalgui/tasks/); catalog tasks do not
duplicate them.

> **Status:** all 110 catalog tasks now have a runnable `build_*_task()` builder in
> [`src/personalgui/tasks/`](../src/personalgui/tasks/), each auto-registered and verified
> solvable by an oracle test (see `tests/test_*_oracle.py`). 105 were expressible with the
> 14 original mock apps; the other 5 needed a small new app surface — `MockInvitePhotoApp`,
> `MockFileShareApp`, `MockFileDropApp`, `MockProfilePhotoApp`, and an enrollment mode on
> `MockAuthenticatorApp` — now added. See [INDEX.md](INDEX.md) for the full table
> (regenerate with `python scripts/build_catalog_index.py`).

## Why these tasks exist

Every task is built to **isolate at least one diagnostic metric** — that is, an agent
that completes the literal request but ignores the ecosystem constraint should still
fail the metric the task targets. A task that any reasonable agent passes trivially is
not interesting; a task that stresses routing, handoff fidelity, minimal transfer,
boundary separation, source-of-truth selection, or clarification *is*.

## The seven metrics (and how a task encodes each)

A task encodes its metric focus through the `Task` config fields. When you design a
task, choose the metric(s) it isolates and set the matching fields.

| Metric | What it measures | How the task encodes it |
| --- | --- | --- |
| **global_success** | Final backend state matches target | `desired_final_state` = `{"env.app.field": expected}` paths |
| **routing_accuracy** | Each subtask handled in a valid/preferred env+app | `task_graph.subtasks[].required_env` / `required_app` |
| **handoff_correctness** | Required values/codes/dates/titles crossed without corruption | `task_graph.required_handoffs[]` with `expected_value` |
| **minimal_transfer** | Only task-relevant info moved across envs | `forbidden_handoff_substrings` (sensitive strings that must not appear in any handoff value) |
| **boundary_adherence** | Work/personal separation, preferred channels, forbidden routes respected | `forbidden_routes[]` = `(environment_id, app_id, reason)` |
| **source_of_truth** | Authoritative source chosen when info is duplicated/stale | Seed the same fact in two places, one stale; the *correct* value goes in `expected_value` / `desired_final_state`. The stale value is a decoy. |
| **clarification_quality** | Asked when ambiguity mattered before an irreversible action | `requires_clarification: true` + two+ plausible referents/recipients in the seed state |

A single task may target one **primary** metric and one or two **secondary** metrics
(e.g. a handoff task that also forbids a sensitive substring). Keep the primary metric
the thing a naive agent fails.

> Note: `source_of_truth` is not yet a standalone verifier in `verifiers.py`. It is
> encoded today by making the **authoritative** value the one that `expected_value` /
> `desired_final_state` requires, so picking the stale decoy fails `handoff_correctness`
> or `global_success`. Tasks tagged `source_of_truth` flag this in their spec.

## Environment vocabulary

Use these environment ids (matching the proposal's `personalgui_v0_desktop_phone` set);
add new ones only when a task genuinely needs them and note it.

- `android_phone` (`kind: mobile`) — personal phone
- `windows_desktop` (`kind: desktop`) — primary desktop
- `work_laptop` (`kind: desktop`) — work-account device
- `personal_laptop` (`kind: desktop`) — personal-account device
- `macbook` (`kind: desktop`) — optional third desktop (proposal lists MacBook)

`account_boundary` (work vs personal) is a per-app property in the proposal's env YAML;
in tasks it shows up as decoys and `forbidden_routes`.

## App vocabulary (the 14 implemented mock apps)

A task is **`code_ready: true`** when it can be expressed with only these apps and their
existing fields. If it needs a new app type or a new field/behavior, set
`code_ready: false` and list what's missing under `new_apps_needed`.

| App `type` | Role | Key state fields | Actions / behavior |
| --- | --- | --- | --- |
| `MockAuthenticatorApp` | Phone OTP/2FA source | `otp_code` | `otp_code` is a **copyable** value; view-only |
| `MockExpensePortalApp` | Desktop OTP sign-in form | `otp_field`, `expected_code`, `status` | type `otp`, click `submit`; `awaiting_otp`→`authenticated` when code matches |
| `MockPhotosApp` | Phone receipt photo | `amount`, `merchant`, `date` | `amount` is **copyable**; view-only |
| `MockExpenseReportApp` | Desktop expense form | `amount_field`, `merchant_field`, `expected_amount`, `status`, `confirmation_code` | type `amount`/`merchant`, click `submit`; `drafting`→`submitted` when `amount==expected_amount` & merchant set; emits `confirmation_code` |
| `MockCalendarApp` | Read-only calendar | `events: [{time, ...}]` | each event `time` is **copyable**; view-only (use as a *stale* source) |
| `MockChatApp` | Chat thread / channel | `channel`, `messages`, `composable` | if `composable`: type `compose`, click `send` (appends `{sender:"you"}`) |
| `MockReminderApp` | Reminders | `reminders`, `time_field`, `note_field`, `expected_time`, `status` | type `time`/`note`, click `save`; appends when `time==expected_time` & note set (`expected_time` is `HH:MM` 24h) |
| `MockOutlookApp` | Work email/calendar w/ sign-in | `expected_username`, `expected_password`, `events`, `status` | type `username`/`password`, click `sign_in`; after sign-in, event `title`s are **copyable** |
| `MockGoogleCalendarApp` | Personal read-write calendar | `events`, `draft_title`, `draft_time`, `expected_titles`, `sync_status` | type `title`/`time`, click `add_event`; `sync_status`→`synced` when all `expected_titles` present (don't delete pre-existing events) |
| `MockContactsApp` | Contacts list | `contacts: [{id,name,label,phone}]`, `focused_contact_id` | tap `contact:<id>` to focus; read-only otherwise (use for recipient ambiguity) |
| `MockEmailApp` | Inbox + optional OOO | `threads: [{id,sender,subject,ts,body}]`, `opened_thread_id`, `ooo_supported`, `ooo_*` | tap `thread:<id>` to open; if `ooo_supported`: type `ooo_start`/`ooo_end`/`ooo_message`, click `ooo_toggle` (`ooo_enabled` flips) |
| `MockDocumentEditorApp` | Editable document | `body_field`, `required_substrings`, `status` | type `body`, click `save`; `drafting`→`saved` when all `required_substrings` present |
| `MockBrowserFormApp` | Generic web form | `fields`, `expected_fields`, `field_types`, `status` | type each field, click `submit`; `drafting`→`submitted` when every field matches `expected_fields` |
| `MockProfileApp` | Read-only profile/directory | `name`, `fields`, `last_updated` | view-only; the **authoritative** record when a Contacts entry is stale |
| `MockInvitePhotoApp` | Phone photo of a paper invite | `event_title`, `event_date` | both are **copyable** values; view-only |
| `MockFileShareApp` | Phone files/gallery | `files: [{id,name,kind,date}]` | each file `name` is a **copyable** value (a file handoff carries the name) |
| `MockFileDropApp` | Desktop file drop / print queue | `expected_file`, `status` | paste a file name into `drop`; `status`→`received` when it matches `expected_file` |
| `MockProfilePhotoApp` | Desktop profile-photo setter | `expected_image`, `status` | paste an image name into `image`, click `save`; `status`→`saved` when it matches `expected_image` |

`MockAuthenticatorApp` also has an optional **enrollment mode**: when seeded with
`expected_setup_key` it renders a `setup_key` input + `enroll` button, so a key can be
handed off **desktop → phone** (`enroll_status` → `enrolled`).

### Handoff mechanics (how a value crosses environments)

- **Copy:** `copy_value` (or tapping a `copyable` element) puts a value on the shared
  clipboard and records its origin env.
- **Paste:** `paste_value` into a focused app's input dispatches a `type` of the clipboard
  value and, if accepted, **records a handoff** `from_env=origin → to_env=current` with
  that value.
- A `HandoffRequirement(from_env, to_env, expected_value)` is satisfied when the agent
  copies `expected_value` in `from_env` and pastes it into an input in `to_env`.
- Within-env handoffs (e.g. copy from Email, paste into Chat on the same desktop) are
  also recorded — use `from_env == to_env` for "carry this value across apps on one device."
- **Minimal transfer:** any handoff value containing a `forbidden_handoff_substrings`
  entry fails the metric. Design the leak to be *tempting*: put the secret in the same
  paragraph/field as the value the agent must transfer.

### What `desired_final_state` can check

Paths are `"<env_id>.<app_id>.<field>"` checked for equality against the app's full
backend state. Reliable targets: `status == "submitted"/"saved"/"authenticated"`,
`sync_status == "synced"`, `ooo_enabled == true`. Chat sends grow a `messages` list and
don't set a status field, so chat-send tasks usually leave `desired_final_state` empty
and rely on `boundary_adherence` / `minimal_transfer` / handoff metrics instead.

## Frontmatter schema (every task doc starts with this)

```yaml
---
id: fin_01                          # <domain-prefix>_<NN>, globally unique
title: Taxi expense reimbursement
domain: finance_expenses
metric_focus: [handoff_correctness] # primary metric(s) the task isolates
secondary_metrics: [routing_accuracy, global_success]
environments: [android_phone, windows_desktop]
apps: [MockPhotosApp, MockExpenseReportApp]
difficulty: 2                       # 1 (single read+enter) .. 5 (multi-env, multi-handoff, decoys)
code_ready: true                    # expressible with the 14 existing mock apps?
new_apps_needed: []                 # e.g. [MockRideShareApp] when code_ready: false
requires_clarification: false
forbidden_routes: false             # true if the task sets forbidden_routes
forbidden_substrings: false         # true if the task sets forbidden_handoff_substrings
source_of_truth: false              # true if a stale/duplicated fact is the crux
---
```

## Document body (sections, in order)

See [`TEMPLATE.md`](TEMPLATE.md). Every doc has: **Request**, **User & constraints**,
**Scenario**, **Environments & apps**, **Latent task graph**, **Required handoffs**,
**Desired final state**, **Decoys / ambiguity / source-of-truth**, **Metric rationale**
(how a naive agent fails the targeted metric), **Verifier sketch** (which config fields
are set and what each verifier returns), and **Implementation notes** (app/field mapping
if `code_ready`, or the new app surface needed).

## Domains and id prefixes

| Domain | Prefix | Folder |
| --- | --- | --- |
| Finance & expenses | `fin` | `finance_expenses/` |
| Scheduling & calendar | `sch` | `scheduling_calendar/` |
| Communication & messaging | `com` | `comms_messaging/` |
| Travel | `trv` | `travel/` |
| Health & wellness | `hlth` | `health_wellness/` |
| Auth & security | `sec` | `auth_security/` |
| Work docs & projects | `wrk` | `work_docs_projects/` |
| Shopping & orders | `shop` | `shopping_orders/` |
| Home & family | `home` | `home_family/` |
| Media & files | `med` | `media_files/` |

The existing 12 implemented tasks (do **not** duplicate): `auth_handoff`,
`receipt_amount`, `standup_reminder`, `work_to_personal_calendar`, `expense_then_notify`,
`clarification_sara`, `boundary_status_update`, `minimal_transfer`, `bank_password_reset`,
`contract_price_update`, `stale_contact_jordan`, `ooo_setup`.
