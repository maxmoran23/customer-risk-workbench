# Impact assessment report

**Status: report skeleton with guidance; no actual assessment or review is recorded.** Section headings and order match `crw.impact_report.SECTIONS` exactly, so the generated `impact-assessment.md` and this commentary align line for line. Keep the order every release; add new material to annexes, not to the core sections.

## Header

| Field | Source |
| --- | --- |
| Assessment ID | `assessment.json` `assessment_id` |
| Assessment hash | `assessment_hash` (full value in the record; the report shows the first 16 characters) |
| Before / after labels | `pre_label`, `post_label` |
| Input row counts and SHA-256 | `inputs` |
| Config digest and tier scale | `config_digest`, `tier_scale` |
| Change manifest | `change_id`, `release`, `change_type` |
| Register entry | `sequence` and `entry_hash` after `crw impact assess --register`; anchor updated |

## 1. Change summary

Generated: config description, manifest line, matched, moved and moved share, up, down, integrity findings in bold.

Guidance: one paragraph stating what changed and why, the headline counts, and the expectation and parity verdicts. If an integrity finding is present, it is the first sentence. A narrative drafted with AI goes here only after `crw impact narrative-check` returns `grounded` and a reviewer has checked meaning. Do not describe the change as correct or approved; the counts describe snapshots.

## 2. Population and exclusions

Generated: per segment and in total, matched, unchanged, up, down, entrants, exits, excluded (pinned), pinned moved, pin changed, segment changed.

Guidance: reconcile the population. Pre rows should equal matched plus exits plus pre-side exclusions; post rows should equal matched plus entrants plus post-side exclusions (each excluded party is counted once). State the source of entrants and exits (onboarding, closure, scope change) and whether any relate to the change. Any nonzero `Pinned moved` is an integrity defect, not a commentary item. Explain nonzero `Pin changed` (a pin applied or released between snapshots; these parties are excluded and their movement is not tested). Explain nonzero `Segment changed`; such parties are counted in their post-change segment.

## 3. Tier migration by segment

Generated: one matrix per paired segment; rows are the tier before, columns the tier after, lowest tier first; row totals and row moved share.

Guidance: identify the cells that carry most movement and tie each to the change mechanism. Comment on any movement of more than one tier, any movement opposite to the intended direction, and any segment whose moved share differs materially from the others. Quote cells as generated; do not recompute shares.

## 4. Aggregate-only segments

Generated: net change per tier, population change, minimum movers; segments configured but missing aggregates.

Guidance: state that no migration matrix exists for these segments and why row-level snapshots were not taken. Quote minimum movers as a lower bound only, and only where the population membership is confirmed unchanged. A segment listed as missing aggregates must be resolved before review. State whether the movement falls within the manifest's `expected_aggregate` bound; an undeclared segment with movement is an unexplained item in Annex A.

## Annex A. Expectation reconciliation

Generated: verdict; observed versus expected per migration expectation and, where declared, `POPULATION-ENTRANTS`, `POPULATION-EXITS` and `AGGREGATE-<segment>`; PASS or FAIL; unexplained items with count and row share (row share for migration cells only).

Generated in `expectations.json` but not in the report table: each unexplained item's `kind` (`migration`, `aggregate_only_movement`, `undeclared_entrants`, `undeclared_exits`) and `overlapping_expectations`, the expectation pairs that both claim a nonzero cell.

Guidance: for each FAIL and each unexplained item, record the explanation, the evidence (parties traced, logic reviewed), and whether the manifest or the change was wrong. Do not replace the original manifest; reference any corrected version separately. A `consistent_with_manifest` verdict needs a sentence confirming the manifest predates deployment. If expectations overlap, say so, since their observed counts are not additive.

## Annex B. Historical comparison

Generated: number of prior assessments, number of flagged rates, up to 20 flags with rate, history median and modified z or "outside observed range", and a count of further flags beyond 20.

Guidance: say which prior assessments were used and whether they are comparable in change type. Comment on each flag. An `outside_observed_range` flag means at least half of the prior rates were identical and this rate lies outside the range of all prior rates; a modified z flag means the rate is far from the median relative to the historical spread. The complete list is in `baseline.json`.

## Annex C. Parity with the standard process

Generated: verdict, cells compared, up to 20 differences, and a count of further differences.

Guidance: required during a parallel run (see the [parity test plan](parity-test-plan.md)). Record the tolerance used and the classification of every difference. State separately whether entrants, exits and exclusions agreed, because the parity check covers matrix cells only.

## Limits

Generated: three fixed statements from the engine.

Guidance: carry them unchanged into any summary for senior reviewers. Add assessment-specific limits: extraction timing, preview population, known definitional differences, aggregate-only segments.

## Review record

This section is outside the generated report and is completed by the adopter.

| Field | Entry |
| --- | --- |
| Prepared by (role) | |
| Reviewed by (role) | |
| Open items (integrity, FAIL, unexplained, parity) | |
| Decision and conditions | |
| Decision date | |
| Register anchor (`entries`, `last_entry_hash`) updated in release record; `verify-register --anchor` intact | |

**Current review result: none recorded.** A completed skeleton, a grounded narrative or a consistent verdict is not a release decision.
