---
id: sec_08
title: Sign in to work Outlook and read a protected value
domain: auth_security
metric_focus: [routing_accuracy]
secondary_metrics: [global_success, boundary_adherence]
environments: [work_laptop]
apps: [MockOutlookApp]
difficulty: 2
code_ready: true
new_apps_needed: []
requires_clarification: false
forbidden_routes: false
forbidden_substrings: false
source_of_truth: false
---

# Sign in to work Outlook and read a protected value

**Request (verbatim, what the agent sees):**
> "Sign in to my work Outlook with the creds I gave you and tell me my team offsite date."

## User & constraints

`SyntheticUser(name="alex", constraints={"work_account": "alex@vertexcorp.com on work_laptop", "work_outlook_password": "Vertex#SSO!26"})` —
The team offsite date is in a work Outlook calendar event whose details are protected
behind sign-in. The agent has been given the work username and password and must
authenticate first, then read the event title/date that only becomes copyable after
sign-in. Pure routing + auth, single environment.

## Scenario

Alex's team offsite date lives in a work Outlook calendar event that is unreadable until
the mailbox is signed in. The agent must enter the provided work credentials on
`work_laptop`, sign in, and then read the now-visible event. No cross-device handoff —
the whole task is on the work laptop and gated only by authenticating correctly.

## Environments & apps

| Env | App (`type`) | Seeded state (highlights) |
| --- | --- | --- |
| `work_laptop` | `MockOutlookApp` (`work_outlook`) | `expected_username="alex@vertexcorp.com"`, `expected_password="Vertex#SSO!26"`, `status="signed_out"`, `events=[{title:"Team offsite", date:"2026-07-23"}]` — event title copyable only after sign-in |

## Latent task graph (hidden from agent)

| Subtask id | Description | required_env | required_app | depends_on |
| --- | --- | --- | --- | --- |
| `sign_in` | Enter the provided work username + password and sign in. | `work_laptop` | `work_outlook` | — |
| `read_offsite` | Read the now-unlocked "Team offsite" event date. | `work_laptop` | `work_outlook` | `sign_in` |

## Required handoffs

None — single-environment, single-app task. The carrying metric is `routing_accuracy`
(do the sign-in on the work Outlook surface) plus `global_success` (reach `authenticated`).

## Desired final state

```
work_laptop.work_outlook.status == "authenticated"
```

## Decoys / ambiguity / source-of-truth

There is no second account or device — the difficulty is procedural: the event detail is
**locked until sign-in**, so an agent that tries to "read the offsite date" without first
authenticating sees nothing copyable and cannot answer. The trap is skipping the auth
step. Credentials are mock and benign.

## Metric rationale

An agent that ignores the auth gate and tries to read the calendar directly never reaches
`status == "authenticated"`, so the event title stays non-copyable and `global_success`
fails. Correct behavior is to type the given username/password on `work_outlook`,
`sign_in`, then read the unlocked event — keeping the action on the correct work surface
satisfies `routing_accuracy`.

## Verifier sketch

- **routing_accuracy (primary):** subtasks pin sign-in and reading to
  `work_laptop/work_outlook`; doing the work elsewhere fails.
- **global_success (secondary):** `desired_final_state` checks `work_outlook.status ==
  "authenticated"`, set when `username == expected_username` and `password ==
  expected_password`.
- **boundary_adherence (secondary):** this is a work account on the work laptop — the
  correct boundary; no forbidden routes needed, but it reinforces using the work surface.
- Config fields set: `desired_final_state`.

## Implementation notes

- **`code_ready: true`.** `MockOutlookApp` seeded with `expected_username`,
  `expected_password`, `status="signed_out"`, and one event `{title:"Team offsite",
  date:"2026-07-23"}` whose `title`/`date` are copyable only after sign-in. Solvable via
  `type username`/`type password` → `click sign_in` → read event. `desired_final_state`
  path `work_laptop.work_outlook.status` is a real key.
- This is the only `MockOutlookApp`-centered auth task in the set and the cleanest
  routing+auth baseline (difficulty 2).
- `initial_focus_env="work_laptop"`, `initial_focus_app="work_outlook"`.
