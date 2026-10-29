# Customer Risk Workbench / 02 data and implementation

Public reference material. Synthetic examples and illustrative policies. No institutional approval or production-performance claim.

Source repository: https://github.com/maxmoran23/customer-risk-workbench

Attachment groups preserve full methods; source code and runnable tests remain in the repository.


---

Source: `docs/architecture.md`


# Architecture and implementation contracts

The workbench separates source records, feature construction, configured policy decisions, compound hypotheses, and outcome research. Bundled records and outcomes are synthetic. Operating weights, caps, bands and investigation thresholds are illustrative.

## Module boundaries

| Module | Responsibility | Boundary |
| --- | --- | --- |
| `contracts.py` | Immutable typed records; finite numbers; canonical UTC timestamps; opaque IDs | Reject unknown fields, booleans passed as numbers, malformed timestamps and invalid temporal ordering |
| `features.py` | Event-time and availability-time windows; support, retention and lineage | Include only evidence effective and available at the cutoff |
| `policy.py` | Versioned factors, transforms, sum/max groups, caps, bands and canonical hash | Every policy choice is inspectable; no regulatory status implied |
| `scoring.py` | Contributions, bounds, score availability, reason traces and review routes | Index is not a probability; unresolved evidence is not silently benign |
| `patterns.py` | Declarative all/any/not hypotheses and three-valued comparisons | Unknown evidence propagates; matches add no hidden score points |
| `storage.py` | Real SQLite ingest, indexed retrieval, snapshot reads and atomic assessment batches | Idempotency, collision rejection, immutable onboarding and complete-run export |
| `workflow.py` | Append-only local review records, separate reviewer identifiers, evidence and hash chain | No authentication, external attestation or production access-control claim |
| `validation.py` | Performance metrics, intervals, sampling, drift and paired uncertainty | Undefined statistics remain null with reasons |
| `learning.py` | Synthetic outcome research, temporal/customer splits and alternative models | Outcomes are generated separately from the policy index; no empirical AML effectiveness claim |
| `monitoring.py` | Population diagnostics, matched-ID migration, weighted review sampling and crossed change attribution | Composition, policy, units and missingness remain explicit |
| `stress.py` | Paired policy perturbations and complete-score availability | A change in a lower bound is not presented as a completed-score change |
| `synthetic.py` / `scenarios.py` | Seeded populations and executable expected-behavior cases | Case coverage demonstrates specified behavior, not exhaustive typology coverage |
| `io.py` / `cli.py` | Strict JSONL/CSV, atomic file writes, pipeline and reproduction commands | Local files; no remote service, AI API or automatic scheduler |
| `render.py` | Standalone offline HTML and safe embedded JSON | Selected examples are separate from portfolio statistics |

## Input, feature and scoring APIs

`Customer` contains `customer_id`, `as_of`, `available_at`, `segment`, `onboarded_at`, `profile`, `expected_monthly_volume`, `source_id`, `history_start`, and `history_complete`. Profiles map policy-declared keys to normalized `[0,1]` values or explicit null. The reference policy declares twelve profile keys; custom policies can declare up to 1,000. `history_start` and `history_complete` describe retained evidence, not assumed customer lifetime. Onboarding is immutable across snapshots of the same customer.

