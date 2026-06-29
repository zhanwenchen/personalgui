---
id: sch_09
title: Resolve a double-booking by keeping the chat-confirmed event
domain: scheduling_calendar
metric_focus: [source_of_truth]
secondary_metrics: [global_success, handoff_correctness]
environments: [windows_desktop]
apps: [MockChatApp, MockGoogleCalendarApp]
difficulty: 4
code_ready: true
new_apps_needed: []
requires_clarification: false
forbidden_routes: false
forbidden_substrings: false
source_of_truth: true
---

# Resolve a double-booking by keeping the chat-confirmed event

**Request (verbatim, what the agent sees):**
> "I'm double-booked at 1pm — keep the one that's actually confirmed."

## User & constraints

`SyntheticUser(name="alex", constraints={"trust_order": "an event confirmed in chat outranks a tentative one"})` — two overlapping 1 PM events exist; only one is confirmed.

## Scenario

Alex's Google Calendar has two overlapping 1:00 PM events: **"Lunch with Morgan"** and **"Vendor demo"**. The chat thread shows Morgan wrote "confirmed for 1, see you then" while the vendor wrote "pencil us in, still tentative." The agent must keep the confirmed "Lunch with Morgan" — i.e. ensure it is the surviving 1 PM entry — and not keep the tentative vendor demo.

## Environments & apps

| Env | App (`type`) | Seeded state (highlights) |
| --- | --- | --- |
| `windows_desktop` | `MockChatApp` (`chat`) | Morgan: "confirmed for 1, see you then" (**authoritative**); Vendor: "pencil us in, still tentative" (**decoy**) |
| `windows_desktop` | `MockGoogleCalendarApp` (`google_calendar`) | pre-existing `[{title:"Lunch with Morgan", time:"13:00"}, {title:"Vendor demo", time:"13:00"}]`; `expected_titles:["Lunch with Morgan"]` |

## Latent task graph (hidden from agent)

| Subtask id | Description | required_env | required_app | depends_on |
| --- | --- | --- | --- | --- |
| `read_confirmation` | Read which 1 PM event is confirmed (Morgan) vs tentative (vendor) in chat | `windows_desktop` | `chat` | — |
| `keep_confirmed` | Ensure "Lunch with Morgan" is the kept 1 PM entry | `windows_desktop` | `google_calendar` | `read_confirmation` |

## Required handoffs

None across environments — same desktop. `handoff_correctness` covers carrying the confirmed title into the calendar edit.

## Desired final state

```
windows_desktop.google_calendar.sync_status == "synced"
```

(`expected_titles == ["Lunch with Morgan"]`; the kept entry must be the confirmed one. Note: `MockGoogleCalendarApp` flips to `synced` when all `expected_titles` are present — model "keep the right one" as ensuring the confirmed title is present/re-added if needed.)

## Decoys / ambiguity / source-of-truth

The "Vendor demo" is the decoy: it occupies the same slot and looks like a real meeting. The trap is that "tentative" status is only legible from the chat thread, not the calendar — both calendar rows look equally valid. Choosing by recency or alphabetical order picks wrong. Only the chat confirmation disambiguates.

## Metric rationale

An agent that keeps the vendor demo (or can't tell which is confirmed and keeps the wrong one) resolves the double-booking literally but on the wrong source — failing `source_of_truth`. Because `expected_titles` requires "Lunch with Morgan", the wrong choice leaves `sync_status` != `synced`, failing `global_success`.

## Verifier sketch

- **source_of_truth:** "Lunch with Morgan" is the value `expected_titles`/`desired_final_state` requires; keeping the tentative vendor event fails.
- **global_success:** `google_calendar.sync_status == "synced"`.
- **handoff_correctness:** the confirmed title must be the value carried into the calendar edit.
- Config fields set: `desired_final_state`.

## Implementation notes

- **`code_ready: true`.** `chat` = `MockChatApp` with the two status messages (read-only). `google_calendar` = `MockGoogleCalendarApp` seeded with both overlapping events and `expected_titles:["Lunch with Morgan"]`. The success condition is "confirmed title present"; since the app does not model deletion, the runnable encoding keeps the pre-existing "Lunch with Morgan" and grades on its presence — the agent's job is to identify and not disturb it (and not be lured into adding/keeping the vendor as the canonical 1 PM). If a delete action is later added, the desired state can additionally assert the vendor entry's removal.
