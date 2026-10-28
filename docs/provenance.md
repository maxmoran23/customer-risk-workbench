# Provenance and public-only implementation

This project is an independently implemented generic reference workbench. It contains invented customer identifiers, invented counterparties, normalized synthetic exposure values and synthetic transaction amounts. It contains no employer-specific model, workflow, dataset, screening list, customer identifier, approval or validation conclusion.

## Prior public resources inspected

The public repository inventory supplied the following exact source revisions. These repositories informed the scope of analyst workflows and documentation, rather than providing a production model or a real customer dataset.

| Public repository | Inspected revision | License at inspected revision | Relationship to this project |
| --- | --- | --- | --- |
| [analyst-toolkit](https://github.com/maxmoran23/analyst-toolkit/tree/f7e569a8f16dfe6bdd179867b7f7473ef8e96846) | `f7e569a8f16dfe6bdd179867b7f7473ef8e96846` | MIT | Prior generic customer-risk-rating scorer and analyst workflow concepts |
| [simple-toolkit](https://github.com/maxmoran23/simple-toolkit/tree/a3f8f0bb1ac7a5b22b1f112df3695891b2fddba4) | `a3f8f0bb1ac7a5b22b1f112df3695891b2fddba4` | MIT | Reference workflow organization and accessible analyst-facing interfaces |
| [markdown-analyst-toolkit](https://github.com/maxmoran23/markdown-analyst-toolkit/tree/40c62d3612a8764f990144fab6059a93bc728459) | `40c62d3612a8764f990144fab6059a93bc728459` | MIT | Customer-risk review, monitoring validation, scenario design and sampling-assurance documentation concepts |

The inspected prior eight-factor customer-risk scorer is located at [`frameworks/customer-risk-rating/scorer.py`](https://github.com/maxmoran23/analyst-toolkit/blob/f7e569a8f16dfe6bdd179867b7f7473ef8e96846/frameworks/customer-risk-rating/scorer.py) in `analyst-toolkit`. Relevant Markdown workflow material includes [`suites/customer-risk-review/03-analysis-method.md`](https://github.com/maxmoran23/markdown-analyst-toolkit/blob/40c62d3612a8764f990144fab6059a93bc728459/suites/customer-risk-review/03-analysis-method.md) and the monitoring-validation, scenario-design and sampling-assurance suites. Those historical materials are reference context, not evidence of validation or approval of this workbench.

No substantial source-code blocks were copied into the new engine, generators or scenario runner. The feature schema, timestamp rules, grouped scoring implementation, executable fixtures and synthetic generation were newly authored for this repository. This provenance statement describes the implementation performed here; it is not a legal opinion on licensing, employment intellectual property or institutional acceptance.

## Data and parameter origins

| Material | Origin | Permitted inference |
| --- | --- | --- |
| Customer and counterparty identifiers | Deterministically invented by `src/crw/synthetic.py` | Stable joins and repeatability on synthetic records |
| Transactions and timing | Seeded distributions over invented base-unit amounts and UTC timestamps | Engineering behavior and performance on declared input sizes |
| Profile concerns | Seeded normalized fixture values in the declared schema | Controlled tests of evidence propagation |
| Jurisdiction exposure | Invented scalar per transaction; no country identities | Arithmetic of a supplied exposure mapping |
| Reference weights, caps, bands and thresholds | Explicit illustrative policy choices | Reviewable model mechanics; no regulatory or empirical calibration claim |
| Scenario expected values | Analytically specified fixtures in `src/crw/scenarios.py` | Conformance to those expected behaviors |
| Synthetic research outcomes | Separate research generator where provided | Mechanics of training/evaluation only; no real detection-efficacy claim |
| Regulatory sources | Public primary-source references documented separately | Guidance context within each source's jurisdiction, date and scope |

A seed records a reproducible random experiment; it does not establish representative sampling. Increasing the number of synthetic customers reduces neither simulator specification bias nor the absence of real outcome evidence. An independent validator must assess intended use, actual data quality, policy calibration, benchmark comparators and out-of-time performance in an approved environment.

## Information flow for later institutional adaptation

The public project is the generic input to a separately authorized institutional implementation. Organization-specific schemas, customer records, risk appetite, thresholds, outcome labels, screening determinations and review decisions belong only inside the approved environment. Public fixtures can be replaced there through explicit adapters; no return flow of institutional data is necessary for this repository to run.

When documenting an adaptation, record its own code revision, source-data lineage, approved parameter version, reviewer, intended use and validation status. A local modification does not inherit evidence for behaviors changed by the modification. Retain generic synthetic regression fixtures alongside approved institution-specific evaluation so that arithmetic regressions and empirical limitations remain distinguishable.
