# Customer Risk Workbench / 03 scoring and scenarios

Public reference material. Synthetic examples and illustrative policies. No institutional approval or production-performance claim.

Source repository: https://github.com/maxmoran23/customer-risk-workbench

Attachment groups preserve full methods; source code and runnable tests remain in the repository.


---

Source: `docs/scoring-method.md`


# Scoring method and worked arithmetic

The reference policy produces an explainable priority index, an arithmetic envelope for missing evidence, a band or review state, and separate screening-workflow routes. It does not estimate the probability of financial crime. Policy coefficients express illustrative judgments, not fitted or regulator-prescribed parameters.

## Normalization

For an increasing factor with observation `x`, lower transition `l`, upper transition `h` and weight `w`:

```text
severity(x) = min(1, max(0, (x-l)/(h-l)))
raw_points  = w * severity(x)
```

A decreasing factor uses `1-severity(x)`. The policy rejects nonfinite values, nonpositive transition widths, unknown feature references, duplicate IDs and invalid caps. Profile evidence must already have a documented `[0,1]` mapping. Raw activity features retain their units until the factor transformation.

For example, an expected-volume ratio of 3.25 with transitions 1.5 and 5 has severity `(3.25-1.5)/(5-1.5)=0.5`. With weight 25, its raw contribution is 12.5. This calculation says where the observation lies on the illustrative scale; it does not establish suspiciousness or calibrated risk.

## Group aggregation

| Group | Cap | Method | Reason for grouping |
| --- | ---: | --- | --- |
| Customer | 25 | Capped sum | Ownership, complexity and source-of-funds evidence |
| Geography | 15 | Capped maximum | Profile and transaction geography can represent the same exposure |
| Product/channel | 15 | Capped sum | Distinct product and delivery-channel dimensions |
| Behavior | 25 | Capped maximum | Overlapping windows and related activity proxies should not each get a full vote |
| Context | 10 | Capped sum | Adverse information and contextual PEP exposure |
| Evidence | 10 | Capped maximum | Documentation and profile-age signal |

For a sum group, `points=min(cap,sum(raw_points))`. For a max group, `points=min(cap,max(raw_points))`. The complete index is the sum of group points. Raw factor points do not necessarily sum to the index; the interface presents group contributions and labels raw points separately.

If five overlapping cash windows each produce 15 raw points, the behavior group receives 15 points, not 75. If another behavior factor produces 20, the group receives 20. This is an intentional conservative aggregation choice with a tradeoff: joint moderate signals are not reinforced within max groups. A different interaction design needs explicit justification, tests, and validation.

## Missing evidence and abstention

Each unavailable factor is allowed to range from zero to its full weight. Apply the same sum/max/cap operation to known and possible values to obtain group lower and upper bounds. Add the group bounds to obtain the portfolio-independent customer envelope. These are worst-case arithmetic bounds; they are neither confidence intervals nor a probability distribution.

- `provisional_index` is the known-evidence lower bound.
- `score` is null unless every configured factor is available and no hard gate applies.
- Missing required evidence forces `REVIEW_REQUIRED` even if its range falls within one band.
- Unconfirmed required history completeness forces review.
- Optional missing evidence whose envelope crosses a band boundary forces review.
- If optional missing evidence stays entirely within one band, the band may be retained with `band_basis=bounded_incomplete_evidence`; the complete score is still null.

Reference band minima are 0, 30 and 60. The comparison is inclusive at each minimum. An envelope `[12,27]` may retain LOW if no hard gate applies. `[15.75,30]` spans LOW and MODERATE and requires review. A null ratio caused by no prior-period activity is not replaced with zero or infinity.

## Screening and compound patterns

An unresolved screening flag produces a separate TRUE/FALSE/UNKNOWN route. It does not change the priority index and cannot be cancelled by a low index. A FALSE route means only that the supplied predicate did not fire; it is not sanctions clearance. Missing screening input remains UNKNOWN.

Compound hypotheses in `patterns.py` use three-valued logic and retain their predicate tree, benign explanation, and next evidence. They add no score points. The balance proxy `min(in,out)/max(in,out)` is not traced pass-through, and a digital-channel ratio is not evidence of illicit activity.

## Extending normalized evidence