`Transaction` contains `transaction_id`, `customer_id`, `occurred_at`, `available_at`, `amount`, `direction`, `counterparty_id`, `channel`, `jurisdiction_risk`, and `source_id`. Amounts are nonnegative and pre-normalized into one declared unit. Direction is `in`/`out`; channel is `wire`/`cash`/`card`/`digital`/`other`. Jurisdiction evidence is a supplied normalized value or null; the suite contains no real country-risk table. Unit normalization and source availability timestamps are adapter responsibilities. See the [data contract](https://github.com/maxmoran23/customer-risk-workbench/blob/main/docs/data-contract.md) and [generated schemas](https://github.com/maxmoran23/customer-risk-workbench/tree/main/configs).

```python
features = build_features(customer, transactions, as_of, base_unit="SYNTHETIC_UNIT")
assessment = score(features, policy, customer.customer_id, as_of)
```

`FeatureSet` holds `values`, `quality`, and `lineage`. Profile features use `profile.<key>` names; transaction aggregates use `txn.<window>.<metric>`. Eleven windows are `1d`, `7d`, `30d`, `90d`, `180d`, `365d`, `lifetime`, `last4`, `last10`, `last25`, and `last50`. Each emits thirteen metrics: `count`, `total`, `in_total`, `out_total`, `cash_share`, `digital_share`, `counterparty_count`, `high_risk_share`, `flow_through`, `concentration`, `mean_amount`, `max_amount`, and `jurisdiction_coverage`.

Five additional features measure expected-volume ratio, preceding-period growth, profile age, tenure and observed history. With twelve reference profile keys this gives **160 features**. Feature count is not model dimension: the reference policy uses 23 factors. The [feature catalog](https://github.com/maxmoran23/customer-risk-workbench/blob/main/configs/features.json) defines denominators and units.

Time windows are `(cutoff-duration, cutoff]`. Last-N ties use occurrence time then transaction ID. A transaction must have occurred and become available by the cutoff. Expected-volume and growth ratios require complete window support; empty, zero-denominator and unmapped exposure ratios are unknown. `flow_through` is an aggregate incoming/outgoing balance proxy; it does not trace movement of particular funds.

`Policy.from_dict()`, `Policy.load()`, `Policy.to_dict()` and `Policy.digest` provide the configuration interface. A factor transforms observed evidence to a bounded severity. Each group applies its declared **sum or max** aggregation and cap; the six reference group caps sum to 100. Unknown factors contribute intervals. A complete point score is emitted only when all configured factors are observed and blocking review gates are absent. An incomplete index may retain a stable band if its bounds occupy that band and required evidence is present; `score` still remains null. The `provisional_index` is the lower bound, never an imputed complete score. [Full arithmetic and examples](https://github.com/maxmoran23/customer-risk-workbench/blob/main/docs/scoring-method.md).

## Database consistency and reproducibility

Ingest occurs atomically. Repeated identical records are idempotent; a reused ID with conflicting content rejects the transaction. Customer snapshots retain effective and availability times. Historical batch eligibility requires at least one snapshot both effective and available at the cutoff. Future-only customers are excluded from that historical population.

A standalone `Store.assess()` owns a deferred read transaction when its caller has none. Customer and transaction reads therefore share one SQLite snapshot. A caller-owned transaction is preserved. Batch scoring uses a single transaction across the population, so chunk boundaries cannot change evidence visibility. Chunks bound retrieval work; they do not create separate portfolio snapshots. This favors coherent research results over multiwriter throughput. The implementation does not claim a distributed or high-availability architecture.

Assessment lineage binds customer ID, cutoff, canonical customer snapshot, included event content, source IDs, feature version, window/tie rules, and **actual amount-unit identifier**. Policy content has a separate hash. Assessment hashes bind the complete result; they detect content changes but are not cryptographic signatures or proof of source truth. Complete-run exports cannot expose a partial failed batch. Review history uses a local append-only hash chain with the security limitations described in [operations](https://github.com/maxmoran23/customer-risk-workbench/blob/main/docs/operations.md).

Monitoring requires one cutoff, policy and unit per population. Between-population unit mismatches are rejected; policy differences are retained and flagged as a confounder. Migration uses matched customer IDs, while entrants and exits are separate. `REVIEW_REQUIRED` is an abstention state, not a risk category above HIGH. Crossed data/policy attribution evaluates all four combinations and allocates their arithmetic interaction across the two factors; it does not establish causality.

## Research and presentation

The optional research module uses separately generated stochastic labels. Preprocessing fits on training records; customers and time periods are separated; label availability is respected. Decision thresholds are selected on calibration data and frozen for holdout evaluation. Refit-regime comparisons and frozen-model perturbations are distinct outputs. Paired fixed-model stresses preserve model parameters and thresholds and report changed probabilities, labels and review workload.

The offline interface embeds synthetic data and research evidence. JSON characters that could terminate a script element are escaped; labels are inserted as text. No credentials, account lookup, network fetch or AI generation occurs in the viewer. Source code and machine-readable results remain authoritative for deeper review.

Prior public toolkit materials informed workflow design; this runtime is independently implemented. [Provenance and licensing](https://github.com/maxmoran23/customer-risk-workbench/blob/main/docs/provenance.md) record the inspected public versions. See [verification](https://github.com/maxmoran23/customer-risk-workbench/blob/main/docs/verification.md) for tested behavior and remaining limits.

## Program kits (0.2.0)

Two kits sit beside the behavioral index and share its contract helpers (`ContractError`, `identifier`, `strict_fields`, `digest`). Neither imports the transaction pipeline, and the behavioral index does not depend on them.

| Layer | Attribute review | Change-impact assessment |
| --- | --- | --- |
| Configuration | `configs/programs/catalog.json`, `model.json`, `rules.json`, `party-roles.json` | `configs/programs/tier-scale.json`, `assessment-config.json`, change manifests |
| Validation | `attributes.Catalog`, `rules.CategoricalModel`, `rules.RuleSet`: strict fields, class-score consistency, evidence references | `impact.TierScale`, `impact.validate_config`, `impact.validate_manifest` |
| Computation | Normalization audit, review diff and coverage, scoping, connections screen, rule simulation, stage gates | Partitioned join, matrices, aggregates, expectation reconciliation, baseline, parity, register; SQL generation for in-database execution |
| Presentation | Per-attribute Markdown sheets and CSV inventories | Fixed-order Markdown, long CSV and standalone HTML; facts pack and drafting prompt |
| Human decision | Policy owner records proposals and decisions; the code never sets `agreed` | Reviewer reads verdicts; the code never accepts or rejects a change |

Data flow between the kits: a reviewed catalog's proposals feed `program_demo.preview_change`, which estimates migrations on a design-time population and seeds the change manifest; the post-deployment assessment then reconciles against that manifest. See [program sequencing](https://github.com/maxmoran23/customer-risk-workbench/blob/main/docs/program-sequencing.md) and [impact automation architecture](https://github.com/maxmoran23/customer-risk-workbench/blob/main/docs/impact-automation-architecture.md).



---

Source: `docs/data-contract.md`


# Data contract and point-in-time reconstruction

The runtime accepts normalized, non-identifying research records. [contracts.py](https://github.com/maxmoran23/customer-risk-workbench/blob/main/src/crw/contracts.py) is the executable field contract; [features.py](https://github.com/maxmoran23/customer-risk-workbench/blob/main/src/crw/features.py) defines the aggregation semantics. Unknown fields are rejected rather than ignored. All fields below must be present, including fields whose value may be null.

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

Before a new adapter is accepted, supply paired source-to-canonical examples, independently calculated aggregates, rejected-record examples, currency/unit reconciliation, historical availability evidence, and collision behavior. Demonstrate that replaying the same snapshot and policy produces the same result regardless of input order or processing chunk size. Use [the adapter workpaper](https://github.com/maxmoran23/customer-risk-workbench/blob/main/templates/data-adapter-review.md).



---

Source: `docs/example-walkthrough.md`


# A compact, reproducible walkthrough

The [`examples/`](https://github.com/maxmoran23/customer-risk-workbench/tree/main/examples) package contains three invented customers and 240 invented transactions. It exercises the actual parsing, feature, scoring, hypothesis and monitoring APIs without a database file or additional dependencies. The expected scores are hand-reconciled below; the executable checks also verify fixture hashes and reconstruct every input record.

## Run it

From the repository root, with the project installed in the active Python environment:

```bash
python examples/walkthrough.py
```

To retain the full evidence, including active hypotheses, assessment hashes, missing-evidence bounds and monitoring diagnostics:

```bash
python examples/walkthrough.py --out runs/example-walkthrough.json
```

A checkout that has not been installed can use the source package directly:

```bash
PYTHONPATH=src python examples/walkthrough.py
```

The walkthrough always verifies its expectations. It raises an exception and exits unsuccessfully if the fixture, active policy, expected arithmetic, screening route, input-order replay or missing-evidence behavior differs. It does not silently refresh expected values from observed engine output.

## Files and intended use

| File | Role |
| --- | --- |
| [`customers.jsonl`](https://github.com/maxmoran23/customer-risk-workbench/blob/main/examples/customers.jsonl) | Three strict normalized customer records with complete declared retained history |
| [`transactions.jsonl`](https://github.com/maxmoran23/customer-risk-workbench/blob/main/examples/transactions.jsonl) | Eighty transactions per customer; 240 rows total |
| [`fixture-manifest.json`](https://github.com/maxmoran23/customer-risk-workbench/blob/main/examples/fixture-manifest.json) | Explicit synthetic unit, assessment cutoff, counts, policy hash and input-file hashes |
| [`expected-summary.json`](https://github.com/maxmoran23/customer-risk-workbench/blob/main/examples/expected-summary.json) | Independently specified score/group expectations and required review outcomes |
| [`build_fixtures.py`](https://github.com/maxmoran23/customer-risk-workbench/blob/main/examples/build_fixtures.py) | Deterministic constructor that can reproduce the JSONL inputs without randomness |
| [`walkthrough.py`](https://github.com/maxmoran23/customer-risk-workbench/blob/main/examples/walkthrough.py) | Runnable verification and explanation using public workbench APIs |

All amounts use `SYNTHETIC_UNIT`; these are invented amounts, not dollars or other currencies. The assessment cutoff is `2026-10-01T00:00:00Z`. The manifest's unit is passed explicitly to feature construction and recorded in assessment lineage. There are no real countries, individuals, companies, screening records or outcome labels in these fixtures.

## What the three examples represent

| Example | Complete index | Stored band | Separate screening route | Purpose |
| --- | --- | --- | --- | --- |
| `example-customer-01` | 15.75 | LOW | FALSE | Low supplied profile concerns with balanced transaction totals |
| `example-customer-02` | 48.40 | MODERATE | FALSE | Increased contextual concerns and activity above its supplied expectation |
| `example-customer-03` | 82.80 | HIGH | TRUE | Several elevated supplied concerns, a fivefold expectation ratio and unresolved screening |

The segment names are descriptive fixture fields. They do not set the scores. The reference policy uses the declared normalized evidence and supported transaction aggregates.

Each customer has sixty recent transactions of 100 units and twenty preceding-month transactions of 300 units. Thus, current-month volume is 6,000 units and preceding-month volume is also 6,000 units. The growth ratio is exactly 1. Incoming and outgoing amounts balance, producing an aggregate balance proxy of 1. This does not establish that any incoming funds financed an outgoing transaction.

The supplied monthly expectations are 6,000, 2,000 and 1,200 units. The expectation ratios are therefore 1, 3 and 5. These expectations are constructed fixture inputs; they are not independently observed business information.

## Reconcile the group arithmetic

| Group | Example 01 | Example 02 | Example 03 |
| --- | ---: | ---: | ---: |
| Customer | 1.25 | 14.50 | 22.00 |
| Geography | 0.75 | 10.50 | 12.00 |
| Product/channel | 0.75 | 6.80 | 12.80 |
| Behavior | 12.00 | 12.00 | 25.00 |
| Context | 0.50 | 2.60 | 6.00 |
| Evidence | 0.50 | 2.00 | 5.00 |
| **Total** | **15.75** | **48.40** | **82.80** |

For example 01, the customer group is `10×0.05 + 5×0.05 + 10×0.05 = 1.25`. Profile geography and observed geography both contribute 0.75, but the geography group takes their maximum rather than their sum. Product and channel contribute `8×0.05 + 7×0.05 = 0.75`. Context contributes `8×0.05 + 2×0.05 = 0.50`. Documentation contributes `10×0.05 = 0.50`; the one-day profile age adds no points.

The balanced-flow proxy supplies 12 behavior points to the first two examples. For example 02, the volume factor's raw contribution is `25×(3−1.5)/(5−1.5) = 10.7142857`; maximum aggregation therefore retains 12. For example 03, ratio 5 supplies 25 points, the behavior-group cap. Overlapping time and event-count windows do not each add another copy of their contributions.

These are policy-arithmetic expectations. They do not imply criminality probabilities, empirical calibration or a recommended institutional risk appetite.

## Follow the executable steps

1. **Verify provenance and parse.** The walkthrough checks input-file SHA-256 values, parses every JSONL row through `Customer.from_dict` or `Transaction.from_dict`, and compares the parsed records with the independent fixture constructor.
2. **Build available-at-cutoff features.** Each customer receives only its own records. `build_features(..., base_unit=manifest["base_unit"])` preserves time, support, retention and unit information.
3. **Score and reconcile.** `score(...)` runs the reference policy. The walkthrough compares every group contribution, complete score, band and screening route with the committed expectations.
4. **Verify replay.** Reversing the input transaction order must reproduce the same assessment hash.
5. **Inspect hypotheses.** `evaluate_patterns(...)` returns contextual review questions. The evidence output retains TRUE hypotheses with their lawful alternatives and next-evidence requirements.
6. **Remove mandatory evidence in a copy.** `dataclasses.replace(...)` creates an altered profile with unknown ownership opacity. The original customer and checked-in records remain unchanged.
7. **Monitor the change with its actual sample size.** `monitor_portfolios(...)` compares the three baseline assessments with the altered portfolio while retaining its illustrative minimum population of 50. It reports insufficient population support instead of treating three examples as adequate monitoring evidence.

## The missing-evidence result is deliberately instructive

| Measure | Complete example 01 | Ownership evidence removed |
| --- | ---: | ---: |
| Final score | 15.75 | `null` |
| Lower bound | 15.75 | 15.25 |
| Upper bound | 15.75 | 25.25 |
| Band | LOW | REVIEW_REQUIRED |
| Mandatory gate | None | `required_evidence_missing` |

Removing the known ownership contribution subtracts 0.50 from the provisional lower bound. The upper bound permits the full 10 ownership points, producing `[15.25,25.25]`. Although that interval remains within the reference LOW band, the mandatory-evidence gate still requires review. The lower-bound decrease is not evidence that the customer's risk declined.

The script preserves both complete-score availability and the interval in its output. It labels the comparison's numerical delta as provisional and reports that the policy stayed fixed while data changed.

## Expected console result

The console summary includes these values:

```text
status: verified
customers: 3
transactions: 240
complete scores: 15.75, 48.40, 82.80
stored bands: LOW, MODERATE, HIGH
missing ownership: score=null; REVIEW_REQUIRED; bounds=[15.25,25.25]
monitoring signal: insufficient_population_support
```

The actual output is valid JSON. The optional evidence file adds full explanatory details. Fixture hashes and the active policy hash are retained so the same result can be tied to the inputs used.

To reproduce the fixture files themselves:

```bash
python examples/build_fixtures.py
python examples/walkthrough.py
```

The constructor rebuilds only the two JSONL files and their manifest. It does not rewrite the hand-specified expected scores. If the active reference policy changes, review its intended effect and update the example's expectations through normal code review; do not treat an unexplained difference as a successful reproduction.

Three engineered examples cannot establish sampling adequacy, detection performance, fairness or portfolio calibration. They make the software's behavior inspectable before a reviewer invests in the larger synthetic run or an independently governed evaluation.



---

Source: `templates/data-adapter-review.md`


# Data adapter review

**Status: synthetic worked design; execution evidence not supplied by this template.** Canonical field rules are in [the data contract](https://github.com/maxmoran23/customer-risk-workbench/blob/main/docs/data-contract.md).

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
