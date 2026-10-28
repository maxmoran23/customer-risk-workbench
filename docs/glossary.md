# Glossary and interpretation rules

| Term | Meaning in this repository | Distinction to preserve |
| --- | --- | --- |
| Assessment | Calculation for one customer at one cutoff using one policy | Not the later human decision |
| Available time | Earliest time a record could be used by the process | Not necessarily event time or database update time |
| Band | Configured index category | Not a probability bucket unless separately established |
| Baseline | Declared comparator such as current policy or simple classifier | Not automatically ground truth |
| Calibration | Relationship between predicted probability and observed target frequency | Not merely choosing score cutoffs |
| Challenger | Alternative method evaluated against a comparator | Not automatically a replacement |
| Complete history | Adapter assertion of supplied retained-history completeness | Not independently proven source delivery |
| Concentration | Largest counterparty event count divided by event count | Not amount concentration |
| Coverage | Usable configured factors divided by configured factors | Not confidence or source truth |
| Cutoff | Knowledge-time boundary for an assessment | A later replay uses a distinct information set |
| Effective time | Time a profile snapshot becomes applicable | Separate from when it becomes available |
| Feature | Defined numeric summary of eligible evidence | Needs units, support, and provenance |
| Flow-through | Aggregate incoming/outgoing balance proxy | Not traced flow of funds |
| Gate | Explicit condition requiring review or abstention | Not a cosmetic warning |
| Group cap | Maximum contribution of a configured factor family | Does not prove factors are independent |
| High-risk share | Amount-weighted supplied jurisdiction severity | Not fraction of sanctioned transactions |
| Holdout | Data withheld from development decisions | Repeated tuning makes it development data |
| Index | Constructed ordinal/quantitative review-priority measure | Not likelihood of criminality |
| Label | Recorded outcome for a defined unit and horizon | A filing or escalation is not proven wrongdoing |
| Leakage | Information used that would not be available under the claimed evaluation | Includes fitting transforms on holdout data |
| Lineage | References describing input, transform, policy, and run origin | A digest is not source authentication |
| Materiality | Significance of a component’s use and consequences | Not solely implementation complexity |
| Missing-evidence bounds | Minimum/maximum policy outputs under unknown severities | Not confidence intervals |
| Monotonicity | Nondecreasing/nonincreasing response under a specified input change | Denominator or eligibility changes can invalidate a simple claim |
| Outcome maturity | Sufficient time for the defined outcome to become observable | Recent unlabeled cases are not automatically negatives |
| Override/exception | Recorded human decision subject to authority and scope | Does not overwrite original calculation |
| Point-in-time | Reconstructed using information effective and available by cutoff | Today’s corrected record is not always historical knowledge |
| Population drift | Change in input/output distribution | Not automatically deterioration or a significant test result |
| Precision | Positive outcomes among selected positive predictions | Depends on prevalence and selection |
| Provisional index | Lower arithmetic bound from observed contributions | Not a posterior mean |
| Recall | Selected positive predictions among positive outcomes | Support is positive outcomes, not all transactions |
| Review route | Separate true/false/unknown workflow condition | Not screening clearance, SAR decision, or legal advice |
| Scenario | Synthetic, falsifiable input/expected-behavior case | Not proof of population effectiveness |
| Severity | Configured normalized feature transformation | Equal numbers need not imply equal empirical risk |
| Shadow evaluation | Evaluation without output action authority | Not a production approval |
| Synthetic target | Generated outcome under stated assumptions | Not a real customer outcome |
| Typology | Pattern/hypothesis requiring contextual evidence | Not a determination that conduct is illicit |
| Validation | Scoped challenge of reliability, assumptions, and use limitations | Developer tests alone are not independent approval |

The current technical definitions are implemented in the source and active policy. Regulatory uses of similar words may differ; consult [the source map](regulatory-map.md) instead of substituting this glossary for legal definitions.
