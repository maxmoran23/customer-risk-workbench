# Typology and evidence atlas

This atlas maps review hypotheses to the evidence the software actually represents. The executable catalog tests engineering behavior. The compound-pattern library tests combinations of represented evidence. Neither is a catalogue of confirmed crime, an empirical typology detector, or a claim that all relevant customer behavior has been modeled.

The underlying design reflects a customer-specific, risk-based review approach: category labels do not establish uniform risk, and a customer's circumstances remain relevant. The public primary-source context and source dates are maintained in [the regulatory map](regulatory-map.md) and [the source register](sources.json), including the [FFIEC CDD overview](https://bsaaml.ffiec.gov/manual/AssessingComplianceWithBSARegulatoryRequirements/02) and [FinCEN CDD FAQs](https://www.fincen.gov/resources/statutes-and-regulations/cdd-rule-faqs). Every threshold below is an illustrative repository parameter, not a threshold prescribed by those sources.

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

Use [the executable catalog](../scenarios/catalog.json), [scenario design](scenario-design.md) and [the scenario workpaper](../templates/scenario-workpaper.md). Evaluate actual intended-use effectiveness separately using appropriately sampled and reviewed outcomes, temporal/entity separation, subgroup diagnostics, and uncertainty measures described in [model validation](model-validation.md). Synthetic fixtures remain valuable for proving a fix did not break a declared calculation; they cannot supply the missing real-world ground truth.
