# Value reclassification request

**Status: synthetic worked request; no reclassification approved.** One request covers one normalized value. Classes, scores and population figures are illustrative or synthetic.

## Request

| Field | Worked example |
| --- | --- |
| Request id | `DEMO-RECLASS-001` |
| Catalog id, version, digest | `reference-attribute-catalog`, `1.0.0`, digest prefix `694a29422ede` |
| Attribute and value | `nature_of_business` / `parking_garage` |
| Current assignment | neutral 50 |
| Requested assignment | elevator 60 |
| Change kind and direction | `reclassified`, up |
| Requesting role | Reviewer role |
| Inventory status after import | `proposed` (the import refuses a change of class without at least one evidence id) |

## Evidence and rationale

| Evidence id | Kind | What it supports | What it does not establish |
| --- | --- | --- | --- |
| `FFIEC-CIB` | supervisory_guidance | The activity appears among common cash-intensive business examples | Any specific class or score |

Rationale: align the value with comparable cash-intensive businesses already classified as elevators. Counterexample to consider: a parking operator with fully electronic receipts, where the cash rationale does not apply.

## Expected population effect

| Field | Worked entry |
| --- | --- |
| Parties holding the value | 110 synthetic parties (inventory `party_count` in the demo workbook) |
| Expected direction | Some parties move up; none move down from this change alone |
| Preview method | Assess the design-time population at stages `current` and `proposed` on a catalog version carrying only this proposal |
| Preview result | Not isolated in the demo. The demo's combined preview (`preview_moved` in `evidence/program-demo-summary.json`) runs on a separate design-time synthetic sample and covers every recorded proposal, including the challenged one, because stage `proposed` ignores review status; it cannot be attributed to this value |
| Interaction with rules | `COMP-03` (draft) lists this value among cash businesses |
| Tolerance for the post-release check | Declared range for the change manifest |

## Decision record

| Field | Entry |
| --- | --- |
| Decision | Agreed, challenged, deferred or rejected |
| Deciding role | Policy owner role |
| Decision date | Actual date, `YYYY-MM-DD` |
| Decision reference | Adopter's decision artifact reference |
| Conditions | Any limits on the agreement |
| Release and impact reference | Catalog version that places the value in force and the change-impact assessment id |

An `agreed` inventory status requires the role, date and reference fields. Agreement does not change the in-force class; promotion happens in a released catalog version, assessed through [the change-impact program](../docs/impact-assessment-playbook.md). **Current decision: none recorded.**
