# Rule specification card

**Status: synthetic worked card for an illustrative rule; no rule approved.** Complete one card per rule. Simulation and leg-test figures come from the synthetic program demo (`evidence/program-demo-summary.json` and the demo's `attribute-review/` outputs) and describe generated data only.

## Specification

| Field | Worked example |
| --- | --- |
| Rule id and rule set | `COMP-01` in `reference-rules` version `1.0.0` |
| Title | Nonbank institution with third-party or unverified funds in an unregulated structure |
| Kind | Compound (three attributes) |
| Condition | `all`: entity type in {`financial_institution_nonbank`}; source of funds in {`third_party_unrelated`, `unverified`}; listed status in {`unlisted_unregulated_structure`} |
| Effect | Floor at `VERY_HIGH` |
| Evidence ids | `FFIEC-NBFI`, `FFIEC-BE`, `FATF-RBA-BANK` |
| Rationale | Each leg is an elevator alone; together they leave no independent check on the origin of funds |
| Why not a value class change | The conclusion applies only to the combination |
| Applicability and negation check | Listed status does not apply to individuals, but the entity-type leg is `FALSE` for them, so the rule evaluates `FALSE` rather than `NOT_APPLICABLE`; intended |

## Leg contribution

| Leg removed | Complement support | Complement rate | p versus full | Conclusion |
| --- | ---: | ---: | ---: | --- |
| Entity type | 42 | 0.071 | 0.0001 | Contributes |
| Source of funds | 264 | 0.083 | 1.5e-11 | Contributes |
| Listed status | 198 | 0.379 | 0.63 | Does not discriminate on this population |

Leg tests use only parties to which every leg applies and whose outcome is observed; simulation counts every party, classing non-applicable legs `NOT_APPLICABLE`, which never fires. Full combination: support 68, rate 0.412 (Wilson 0.303 to 0.530), base rate 0.074. Connections candidate and grade: nonbank institution with third-party funds, `supported_synergy`.

## Simulation

| Measure | Worked result |
| --- | --- |
| Stage and population | `proposed`; 20,000 synthetic parties |
| TRUE / UNKNOWN / NOT_APPLICABLE / FALSE | 74 / 23 / 0 / 19,903 |
| Marginal tier changes | 20 |
| Shadowed share; shadowed by triggers | 0.730; 1 |
| Largest overlap | `ATOM-01`, 43 parties, Jaccard 0.043 |
| Population redundancy | None |

## Status and history

| Field | Entry |
| --- | --- |
| Current status | `proposed` |
| Open issues | Listed-status leg shows no contribution on the synthetic population; decide whether to remove it or justify it on evidence |
| Change history | Version, date, changed field, before, after, reason, requesting role |
| Decision | Decision, deciding role, date, reference, conditions |

**Current decision: none recorded.** A passing simulation or a supported screen grade is not rule approval.