The default catalog includes the declared reference profile keys. A custom policy can supply an explicit `profile_keys` list of up to 1,000 normalized fields and reference them as `profile.<key>`. Declare each mapping's source, effective date, unit, missing treatment, monotonicity and rationale. Extra undeclared profile keys are rejected during scoring so spelling errors cannot silently disappear. Keep unused reference keys declared when the input schema still supplies them.

Normalization does not make heterogeneous evidence scientifically commensurate. Calibration, factor dependence, segment effects, missingness, qualitative judgment, and intended use still require challenge. Adding more factors or more decimal places cannot substitute for that evidence.

## Change attribution

`monitoring.attribute_change` evaluates old/new data under old/new policies, producing four results. It averages the two orderings to allocate total provisional movement between data and policy effects, and exposes the interaction. This is an arithmetic decomposition. It does not isolate causal effects, and changes in missingness or elapsed time remain part of the data effect.

Sensitivity output labels changes in provisional lower bounds explicitly. Removing evidence can lower a bound while increasing uncertainty and suppressing the final score; this is not evidence of a risk reduction. Complete-score deltas are calculated only for pairs with two complete scores, with the paired denominator retained.



---

Source: `docs/scenario-design.md`


# Scenario design and coverage

A scenario is a falsifiable statement about behavior under specified inputs. A typology is a hypothesis about a pattern requiring context. Neither is evidence that a named individual committed an offense. Public examples remain synthetic and use no real customer or live screening data.

## Case anatomy

Each case should specify an ID, purpose, input fixture, cutoff, source provenance, expected calculation or relation, expected gates/routes, lawful counterexample, missing evidence, and failure interpretation. An expected result should be independent of the function being tested. Copying the engine output into the expected field creates a regression snapshot, not independent correctness evidence.

| Case family | What it tests | Example question |
| --- | --- | --- |
| Positive mechanism | Signal responds to a constructed condition | Does a configured cash-share ramp change severity as declared? |
| Benign counterexample | Same observable pattern with lawful explanation | Does balanced treasury activity get described as a proxy rather than traced laundering? |
| Missing evidence | Incomplete data remains visible | Does unmapped exposure become unknown rather than zero? |
| Temporal adversary | Information unavailable at cutoff is excluded | Can a late-arriving event leak into a backtest? |
| Boundary | Exact threshold and window semantics | Which band contains a value exactly at its minimum? |
| Structural invariant | Behavior preserved under irrelevant changes | Does permutation or chunk size change the assessment? |
| Cross-control | One workflow cannot neutralize another | Does a low index suppress an unresolved screening referral? |
| Operational fault | Invalid input is handled predictably | Is a conflicting duplicate rejected without partial success? |

## Worked behavioral example: balanced flows

Synthetic events total 120 incoming units and 120 outgoing units in a complete window. The balance proxy is `min(120,120)/max(120,120)=1`. A policy ramp from `0.7` to `1` produces maximum severity for that feature.

This establishes an aggregate numerical pattern. It does not show that the outgoing events used the incoming funds, occurred after them, involved the same counterparties, or lacked an economic purpose. A legitimate settlement business can produce the same proxy. The case should therefore assert arithmetic and reason wording, while recording the contextual questions necessary for review.

Counterexample variations include incoming-only activity, no activity, equal flows with a documented expected business pattern, and equal flows with incomplete history. Empty activity should produce an undefined ratio. Incomplete history should affect eligibility according to the declared policy; it should not be relabeled complete for convenience.

## Worked temporal example

Let cutoff be `2026-10-28T12:00:00Z`. Event A occurred one hour earlier and was available at `11:30Z`. Event B occurred one day earlier but was available the next day. Both amounts are 100 synthetic units.

At cutoff, the eligible total is 100. Replaying after B becomes available can produce 200 for a sufficiently broad window. The two results are both correct for their knowledge cutoffs. Replacing B’s availability with occurrence time would erase the difference and contaminate a historical evaluation.

## Worked missing-evidence example

Suppose observed groups contribute a lower bound of 22 and optional unknown evidence could add up to 12 after group caps. The interval is `[22,34]`. With illustrative band minima at 0, 30, and 60, it crosses a boundary and must produce `REVIEW_REQUIRED`. This is arithmetic uncertainty about a configured index, not statistical uncertainty about criminal behavior.

