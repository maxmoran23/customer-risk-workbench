# Customer Risk Workbench / 09 attribute review program

Public reference material. Synthetic examples and illustrative policies. No institutional approval or production-performance claim.

Source repository: https://github.com/maxmoran23/customer-risk-workbench

Attachment groups preserve full methods; source code and runnable tests remain in the repository.


---

Source: `docs/program-sequencing.md`


# Program sequencing and stage gates

A categorical rating-model rebuild has seven stages. Each consumes the artifacts of earlier ones, so `crw/program.py` reports a later stage as `blocked` until every prerequisite meets its exit criteria. Gate status is a planning control computed from supplied artifacts and configured thresholds. It is not an approval, and a `complete` gate says only that the configured checks passed on the artifacts supplied.

## The seven stages

| Order | Stage | Prerequisites | Exit criterion (as described) | What the code checks |
| ---: | --- | --- | --- | --- |
| 1 | `population_scoping` | None | Rated population defined: every role code resolves to a scope class | Unresolved share at or below `max_unresolved_scope_share`; no unmapped role codes |
| 2 | `entity_segmentation` | 1 | Every rated party carries one recognized entity type | Parties with more than one entity type at or below `max_conflicting_entity_parties`, counted over all scoped parties |
| 3 | `value_classification` | 2 | Every normalized value classified; overrides evidenced; normalization audit free of blocking issues | Classified and reviewed shares at or above thresholds; open proposals (`proposed` or `challenged`) at or below `max_open_proposals`; overrides evidenced; audit supplied and not `blocking_issues` |
| 4 | `connections_review` | 3 | Cross-attribute screen run and its outcome-label status recorded | A connections report is supplied |
| 5 | `rule_design` | 3, 4 | Rules validated against the catalog and simulated on the population | Highest per-rule UNKNOWN share at or below `max_rule_unknown_share`; no `draft` rules |
| 6 | `weighting_and_calibration` | 5 | Weights and tier thresholds fixed with a referenced calibration analysis | A calibration reference is supplied |
| 7 | `output_validation` | 6 | Independent validation and change-impact evidence referenced | A validation reference is supplied |

Rule validation against the catalog happens earlier than the gate: a rule set that references an unknown attribute, value, tier or evidence id cannot be loaded, so it cannot be simulated. Where the right-hand column is narrower than the description, the difference is a reviewer responsibility, not something the gate verifies.

## Status values

| Status | Meaning |
| --- | --- |
| `not_started` | The stage's artifact was not supplied |
| `in_progress` | The artifact was supplied and at least one own blocker remains |
| `complete` | No blockers and every prerequisite complete |
| `blocked` | At least one prerequisite is not complete; the stage's own blockers, if any, are listed after the prerequisite blockers |

A blocked stage still reports its metrics, so work can be inspected before its turn. `next_actionable` names the first stage in order that is not complete.

## Why order matters

| Later stage | Depends on earlier output because |
| --- | --- |
| Entity segmentation | Applicability of attributes depends on entity type; only scoped parties need a type |
| Value classification | Which values occur, and in what volumes, depends on the scoped and segmented population; the normalization audit depends on the same extract |
| Connections review | A combination screen on unsettled classes measures the old catalog; already-triggered annotations depend on current classes |
| Rule design | Floors are judged against the tiers the classified values already produce; a compound rule should rest on a screened combination |
| Weighting and calibration | Weights and thresholds tuned before rules settle are tuned to the wrong tier distribution |
| Output validation | Validates the calibrated output; validating earlier output validates a different model |

Starting a later stage early is not prevented by the tool. Its results should be labeled provisional and rerun once prerequisites complete.

## Criteria and overrides

| Criterion | Default | Used by |
| --- | ---: | --- |
| `max_unresolved_scope_share` | 0.0 | `population_scoping` |
| `max_conflicting_entity_parties` | 0 | `entity_segmentation` |
| `min_classified_share` | 1.0 | `value_classification` |
| `min_reviewed_share` | 1.0 | `value_classification` |
| `max_open_proposals` | 0 | `value_classification` |
| `max_rule_unknown_share` | 0.25 | `rule_design` |

Defaults are illustrative and strict on purpose. Override them with `python -m crw attributes status ... --criteria criteria.json`, where the file holds a JSON object of criterion names to values (for example `{"max_rule_unknown_share": 0.1}`), or through `program_status(artifacts, criteria={...})`. Unknown criterion names fail, values must be finite nonnegative numbers, and criteria not named keep their defaults. The report echoes the merged criteria. Record any override, with its rationale and the role that approved it, alongside the gate report. A relaxed threshold is a decision, not a configuration detail.

`min_reviewed_share` counts every status except `unreviewed`. `max_open_proposals` blocks the gate while any value is `proposed` or `challenged`, but `deferred` values pass both checks. Report `agreed` and status counts from the coverage report with the gate result. The coverage file is the one written by `python -m crw attributes validate --out`.

## Planning checklist

**1. Population scoping.** Extract one row per role held. Map every role code to a scope class. Confirm the precedence rule (a party holding several roles takes its most-precedent scope) against policy. Review partially unmapped parties even when resolved through another role.

**2. Entity segmentation.** Resolve every conflicting entity type in the source. Confirm that each rated party's entity type is a catalog entity type; the gate does not test this.

