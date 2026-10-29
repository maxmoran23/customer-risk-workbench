# Customer Risk Workbench / 01 start here

Public reference material. Synthetic examples and illustrative policies. No institutional approval or production-performance claim.

Source repository: https://github.com/maxmoran23/customer-risk-workbench

Attachment groups preserve full methods; source code and runnable tests remain in the repository.


---

Source: `README.md`


# Customer Risk Workbench

**An executable, public reference suite for customer risk assessment, model research, and technical challenge.** Release 0.2.0 adds two program kits: a categorical rating-model rebuild (attribute review, connections, rules) and change-impact assessment (migration matrices, reconciliation, parity, AI-drafting guard). Start with normalized customer and transaction records; reconstruct retained evidence available at an assessment cutoff; inspect a configurable risk index; test scenarios, alternative models, uncertainty, and operational behavior.

This is original open-source research software by Max Moran, developed with AI assistance. All bundled customers, transactions, labels, and operating policies are synthetic or illustrative. It has not undergone institutional independent validation and does not claim real-world detection effectiveness, regulatory approval, or production readiness.

## Start here

| Reader | First stop | What to inspect next |
| --- | --- | --- |
| Review the working product | Download the repository and open [`web/workbench.html`](https://github.com/maxmoran23/customer-risk-workbench/blob/main/web/workbench.html) in a browser | Customer review, executable cases, model research, sensitivity lab |
| Understand the method | [Scoring method](https://github.com/maxmoran23/customer-risk-workbench/blob/main/docs/scoring-method.md) and [reviewer guide](https://github.com/maxmoran23/customer-risk-workbench/blob/main/docs/reviewer-guide.md) | [Data contract](https://github.com/maxmoran23/customer-risk-workbench/blob/main/docs/data-contract.md), [development protocol](https://github.com/maxmoran23/customer-risk-workbench/blob/main/docs/model-development.md) |
| Run a small transparent example | [Three-customer walkthrough](https://github.com/maxmoran23/customer-risk-workbench/blob/main/docs/example-walkthrough.md) | Hand-reconciled contributions, required-evidence removal, replay and monitoring |
| Challenge the mathematics | [Statistical methods and APIs](https://github.com/maxmoran23/customer-risk-workbench/blob/main/docs/statistical-methods.md) | [Tests](https://github.com/maxmoran23/customer-risk-workbench/tree/main/tests), [research evidence](https://github.com/maxmoran23/customer-risk-workbench/blob/main/evidence/research.json), [verification](https://github.com/maxmoran23/customer-risk-workbench/blob/main/docs/verification.md) |
| Evaluate adaptation | [Adoption guide](https://github.com/maxmoran23/customer-risk-workbench/blob/main/docs/adoption-guide.md) | [Worked templates](https://github.com/maxmoran23/customer-risk-workbench/tree/main/templates), [AI-assisted adaptation](https://github.com/maxmoran23/customer-risk-workbench/blob/main/docs/ai-assistance.md) |
| Rebuild a categorical rating model | [Attribute-review playbook](https://github.com/maxmoran23/customer-risk-workbench/blob/main/docs/attribute-review-playbook.md) | [Program sequencing](https://github.com/maxmoran23/customer-risk-workbench/blob/main/docs/program-sequencing.md), [connections method](https://github.com/maxmoran23/customer-risk-workbench/blob/main/docs/connections-method.md), [rule design](https://github.com/maxmoran23/customer-risk-workbench/blob/main/docs/rule-design.md) |
| Automate change-impact assessments | [Impact-assessment playbook](https://github.com/maxmoran23/customer-risk-workbench/blob/main/docs/impact-assessment-playbook.md) | [Automation architecture](https://github.com/maxmoran23/customer-risk-workbench/blob/main/docs/impact-automation-architecture.md), [AI workflows](https://github.com/maxmoran23/customer-risk-workbench/blob/main/docs/ai-workflows.md), [prompts](https://github.com/maxmoran23/customer-risk-workbench/tree/main/prompts) |
| Transfer a compact reading pack | [Ten attachment groups](https://github.com/maxmoran23/customer-risk-workbench/tree/main/review-pack) | Full source remains organized by responsibility below |

The HTML runs offline: no login, installation, external fonts, telemetry, AI API, or hosted service is required. It contains selected synthetic examples and retained research evidence. GitHub displays HTML source; download/open the file to use the interface.

## What is implemented

| Capability | Working implementation | Evidence / boundary |
| --- | --- | --- |
| Canonical input and lineage | Strict JSONL/CSV adapters, UTC event/availability times, normalized units, content hashes | Invalid, missing, duplicate, late, and conflicting records tested |
| Temporal features | 160 reference features across 11 windows: 1/7/30/90/180/365 days, observed lifetime, last 4/10/25/50 events | [Generated feature catalog](https://github.com/maxmoran23/customer-risk-workbench/blob/main/configs/features.json); retained history and denominators explicit |
| Explainable policy index | 23 illustrative factors across six sum/max groups; configurable normalization, weights, caps and bands | Missing evidence produces bounds and can force review; index is not a probability |
| Compound hypotheses | 20 declarative patterns with TRUE/FALSE/UNKNOWN logic | Benign alternatives and next evidence included; matches add no hidden points |
| Executable case library | 96 named cases with expected and observed behavior | [Case catalog](https://github.com/maxmoran23/customer-risk-workbench/blob/main/scenarios/catalog.json); arithmetic, temporal edges, missingness, counterexamples and invariants |
| Supervised challengers | Prevalence baseline, standardized logistic regression, monotonic histogram gradient boosting | Training-only preprocessing, matured labels, temporal and customer separation |
| Robustness experiments | Three seeds across four refitted regimes; separate fixed-model perturbations | Frozen parameters and thresholds, paired records, probability/label/workload changes |
| Statistical validation | Tied AUC/AP, Brier/log loss, calibration, intervals, sampling, paired bootstrap, segment support | Undefined metrics explicit; synthetic labels generated independently of policy scores |
| Monitoring and attribution | PSI/KS/effect diagnostics, matched-ID migrations, entrants/exits, score availability, crossed data/policy decomposition | No universal drift cutoff; arithmetic attribution is not causality |
| Operational reference | Real SQLite, atomic ingest, immutable content IDs, snapshot reads, complete-run export, append-only review records | Local single-writer implementation; authentication and production operations remain adopter work |
| Review interface | Eight offline views with explanations, search, comparisons and evidence export | Selected examples labeled; complete portfolio statistics separate |
| Governance and adoption | Current-source regulatory map, worked model/validation/adapter/decision templates, compact review packs | No fabricated sign-off or employer-specific content |

## Program kits (0.2.0)

Two independent kits for work that institutions running a categorical customer risk rating model repeat on every rebuild and every release. Both use the same contracts, synthetic data and evidence conventions as the core.

**Categorical rating rebuild (attribute review).** Stages run in dependency order and later stages report as blocked until earlier ones meet their exit criteria: population scoping, entity segmentation, value classification, connections review, rule design, weighting and calibration, output validation.

| Capability | Implementation | Boundary |
| --- | --- | --- |
| Value catalog | Five classes (override_high, elevator, neutral, mitigator, override_low) with score rules relative to a configurable neutral point; current and proposed assignments; evidence register; review statuses with decision records | Classes are illustrative; policy owners decide them |
| Normalization audit | Unmapped, unknown, conflicting, duplicate and orphan values; lexical fragmentation candidates; party-weighted coverage | Lexical similarity is a review prompt, not equivalence |
| Review workbook | Per-attribute sheet (instructions, profile, evidence, value inventory) plus CSV inventories; validated round-trip import with read-only current assignments | Spreadsheet edits never change in-force classes |
| Connections screen | Bias-corrected Cramer's V; interaction odds ratio per value pair with Benjamini-Hochberg control; proxy flag; leg-contribution test for proposed combinations | Descriptive and label-dependent; recovers a planted synthetic synergy |
| Rules | Atomic and compound three-valued rules with floor or route effects; simulation of firing, unknowns, overlap, redundancy, shadowing and marginal tier changes | Population-specific; not effectiveness |
| Scoping and gates | Role-to-scope resolution with precedence; seven-stage gate report | Planning control, not approval |

**Change-impact assessment.** For each change promoted to a test environment: join before/after tier snapshots, report per-segment migration in a fixed familiar layout, and put new analysis in annexes.

| Capability | Implementation | Boundary |
| --- | --- | --- |
| Migration engine | Hash-partitioned streaming join with bounded memory; pinned-party exclusion and integrity check; entrants, exits, segment changes; aggregate-only segments with a minimum-movers bound | Single node; snapshots must be immutable during a run |
| In-database SQL | Generated set-based SQL with a scope-table join in place of repeated list imports; identifier validation; cell-for-cell parity with the Python engine on SQLite | Adapter and indexing are adopter work |
| Expectations | Change manifest derived from a pre-deployment preview; post-run reconciliation surfaces every unexplained movement | Validates consistency with the manifest, not the manifest |
| History and parity | Modified z-score against prior assessments; cell-level parity with an existing process (exact, within tolerance, mismatch); hash-chained register | Parity with a flawed standard is still parity |
| AI drafting guard | Facts pack and vendor-neutral prompt; rejects any drafted narrative containing numbers not in the facts | Numeric grounding only; human review remains |

```bash
python -m crw program-demo --out runs/program-demo
python -m crw attributes workbook --normalization runs/program-demo/attribute-review/normalization-table.csv --out runs/workbook
python -m crw attributes import --inventory runs/workbook --out runs/catalog-reviewed.json
cd examples/programs && python -m crw impact assess --pre snapshot-pre.csv --post snapshot-post.csv --config assessment-config.json --manifest change-manifest.json --standard standard-matrix.csv --out ../../runs/example-impact
```

The ten-party example in [`examples/programs`](https://github.com/maxmoran23/customer-risk-workbench/tree/main/examples/programs) is hand-checkable: two parties move up, one down, one pinned party is excluded, one exits and one enters. Reference configurations are generated into [`configs/programs`](https://github.com/maxmoran23/customer-risk-workbench/tree/main/configs/programs). A rendered synthetic report is in [`web/impact-assessment-example.html`](https://github.com/maxmoran23/customer-risk-workbench/blob/main/web/impact-assessment-example.html).

The current verification record, exact test counts, measured timings, source hashes and limitations are in [the evidence dossier](https://github.com/maxmoran23/customer-risk-workbench/blob/main/docs/verification.md). The case count is not a count of independently validated financial-crime typologies.

## Run it

Python 3.11 or later supports the core. Python 3.12 is the pinned reference research environment. From a downloaded or cloned checkout:

```bash
python -m pip install '.[dev,research]'
python -m pytest
python -m crw demo --customers 1000 --transactions 80 --research --out runs/my-demo
```

Open `runs/my-demo/workbench.html`. The command generates 1,000 synthetic customers and 80,000 transactions, ingests a real SQLite database, scores twice with different chunk sizes, executes the case library, runs research experiments, and writes the standalone interface. Use a fresh output directory when changing seed or population parameters; existing event identifiers reject conflicting content.

For a dependency-locked environment with [uv](https://docs.astral.sh/uv/):

```bash
uv sync --frozen --all-extras --python 3.12
uv run python -m pytest
uv run crw demo --research --out runs/locked-demo
```

For a core-only install, use `python -m pip install .` and omit `--research`. Core scoring, SQLite, scenarios, monitoring and HTML rendering require no third-party runtime libraries. Research uses the optional numerical dependencies. Shell-specific virtual-environment activation is not required when using these commands through the chosen Python environment; follow local software installation policy.

## Inspect a pipeline step

```bash
python -m crw generate --customers 1000 --transactions 80 --out runs/input
python -m crw ingest --db runs/portfolio.sqlite --customers runs/input/customers.jsonl --transactions runs/input/transactions.jsonl
python -m crw score --db runs/portfolio.sqlite --as-of 2026-10-01T00:00:00Z --out runs/assessments.jsonl
python -m crw scenarios --out runs/scenarios.json
python -m crw research --rows 3000 --seeds 7 19 41 --out runs/research.json
python -m crw benchmark --customers 100000 --transactions 10 --out runs/benchmark.json
```

See [operations](https://github.com/maxmoran23/customer-risk-workbench/blob/main/docs/operations.md) for repeatable execution, monitoring and sampling APIs, failure behavior, packaging, and platform limits.

## How to challenge it

Start by removing required evidence from a customer and verify that the final score becomes null. Add a transaction unavailable at the historical cutoff and verify that the calculation does not change. Increase overlapping-window evidence and inspect the max-group cap. Change both data and policy and use the four crossed calculations to attribute the movement. In research, compare the same frozen model before and after feature masking; preserve its failures in the report.

Regression is a useful transparent benchmark. Complexity is justified only when independent evaluation supports a worthwhile improvement. A unique score for every customer is not a goal: different customers may share an index while retaining different evidence and explanations.

## Repository map

```text
src/crw/       Typed contracts, features, policy, patterns, storage, research and diagnostics;
               attributes, connections, rules, program, impact, impact_sql, impact_report, narrative
configs/       Versioned illustrative policy, schemas, feature and pattern catalogs; programs/ reference configs
examples/      Three-customer fixtures, executable walkthrough, and hand-checkable program fixtures
scenarios/     Named executable-case catalog and extension guide
tests/         Independent arithmetic, boundary, statistical and real-database tests
docs/          Technical methods, source registry, governance and reviewer routes
templates/     Worked adoption, review, attribute-review and impact-assessment workpapers
prompts/       Vendor-neutral AI prompt pack with output contracts and required human checks
evidence/      Generated results, benchmarks, verification and source-hash manifest
web/           Standalone offline workbench
review-pack/   Ten complete Markdown attachment groups and source manifest
scripts/       Reproduction, packaging and public-boundary checks
```

## Current guidance and use boundary

The public regulatory map uses the April 2026 interagency model-risk guidance; it identifies SR 11-7 and SR 21-8 as superseded and distinguishes component classification from governance responsibilities. No regulator prescribes this suite's weights, feature count, score bands or example review thresholds. [Current source map](https://github.com/maxmoran23/customer-risk-workbench/blob/main/docs/regulatory-map.md), [Federal Reserve SR 26-2](https://www.federalreserve.gov/supervisionreg/srletters/sr2602.htm).

Institution-specific data mapping, risk appetite, outcome definitions, calibration, validation, authorization, and deployment belong in the adopter's approved environment. Public resources should not be interpreted as authorization to import software or data into an institution. The suite does not perform sanctions clearance, determine SAR filing, establish misconduct, or autonomously approve/close relationships.

[MIT license](https://github.com/maxmoran23/customer-risk-workbench/blob/main/LICENSE) · [Security](https://github.com/maxmoran23/customer-risk-workbench/blob/main/SECURITY.md) · [Provenance](https://github.com/maxmoran23/customer-risk-workbench/blob/main/docs/provenance.md) · [Contributing](https://github.com/maxmoran23/customer-risk-workbench/blob/main/CONTRIBUTING.md)



---

Source: `docs/reviewer-guide.md`


# Reviewer guide

The core proposition is inspectability: a reviewer can trace normalized evidence through time-aware features, declared policy, arithmetic bounds, and a separate review workflow. The package also provides research and testing utilities. Its acceptance case rests on executable evidence and explicit limits, not on the number of files.

## A practical review route

| Step | Inspect | Expected understanding |
| --- | --- | --- |
| 1. Purpose | [README](https://github.com/maxmoran23/customer-risk-workbench/blob/main/README.md), [limitations](https://github.com/maxmoran23/customer-risk-workbench/blob/main/docs/limitations.md) | What this package can support and what it cannot authorize |
| 2. One assessment | Generated assessment/reason output from the documented demo | How supplied evidence becomes group contributions, bounds, gates, and routes |
| 3. Inputs and time | [Data contract](https://github.com/maxmoran23/customer-risk-workbench/blob/main/docs/data-contract.md), [architecture](https://github.com/maxmoran23/customer-risk-workbench/blob/main/docs/architecture.md) | Which information was eligible at the cutoff and why |
| 4. Policy mathematics | [Development method](https://github.com/maxmoran23/customer-risk-workbench/blob/main/docs/model-development.md), active policy file | How ramps, caps, sum/max groups, and missing evidence behave |
| 5. Challenge | [Validation](https://github.com/maxmoran23/customer-risk-workbench/blob/main/docs/model-validation.md), [scenario design](https://github.com/maxmoran23/customer-risk-workbench/blob/main/docs/scenario-design.md), actual test report | What was checked and what remains untested |
| 6. Evidence strength | Research/benchmark outputs and their manifests | Which claims are synthetic, measured, inferred, or unavailable |
| 7. Governance | [Regulatory map](https://github.com/maxmoran23/customer-risk-workbench/blob/main/docs/regulatory-map.md), [governance](https://github.com/maxmoran23/customer-risk-workbench/blob/main/docs/governance.md), [adoption](https://github.com/maxmoran23/customer-risk-workbench/blob/main/docs/adoption-guide.md) | What an authorized evaluation would require |

Generated artifact locations and runnable commands are listed by the current README/CLI. Do not treat a static worked example in `templates/` as an executed run.

## Questions worth asking in a technical demonstration

1. **Why did this customer get this result?** Open the reasons, raw feature values, severities, weights, group aggregation, and caps. Show missing factors and the exact policy hash.
2. **What information did the process know at the time?** Show event time, availability time, profile effective/availability timestamps, cutoff, and retained-history coverage.
3. **What happens if information is missing?** Demonstrate a required missing factor, an optional missing factor with a bounded band, and an interval spanning bands.
4. **Are multiple windows double-counted?** Show the reference policy’s maximum aggregation and the factors sharing a group. Explain its trade-off against summation.
5. **Can a low score clear a screening issue?** Show the independent route state and its limited interpretation.
6. **Can the result be reproduced?** Rerun the same data, policy, and cutoff; compare hashes and explain any differences.
7. **Where can the system be wrong?** Start with the counterexamples and limitations, then the open findings and unsupported uses.
8. **Does the research result generalize?** Show target definition, generator or source, splits, support, label maturity, uncertainty, and the exact population to which the claim applies.

## Reading an assessment

| Field | Meaning | Frequent misreading |
| --- | --- | --- |
| `score` | Fully observed index when no gate is active; otherwise null | Probability or automatic disposition |
| `provisional_index` | Arithmetic lower bound from known contributions | Best guess or imputed central value |
| `lower_bound`, `upper_bound` | Missing-evidence policy envelope | Statistical confidence interval |
| `band` | Configured category or `REVIEW_REQUIRED` | A regulator-prescribed category |
| `coverage` | Fraction of configured factors usable | Verified source accuracy or independent evidence count |
| `gates` | Reasons a final category requires review | Optional presentation warnings |
| `review_flags` | Separate configured true/false/unknown route states | Confirmed legal or screening disposition |
| `lineage`, hashes | Reproduction and comparison references | Proof that the source was truthful or storage immutable |

An incomplete assessment can retain one bounded band while `score` remains null. This avoids pretending the exact index is known. A required missing factor still blocks the band even if the arithmetic range is narrow.

## Reviewing the evidence pack

An adequate pack identifies the source revision, environment, policy/config digest, input manifest, cutoff, seed where relevant, invocation, output hashes, and actual results. It distinguishes passed, failed, skipped, and not performed. Research outputs should include denominators and undefined-value reasons. Benchmarks should describe measured workload and hardware.

Trace a small number of cases end to end before reading aggregate results. Include an ordinary case, a high-contribution case, an abstention, a late-arrival case, and a benign counterexample. Verify at least one calculation independently of the engine.

## What adoption does and does not inherit

An adopter can reuse source code, interfaces, test patterns, documentation structure, and synthetic exercises subject to the license. It does not inherit an approved policy, reliable private inputs, population validation, customer-action authority, or institutional approval. Those are evidence and governance tasks in the adopting environment.

Use [the adoption decision](https://github.com/maxmoran23/customer-risk-workbench/blob/main/templates/adoption-decision.md) to record the next defensible step. The template permits further research, restricted evaluation, rejection, and later approval by an authorized reviewer; it does not preselect success.



---

Source: `docs/limitations.md`


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

The source review is targeted, dated, and public-only. It is not a complete survey of every institution type, jurisdiction, rule, sanctions program, or subsequent administrative action. Supervisory guidance, international standards, FAQs, and proposed rules have different authority. Read [the source register](https://github.com/maxmoran23/customer-risk-workbench/blob/main/docs/sources.json) and [regulatory map](https://github.com/maxmoran23/customer-risk-workbench/blob/main/docs/regulatory-map.md) for status and retrieval caveats.

## Conditions that should stop or constrain evaluation

* Historical knowledge time cannot be established for a claimed historical backtest.
* Input units or customer identities cannot be reconciled.
* Required evidence is being silently replaced with zero or a guessed value.
* Outcome labels are generated from the policy being evaluated, or only selected positives were reviewed without an appropriate design.
* A reported metric has no denominator, target definition, partition provenance, or reproducible artifact.
* An output is being used to clear sanctions or authorize an adverse customer action beyond its stated purpose.

Record the failure and choose a narrower valid claim or repair the underlying issue. Changing the wording of the report cannot substitute for missing evidence.
