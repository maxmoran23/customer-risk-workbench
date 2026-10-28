# Data adapter review

**Status: synthetic worked design; execution evidence not supplied by this template.** Canonical field rules are in [the data contract](../docs/data-contract.md).

## Worked mapping

| Source concept | Canonical field | Transformation | Evidence/control |
| --- | --- | --- | --- |
| Synthetic event identity | `transaction_id` | Preserve opaque stable ID | Conflicting content under same ID must reject |
| Synthetic posting direction | `direction` | Map credit to `in`, debit to `out` relative to customer | Test direction with a hand-calculated case |
| Synthetic amount | `amount` | Already in declared base units | Reconcile totals; no mixed-unit input |
| Event timestamp | `occurred_at` | Parse explicit offset and normalize UTC | Boundary fixtures |
| Source delivery time | `available_at` | Preserve earliest usable timestamp | Late-arrival fixture |
| History manifest | `history_start`, `history_complete` | Preserve declared retention and completeness | Reconcile source counts and watermark |

## Worked reconciliation

Assume a synthetic source has four records with amounts `40,60,25,75`. Their gross total is `200`. One record is available after the evaluation cutoff. The canonical input may retain all four, while the eligible total at cutoff excludes the late record. These are different reconciliation stages; do not compare source total to eligible total without an exclusion bridge.

Required bridge: source rows/amount; parsing rejects; intentional exclusions; exact duplicates; collisions; canonical rows/amount; unavailable/future exclusions; eligible rows/amount. Each category needs a documented reason and must reconcile. A collision is a failure to resolve, not an ordinary duplicate to discard silently.

## Failure cases to execute

* Naive timestamp, impossible availability ordering, and profile before onboarding.
* Boolean numeric value, NaN/infinity, negative amount, unknown field, invalid direction/channel.
* Duplicate ID with equal content and duplicate ID with changed amount.
* Foreign-customer event and event before onboarding.
* Partially mapped jurisdiction evidence and incomplete retained history.

## Acceptance evidence

| Required artifact | Required detail |
| --- | --- |
| Mapping specification | Source field meaning, unit, conversion, null rules, version |
| Reconciliation report | Counts, totals, exclusions, rejected rows, delivery cutoff |
| Historical availability review | How knowledge time is established, known limitations |
| Independent calculations | Expected aggregates derived without calling engine helpers |
| Replay result | Same data/policy/cutoff produces same result under reordered input |

Record adapter owner, source version, code hash, tested fixtures, failures, unresolved limitations, and actual acceptance decision. **Current decision: not evaluated.**
