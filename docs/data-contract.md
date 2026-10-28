# Data contract and point-in-time reconstruction

The runtime accepts normalized, non-identifying research records. [contracts.py](../src/crw/contracts.py) is the executable field contract; [features.py](../src/crw/features.py) defines the aggregation semantics. Unknown fields are rejected rather than ignored. All fields below must be present, including fields whose value may be null.

## Customer snapshot

| Field | Type and constraint | Meaning and adapter obligation |
| --- | --- | --- |
| `customer_id` | Opaque string | Stable customer identity; no name, account number, or direct identifier |
| `as_of` | Timezone-aware ISO timestamp | Effective time of the supplied profile snapshot |
| `available_at` | Timezone-aware ISO timestamp, not earlier than `as_of` | Earliest time this snapshot was available to the process |
| `segment` | Opaque string | Declared comparison or reporting population; not a substitute for individual evidence |
| `onboarded_at` | Timezone-aware ISO timestamp, not later than `as_of` | Start of the customer relationship represented by this record |
| `profile` | Object of string keys to finite `[0,1]` numbers or null | Adapter-supplied evidence severities; active policy determines recognized scoring features |
| `expected_monthly_volume` | Nonnegative finite number or null | Declared expectation in the same base unit as transaction amounts |
| `source_id` | Opaque string | Reference to the adapter/source manifest |
| `history_start` | Timestamp between onboarding and snapshot `as_of` | Earliest retained history represented as available |
| `history_complete` | Explicit boolean | Adapter assertion that the supplied retained history is complete; not independently proved by the flag |

Identifier validation permits letters, numbers, underscore, period, colon, and hyphen with a bounded length. This is syntactic validation, not anonymization. Do not place personal information into syntactically valid identifiers. Null means unavailable or not established; `0` means an observed value on the supplied scale.

## Transaction

| Field | Type and constraint | Meaning |
| --- | --- | --- |
| `transaction_id` | Opaque string | Unique event identity for collision detection and stable sorting |
| `customer_id` | Opaque string | Owner of the observation |
| `occurred_at` | Timezone-aware ISO timestamp | Business event time |
| `available_at` | Timestamp not earlier than occurrence | Knowledge time for historical replay |
| `amount` | Finite nonnegative number | Amount already normalized into one dataset-declared base unit |
| `direction` | `in` or `out` | Direction relative to this customer |
| `counterparty_id` | Opaque string | Stable counterpart identity within the research dataset |
| `channel` | `wire`, `cash`, `card`, `digital`, or `other` | Adapter classification, with mapping version retained |
| `jurisdiction_risk` | Finite `[0,1]` number or null | Illustrative supplied exposure severity; no real jurisdiction list is bundled |
| `source_id` | Opaque string | Source/adapter lineage reference |

Booleans, NaN, and infinity are rejected as numeric values. Signed reversals, multiple currencies, settlement lifecycle, and transaction corrections are not represented directly by this schema. An adapter must establish an explicit canonical treatment before input; it must not silently discard negative signs or convert an invalid row into zero.

## Time eligibility

At cutoff `c`, an event is eligible only when it belongs to the customer, does not predate onboarding, occurred no later than `c`, became available no later than `c`, and is within retained history. A profile must be both effective and available at `c`. Timestamps are normalized to UTC after requiring an explicit timezone.

For duration `d`, the window is `(c-d, c]`. The lower boundary is excluded and cutoff included. The previous-month comparator uses `[30 days,60 days)` of age, so an event exactly 30 days old is in the prior period, not the current period. The word month in feature names refers to a fixed 30-day window, not a calendar month.

For last-N windows, eligible events are ordered by occurrence time and then transaction ID. This makes ties and input permutation deterministic. The window contains up to N records; having fewer than N is visible in support and completeness.

