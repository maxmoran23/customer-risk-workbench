# Limitations and appropriate claims

This workbench is an executable reference and review resource. It is not a validated institutional risk-rating system. The limits below are part of the product description, not optional footnotes.

## Claim register

| Evidence available | Appropriate statement | Unsupported upgrade |
| --- | --- | --- |
| Scenario tests pass in a recorded run | The stated assertions passed for those fixtures and version | All AML typologies are detected |
| Synthetic evaluation reports a metric | The metric describes the stated generated population and target | The model predicts criminal behavior in real customers |
| Benchmark completes | The measured workload ran on the recorded hardware/configuration | Unlimited scale or production service-level guarantee |
| Current sources are mapped | The design references identified public guidance | Regulatory certification or institution-specific compliance |
| Explanations show contributions | The arithmetic and supplied evidence can be inspected | Every feature has causal meaning |
| Data hashes and history exist | Changes can be compared or replayed under stated controls | Tamper-proof, authenticated, immutable records |
| Separate reviewer challenges code | An additional review found or did not find scoped issues | Formal independent institutional validation |

## Measurement limits

The index is constructed from configured transformations and group aggregations. Equal scores may arise from different evidence, and different scores can reflect differences in data availability rather than underlying behavior. Inspect the reason record, bounds, coverage, and routes before comparing customers.

Scores are not probabilities. The arithmetic interval describes possible outputs under missing severity assignments. It does not quantify probability of wrongdoing, statistical confidence, source reliability, model uncertainty, or unknown missing features. Coverage is the share of configured factors that are usable; correlated factors make it unsuitable as an independent evidence count.

The feature engine does not establish complete source delivery. `history_complete` is an upstream assertion. Eligible data can still be incorrect, duplicated before canonicalization, poorly resolved, or biased. A strict contract reduces ambiguity; it does not verify truth.

## Scope limits in the record model

The canonical transaction schema uses one normalized base unit, nonnegative amounts, and a simple direction. It has no native FX history, reversal ledger, settlement-state machine, origin/destination countries, real beneficial-ownership graph, or legal screening determination. Cross-border transaction behavior cannot be inferred from a jurisdiction-severity value alone.

`flow_through` compares aggregate incoming and outgoing amounts. `concentration` uses event counts. `high_risk_share` is an amount-weighted supplied severity. Those names must not be expanded into fund tracing, monetary concentration, or prohibited-exposure claims. Counterparty identifiers depend on upstream resolution.

The reference policy’s maximum groups reduce repeated contribution from overlapping windows, but do not prove a uniquely correct dependence treatment. Maximum aggregation can suppress distinct simultaneous signals; summation can overcount related ones. Both need empirical and conceptual review in the intended use.

## Synthetic research limits

Synthetic populations are generated from declared assumptions. Models can exploit generator structure that does not exist in operational data. Even a separate stochastic latent target is not a real outcome. More generated rows improve Monte Carlo precision within the generator; they do not remove misspecification.

A synthetic test suite can reveal implementation failures, construct edge cases, and support reproducibility. It cannot establish actual typology prevalence, customer harm, review productivity, or detection effectiveness. No monetary value or vendor-equivalence claim follows from code volume or test counts.

## Statistical limits

Confidence intervals depend on sampling and independence assumptions. Rare events, correlated observations, unreviewed populations, delayed labels, selective investigation, and repeated tuning can invalidate simple interpretations. An unknown metric is reported as undefined with a reason; a null value cannot be filled with zero to improve presentation.

Discrimination, calibration, stability, fairness, and operational usefulness are different properties. Good discrimination does not establish valid probabilities. Stable scores can consistently encode a poor rule. Subgroup comparisons with little support cannot establish absence of harm. A single aggregate number is insufficient acceptance evidence.

## Operational limits

The local package does not supply a managed production service, authentication, institution-grade access control, deployment approval, live list maintenance, case-management adjudication, or automatic customer actions. Review templates are not operating controls. Local storage and application-level append behavior need stronger independently governed controls where the use demands them.

Dependencies, hardware, data shape, disk, concurrency, and retention affect capacity. Preserve actual benchmark context and distinguish observed from extrapolated capacity. A run on one laptop is not a distributed-system resilience test.

## Source and legal limits

The source review is targeted, dated, and public-only. It is not a complete survey of every institution type, jurisdiction, rule, sanctions program, or subsequent administrative action. Supervisory guidance, international standards, FAQs, and proposed rules have different authority. Read [the source register](sources.json) and [regulatory map](regulatory-map.md) for status and retrieval caveats.

## Conditions that should stop or constrain evaluation

* Historical knowledge time cannot be established for a claimed historical backtest.
* Input units or customer identities cannot be reconciled.
* Required evidence is being silently replaced with zero or a guessed value.
* Outcome labels are generated from the policy being evaluated, or only selected positives were reviewed without an appropriate design.
* A reported metric has no denominator, target definition, partition provenance, or reproducible artifact.
* An output is being used to clear sanctions or authorize an adverse customer action beyond its stated purpose.

Record the failure and choose a narrower valid claim or repair the underlying issue. Changing the wording of the report cannot substitute for missing evidence.