If optional unknown evidence can increase 22 only to 28, the interval remains within one band. The engine may report that bounded band while keeping `score=null`. If the missing factor is mandatory, it still abstains. Fixtures must exercise these distinct paths.

## Coverage dimensions

Build a coverage matrix across mechanisms and dimensions, rather than creating many nearly identical scenarios:

| Dimension | Variations worth covering |
| --- | --- |
| History | New relationship, full retention, truncated retention, late arrivals |
| Activity | Empty, zero-value, sparse, concentrated, diverse, one-way, balanced |
| Expectation | Known positive, zero, missing, stale meaning |
| Jurisdiction evidence | Complete mapping, partially missing, all missing, changed version |
| Profile | Observed low/high severity, missing required, missing optional, stale |
| Policy | Sum/max aggregation, saturation, increasing/decreasing ramp, threshold equality |
| Review route | True, false, unknown; all independent of index band |
| Data integrity | Duplicate, collision, foreign customer, future row, malformed numeric value |

Pairwise combinations can uncover interactions economically, but do not guarantee coverage of all higher-order failures. Reserve explicit cases for critical combinations such as missing required evidence plus a low provisional index, or an unresolved screening route plus a high-confidence observed score.

## Metamorphic relations

Useful relations include: permuting eligible input rows preserves the result; adding an unavailable event does not change eligible aggregates; changing only an opaque identifier should not change arithmetic unless it changes grouping/tie semantics; and increasing an observed severity cannot reduce a nonnegative monotone group contribution under fixed data and policy. A comparison that changes eligibility, missingness, or a denominator needs a more careful relation.

For a maximum group, increasing a non-leading factor may leave the group contribution unchanged until it exceeds the leader. For a saturated sum group, increases can have no effect. These are declared policy properties, not bugs. Explanation tests should make that behavior visible.

## Compound hypotheses and unknown evidence