| Example | At cutoff `2026-10-28T12:00:00Z` |
| --- | --- |
| Occurred `11:00Z`, available `11:05Z` | Eligible |
| Occurred yesterday, available tomorrow | Excluded as unavailable |
| Occurred tomorrow | Excluded as future |
| Occurred exactly 7 days before cutoff | Excluded from 7-day window |
| Profile effective yesterday, available tomorrow | Assessment rejected using that profile |

These timestamps are synthetic illustrations. An upstream `available_at` reconstructed from today’s database modification time may be unsuitable for historical backtesting. If true historical availability is unavailable, disclose that limitation and do not claim leakage-free reconstruction.

## Aggregates

For eligible events in a window, let `n` be count, `A` total amount, `I` incoming amount, and `O` outgoing amount:

| Metric | Implemented calculation | Interpretation limit |
| --- | --- | --- |
| `count` | `n` | Event count, not independent customer support |
| `total`, `in_total`, `out_total` | Sums in the declared base unit | Gross observed amounts; not net economic exposure |
| `cash_share`, `digital_share` | Channel amount divided by `A` | Null if `A=0` |
| `counterparty_count` | Number of distinct counterpart IDs | Depends on entity resolution upstream |
| `high_risk_share` | `sum(amount*risk)/A` when all events have mapped risk | Amount-weighted supplied severity, not a count of prohibited transactions |
| `flow_through` | `min(I,O)/max(I,O)` | Aggregate balance proxy; no timing or fund tracing |
| `concentration` | Largest counterparty event count divided by `n` | Count concentration, not amount concentration or a network metric |
| `mean_amount`, `max_amount` | Mean and maximum event amount | Null on an empty window |
| `jurisdiction_coverage` | Mapped-event count divided by `n` | Count-based mapping coverage; not source accuracy |

Empty windows have count and sums equal to zero, with undefined ratios null. If even one eligible event lacks jurisdiction mapping, `high_risk_share` is null; treating unmapped exposure as zero would bias it downward. There is no computed `cross_border_share`: the record lacks explicit origin/destination geography. `profile.cross_border_exposure` is a supplied profile concept and cannot repair that absence.

`txn.30d.expected_volume_ratio` requires positive expected volume and a complete current 30-day history. `txn.30d.growth_ratio` requires a positive preceding-period denominator and complete retained history spanning 60 days. Zero baseline is undefined, not infinite growth. The expectation is compared to a fixed 30-day gross total; adapters must reconcile differing expectation definitions.

## Coverage and scoring eligibility

Window aggregates may exist even when a window is incomplete. `quality.complete_windows` records coverage; factor configuration separately controls minimum support and whether full coverage is necessary. Duration completeness requires confirmed history and sufficient retained days. Last-N completeness requires confirmed history and enough events. Lifetime completeness requires confirmed history beginning at onboarding.

`history_complete=true` does not prove that every upstream event arrived. An adopting adapter needs reconciliation evidence: source counts/totals, delivery watermark, rejected rows, duplicate/collision counts, and known late-arrival bounds. The engine cannot infer omissions it never receives.

## Provenance and reproducibility

Feature lineage includes the cutoff, customer snapshot digest, eligible event digest, source IDs, feature version, window boundary convention, tie-break rule, and unit declaration. The assessment adds policy and assessment hashes. A content hash detects changed content; it is not a digital signature, proof of source authenticity, or immutable storage guarantee.

A source manifest should record the adapter version, declared unit, normalization rule, source schema/version, extraction cutoff, availability interpretation, retained-history start, and reconciliation evidence. Keep private mapping details in an approved adopting environment. Public examples use synthetic identifiers and values only.

## Adapter acceptance checks

Before a new adapter is accepted, supply paired source-to-canonical examples, independently calculated aggregates, rejected-record examples, currency/unit reconciliation, historical availability evidence, and collision behavior. Demonstrate that replaying the same snapshot and policy produces the same result regardless of input order or processing chunk size. Use [the adapter workpaper](../templates/data-adapter-review.md).
