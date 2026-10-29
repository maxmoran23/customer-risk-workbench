# Attribute review sheet

**Status: synthetic worked sheet; no classification decision recorded.** Values shown come from the illustrative reference catalog. Use the generated sheet from `python -m crw attributes workbook` as the authoritative inventory, and this template for the narrative fields the generated sheet leaves open.

## 1. Instructions

1. Confirm each source value maps to the right normalized value. Record mapping defects in the normalization audit, not on this sheet.
2. Record a proposed class for each value: `override_high`, `elevator`, `neutral`, `mitigator` or `override_low`. Scored classes use the catalog scale: neutral equals the configured neutral score, elevators score above it and mitigators below it. Override classes carry no score.
3. Cite at least one evidence identifier for every override class and for any change of class. The import enforces both; it checks that the identifier exists, not that the source supports the proposal.
4. Note values that are unremarkable alone but may matter in combination.
5. Do not edit `current_*` columns. Edit the CSV inventory and validate it with `python -m crw attributes import`.

## 2. Attribute profile

| Field | Worked example |
| --- | --- |
| Catalog id, version, digest | `reference-attribute-catalog`, `1.0.0`, digest prefix from the generated sheet |
| Attribute id and category | `nature_of_business`, `customer` |
| Definition | Primary business activity of a non-individual party, normalized to a controlled list |
| Applies to entity types | Sole proprietor, private and public company, investment vehicle, regulated and nonbank financial institution |
| Missing-value policy | `review`: a party missing this attribute receives a `missing_review_attribute` flag; the score still uses neutral unless the model abstains |
| Normalized values | 15 |

## 3. Research evidence

| Evidence id | Kind | Issuer | Locator | Supports which values | Limits of the source |
| --- | --- | --- | --- | --- | --- |
| `FFIEC-CIB` | supervisory_guidance | FFIEC | Cash-intensive businesses overview | Cash-intensive business values | Lists examples and factors; prescribes no score |
| `CFR-1022-380` | regulation | FinCEN | Registration requirement | Unregistered money transmission | Defines an obligation, not a rating class |

## 4. Value inventory

| Value | Source values | Parties | Current | Proposed | Evidence | Status |
| --- | --- | ---: | --- | --- | --- | --- |
| `parking_garage` | Two source spellings | 110 synthetic | neutral 50 | elevator 60 | `FFIEC-CIB` | proposed |
| `privately_owned_atm_operator` | Two source spellings | 63 synthetic | elevator 75 | override_high | `FFIEC-CIB`; `POLICY-ILLUSTRATIVE` | proposed |
| `online_marketplace_seller` | Two source spellings | 0 in the synthetic extract | unclassified | Reviewer to propose | Reviewer to cite | unreviewed |

## 5. Proposed changes

For each proposal record the change kind (`new_classification`, `reclassified`, `rescored`), ordinal direction, rationale, counterexample (a lawful profile the class would misdescribe), and the evidence relied on.

## 6. Combination notes and open questions

| Field | Entry |
| --- | --- |
| Values that may matter in combination | Value, partner attribute, mechanism, and whether the connections screen tested it |
| Questions for policy owners | Question, the decision it blocks, and the evidence that would resolve it |

## Review record

| Field | Reviewer | Policy owner |
| --- | --- | --- |
| Role | Reviewer role | Policy owner role |
| Date | Actual date of review | Actual decision date |
| Values covered | Value ids proposed or challenged | Value ids agreed, challenged or deferred |
| Reference | Workpaper location | Decision reference entered in `decision_reference` |
| Conditions | Assumptions and open questions | Conditions attached to agreement |

**Current record: no review or decision recorded.** Recording a proposal does not change the in-force classification, and completing this sheet is not a decision.
