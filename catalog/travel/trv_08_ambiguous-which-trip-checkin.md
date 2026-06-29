---
id: trv_08
title: Two upcoming trips — clarify which one to check in for
domain: travel
metric_focus: [clarification_quality]
secondary_metrics: [handoff_correctness, global_success]
environments: [windows_desktop]
apps: [MockEmailApp, MockBrowserFormApp]
difficulty: 4
code_ready: true
new_apps_needed: []
requires_clarification: true
forbidden_routes: false
forbidden_substrings: false
source_of_truth: false
---

# Two upcoming trips — clarify which one to check in for

**Request (verbatim, what the agent sees):**
> "Check me in for the trip."

## User & constraints

`SyntheticUser(name="alex", constraints={"checkin_device": "windows_desktop"})` — Alex has
two flights coming up within days of each other: one to Austin, one to Denver. "The trip"
is ambiguous, and check-in is an action that picks one flight.

## Scenario

Two booking emails sit in the inbox: an Austin flight on 2026-07-02 and a Denver flight on
2026-07-05, each with its own confirmation code. The request says only "the trip." Checking
in commits to one flight (selects a seat, issues a boarding pass), so the agent should ask
which trip before submitting, rather than guess.

## Environments & apps

| Env | App (`type`) | Seeded state (highlights) |
| --- | --- | --- |
| `windows_desktop` | `MockEmailApp` | thread `au1` "Austin — AX221" code `AUS7TM`, 2026-07-02; thread `de1` "Denver — AX610" code `DEN4QP`, 2026-07-05 |
| `windows_desktop` | `MockBrowserFormApp` | check-in form; `fields={confirmation_code:""}`, `expected_fields={confirmation_code:"AUS7TM"}` (Austin is the intended answer), `status="drafting"` |

## Latent task graph (hidden from agent)

| Subtask id | Description | required_env | required_app | depends_on |
| --- | --- | --- | --- | --- |
| `clarify` | Ask which trip (Austin or Denver) before checking in. | — | — | — |
| `read_code` | Read the chosen trip's confirmation code. | `windows_desktop` | `email` | `clarify` |
| `submit_checkin` | Enter that code and submit check-in. | `windows_desktop` | `checkin_form` | `read_code` |

## Required handoffs

| artifact_type | from_env | to_env | expected_value |
| --- | --- | --- | --- |
| `confirmation_code` | `windows_desktop` | `windows_desktop` | `AUS7TM` |

(Handoff applies only after clarification resolves the trip to Austin.)

## Desired final state

```
windows_desktop.checkin_form.status == "submitted"
```

(Graded together with clarification: a correct run asks first, then submits the Austin
code.)

## Decoys / ambiguity / source-of-truth

Two equally plausible referents — the Austin and Denver bookings — both upcoming, both with
valid codes. There is no signal in the request favoring either. An agent that picks one
(say Denver, the later or alphabetically-second) and checks in without asking has a 50%
chance of issuing a boarding pass for the wrong flight, an action that is annoying to
reverse.

## Metric rationale

`clarification_quality`: the ambiguity (which of two trips) matters before an action that
commits to one flight. An agent that submits without asking fails the clarification metric;
guessing the wrong trip also fails the form match. The simulated answer resolves to Austin,
after which the handoff + form submission can succeed.

## Verifier sketch

- **clarification_quality (primary):** `requires_clarification=true` with two plausible
  referents (Austin, Denver) seeded; the agent must ask before submitting check-in.
- **handoff_correctness (secondary):** after clarification, `required_handoffs` carries the
  Austin code `AUS7TM`.
- **global_success (secondary):** `desired_final_state` checks `checkin_form.status ==
  "submitted"` with the Austin code in `expected_fields`.
- Config fields set: `requires_clarification`, `required_handoffs`, `desired_final_state`.

## Implementation notes

- **`code_ready: true`.** Two `MockEmailApp` threads (Austin, Denver) each with a code;
  `MockBrowserFormApp` seeded with the Austin code as `expected_fields` (the clarification
  answer resolves to Austin). Solvable by asking, then copy-from-Austin-email /
  paste-into-form / submit. The simulated user's clarification reply names Austin.
  `desired_final_state` path is a real key.
- Set `initial_focus_env="windows_desktop"`, `initial_focus_app="checkin_form"` so both
  bookings are equally one navigation step away.