[patterns.py](https://github.com/maxmoran23/customer-risk-workbench/blob/main/src/crw/patterns.py) evaluates declarative conditions using `all`, `any`, and `not`. Leaves compare a known feature with a declared threshold and can require event support and full history. Missing or ineligible evidence evaluates as `UNKNOWN`. Conditions do not execute arbitrary code and do not add score points or authorize an action.

| A | B | `all(A,B)` | `any(A,B)` |
| --- | --- | --- | --- |
| TRUE | TRUE | TRUE | TRUE |
| TRUE | FALSE | FALSE | TRUE |
| TRUE | UNKNOWN | UNKNOWN | TRUE |
| FALSE | FALSE | FALSE | FALSE |
| FALSE | UNKNOWN | FALSE | UNKNOWN |
| UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |

Negation swaps TRUE/FALSE and preserves UNKNOWN. For example, a known false cash-exposure predicate makes an `all` hypothesis false even when volume evidence is unknown. That conclusion means the specified compound condition is not established under its definition; it does not establish low customer risk. A true `any` hypothesis similarly does not make every underlying predicate known.

Each reference hypothesis carries a benign explanation, next evidence to obtain, and an interpretation limit. Review those fields alongside the evaluation tree. A pattern name is a concise search aid, not a typology finding or a case conclusion.

## Coverage reporting and interpretation

Report generated case counts and outcomes from the actual run. Include case IDs, assertion types, failures, skipped cases and reasons, and code/policy hashes. A large case count is not a claim of exhaustive typology coverage. Repeated amounts or permutations expand structural testing but do not add distinct real-world risk mechanisms.

Use [the scenario workpaper](https://github.com/maxmoran23/customer-risk-workbench/blob/main/templates/scenario-workpaper.md). A new typology should bring a falsifiable mechanism, a benign counterexample, a missing-evidence case, and a clear boundary on what the observable pattern can establish.



---

Source: `docs/typology-atlas.md`


# Typology and evidence atlas

This atlas maps review hypotheses to the evidence the software actually represents. The executable catalog tests engineering behavior. The compound-pattern library tests combinations of represented evidence. Neither is a catalogue of confirmed crime, an empirical typology detector, or a claim that all relevant customer behavior has been modeled.

The underlying design reflects a customer-specific, risk-based review approach: category labels do not establish uniform risk, and a customer's circumstances remain relevant. The public primary-source context and source dates are maintained in [the regulatory map](https://github.com/maxmoran23/customer-risk-workbench/blob/main/docs/regulatory-map.md) and [the source register](https://github.com/maxmoran23/customer-risk-workbench/blob/main/docs/sources.json), including the [FFIEC CDD overview](https://bsaaml.ffiec.gov/manual/AssessingComplianceWithBSARegulatoryRequirements/02) and [FinCEN CDD FAQs](https://www.fincen.gov/resources/statutes-and-regulations/cdd-rule-faqs). Every threshold below is an illustrative repository parameter, not a threshold prescribed by those sources.

## Four layers of meaning

| Layer | Implemented representation | What it can establish |
| --- | --- | --- |
| Observation | Time-aware profile and transaction records | A supplied fact was represented and available at a specified cutoff |
| Feature | Documented aggregation or normalized adapter value | An arithmetic property of the eligible supplied observations |
| Hypothesis | Explicit compound predicates with TRUE/FALSE/UNKNOWN states | A configured review question has, lacks, or cannot establish its required observable conditions |
| Decision support | Grouped index, bounded missing-evidence interval, review routes | A reproducible result under a declared policy; never a legal finding or probability of misconduct |

The compound hypotheses in `src/crw/patterns.py` are separate from the scoring calculation. A TRUE pattern adds no hidden points and makes no automatic disposition. A FALSE pattern is not a customer clearance. UNKNOWN identifies missing or insufficient evidence. The `all`, `any` and `not` operators preserve unknown states rather than treating an absent observation as false.

## Implemented evidence families

| Evidence family | Contract and calculation | Lawful or benign alternative | Limit and required additional context |
| --- | --- | --- | --- |
| Ownership opacity | `profile.ownership_opacity`, normalized supplied evidence | Documented multi-entity ownership with lawful purpose | The engine does not resolve beneficial owners or verify ownership documents |
| Business complexity | `profile.business_complexity` | Multinational operations, holding companies, specialized investment structures | Complexity is not secrecy; require actual operating-purpose and control evidence |
| Source-of-funds concern | `profile.source_of_funds_concern` | Supported business revenue, asset sales or wealth transfers | No document extraction, authenticity validation or source-of-wealth investigation is implemented |
| Product complexity | `profile.product_complexity` | Legitimate use of a specialized product | Product mapping and appropriate expectation require an approved adapter |
| Channel opacity | `profile.channel_opacity` | Traceable intermediated or digital delivery | Channel type and opacity are distinct; one must not be inferred mechanically from the other |
| Geography exposure | Profile exposure plus amount-weighted transaction exposure | Documented lawful international business | No live country list, physical location inference or sanctions-jurisdiction decision exists |
| Cash share | Cash amount divided by all observed amount | Retail sales, cash logistics or other cash-dependent business | No cash-reporting threshold or intent inference; this does not detect structuring |
| Digital share | Digital-channel amount divided by all observed amount | Lawful platform settlement | This is a supplied channel category, not blockchain tracing or wallet classification |
| Aggregate balance | `min(in_total,out_total)/max(in_total,out_total)` | Treasury sweeps, payroll, merchant settlement | The label `flow_through` is a historical API name; the calculation does not trace funds, order flows or prove pass-through |
| Expected-volume excess | Observed complete 30d volume / positive supplied monthly expectation | Seasonal demand, business expansion, one-off asset sale | The expectation must be independent and fit for the period in a real implementation |
| Growth | Current 30d volume / immediately preceding 30d volume | Seasonality, business acquisition, change in product use | Requires 60d history and positive prior volume; no seasonal adjustment is inferred |
| Counterparty concentration | Largest counterparty event count / event count | One payroll processor, merchant acquirer or primary supplier | Count concentration is not amount concentration; opaque IDs are not resolved entities |
| Adverse information | `profile.adverse_information`, supplied assessed evidence | Wrong identity, unreliable source, unrelated allegation | No news retrieval, identity matching or source credibility analysis is performed |
| PEP contextual exposure | `profile.pep_exposure`, limited reference weight | A public role with legitimate disclosed activity | Does not automatically impose HIGH or establish misconduct |
| Documentation gap | Known normalized profile gap plus separate mandatory missing-value gates | Administrative delay or incomplete data integration | A known gap is different from an unknown value; neither proves underlying wrongdoing |
| Snapshot age | Cutoff minus effective profile timestamp | An unchanged relationship with older retained information | Age measures staleness under this policy; it is not a regulator-prescribed refresh schedule |
| Screening unresolved | Separate TRUE/FALSE/UNKNOWN route | A false-positive match awaiting resolution | No sanctions clearance, designation determination or legal disposition is produced |

`profile.cash_intensity` and `profile.cross_border_exposure` are accepted normalized profile inputs but are not reference score factors. They do not silently add to observed cash share or geography exposure. There is no transaction-level `cross_border_share` because the ledger contract does not contain the origin and destination geography required to calculate it.

## Compound review hypotheses implemented in the pattern library

These are contextual review hypotheses. “AND” means all required conditions must be established; missing evidence may make the combined condition UNKNOWN. Transaction predicates require the configured minimum support and full window. Thresholds are illustrative and must be calibrated and approved for any actual intended use.

| Pattern ID | Implemented trigger | Plausible benign explanation | Next evidence needed |
| --- | --- | --- | --- |
| `cash_volume` | 30d cash share ≥0.6 AND expectation ratio ≥2 | Cash-dependent seasonal trade | Seasonal sales, deposit composition and independent expected activity |
| `cash_growth` | 30d cash share ≥0.6 AND growth ratio ≥3 | Holiday retail demand | Comparable seasonal history and revenue corroboration |
| `geography_volume` | 30d exposure ≥0.6 AND expectation ratio ≥2 | Documented international supply chain | Counterparty location, actual purpose and mapping provenance |
| `geography_opacity` | Profile geography ≥0.6 AND ownership opacity ≥0.6 | Complex lawful multinational structure | Verified ownership and operational explanation |
| `flow_growth` | Aggregate balance ≥0.85 AND growth ratio ≥3 | Treasury sweeps or settlement | Account purpose and actually linked transfers |
| `flow_concentration` | Aggregate balance ≥0.85 AND count concentration ≥0.5 | Merchant acquirer or payroll provider | Counterparty identity and contractual relationship |
| `digital_volume` | Digital share ≥0.7 AND expectation ratio ≥2 | Lawful digital settlement | Platform purpose and source/destination evidence |
| `digital_geography` | Digital share ≥0.7 AND exposure ≥0.6 | Authorized international service | Mapped jurisdictions and transaction purpose |
| `ownership_funds` | Ownership opacity ≥0.7 AND funds concern ≥0.5 | Incomplete onboarding documentation | Ownership chain and independently corroborated funds |
| `complexity_docs` | Business complexity ≥0.7 AND documentation gap ≥0.6 | Legitimate multi-entity enterprise | Entity purpose, footprint and legal structure |
| `pep_corroboration` | PEP context ≥0.5 AND separate adverse information ≥0.6 | Name ambiguity or unrelated allegations | Identity resolution, source reliability and chronology |
| `channel_funds` | Channel opacity ≥0.7 AND funds concern ≥0.5 | Documented intermediary service | Intermediary controls and underlying transaction purpose |
| `recent_cash` | Last4 cash share ≥0.8 AND last10 cash share ≥0.6 | Recurring cash deposit pattern | Longer history and nature of business |
| `recent_balanced` | Last4 balance ≥0.9 AND last10 balance ≥0.8 | Ordinary payment settlement | Time-ordered linkage; aggregates alone do not establish pass-through |
| `short_long_cash` | 7d cash share ≥0.7 AND 90d cash share ≥0.6 | Stable cash-intensive business | Consistency with the relationship's purpose |
| `volume_adverse` | Expectation ratio ≥3 AND adverse information ≥0.6 | Business expansion and unrelated adverse item | Relevance, reliability and event chronology |
| `stale_complex` | Profile age ≥365 days AND business complexity ≥0.7 | Unchanged business with delayed documentation | Material changes and policy-specific refresh context |
| `product_ownership` | Product complexity ≥0.7 AND ownership opacity ≥0.7 | Lawful specialized investment structure | Product-use rationale and ownership evidence |
| `concentrated_cash` | Cash share ≥0.6 AND count concentration ≥0.7 | Cash logistics service | Economic counterparty definition and operating model |
| `large_funds_gap` | Expectation ratio ≥4 AND funds concern ≥0.6 | Documented asset sale | Sale proceeds and corroborated source of wealth |

Pattern presence can direct further evidence collection. The schema does not encode “benign explanation confirmed,” so the current runtime cannot claim to suppress a case because that explanation has been verified. A later adapter can represent the adjudicated context with explicit provenance and governance. It should not turn narrative plausibility into an automatic negative label.

## Observation-window choices

| Window | Question it answers | Distortion to test |
| --- | --- | --- |
| 1d / 7d | What happened recently in elapsed time? | Sparse activity, holidays and timing cliffs |
| 30d | How does recent activity compare with a monthly expectation? | Partial retention and seasonality |
| 90d / 180d / 365d | Does a longer observed period change the picture? | Old activity obscuring a recent change |
| Lifetime | What is retained for the declared relationship history? | Calling truncated history “lifetime complete” |
| Last4 / last10 / last25 / last50 | What characterizes the most recent observations? | Four events can span minutes or years |

Time windows exclude the exact lower bound and include the cutoff: `(cutoff-duration, cutoff]`. Last-N windows order by occurrence time and then transaction ID. The tie rule is deterministic, not a claim to know sub-timestamp event ordering. A future event and an old event arriving after cutoff are both excluded for different reasons. These differences are preserved in quality diagnostics.

Multiple windows can contain the same records. The reference behavior group uses a maximum across its configured contributions, so overlapping views of one event population do not automatically multiply its points. This trades accumulation sensitivity for a transparent overlap constraint. It does not establish an empirically optimal dependence model; alternatives need explicit comparative testing.

## Decision paths to inspect in a review

| If the evidence shows… | Then the current runtime… | Reviewer should examine… |
| --- | --- | --- |
| Invalid timestamp, identity collision or unsupported numeric domain | Rejects the fixture or record | Adapter repair and whether the batch failure was handled atomically |
| Mandatory profile evidence absent | Returns required-evidence review gate and no final score | Why evidence is absent and whether follow-up is required |
| Optional factor missing but its possible contribution stays within one band | May retain a bounded band with `score=null` | Lower/upper bounds and the unknown factor's importance |
| Optional missing contribution could reach another band | Returns REVIEW_REQUIRED | Evidence needed to narrow the interval |
| History completeness not confirmed | Returns a completeness review gate under reference policy | Upstream completeness evidence, not merely the count of received rows |
| Full calendar window but insufficient events | Marks the factor unsupported | Whether the ratio is meaningful for the intended use |
| High cash or balanced-flow proxy | Emits configured feature/reason and possibly a pattern | Operating purpose and plausible lawful alternatives |
| Unresolved screening | Activates the separate review route | Approved screening workflow; the index supplies no disposition |
| Known low concern and complete supplied evidence | Computes the configured index | Quality and relevance of the supplied evidence; low is not clearance |

The uncertainty interval is an arithmetic envelope from missing configured inputs. It is not a statistical confidence interval, a posterior probability or a guarantee about unmodeled risk. A narrow envelope can coexist with poor upstream data, weak parameter choices or an omitted risk mechanism.

## Capabilities requiring additional contracts and independent implementation

| Proposed capability | Missing evidence or computation | Required work before claiming support |
| --- | --- | --- |
| Linked rapid movement / pass-through | Time-ordered fund linkage and account balance context | Specify linkage assumptions, ambiguous matching, partial funding and external-account coverage; validate against known paths |
| Circular flow / network layering | Multi-entity graph, edge provenance and resolution quality | Build entity resolution and graph-time contracts; test lawful treasury and payment-network structures |
| Transaction structuring | Applicable reporting framework, aggregation units, location and customer context | Define legally appropriate hypotheses and benign counterexamples; avoid an intent claim from threshold proximity alone |
| Trade-based laundering | Invoices, goods, quantities, prices, shipment and counterparties | Create invoice/shipment matching and valuation baselines with coverage and source-quality controls |
| Crypto tracing | Addresses, chains, assets, token units, protocol events and attribution provenance | Build chain-specific adapters and entity-resolution confidence; distinguish direct observation from vendor attribution |
| Ownership/control screening | Ownership graph, percentages, control rights, effective dates and validated list data | Implement relevant ownership/control semantics in a separate governed screening component |
| Name screening | Names, aliases, transliteration, identifiers and matching thresholds | Establish matching quality, tuning, adjudication workflow and false-positive/negative evaluation |
| Geographic route anomalies | Origin/destination/intermediary locations with versioned mapping | Resolve geographic field meaning, risk-source timing and incomplete routing paths |
| Peer-relative anomalies | Defensible peer cohorts, seasonality, drift and appropriate sample sizes | Fit baselines only on development data; evaluate subgroup support and out-of-time stability |
| Document-grounded profile evidence | Approved document access, extraction and source references | Validate extraction, conflicting facts, stale evidence and reviewer override before assigning normalized concerns |
| Narrative generation | Evidence-bounded generation and approved deployment | Require claim-to-evidence tracing, unsupported-claim tests and human control of consequential actions |
| Customer disposition or filing workflow | Approved legal/operational authorities and case decisions | Remain in a separately authorized process with its own controls; never infer authority from a score |

These entries describe design boundaries and next implementation requirements. They are not placeholder features advertised as already delivered.

## Evidence standard for adding a hypothesis

An added hypothesis should have a named mechanism, the exact observable inputs, an expected numerical behavior or logical relation, a lawful lookalike, a missing-data behavior, a temporal cutoff rule and a clear limit on the conclusion. A new predicate assembled from an existing metric may be a useful scenario without constituting a new typology.

Use [the executable catalog](https://github.com/maxmoran23/customer-risk-workbench/blob/main/scenarios/catalog.json), [scenario design](https://github.com/maxmoran23/customer-risk-workbench/blob/main/docs/scenario-design.md) and [the scenario workpaper](https://github.com/maxmoran23/customer-risk-workbench/blob/main/templates/scenario-workpaper.md). Evaluate actual intended-use effectiveness separately using appropriately sampled and reviewed outcomes, temporal/entity separation, subgroup diagnostics, and uncertainty measures described in [model validation](https://github.com/maxmoran23/customer-risk-workbench/blob/main/docs/model-validation.md). Synthetic fixtures remain valuable for proving a fix did not break a declared calculation; they cannot supply the missing real-world ground truth.



---

Source: `templates/scenario-workpaper.md`


# Scenario workpaper

**Status: synthetic worked scenario specification; execution status must come from a run.**

| Field | Worked case |
| --- | --- |
| ID | `DEMO-SCENARIO-BALANCED-01` |
| Objective | Verify the balance proxy and its interpretation limit |
| Inputs | Complete window; incoming amounts `70,50`; outgoing amounts `90,30` |
| Expected aggregate | Incoming `120`, outgoing `120`, total `240`, balance proxy `1` |
| Hypothesis | Balanced movement can be a review signal in context |
| Lawful counterexample | Expected settlement activity can produce the same aggregate |
| Missing evidence | Transaction linkage, timing causality, economic purpose, source of funds |
| Prohibited inference | Funds were traced or unlawful activity established |

## Companion cases

| Variation | Expected behavior to assert |
| --- | --- |
| Remove all outgoing events | Balance proxy `0` when incoming remains positive |
| Replace all amounts with zero | Balance proxy null because denominator is zero |
| Make one event available after cutoff | Exclude it from eligible aggregates |
| Mark history incomplete | Preserve values but apply policy eligibility/gate rules |
| Permute input order | Same eligible set, arithmetic, and deterministic result |
| Set unresolved screening evidence | Separate route behavior; no legal conclusion |

## Assertion design

Record whether each assertion is arithmetic, relational, contract rejection, temporal exclusion, workflow separation, or explanation wording. Independent expected values should come from simple calculations or a separately reviewed specification. A snapshot generated by the engine is useful for regression detection but not independent proof.

## Execution record

Required fields: fixture version/hash, code revision, policy digest, cutoff, command, actual output, assertion results, failures/skips, and reviewer comments. **Current execution: not recorded in this template.** Link the real result rather than manually typing a pass.

## Coverage decision

State which mechanism the case adds beyond existing coverage. More amount permutations may strengthen arithmetic testing but should not be counted as new real-world typologies. Record related cases and any important combination still absent.
