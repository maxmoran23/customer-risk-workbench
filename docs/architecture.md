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

`Transaction` contains `transaction_id`, `customer_id`, `occurred_at`, `available_at`, `amount`, `direction`, `counterparty_id`, `channel`, `jurisdiction_risk`, and `source_id`. Amounts are nonnegative and pre-normalized into one declared unit. Direction is `in`/`out`; channel is `wire`/`cash`/`card`/`digital`/`other`. Jurisdiction evidence is a supplied normalized value or null; the suite contains no real country-risk table. Unit normalization and source availability timestamps are adapter responsibilities. See the [data contract](data-contract.md) and [generated schemas](../configs).

```python
features = build_features(customer, transactions, as_of, base_unit="SYNTHETIC_UNIT")
assessment = score(features, policy, customer.customer_id, as_of)
```

`FeatureSet` holds `values`, `quality`, and `lineage`. Profile features use `profile.<key>` names; transaction aggregates use `txn.<window>.<metric>`. Eleven windows are `1d`, `7d`, `30d`, `90d`, `180d`, `365d`, `lifetime`, `last4`, `last10`, `last25`, and `last50`. Each emits thirteen metrics: `count`, `total`, `in_total`, `out_total`, `cash_share`, `digital_share`, `counterparty_count`, `high_risk_share`, `flow_through`, `concentration`, `mean_amount`, `max_amount`, and `jurisdiction_coverage`.

Five additional features measure expected-volume ratio, preceding-period growth, profile age, tenure and observed history. With twelve reference profile keys this gives **160 features**. Feature count is not model dimension: the reference policy uses 23 factors. The [feature catalog](../configs/features.json) defines denominators and units.

Time windows are `(cutoff-duration, cutoff]`. Last-N ties use occurrence time then transaction ID. A transaction must have occurred and become available by the cutoff. Expected-volume and growth ratios require complete window support; empty, zero-denominator and unmapped exposure ratios are unknown. `flow_through` is an aggregate incoming/outgoing balance proxy; it does not trace movement of particular funds.

`Policy.from_dict()`, `Policy.load()`, `Policy.to_dict()` and `Policy.digest` provide the configuration interface. A factor transforms observed evidence to a bounded severity. Each group applies its declared **sum or max** aggregation and cap; the six reference group caps sum to 100. Unknown factors contribute intervals. A complete point score is emitted only when all configured factors are observed and blocking review gates are absent. An incomplete index may retain a stable band if its bounds occupy that band and required evidence is present; `score` still remains null. The `provisional_index` is the lower bound, never an imputed complete score. [Full arithmetic and examples](scoring-method.md).

## Database consistency and reproducibility

Ingest occurs atomically. Repeated identical records are idempotent; a reused ID with conflicting content rejects the transaction. Customer snapshots retain effective and availability times. Historical batch eligibility requires at least one snapshot both effective and available at the cutoff. Future-only customers are excluded from that historical population.

A standalone `Store.assess()` owns a deferred read transaction when its caller has none. Customer and transaction reads therefore share one SQLite snapshot. A caller-owned transaction is preserved. Batch scoring uses a single transaction across the population, so chunk boundaries cannot change evidence visibility. Chunks bound retrieval work; they do not create separate portfolio snapshots. This favors coherent research results over multiwriter throughput. The implementation does not claim a distributed or high-availability architecture.

Assessment lineage binds customer ID, cutoff, canonical customer snapshot, included event content, source IDs, feature version, window/tie rules, and **actual amount-unit identifier**. Policy content has a separate hash. Assessment hashes bind the complete result; they detect content changes but are not cryptographic signatures or proof of source truth. Complete-run exports cannot expose a partial failed batch. Review history uses a local append-only hash chain with the security limitations described in [operations](operations.md).

Monitoring requires one cutoff, policy and unit per population. Between-population unit mismatches are rejected; policy differences are retained and flagged as a confounder. Migration uses matched customer IDs, while entrants and exits are separate. `REVIEW_REQUIRED` is an abstention state, not a risk category above HIGH. Crossed data/policy attribution evaluates all four combinations and allocates their arithmetic interaction across the two factors; it does not establish causality.

## Research and presentation

The optional research module uses separately generated stochastic labels. Preprocessing fits on training records; customers and time periods are separated; label availability is respected. Decision thresholds are selected on calibration data and frozen for holdout evaluation. Refit-regime comparisons and frozen-model perturbations are distinct outputs. Paired fixed-model stresses preserve model parameters and thresholds and report changed probabilities, labels and review workload.

The offline interface embeds synthetic data and research evidence. JSON characters that could terminate a script element are escaped; labels are inserted as text. No credentials, account lookup, network fetch or AI generation occurs in the viewer. Source code and machine-readable results remain authoritative for deeper review.

Prior public toolkit materials informed workflow design; this runtime is independently implemented. [Provenance and licensing](provenance.md) record the inspected public versions. See [verification](verification.md) for tested behavior and remaining limits.

## Program kits (0.2.0)

Two kits sit beside the behavioral index and share its contract helpers (`ContractError`, `identifier`, `strict_fields`, `digest`). Neither imports the transaction pipeline, and the behavioral index does not depend on them.

| Layer | Attribute review | Change-impact assessment |
| --- | --- | --- |
| Configuration | `configs/programs/catalog.json`, `model.json`, `rules.json`, `party-roles.json` | `configs/programs/tier-scale.json`, `assessment-config.json`, change manifests |
| Validation | `attributes.Catalog`, `rules.CategoricalModel`, `rules.RuleSet`: strict fields, class-score consistency, evidence references | `impact.TierScale`, `impact.validate_config`, `impact.validate_manifest` |
| Computation | Normalization audit, review diff and coverage, scoping, connections screen, rule simulation, stage gates | Partitioned join, matrices, aggregates, expectation reconciliation, baseline, parity, register; SQL generation for in-database execution |
| Presentation | Per-attribute Markdown sheets and CSV inventories | Fixed-order Markdown, long CSV and standalone HTML; facts pack and drafting prompt |
| Human decision | Policy owner records proposals and decisions; the code never sets `agreed` | Reviewer reads verdicts; the code never accepts or rejects a change |

Data flow between the kits: a reviewed catalog's proposals feed `program_demo.preview_change`, which estimates migrations on a design-time population and seeds the change manifest; the post-deployment assessment then reconciles against that manifest. See [program sequencing](program-sequencing.md) and [impact automation architecture](impact-automation-architecture.md).