**3. Value classification.** Run the normalization audit on the extract used for rating and clear blocking issues. Export the workbook; assign reviewers per attribute; collect evidence; import; obtain policy-owner decisions for agreed values; reach the coverage thresholds. See [attribute-review-playbook.md](https://github.com/maxmoran23/customer-risk-workbench/blob/main/docs/attribute-review-playbook.md).

**4. Connections review.** Record the outcome definition and labeled share. Run the screen; record a disposition for every supported candidate and every proxy flag; test candidate combinations. See [connections-method.md](https://github.com/maxmoran23/customer-risk-workbench/blob/main/docs/connections-method.md) and [the connections review template](https://github.com/maxmoran23/customer-risk-workbench/blob/main/templates/connections-review.md).

**5. Rule design.** Specify each rule, simulate, resolve high UNKNOWN shares, and move every rule out of `draft`. See [rule-design.md](https://github.com/maxmoran23/customer-risk-workbench/blob/main/docs/rule-design.md).

**6. Weighting and calibration.** Fix weights and tier minima with a documented calibration analysis and pass its reference to the gate. This program supplies no calibration method; [model-development.md](https://github.com/maxmoran23/customer-risk-workbench/blob/main/docs/model-development.md) and [statistical-methods.md](https://github.com/maxmoran23/customer-risk-workbench/blob/main/docs/statistical-methods.md) describe the workbench's general experiment and calibration tooling.

**7. Output validation.** Obtain independent validation of the calibrated output and change-impact evidence; pass the reference to the gate. See [model-validation.md](https://github.com/maxmoran23/customer-risk-workbench/blob/main/docs/model-validation.md).

## Hand-off to the change-impact program

The attribute review produces proposals. Moving a proposal into force changes tiers for real parties, so its effect is measured by the change-impact program described in [impact-assessment-playbook.md](https://github.com/maxmoran23/customer-risk-workbench/blob/main/docs/impact-assessment-playbook.md). The hand-off has three parts:

1. **Preview.** Assess a design-time population at stage `current` and stage `proposed` and count tier movements. The demo implements this as `preview_change` in `crw/program_demo.py`; it skips pinned parties and runs on a separately drawn synthetic sample (seed plus 200), not on the population later assessed, so the manifest is a forecast rather than a restatement of the outcome.
2. **Manifest.** Declare expected movement by destination tier and direction before release. The demo derives bounds of plus or minus 25% around the preview (`manifest_from_preview`).
3. **Assessment.** After release, compare pre- and post-release tier snapshots with `python -m crw impact assess` and reconcile observed movement with the manifest.

In the synthetic demo, the preview on the design-time sample estimated 549 synthetic parties moving, 313 of them MODERATE to LOW. After a simulated release with population churn, the assessment of the demo population counted 545 synthetic parties moving, and the expectation reconciliation verdict was `consistent_with_manifest`. Current figures are in `evidence/program-demo-summary.json`, regenerated at release. Stage `proposed` uses any recorded proposal regardless of its review status, so the preview included the challenged de-escalation of `source_of_funds/virtual_asset_service_provider`. Preview only the proposals intended for release.

## Synthetic demo gate state

With all attribute-review artifacts supplied, the demo gate report reads: `population_scoping` complete, `entity_segmentation` complete, `value_classification` in progress (one unclassified value, 8.9% reviewed, three open proposals, normalization audit with blocking issues), and every later stage blocked. `rule_design` also reports its own blocker (one draft rule) and a highest UNKNOWN share of 0.032, below the 0.25 default. `next_actionable` is `value_classification`. These outcomes are designed into the synthetic reference to exercise the gates.



---

Source: `docs/attribute-review-playbook.md`


# Attribute review playbook

This guide describes how to run a value-classification review for a categorical customer-risk rating model with the `crw attributes` commands. The tooling records proposals, validates them against a catalog contract, and simulates their effect on a population. It does not decide a classification. Policy owners decide; the record shows who decided, when, and under what reference. All bundled catalogs, scores, weights, rules, and populations are illustrative and synthetic.

## The problem the program serves

A categorical rating model collects normalized attribute values for each rated party (for example nature of business, occupation, listed status, source of wealth, source of funds, jurisdiction exposure, entity type and account purpose), assigns each value a class and score, weights attributes, and bands the weighted result into tiers. Rebuilding such a model has a dependency order. The rated population must be scoped before entity types can be segmented; values must be classified before anyone can tell which combinations matter; rules must be designed on settled classifications before weights and tier thresholds are calibrated; and calibrated output must exist before it can be validated. Work done out of order is usually redone.

The review itself needs three things the program supplies: a repeatable per-attribute workpaper (instructions, attribute profile, research evidence, and an inventory of source and normalized values with current and proposed classes), a screen for values that matter in combination ([connections-method.md](https://github.com/maxmoran23/customer-risk-workbench/blob/main/docs/connections-method.md)), and a test of whether every leg of a compound rule contributes ([rule-design.md](https://github.com/maxmoran23/customer-risk-workbench/blob/main/docs/rule-design.md)). Stage sequencing and gate criteria are in [program-sequencing.md](https://github.com/maxmoran23/customer-risk-workbench/blob/main/docs/program-sequencing.md).

## Roles

Role names are generic. Map them to the adopter's own governance; do not record individual names in this repository.

| Role | Owns | Does not own |
| --- | --- | --- |
| Model owner | Catalog structure, model configuration, rule set, gate criteria, run of every command, artifact retention | Classification decisions |
| Policy owner | Decision on each proposed class and score; the `decision_by_role`, `decision_date` and `decision_reference` fields; acceptance of rule floors | Data mappings and tooling |
| Data owner | Source-to-normalized mapping table, party role extract, entity-type resolution, remediation of normalization defects | Classification decisions |
| Reviewer | Per-attribute research, evidence citations, proposed class and score, rationale, combination notes, challenge of other proposals | Final decision; in-force (`current`) assignments |

An independent validator, separate from the four roles above, is needed only at the output-validation gate. Nothing in this program substitutes for that review.

## Inputs

| Input | Format | Required content | Reference example |
| --- | --- | --- | --- |
| Catalog | JSON | `catalog_id`, `version`, `description`, `scale` (minimum, neutral, maximum), `entity_types`, `attributes` (id, label, category, definition, applies_to, missing, values), `evidence` register | `configs/programs/catalog.json` |
| Party roles | CSV | `party_id`, `role_code`, `entity_type`; one row per role held | Generated inside the demo |
| Role-to-scope configuration | JSON | `scope_classes` ordered from most to least precedent, each with `id`, `rated`, `description`; `roles` mapping role codes to scope ids | `configs/programs/party-roles.json` |
| Normalization table | CSV | `attribute_id`, `source_system`, `source_value`, `value_id` (empty when unmapped), optional `party_count` (nonnegative integer) | `runs/<demo>/attribute-review/normalization-table.csv` |
| Parties | JSONL | `party_id`, `entity_type`, `values` (attribute to normalized value or null), optional `segment`, `pinned`, `outcome` | Generated inside the demo |
| Model and rules | JSON | See [rule-design.md](https://github.com/maxmoran23/customer-risk-workbench/blob/main/docs/rule-design.md) | `configs/programs/model.json`, `configs/programs/rules.json` |

Every command that takes `--catalog`, `--model` or `--rules` falls back to the illustrative reference configuration when the option is omitted. Pass the adopter's files explicitly in any real exercise so that a missing option cannot silently substitute the reference catalog.

## Sequence and commands

Commands below write to `runs/review/`; `runs/` is excluded from version control. Each JSON artifact is written atomically. The command also prints a short JSON summary.

1. **Scope the population.** `python -m crw attributes scope --config configs/programs/party-roles.json --roles roles.csv --out runs/review/scoping.json`. Each party resolves to its most-precedent mapped scope; a party with no mapped role is `unresolved`. The report counts parties per scope, the rated population, parties per scope and entity type, unmapped role codes with row counts, multi-role parties, partially unmapped parties, and parties carrying more than one entity type.
2. **Segment entity types.** Entity segmentation is read from the same scoping report: `conflicting_entity_type_parties` must reach the configured maximum (default zero). Resolve conflicts in the source extract, not in the catalog.
3. **Audit normalization.** `python -m crw attributes audit --catalog catalog.json --table normalization.csv --out runs/review/normalization-audit.json`. See [Normalization defects](#unclassified-values-new-values-and-normalization-defects).
4. **Export the workbook.** `python -m crw attributes workbook --catalog catalog.json --normalization normalization.csv --out runs/review/workbook`. This writes, per attribute, a Markdown sheet (`NN-<attribute>.md`) and a CSV inventory (`NN-<attribute>-inventory.csv`), plus `all-values-inventory.csv` and a `README.md` index with classified and reviewed shares.
5. **Review.** Reviewers read the sheet, research evidence, and edit only the editable inventory columns (below). The fill-in companion is [the attribute review sheet template](https://github.com/maxmoran23/customer-risk-workbench/blob/main/templates/attribute-review-sheet.md); a change to one in-force value uses [the value reclassification request](https://github.com/maxmoran23/customer-risk-workbench/blob/main/templates/value-reclassification-request.md).
6. **Import.** `python -m crw attributes import --catalog catalog.json --inventory runs/review/workbook --out runs/review/catalog-r1.json`. The result is a new, fully revalidated catalog and a change log at `runs/review/catalog-r1.changes.json`.
7. **Check review state.** `python -m crw attributes validate --catalog runs/review/catalog-r1.json --out runs/review/coverage.json` prints the catalog digest, coverage totals and proposed-change counts, and writes the full coverage report to `coverage.json` and the current-versus-proposed diff to `coverage-diff.json` (the output stem plus `-diff.json`). Without `--out` nothing is written.
8. **Screen connections.** `python -m crw attributes connections --catalog runs/review/catalog-r1.json --parties parties.jsonl --out runs/review/connections.json`. Add `--combination combination.json` to test the legs of a candidate compound rule. Record decisions in [the connections review template](https://github.com/maxmoran23/customer-risk-workbench/blob/main/templates/connections-review.md).
9. **Simulate rules.** `python -m crw attributes rules --catalog runs/review/catalog-r1.json --model model.json --rules rules.json --parties parties.jsonl --stage proposed --out runs/review/rule-simulation.json`. Record each rule on [the rule specification card](https://github.com/maxmoran23/customer-risk-workbench/blob/main/templates/rule-specification.md).
10. **Report gate status.** `python -m crw attributes status --scoping runs/review/scoping.json --coverage runs/review/coverage.json --normalization-audit runs/review/normalization-audit.json --connections runs/review/connections.json --rule-simulation runs/review/rule-simulation.json`, with `--calibration-reference` and `--validation-reference` once those analyses exist. `--criteria criteria.json` overrides gate thresholds; see [program-sequencing.md](https://github.com/maxmoran23/customer-risk-workbench/blob/main/docs/program-sequencing.md).

The coverage report passed to `status` must be the file written by `validate --out`; the printed summary has a different shape.

`python -m crw program-demo --out runs/program-demo` runs every step above on 20,000 synthetic parties (seed 11) and writes the artifacts under `attribute-review/`. Its summary is kept at `evidence/program-demo-summary.json` and regenerated at release; cite that file for current synthetic figures rather than copying them.

## Artifacts produced

| Artifact | Producer | Key contents | Consumed by |
| --- | --- | --- | --- |
| `scoping.json` | `attributes scope` | Scope counts, rated population, unmapped role codes, conflicting entity types | Population-scoping and entity-segmentation gates |
| `normalization-audit.json` | `attributes audit` | Issue lists and counts, party coverage, status, catalog digest | Value-classification gate |
| Workbook directory | `attributes workbook` | Per-attribute sheet and inventory, combined inventory, index | Reviewers, then `attributes import` |
| New catalog and `.changes.json` | `attributes import` | Revalidated catalog; per-value changed fields with before and after | Every later step |
| `coverage.json` and `coverage-diff.json` | `attributes validate --out` | Catalog digest; per-attribute and total classified, reviewed, override, open-proposal and agreed counts; current-versus-proposed diff | Value-classification gate; reclassification requests |
| `connections.json` | `attributes connections` | `associations`, `pairs`, optional `combination` | Connections-review gate, rule design |
| `rule-simulation.json` | `attributes rules` | Per-rule firing counts, marginal changes, shadowing, overlaps, redundancy | Rule-design gate |

Retain every artifact with the catalog digest it was produced from. The normalization audit, coverage report, diff and rule simulation carry a catalog digest; the connections report does not, so record the catalog file and digest next to it. The gate report does not check that its inputs share one catalog version; compare the digests before relying on it.

## The CSV round trip

The inventory is the only editing surface. Its columns, in order, are fixed by `INVENTORY_COLUMNS`:

| Column | Treatment on import |
| --- | --- |
| `attribute_id`, `value_id` | Key. Must name an existing catalog value; a repeated key fails the import. |
| `label` | Read-only. Must match the catalog label; an edit fails the import. Labels change in the catalog. |
| `source_values`, `party_count` | Informational. Ignored on import. |
| `current_class`, `current_score` | Read-only. Parsed and compared with the catalog; any difference fails the import. |
| `proposed_class`, `proposed_score` | Editable. Both empty means no proposal. A score without a class, a score on an override class, or a nonnumeric score on a scored class fails. |
| `evidence_ids` | Editable. Semicolon-separated register identifiers; each must exist in the catalog's evidence register. |
| `rationale`, `status` | Editable. See the status workflow. |
| `decision_by_role`, `decision_date`, `decision_reference` | Editable. Filling any of them creates a decision record, which only an `agreed` value may carry. |

Files are written as UTF-8 with a byte-order mark so that spreadsheet tools open them directly; the reader accepts files with or without it. A directory import reads every `*-inventory.csv` and skips `all-values-inventory.csv` so that the same value is not imported twice; the combined file is read only if it is the sole inventory. Values absent from the imported rows are left unchanged, so attributes can be imported one at a time. An import cannot add a new value or a new evidence entry; those are catalog edits made by the model owner.

Current assignments are read-only because the in-force classification should change only through the adopter's approved release process, not through a spreadsheet edit that bypasses it. The import refuses with `current assignment is read-only in review imports`. No command promotes a proposal to `current`. Promotion is a new catalog version produced under release control, and its population effect is assessed by the change-impact program ([impact-assessment-playbook.md](https://github.com/maxmoran23/customer-risk-workbench/blob/main/docs/impact-assessment-playbook.md)).

On the synthetic demo workbook, importing the unedited directory produced zero changed values and the same catalog digest (`694a29422ede...`), which is the expected identity check before any review begins.

## Status workflow

Statuses are `unreviewed`, `proposed`, `challenged`, `agreed`, `deferred`. The catalog contract enforces conditions on each status; it does not enforce the order in which statuses are reached.

| Status | Enforced conditions | Intended meaning |
| --- | --- | --- |
| `unreviewed` | No proposed assignment | Not yet examined |
| `proposed` | Proposed assignment present; nonblank rationale | Reviewer recommendation awaiting decision |
| `challenged` | Proposed assignment present; nonblank rationale | Recommendation disputed; evidence or reasoning outstanding |
| `agreed` | Proposed assignment present; nonblank rationale; decision record with nonblank `by_role`, `date` in `YYYY-MM-DD`, nonblank `reference` | Policy owner accepted the proposal |
| `deferred` | None beyond the general rules | Consciously postponed |

General rules applying to every value: a proposal whose class differs from the current class needs at least one evidence reference; a scored class (`mitigator`, `neutral`, `elevator`) needs a score inside the scale, `neutral` must equal the scale neutral, `elevator` must exceed it and `mitigator` must fall below it; an override class (`override_low`, `override_high`) carries no score; the effective assignment (proposal if present, otherwise current) of an override class needs at least one evidence reference; only an `agreed` value may carry a decision record.

"Agreed" requires a decision record naming a role, a date and a reference to the adopter's decision artifact. It does not change the in-force assignment. Two consequences need attention:

- Assessment at stage `proposed` uses every recorded proposal regardless of status, falling back to current where none exists. A `challenged` or `deferred` proposal therefore moves tiers in a `proposed` simulation. In the synthetic demo, the challenged de-escalation of `source_of_funds/virtual_asset_service_provider` (elevator 60 to neutral 50) is included in the preview. To simulate agreed proposals only, build a catalog version with the other proposals removed.
- Evidence is enforced for a change of class and for override classes, not for a rescore within the same class. The contract checks that an evidence id exists in the register, not that the source supports the proposal; reviewers and policy owners must read it.

## Unclassified values, new values, and normalization defects

A value with neither a current nor a proposed assignment is unclassified. It is listed in the coverage report and blocks the value-classification gate at the default threshold. Assessment fails explicitly (`has no classification at stage`) if any party holds such a value; it is never scored as neutral by default. A party value that is not a catalog value fails validation with an instruction to resolve it in the normalization table. Party validation also rejects a non-null value on an attribute that does not apply to the party's entity type, a value that is not text, a non-boolean `pinned`, and an outcome other than 0, 1 or null. A new source value therefore requires, in order: a mapping row from the data owner, a catalog value if no existing value fits (model owner), and a classification proposal with evidence (reviewer).

A missing value is different from an unclassified one. Each catalog attribute declares a missing-value policy. Under `review`, a party missing an applicable attribute receives the review flag `missing_review_attribute:<attribute>` at assessment; under `neutral`, it receives no flag. In both cases the score uses the neutral value unless the model abstains ([rule-design.md](https://github.com/maxmoran23/customer-risk-workbench/blob/main/docs/rule-design.md)). Policy owners should confirm the policy for each attribute as part of the review.

The normalization audit checks the mapping table against the catalog. Source strings are compared after canonicalization: Unicode NFKC, case folding, `&` read as `and`, punctuation and spacing collapsed.

| Issue | Definition | Blocking | Typical remedy |
| --- | --- | --- | --- |
| `unknown_attribute` | Row names an attribute not in the catalog | Yes | Correct the row or extend the catalog |
| `unknown_value` | Row maps to a value id not in the attribute | Yes | Correct the mapping or add the value |
| `unmapped` | Row has an empty `value_id` | Yes | Map it or add a value |
| `conflicting_mapping` | Same attribute and canonical text map to more than one value | Yes | Choose one mapping |
| `fragmentation_candidates` | Different canonical strings with token Jaccard similarity at or above the threshold mapping to different value sets | No | Human review; lexical similarity is not equivalence |
| `duplicate_rows` | Exact repeat of attribute, source system and source value | No | Remove the repeat; repeats are skipped and their counts excluded |
| `orphan_catalog_values` | Catalog value with no mapped source row | No | Decide whether it is pending adoption or stale |

Status is `blocking_issues` when any blocking list is nonempty, otherwise `review_candidates` when fragmentation candidates or duplicates exist, otherwise `clean`. Orphans never change the status. `party_coverage` is mapped party count over total party count when counts are supplied.

The synthetic demo table has 116 rows and status `blocking_issues`: one unmapped row ("Gas station / convenience", 37 synthetic parties), one conflicting mapping (canonical "liquor store" mapped to `liquor_store` by two systems and to `general_retail` by a third), and one duplicate row; party coverage is 0.9997. A further injected defect, "Store, liquor" mapped to `general_retail`, canonicalizes to "store liquor"; because token Jaccard similarity ignores word order, it was flagged at the default threshold of 0.8 as a fragmentation candidate against "liquor store" with similarity 1.0. A defect with different wording (an added or substituted word) can fall below the threshold. Lexical checks find some defects; they do not certify a mapping table.

## Review-coverage metrics

`review_coverage` reports progress, not correctness.

| Metric | Definition |
| --- | --- |
| `classified_share` | Values with a proposed or current assignment, over all values |
| `reviewed_share` | Values whose status is not `unreviewed`, over all values. `challenged` and `deferred` count as reviewed. |
| `by_effective_class` | Count per effective class, plus `unclassified` |
| `status_counts` | Count per status |
| `overrides`, `overrides_evidenced` | Values whose effective class is an override, and how many cite evidence |
| `open_proposals` | Values with status `proposed` or `challenged`, awaiting a decision |
| `agreed` | Values with status `agreed` |
| `catalog_digest`, `note` | Digest of the catalog measured; a fixed note restating the reviewed-share definition |

A reviewed share of 100% does not mean every value is agreed: `deferred` values count as reviewed and do not count as open proposals. Report `open_proposals`, `agreed` and `status_counts` alongside it. In the synthetic reference catalog, 55 of 56 values are classified (98.2%), 5 are reviewed (8.9%), 3 are open proposals, none are agreed, and all 4 override values cite evidence. The two reviewed values with no proposal are evidenced `override_high` values that the reference builder marks `deferred`.

## Stage gates as implemented

Gate logic is in `crw/program.py`. A stage whose prerequisite is not `complete` is `blocked`, whatever its own metrics show.

| Stage | Artifact read | Complete when | Default threshold |
| --- | --- | --- | --- |
| `population_scoping` | Scoping report | Unresolved share at or below threshold and no unmapped role codes | `max_unresolved_scope_share` 0.0 |
| `entity_segmentation` | Scoping report | Parties with more than one entity type at or below threshold | `max_conflicting_entity_parties` 0 |
| `value_classification` | Coverage report and normalization audit | Classified and reviewed shares at or above thresholds; open proposals at or below threshold; every override evidenced; audit present and not `blocking_issues` | `min_classified_share` 1.0, `min_reviewed_share` 1.0, `max_open_proposals` 0 |
| `connections_review` | Connections report | A report is supplied | None |
| `rule_design` | Rule simulation | No rule UNKNOWN for more than the threshold share of parties; no `draft` rules | `max_rule_unknown_share` 0.25 |
| `weighting_and_calibration` | Calibration reference text | A reference is supplied | None |
| `output_validation` | Validation reference text | A reference is supplied | None |

Several exit criteria are narrower in code than in their descriptions. The entity-segmentation check counts conflicting entity types across all scoped parties, including unrated ones, and does not test that entity types are recognized catalog entity types. The connections gate tests only that a screen exists. The calibration and validation gates test only that a reference string exists. Reviewers must confirm the substance behind each.

## Common failure modes

| Failure | Symptom | Prevention |
| --- | --- | --- |
| Editing current assignments in the CSV | Import refuses the row | Raise a reclassification request; promote through release |
| Status `agreed` without a decision record | Import refuses with `agreed status requires a recorded decision` | Policy owner completes all three decision fields |
| Decision fields on a non-agreed value | Import refuses | Clear the fields until agreement |
| Treating reviewed share as agreement | Values `deferred` indefinitely, or open proposals tolerated by a relaxed `max_open_proposals` | Report status counts with coverage; record any criteria override |
| Change of class without evidence | Import refuses with `a change of class requires at least one evidence reference` | Cite register evidence; add the entry to the register first if needed |
| Simulating `proposed` and reading it as the agreed position | Challenged proposals move tiers | Simulate a catalog containing only agreed proposals |
| Omitting `--catalog` | Reference catalog silently used | Always pass the adopter's catalog |
| Mixing catalog versions across artifacts | Gate report combines inconsistent inputs | Record and compare catalog digests |
| Mapping fixes made in the catalog | Values proliferate to absorb spelling variants | Fix spellings in the normalization table |
| New source value reaches assessment unmapped | Assessment fails on a non-normalized value | Run the audit on every extract before simulation |

## Limits

The program records and checks review state; it does not establish that any classification is correct, that the evidence supports it, or that the model is fit for use. Evidence entries in the reference catalog cite public sources that discuss the risk area; none of them prescribes the bundled classes or scores. Synthetic demo figures demonstrate mechanics on generated data and are not evidence of real-world performance. See [limitations.md](https://github.com/maxmoran23/customer-risk-workbench/blob/main/docs/limitations.md) and [model-validation.md](https://github.com/maxmoran23/customer-risk-workbench/blob/main/docs/model-validation.md).



---

Source: `docs/connections-method.md`


# Connections screen: statistical method

The connections screen in `crw/connections.py` helps reviewers find attribute values that may matter in combination, before compound rules are designed. It answers three separate questions because each needs different evidence:

1. **Structure.** Which attributes are associated at all, and how much jointly observed data supports the measurement?
2. **Synergy.** For a pair of values from different attributes, is the outcome rate when both are present different from what the two values predict separately?
3. **Contribution.** For a proposed multi-attribute combination, does each condition add to the outcome rate of the others?

Results are descriptive statistics on one population. They do not establish causation, misconduct, or the correctness of a rule. Outcome labels are adopter-defined review outcomes (for example a historical escalation decision), never a proxy for confirmed misconduct. Exact signatures are in the source; this document states the arithmetic and its interpretation limits.

## Rows, observation, and labels

Each row is one party's normalized values, plus an optional `outcome` that is `0`, `1` or null. Any other outcome value, including a boolean, fails. Attribute values must be text value ids or null; other types fail, and an attribute list naming the same attribute twice fails. A value is observed when it is neither null nor an empty string. An attribute that does not apply to a party's entity type has no value and is therefore unobserved here; rule evaluation instead classes such a leaf `NOT_APPLICABLE`, which never fires ([rule-design.md](https://github.com/maxmoran23/customer-risk-workbench/blob/main/docs/rule-design.md)).

The screen is in labeled mode when at least one row carries a non-null outcome. In labeled mode, rows with a null outcome are excluded from every count for that pair, including co-occurrence lift. A single labeled row therefore switches the whole screen to the labeled subset. Check `outcome_status` and the labeled share before reading any result.

## Structure: bias-corrected Cramer's V

`attribute_associations(rows, attributes, min_n=30)` builds, for each attribute pair, the contingency table of rows where both are observed. With `n` jointly observed rows, `r` and `k` observed levels, and Pearson chi-square `chi2`:

```text
phi2   = chi2 / n
phi2c  = max(0, phi2 - (k-1)(r-1)/(n-1))
rc     = r - (r-1)^2/(n-1)
kc     = k - (k-1)^2/(n-1)
V      = sqrt(phi2c / min(kc-1, rc-1))
```

This is the bias correction of Bergsma (2013). The uncorrected statistic is inflated in small tables with many levels. The result is `null` with status `insufficient_support` when `n < min_n`, when either attribute has fewer than two observed levels, or when the corrected denominator is not positive. A null V is unmeasured, not zero. `joint_coverage` is `n` over all rows; attributes whose `applies_to` lists do not overlap, such as occupation (individuals and sole proprietors) and listed status (legal entities), are never jointly observed and report `insufficient_support`.

V measures association between whole attributes. It does not identify which values drive it and says nothing about outcomes. The correction truncates at zero, so many weakly associated pairs report exactly 0.0.

In the synthetic demo, 27 of 28 attribute pairs were measured. The highest V was nature of business with entity type (0.369, 7,201 jointly observed rows), reflecting the generator's entity-specific business mix; source of funds with entity type, which carries the planted synergy, reached only 0.063. Ten pairs reported 0.0, and occupation with listed status was never jointly observed. A low V does not rule out a value-level interaction with the outcome.

## Co-occurrence lift

For values `va` of attribute `a` and `vb` of attribute `b`, among the `N` rows where both attributes are observed (and, in labeled mode, the outcome is observed):

```text
lift = n11 * N / (n_va * n_vb)
```

where `n11` counts rows holding both values and `n_va`, `n_vb` are the marginal counts. Lift above 1 means the values occur together more often than independence predicts. A pair is reported only if `n11 >= min_support` (default 30). Lift alone is the entire result when labels are absent.

## Synergy: the interaction odds ratio

In labeled mode, each reported pair is cross-classified into four cells among the `N` rows: both values (`11`), `va` without `vb` (`10`), `vb` without `va` (`01`), and neither (`00`). Each cell has `n` rows and `e` events. Consider the saturated logistic model with indicators `A = [a = va]` and `B = [b = vb]`:

```text
logit P(outcome = 1) = b0 + b1*A + b2*B + b3*A*B
```

A saturated model reproduces each cell's observed odds exactly, so `exp(b0) = odds00`, `exp(b0+b1) = odds10`, `exp(b0+b2) = odds01`, and `exp(b0+b1+b2+b3) = odds11`. The interaction coefficient is therefore available in closed form:

```text
interaction OR = exp(b3) = (odds11 * odds00) / (odds10 * odds01)
```

An interaction OR above 1 means the pair's odds exceed what the two main effects predict on the multiplicative (odds) scale. Below 1 means the combination is less than the main effects predict. Interaction on the additive (risk-difference) scale is not computed and can differ in sign. The `00` reference cell pools every other value of both attributes, so its composition matters; see the proxy section.

### Standard error, interval and test

The code adds 0.5 to every one of the eight event and non-event counts, whether or not any is zero (the Haldane-Anscombe correction; Haldane 1956, Anscombe 1956), and uses the Woolf (1955) variance for a log odds ratio:

```text
log_IOR = sum over cells c of sign_c * log((e_c + 0.5) / (n_c - e_c + 0.5)),  signs: 11 +, 10 -, 01 -, 00 +
SE      = sqrt(sum over cells c of 1/(e_c + 0.5) + 1/(n_c - e_c + 0.5))
z       = log_IOR / SE
p       = two-sided normal tail of z
interval (reported on the log scale) = log_IOR +/- 1.959964 * SE
```

The reported `interaction_odds_ratio` is computed from the corrected counts, so it differs slightly from the uncorrected cell odds. The Wald interval and test rely on large-sample normality of the log ratio; with few events in any cell they are unreliable even when they can be computed. `rate_both_interval` is a Wilson (1927) score interval for the `11` cell rate; the interval function rejects an event count outside `0..n`.

A pair is not tested, and is graded `insufficient_support`, when the `11` cell has fewer than `min_events` events (default 5) or when any of the `10`, `01` or `00` cells is empty. The event threshold applies only to the `11` cell.

### Multiplicity control

Every tested pair in one call forms one family. P-values are adjusted with the Benjamini and Hochberg (1995) step-up procedure; the reported `q_value` is the monotone adjusted value, capped at 1, in input order. BH controls the false discovery rate under independence or positive regression dependence (Benjamini and Yekutieli 2001). Pairs that share values or rows are dependent, so the nominal rate is an approximation. The family is defined by the attributes, thresholds and population of that call; rerunning with different settings and keeping the most favorable result is an unreported search.

### Grades

| Grade | Condition |
| --- | --- |
| `supported_synergy` | `q <= alpha` and interaction OR above 1 |
| `supported_antagonism` | `q <= alpha` and interaction OR not above 1 |
| `unadjusted_signal_only` | `q > alpha` and `p <= alpha` |
| `not_supported` | `p > alpha` |
| `insufficient_support` | Not tested; see thresholds above |

`alpha` defaults to 0.05 and is bounded to `(0, 0.5]`. Labeled candidates are sorted by grade in the order above, then by q-value, then by descending support. Unlabeled candidates carry no grade, are sorted by descending lift, and are counted as `structural_only`.

When a catalog is supplied, each candidate lists `already_triggered_by`: values in the pair whose effective assignment at the chosen stage (the CLI uses `proposed`) is `override_high`. Where the configured override-high tier is the top tier, as in the reference model, a compound rule on such a pair cannot raise the tier further.

## Proxy annotation

A marginal pairwise screen sees only two attributes at a time. If a true effect involves values `X` and `Y`, and a third value `Z` is strongly associated with `X`, then the pair (`Z`, `Y`) can test as supported only because `Z` stands in for `X`. The same mechanism produces mirror antagonisms: when the `10` or `01` cell of another pair absorbs the high-rate (`X`, `Y`) parties, that pair's reference cells are inflated and its interaction OR falls below 1 without any genuine protective effect.

`_annotate_proxies` flags the simplest case. Walking supported pairs in sort order, a pair is marked `possible_proxy_of` an earlier supported pair when the two share exactly one value and their non-shared values, which must belong to different attributes, co-occur with lift of at least 2.0. The lift is looked up among reported candidates, so a linking pair below `min_support` is never used. Only the first match is recorded. Because synergies sort before antagonisms, "earlier" means earlier in grade order, not necessarily stronger in q-value.

The annotation is a prompt to investigate, not a conclusion. Unflagged pairs can still be proxies (for example through a chain of associations, or a link pair below support). Confirm with a stratified analysis or a multivariable model before designing a rule on any flagged pair.

## Contribution: evaluating a combination

`evaluate_combination(rows, conditions)` takes a mapping of two or more attributes, each to a nonempty list of allowed value ids. It restricts to rows where every named attribute and the outcome are observed, then computes:

- `support`, `events`, `rate` and a Wilson interval for rows meeting all conditions;
- `base_rate` over all fully observed rows;
- for each condition (leg), the complement: rows meeting every other condition but not this one, with its rate, Wilson interval, and a pooled two-proportion z-test p-value against the full combination.

A leg contributes discrimination when its complement rate is clearly below the full combination rate. A leg whose complement has a similar rate adds support (more parties) but not discrimination; removing it would leave the rate largely unchanged. P-values are unadjusted. Pre-register the combinations to be tested, or adjust for the number tested, before treating any as confirmed. Without labels every row is excluded, support is zero, and rates and p-values are null.

## What changes without labels

| Output | Labeled | Unlabeled |
| --- | --- | --- |
| Cramer's V | Computed | Computed (it never uses labels) |
| Co-occurrence lift | Computed on labeled rows only | Computed on all jointly observed rows |
| Cell rates, interaction OR, p, q | Computed when supported | Absent |
| Grades | Five grades | None (`structural_only`) |
| Proxy annotation | Applied to supported pairs | Not applied |
| Combination evaluation | Rates and leg tests | Zero support |

Without labels the screen can show which values co-occur, which is useful for rule-overlap planning and data checks. It cannot show synergy. Do not treat high lift as evidence of elevated risk.

## Synthetic recovery check

The demo generator (`crw/synthetic_program.py`) draws a synthetic escalation label from a logistic model with small main effects for elevator, override and mitigator values, one planted synergy that adds 1.9 to the log-odds for `entity_type/financial_institution_nonbank` with `source_of_funds/third_party_unrelated`, and one planted null pair (`entity_type/trust` with `source_of_wealth/inheritance_or_gift`) that co-occurs often but has no interaction. Labels are missing for 10% of parties.

On 20,000 synthetic parties (seed 11) the screen reported 694 pairs and tested 513: 2 `supported_synergy`, 3 `supported_antagonism`, 26 `unadjusted_signal_only`, 482 `not_supported`, 181 `insufficient_support`.

| Synthetic pair | Support | Lift | Rates: both / a only / b only / neither | Interaction OR | Log-OR 95% interval | q | Grade |
| --- | ---: | ---: | --- | ---: | --- | ---: | --- |
| Planted synergy: third-party funds, nonbank institution | 240 | 3.244 | 0.442 / 0.063 / 0.077 / 0.046 | 6.658 | 1.445 to 2.346 | 8.4e-14 | `supported_synergy` |
| Money services business, third-party funds | 158 | 2.467 | 0.449 / 0.076 / 0.156 / 0.054 | 2.981 | 0.561 to 1.623 | 0.0057 | `supported_synergy`, flagged `possible_proxy_of` the planted pair |
| External bank transfer, nonbank institution | 465 | 0.884 | 0.060 / 0.046 / 0.212 / 0.047 | 0.250 | -1.829 to -0.940 | 2.6e-07 | `supported_antagonism` |
| Planted null: inheritance or gift, trust | 437 | 3.291 | 0.076 / 0.051 / 0.056 / 0.053 | 1.436 | -0.171 to 0.895 | 0.908 | `not_supported` |

The planted synergy was recovered, and its log-OR interval contains the planted 1.9. The planted null was not graded as supported despite lift above 3. The second synergy is a proxy: money services businesses are concentrated among nonbank institutions in the generator, and the annotation flagged it. The antagonism is a mirror artifact: nonbank institutions without external bank transfers include the high-rate third-party-funds group (rate 0.212 in the `01` cell). The other two antagonisms (third-party funds with individuals; money services business with external transfers, also flagged as a proxy) arise the same way. The smallest cells remain unstable: one unadjusted pair reported an interaction OR of 19.509 with a zero-rate `10` cell.

For the three-leg reference rule `COMP-01` (nonbank institution, third-party or unverified funds, unlisted unregulated structure), 5,057 rows were fully observed; 68 met all legs with rate 0.412 (Wilson 0.303 to 0.530) against a base rate of 0.074. Complement rates were 0.071 without the entity-type leg (p 0.0001), 0.083 without the source-of-funds leg (p 1.5e-11), and 0.379 without the listed-status leg (p 0.63). The listed-status leg adds no discrimination in this synthetic population, consistent with the generator, which planted no effect on it.

The release copy of the demo summary, including the planted-pair grades, is `evidence/program-demo-summary.json`; it is regenerated at release and supersedes the figures above if they differ. These results show that the implementation recovers structure the generator planted. They are not evidence of real-world performance, of any real interaction between these attributes, or of the screen's power on real data.

The CLI combines the three questions: `python -m crw attributes connections --parties parties.jsonl [--attributes ...] [--min-support 30] [--min-events 5] [--alpha 0.05] [--combination combination.json] --out runs/connections.json`. The demo writes the same three results to `associations.json`, `pair-screen.json` and `combination-COMP-01.json`.

## Limits

- **Label selection bias.** Labels inherit the selection, review intensity and recording practices that produced them. A synergy can reflect where reviewers looked in the past rather than where risk is. Unlabeled parties are excluded, and if labeling depended on attribute values, rates are biased in unknown directions.
- **Confounding.** Interactions are marginal over every attribute not in the pair. Segment mix, entity type and onboarding channel can create or mask an apparent interaction. Stratify or fit a multivariable model before acting.
- **Multiplicity.** Hundreds of pairs are tested per run. BH controls the expected share of false discoveries among supported pairs under its assumptions; it does not make any single supported pair confirmed. Combination leg tests are unadjusted.
- **Small cells.** The 0.5 correction and Wald interval are approximations. Sparse cells give wide intervals and extreme odds ratios. Pairs below support thresholds are unmeasured, not absent.
- **Scale.** Results are on the odds-ratio scale and are specific to this population and period. They do not transfer to another population without re-estimation.

## References

Anscombe, F. J. (1956). On estimating binomial response relations. *Biometrika*, 43.
Benjamini, Y., and Hochberg, Y. (1995). Controlling the false discovery rate. *Journal of the Royal Statistical Society, Series B*, 57.
Benjamini, Y., and Yekutieli, D. (2001). The control of the false discovery rate in multiple testing under dependency. *Annals of Statistics*, 29.
Bergsma, W. (2013). A bias-correction for Cramer's V and Tschuprow's T. *Journal of the Korean Statistical Society*, 42.
Haldane, J. B. S. (1956). The estimation and significance of the logarithm of a ratio of frequencies. *Annals of Human Genetics*, 20.
Wilson, E. B. (1927). Probable inference, the law of succession, and statistical inference. *Journal of the American Statistical Association*, 22.
Woolf, B. (1955). On estimating the relation between blood group and disease. *Annals of Human Genetics*, 19.

The change-impact program's baseline screen uses the modified z-score of Iglewicz and Hoaglin (1993); it is not part of the connections screen.



---

Source: `docs/rule-design.md`


# Rule design for the categorical model

Rules in `crw/rules.py` act on a categorical model's tier after the weighted score is banded. A rule either sets a minimum tier (a floor) or requests a review action without changing the tier (a route). Rules exist because some conclusions should not depend on how a weighted mean happens to land, and because some values matter only in combination. Every rule, weight and tier threshold in the reference configuration is an illustrative assumption.

## Atomic and compound rules

A rule is **atomic** when its condition references exactly one attribute and **compound** when it references two or more. `RuleSet.kind` computes this from the condition, so a rule over one attribute with an `any` of several values is still atomic.

| Question | Atomic rule | Compound rule |
| --- | --- | --- |
| When it is the right tool | A single value should set a minimum tier or a review action regardless of everything else, but an override class is too strong or too broad | A combination of values warrants a tier the weighted mean would not reach, and no single value does |
| Alternative to consider first | Reclassify the value (for example elevator to `override_high`) | Raise a component value's score, if the effect is not specific to the combination |
| Evidence expected | Evidence for the value alone | Evidence for the combination, a connections screen result, and a leg-contribution result |
| Typical failure | Duplicates an override class or another atomic rule | A leg adds parties but not discrimination; the combination is a proxy for a stronger pair |

## Rule record and grammar

A rule set is a JSON object with `ruleset_id`, `version`, `description` and `rules`. Each rule has exactly these fields:

| Field | Requirement |
| --- | --- |
| `id` | Opaque identifier, unique in the set |
| `title` | Text |
| `condition` | Condition object (below) |
| `effect` | `{"type": "floor", "tier": <model tier>}` or `{"type": "route", "action": <nonempty text>}` |
| `evidence` | Nonempty list; every id must exist in the catalog's evidence register |
| `rationale` | Nonblank text |
| `status` | `draft`, `proposed`, `challenged`, `agreed` or `retired` |

A condition is either a leaf or one logical operator:

```json
{"attribute": "source_of_wealth", "in": ["undocumented"]}
{"all": [<condition>, <condition>, ...]}
{"any": [<condition>, <condition>, ...]}
{"not": <condition>}
```

A leaf's attribute must be a catalog attribute and every value in `in` must be one of its normalized values; `in` must be nonempty. An operator object carries exactly one key. `all` and `any` take 1 to 50 operands. The validator rejects conditions nested more than eight levels below the root. Unknown fields anywhere fail validation.

## Four-state evaluation

`evaluate(condition, values, applicable)` returns `TRUE`, `FALSE`, `UNKNOWN` or `NOT_APPLICABLE`. Only `TRUE` fires a rule.

| Construct | Result |
| --- | --- |
| Leaf, attribute not applicable to the party's entity type | `NOT_APPLICABLE` |
| Leaf, applicable attribute missing (null or absent) | `UNKNOWN` |
| Leaf, value present | `TRUE` if the value is in `in`, else `FALSE` |
| `all` | `FALSE` if any operand is `FALSE`; else `NOT_APPLICABLE` if any is; else `UNKNOWN` if any is; else `TRUE` |
| `any` | `TRUE` if any operand is `TRUE`; else `UNKNOWN` if any is; else `NOT_APPLICABLE` if any is; else `FALSE` |
| `not` | Swaps `TRUE` and `FALSE`; `UNKNOWN` and `NOT_APPLICABLE` are preserved |

A business-type condition says nothing about a natural person, so it is `NOT_APPLICABLE` rather than false or unknown, and negation preserves that: `not (listed_status in [listed_regulated_exchange])` does not fire for an individual. In an `all`, a `FALSE` operand still decides the result, so a compound rule whose entity-type leaf is false for a party evaluates `FALSE` for it even when another leg is not applicable. A non-applicable leg never makes a rule fire and never raises an UNKNOWN review flag.

The connections screen's `evaluate_combination` excludes the same parties instead: a non-applicable attribute has no value there, so the row is unobserved ([connections-method.md](https://github.com/maxmoran23/customer-risk-workbench/blob/main/docs/connections-method.md)). Leg-contribution figures therefore describe only parties to which every leg applies, while rule simulation counts every party in one of the four states.

## Assessment precedence

`CategoricalModel.assess(party, rules, stage)` applies a fixed order that a reviewer can recompute by hand:

1. **Validate the party.** The entity type must be a catalog entity type; every attribute must be a catalog attribute; every non-null value must be text, a normalized catalog value, and on an attribute that applies to the entity type; an `entity_type` value, if present, must agree with the party's entity type; `pinned`, if present, must be boolean; `outcome`, if present, must be 0, 1 or null.
2. **Weighted mean.** Over weighted attributes that apply to the entity type, each value contributes its score at the chosen stage (`proposed` uses a value's proposal where one exists, else its current assignment). Override classes contribute the scale neutral. A missing value contributes the neutral and is listed. A value with no assignment at the stage fails the assessment. Catalog attributes without a weight do not enter the score but remain available to rules, and their override classes still act in steps 5 and 6. The mean is rounded to nine decimal places before banding, so a score equal to a tier minimum is not demoted by floating-point error.
3. **Abstention.** If the model's `missing` setting is `abstain` and any applicable weighted attribute is missing, the score is withheld (`null`). The catalog's per-attribute `missing` policy does not change the score; it controls the review flag in step 8.
4. **Base tier.** The highest tier whose minimum is at or below the score.
5. **Floors.** Any `override_high` value on an applicable attribute, weighted or not, adds the model's `override_high_tier`. Each non-retired rule evaluating `TRUE` with a floor effect adds its tier. Route rules evaluating `TRUE` are listed in `routes` and do not touch the tier.
6. **Cap.** If any applicable value, weighted or not, is `override_low`, the base tier is capped at the model's `override_low_tier`. Floors from step 5 then apply on top, so an auto-low value never suppresses a trigger or a rule.
7. **Resolution.** The final tier is the higher of the (capped) base tier and the highest floor. If the score was withheld, the final tier is the top tier when the highest floor is the top tier, and `REVIEW_REQUIRED` otherwise.
8. **Review flags.** Each missing applicable weighted attribute whose catalog missing policy is `review` adds `missing_review_attribute:<attribute>`, whatever the tier; under policy `neutral` no flag is added. A rule evaluating `UNKNOWN` never fires. If the final tier is not `REVIEW_REQUIRED` and an UNKNOWN floor rule's tier is above the final tier, the party carries `unknown_rule_could_raise_tier:<rule id>`. Neither flag changes the tier.

`caps_applied` is true whenever an `override_low` value is present and the tier is not `REVIEW_REQUIRED`, including when the cap did not bind. Retired rules are skipped in assessment and in simulation.

## Worked arithmetic

Reference weights: entity type 1.0, nature of business 1.5, occupation 1.0, listed status 1.0, source of wealth 1.2, source of funds 1.5, jurisdiction exposure 1.5, account purpose 1.0. Tier minima: LOW 0, MODERATE 50.5, HIGH 54, VERY_HIGH 58. These are illustrative. The values below were calculated by hand from the reference configuration; the engine returned the same results.

**Case 1, compound floor binds.** A nonbank financial institution (elevator 70) in professional services (neutral 50), unlisted unregulated structure (elevator 65), business-ownership wealth (neutral 50), unrelated third-party funds (elevator 65), domestic only (neutral 50), operating account (neutral 50). Occupation does not apply. Weighted sum `70 + 75 + 65 + 60 + 97.5 + 75 + 50 = 492.5` over weight 8.7 gives 56.609, base tier HIGH. `COMP-01` evaluates TRUE with a VERY_HIGH floor; final tier VERY_HIGH.

**Case 2, missing leg.** The same party with listed status missing. Listed status now contributes neutral 50: `477.5 / 8.7 = 54.885`, base tier HIGH. `COMP-01` is UNKNOWN and does not fire. Final tier HIGH with flags `missing_review_attribute:listed_status` (the reference policy for listed status is `review`) and `unknown_rule_could_raise_tier:COMP-01`. Under `missing: abstain` the same party has a null score; no floor reaches the top tier, so the result is `REVIEW_REQUIRED`, and only the missing-attribute flag is added. An individual missing occupation, whose reference policy is `neutral`, receives no flag.

**Case 3, cap and floor together.** A domestic governmental entity (`override_low`, contributes neutral 50) with employment-income wealth (50), external bank transfer (50), elevated-risk jurisdiction (elevator 70) and operating account (50). Nature of business, occupation and listed status do not apply. `(50 + 60 + 75 + 105 + 50) / 6.2 = 54.839`, base tier HIGH, capped to LOW. `ATOM-02` fires with a HIGH floor; final tier HIGH. With a standard international jurisdiction instead, the score is exactly 50.0, base LOW, final LOW, and `caps_applied` is still true.

**Case 4, floor and route.** An individual who is a senior foreign public official (elevator 65) with undocumented wealth (elevator 70), external bank transfer (50), domestic only (50), and unclear account purpose (elevator 70). Score 58.194, base VERY_HIGH. `COMP-02` fires but changes nothing; `ROUTE-01` fires and adds a purpose-clarification route without affecting the tier.

## Simulation

`simulate_rules(parties, model, rules, stage)` (CLI: `python -m crw attributes rules`) evaluates every non-retired rule on every party and reports:

| Output | Definition | How to read it |
| --- | --- | --- |
| `tier_distribution_without_rules` | Tiers from score, value triggers and caps only | Baseline that rules modify |
| `tier_distribution_with_rules` | Tiers with every floor rule applied | Combined effect of the rule set |
| `true`, `unknown`, `not_applicable`, `false` | Evaluation counts per rule | High `unknown` is a data-quality finding first; `not_applicable` shows how much of the population the rule cannot address |
| `marginal_tier_changes` (floors) | Parties whose final tier changes when only this rule is removed | The rule's unique effect given all others; not effectiveness |
| `shadowed_share` (floors) | Share of firing parties already at or above the floor tier without this rule | Near 1 means the rule mostly restates other logic |
| `shadowed_by_triggers` (floors) | Firing parties that also hold an `override_high` value | Overlap with value triggers |
| `overlaps` | Rule pairs, routes included, firing together, with Jaccard similarity and joint count | Candidates for consolidation or ordering review |
| `population_redundancy` | Floor rule whose firing set is contained in another floor rule's set with an equal or higher tier | Removable on this population; may not hold on another |

Simulation does not compute review flags; use `assess` on individual parties for those. Routes have no marginal or shadowing statistics because they do not change tiers.

Synthetic demo results (20,000 synthetic parties, seed 11, stage `proposed`; the release summary is regenerated at `evidence/program-demo-summary.json`):

| Rule | Kind | Effect | TRUE | UNKNOWN | NOT_APPLICABLE | Marginal changes | Shadowed share |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| `ATOM-01` | atomic | floor HIGH | 966 | 222 | 12,577 | 111 | 0.885 |
| `ATOM-02` | atomic | floor HIGH | 1,473 | 580 | 0 | 426 | 0.711 |
| `COMP-01` | compound | floor VERY_HIGH | 74 | 23 | 0 | 20 | 0.730 |
| `COMP-02` | compound | floor VERY_HIGH | 7 | 25 | 455 | 6 | 0.143 |
| `COMP-03` | compound | floor HIGH (draft) | 2 | 7 | 148 | 1 | 0.500 |
| `ROUTE-01` | atomic | route | 583 | 638 | 0 | n/a | n/a |

Reading these synthetic figures: `ATOM-01` fires often but changes few tiers because 88.5% of its firing parties already reach HIGH without it, through their scores, value triggers or other rules; its large `NOT_APPLICABLE` count is the natural persons and other entity types to which nature of business does not apply. `COMP-01` has no `NOT_APPLICABLE` parties because its entity-type leg is `FALSE` for every other entity type. `COMP-02` is UNKNOWN for more parties than it fires on, so its practical reach depends on wealth documentation. `COMP-03` remains `draft`, which blocks the rule-design gate. The `COMP-01` leg test in [connections-method.md](https://github.com/maxmoran23/customer-risk-workbench/blob/main/docs/connections-method.md) found that its listed-status leg adds no discrimination in this synthetic population, which is a reason to revisit that leg before agreement. Tier distributions with and without rules, overlaps and redundancy are in `rule-simulation.json`.

## Rule lifecycle

| Status | Effect in assessment and simulation | Effect on the rule-design gate |
| --- | --- | --- |
| `draft` | Evaluated | Blocks the gate |
| `proposed` | Evaluated | None |
| `challenged` | Evaluated | None |
| `agreed` | Evaluated | None |
| `retired` | Skipped | Excluded from the simulation, so not counted |

Unlike catalog values, rule statuses carry no decision record in the rule-set contract, and no status sequence is enforced. Record the policy owner's decision, date and reference on [the rule specification card](https://github.com/maxmoran23/customer-risk-workbench/blob/main/templates/rule-specification.md). A simulation of `proposed` or `challenged` rules describes candidate behavior, not an approved position.

## Design checklist

1. State the conclusion the rule encodes and why a value class or score change cannot express it.
2. For a compound rule, cite the connections screen candidate and its grade, and confirm it is not flagged as a proxy.
3. Run `evaluate_combination` and drop or justify any leg whose complement rate is close to the full rate.
4. Choose floor or route. A route is the honest effect when the condition marks missing information rather than a risk conclusion, as `ROUTE-01` does.
5. Simulate; record UNKNOWN share, marginal changes, shadowing and overlaps; investigate any UNKNOWN share near the gate threshold.
6. Check the `NOT_APPLICABLE` count and confirm that the entity types it covers are meant to be outside the rule.
7. Record evidence, rationale and status; obtain the policy owner's decision outside the rule file.

## Limits

Simulation describes one population. Marginal changes count tier dependence, not detection value, and a rule with few marginal changes can still matter for a future population. UNKNOWN behavior depends on missing data. Rule floors are set by judgment; nothing here estimates their correctness. See [program-sequencing.md](https://github.com/maxmoran23/customer-risk-workbench/blob/main/docs/program-sequencing.md) for where rule design sits relative to calibration and validation.



---

Source: `templates/attribute-review-sheet.md`


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



---

Source: `templates/connections-review.md`


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



---

Source: `templates/rule-specification.md`


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



---

Source: `templates/value-reclassification-request.md`


# Value reclassification request

**Status: synthetic worked request; no reclassification approved.** One request covers one normalized value. Classes, scores and population figures are illustrative or synthetic.

## Request

| Field | Worked example |
| --- | --- |
| Request id | `DEMO-RECLASS-001` |
| Catalog id, version, digest | `reference-attribute-catalog`, `1.0.0`, digest prefix `694a29422ede` |
| Attribute and value | `nature_of_business` / `parking_garage` |
| Current assignment | neutral 50 |
| Requested assignment | elevator 60 |
| Change kind and direction | `reclassified`, up |
| Requesting role | Reviewer role |
| Inventory status after import | `proposed` (the import refuses a change of class without at least one evidence id) |

## Evidence and rationale

| Evidence id | Kind | What it supports | What it does not establish |
| --- | --- | --- | --- |
| `FFIEC-CIB` | supervisory_guidance | The activity appears among common cash-intensive business examples | Any specific class or score |

Rationale: align the value with comparable cash-intensive businesses already classified as elevators. Counterexample to consider: a parking operator with fully electronic receipts, where the cash rationale does not apply.

## Expected population effect

| Field | Worked entry |
| --- | --- |
| Parties holding the value | 110 synthetic parties (inventory `party_count` in the demo workbook) |
| Expected direction | Some parties move up; none move down from this change alone |
| Preview method | Assess the design-time population at stages `current` and `proposed` on a catalog version carrying only this proposal |
| Preview result | Not isolated in the demo. The demo's combined preview (`preview_moved` in `evidence/program-demo-summary.json`) runs on a separate design-time synthetic sample and covers every recorded proposal, including the challenged one, because stage `proposed` ignores review status; it cannot be attributed to this value |
| Interaction with rules | `COMP-03` (draft) lists this value among cash businesses |
| Tolerance for the post-release check | Declared range for the change manifest |

## Decision record

| Field | Entry |
| --- | --- |
| Decision | Agreed, challenged, deferred or rejected |
| Deciding role | Policy owner role |
| Decision date | Actual date, `YYYY-MM-DD` |
| Decision reference | Adopter's decision artifact reference |
| Conditions | Any limits on the agreement |
| Release and impact reference | Catalog version that places the value in force and the change-impact assessment id |

An `agreed` inventory status requires the role, date and reference fields. Agreement does not change the in-force class; promotion happens in a released catalog version, assessed through [the change-impact program](https://github.com/maxmoran23/customer-risk-workbench/blob/main/docs/impact-assessment-playbook.md). **Current decision: none recorded.**
