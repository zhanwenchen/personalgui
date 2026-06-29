---
id: shop_03
title: Price-match using the retailer's current listed price
domain: shopping_orders
metric_focus: [source_of_truth]
secondary_metrics: [handoff_correctness, global_success]
environments: [windows_desktop]
apps: [MockBrowserFormApp, MockDocumentEditorApp]
difficulty: 3
code_ready: true
new_apps_needed: []
requires_clarification: false
forbidden_routes: false
forbidden_substrings: false
source_of_truth: true
---

# Price-match using the retailer's current listed price

**Request (verbatim, what the agent sees):**
> "Submit a price-match request for the Vellora blender at the price it's listed at now."

## User & constraints

`SyntheticUser(name="alex", constraints={"authoritative_source": "live_listing"})` — Alex
saved a price in a note last week, but the retailer's live product page is the source of
truth when the two disagree. The price-match form must carry the **currently listed** price,
not the stale note.

## Scenario

Alex jotted "Vellora blender $89.99" in a shopping note days ago, but the retailer has since
changed the listing to a higher current price. The product page (a browser page, treated as
the authoritative listing) shows the price that now applies. The agent must read the live
listed price and enter it into the price-match request form, ignoring the stale note — all
on the same desktop.

## Environments & apps

| Env | App (`type`) | Seeded state (highlights) |
| --- | --- | --- |
| `windows_desktop` | `MockBrowserFormApp` (listing page) | a read-context product page exposing `listed_price` as a copyable value `$94.50` (authoritative current price); this page is view-only context, not the form to submit |
| `windows_desktop` | `MockDocumentEditorApp` (shopping note) | `body_field="Shopping note: Vellora blender $89.99 (saw it last week)"`, `status="saved"` (stale decoy) |
| `windows_desktop` | `MockBrowserFormApp` (price-match form) | `fields={"match_price":"","product":""}`, `expected_fields={"match_price":"$94.50","product":"Vellora blender"}`, `status="drafting"` |

## Latent task graph (hidden from agent)

| Subtask id | Description | required_env | required_app | depends_on |
| --- | --- | --- | --- | --- |
| `read_listed` | Read the current listed price from the live product page. | `windows_desktop` | `listing_page` | — |
| `submit_match` | Enter the listed price + product on the price-match form and submit. | `windows_desktop` | `match_form` | `read_listed` |

## Required handoffs

| artifact_type | from_env | to_env | expected_value |
| --- | --- | --- | --- |
| `price` | `windows_desktop` | `windows_desktop` | `$94.50` |

## Desired final state

```
windows_desktop.match_form.status == "submitted"
```

## Decoys / ambiguity / source-of-truth

Two prices exist for the same product: the **stale shopping note** `$89.99` (read first
because it is the obvious "Vellora blender" mention and a lower, more appealing number) and
the **authoritative live listing** `$94.50` on the product page. The form's `expected_fields`
requires `$94.50`. An agent that trusts the saved note submits the stale figure and fails.
The note is the trap; the live listing is the source of truth.

## Metric rationale

The "Vellora price" fact is duplicated with one stale value. An agent that picks the
convenient lower note (`$89.99`) submits the wrong number and fails `global_success`, because
`expected_fields` is set to the authoritative live price. Reading the listing page is the only
path that matches.

## Verifier sketch

- **source_of_truth (primary):** the authoritative `$94.50` is what `expected_fields` /
  `desired_final_state` require; the note's `$89.99` is a decoy that fails the form match.
  (Encoded via the expected value, per README note.)
- **handoff_correctness (secondary):** within-env handoff carries `$94.50` from the listing
  page into the form.
- **global_success (secondary):** `match_form.status == "submitted"`.
- Config fields set: `desired_final_state`, `required_handoffs`.

## Implementation notes

- **`code_ready: true`.** The live listing is a `MockBrowserFormApp` used as read-context
  exposing a copyable `listed_price` (or a `MockProfileApp` `fields={"listed_price":"$94.50"}`
  if a strictly view-only authoritative surface is preferred); `MockDocumentEditorApp`
  (already `saved`) holds the stale note; the price-match `MockBrowserFormApp` enforces
  `expected_fields={"match_price":"$94.50","product":"Vellora blender"}`. Solvable via reading
  the listed price, copy/paste into `match_price`, enter `product`, `click submit`.
- Seed `initial_focus_app` on the note so the stale price is encountered first and the agent
  must navigate to the live listing to find the authoritative value.
