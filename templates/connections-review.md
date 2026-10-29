# Connections review

**Status: synthetic worked review; no candidate disposition approved.** Figures are from the synthetic program demo (20,000 synthetic parties, seed 11; summary at `evidence/program-demo-summary.json`) and describe generated data only.

## Screen record

| Field | Worked example |
| --- | --- |
| Command and output | `python -m crw attributes connections --parties ... --out runs/connections.json` |
| Catalog version and digest | Reference catalog; digest prefix `694a29422ede` |
| Population and extract date | Synthetic demo parties |
| Outcome definition | Synthetic historical escalation label; not confirmed misconduct |
| Outcome status and labeled share | `labeled`; 10% of synthetic labels withheld by design |
| Attributes screened | All eight reference attributes |
| Settings | `min_support` 30, `min_events` 5, `alpha` 0.05 |
| Pairs screened and tested | 694 screened, 513 tested |
| Strongest attribute association | Nature of business with entity type, bias-corrected Cramer's V 0.369 (27 of 28 pairs measured) |
| Grade counts | 2 synergy, 3 antagonism, 26 unadjusted only, 482 not supported, 181 insufficient support |
| Prior screens on this population | List every earlier run and setting; selective reruns are an unreported search |

## Candidate dispositions

| Candidate | Grade and q | Proxy flag | Disposition requested | Rationale |
| --- | --- | --- | --- | --- |
| Nonbank institution with third-party funds | Synergy, q 8.4e-14 | None | Test as a compound rule | Planted synthetic effect; requires mechanism and evidence before design |
| Money services business with third-party funds | Synergy, q 0.0057 | Possible proxy of the pair above | Do not design separately | Business type concentrated within nonbank institutions |
| Nonbank institution with external bank transfer | Antagonism, q 2.6e-07 | None | No rule | Mirror of the synergy through the pooled reference cell |
| Trust with inheritance or gift | Not supported, q 0.908 | Not applicable | No rule | High co-occurrence without outcome interaction |

Dispositions are: test as a compound rule, adjust a value class instead, investigate further (stratified or multivariable analysis), or no action. Every supported candidate and every proxy flag needs one.

## Combination test

| Leg removed | Complement support | Complement rate | p versus full | Reading |
| --- | ---: | ---: | ---: | --- |
| Entity type | 42 | 0.071 | 0.0001 | Contributes |
| Source of funds | 264 | 0.083 | 1.5e-11 | Contributes |
| Listed status | 198 | 0.379 | 0.63 | Adds support, not discrimination |

Full combination (`COMP-01` legs): support 68, rate 0.412, base rate 0.074. P-values are unadjusted; record whether the combination was pre-registered. Leg tests exclude parties to which any leg does not apply, whereas rule evaluation classes them `NOT_APPLICABLE`, which never fires.

## Limits acknowledged

Record label selection effects, known confounders not stratified, multiplicity across screens and combination tests, and pairs left unmeasured by support thresholds.

## Decision record

Record each disposition's decision, decision role, date, reference, and conditions. **Current decision: none recorded.** A supported grade is a statistical screen result, not approval of a rule.
