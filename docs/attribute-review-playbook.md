# Attribute review playbook

This guide describes how to run a value-classification review for a categorical customer-risk rating model with the `crw attributes` commands. The tooling records proposals, validates them against a catalog contract, and simulates their effect on a population. It does not decide a classification. Policy owners decide; the record shows who decided, when, and under what reference. All bundled catalogs, scores, weights, rules, and populations are illustrative and synthetic.

## The problem the program serves

A categorical rating model collects normalized attribute values for each rated party (for example nature of business, occupation, listed status, source of wealth, source of funds, jurisdiction exposure, entity type and account purpose), assigns each value a class and score, weights attributes, and bands the weighted result into tiers. Rebuilding such a model has a dependency order. The rated population must be scoped before entity types can be segmented; values must be classified before anyone can tell which combinations matter; rules must be designed on settled classifications before weights and tier thresholds are calibrated; and calibrated output must exist before it can be validated. Work done out of order is usually redone.

The review itself needs three things the program supplies: a repeatable per-attribute workpaper (instructions, attribute profile, research evidence, and an inventory of source and normalized values with current and proposed classes), a screen for values that matter in combination ([connections-method.md](connections-method.md)), and a test of whether every leg of a compound rule contributes ([rule-design.md](rule-design.md)). Stage sequencing and gate criteria are in [program-sequencing.md](program-sequencing.md).

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
| Model and rules | JSON | See [rule-design.md](rule-design.md) | `configs/programs/model.json`, `configs/programs/rules.json` |

Every command that takes `--catalog`, `--model` or `--rules` falls back to the illustrative reference configuration when the option is omitted. Pass the adopter's files explicitly in any real exercise so that a missing option cannot silently substitute the reference catalog.

## Sequence and commands

Commands below write to `runs/review/`; `runs/` is excluded from version control. Each JSON artifact is written atomically. The command also prints a short JSON summary.

1. **Scope the population.** `python -m crw attributes scope --config configs/programs/party-roles.json --roles roles.csv --out runs/review/scoping.json`. Each party resolves to its most-precedent mapped scope; a party with no mapped role is `unresolved`. The report counts parties per scope, the rated population, parties per scope and entity type, unmapped role codes with row counts, multi-role parties, partially unmapped parties, and parties carrying more than one entity type.
2. **Segment entity types.** Entity segmentation is read from the same scoping report: `conflicting_entity_type_parties` must reach the configured maximum (default zero). Resolve conflicts in the source extract, not in the catalog.
3. **Audit normalization.** `python -m crw attributes audit --catalog catalog.json --table normalization.csv --out runs/review/normalization-audit.json`. See [Normalization defects](#unclassified-values-new-values-and-normalization-defects).
4. **Export the workbook.** `python -m crw attributes workbook --catalog catalog.json --normalization normalization.csv --out runs/review/workbook`. This writes, per attribute, a Markdown sheet (`NN-<attribute>.md`) and a CSV inventory (`NN-<attribute>-inventory.csv`), plus `all-values-inventory.csv` and a `README.md` index with classified and reviewed shares.
5. **Review.** Reviewers read the sheet, research evidence, and edit only the editable inventory columns (below). The fill-in companion is [the attribute review sheet template](../templates/attribute-review-sheet.md); a change to one in-force value uses [the value reclassification request](../templates/value-reclassification-request.md).
6. **Import.** `python -m crw attributes import --catalog catalog.json --inventory runs/review/workbook --out runs/review/catalog-r1.json`. The result is a new, fully revalidated catalog and a change log at `runs/review/catalog-r1.changes.json`.
7. **Check review state.** `python -m crw attributes validate --catalog runs/review/catalog-r1.json --out runs/review/coverage.json` prints the catalog digest, coverage totals and proposed-change counts, and writes the full coverage report to `coverage.json` and the current-versus-proposed diff to `coverage-diff.json` (the output stem plus `-diff.json`). Without `--out` nothing is written.
8. **Screen connections.** `python -m crw attributes connections --catalog runs/review/catalog-r1.json --parties parties.jsonl --out runs/review/connections.json`. Add `--combination combination.json` to test the legs of a candidate compound rule. Record decisions in [the connections review template](../templates/connections-review.md).
9. **Simulate rules.** `python -m crw attributes rules --catalog runs/review/catalog-r1.json --model model.json --rules rules.json --parties parties.jsonl --stage proposed --out runs/review/rule-simulation.json`. Record each rule on [the rule specification card](../templates/rule-specification.md).
10. **Report gate status.** `python -m crw attributes status --scoping runs/review/scoping.json --coverage runs/review/coverage.json --normalization-audit runs/review/normalization-audit.json --connections runs/review/connections.json --rule-simulation runs/review/rule-simulation.json`, with `--calibration-reference` and `--validation-reference` once those analyses exist. `--criteria criteria.json` overrides gate thresholds; see [program-sequencing.md](program-sequencing.md).

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

Current assignments are read-only because the in-force classification should change only through the adopter's approved release process, not through a spreadsheet edit that bypasses it. The import refuses with `current assignment is read-only in review imports`. No command promotes a proposal to `current`. Promotion is a new catalog version produced under release control, and its population effect is assessed by the change-impact program ([impact-assessment-playbook.md](impact-assessment-playbook.md)).

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

A missing value is different from an unclassified one. Each catalog attribute declares a missing-value policy. Under `review`, a party missing an applicable attribute receives the review flag `missing_review_attribute:<attribute>` at assessment; under `neutral`, it receives no flag. In both cases the score uses the neutral value unless the model abstains ([rule-design.md](rule-design.md)). Policy owners should confirm the policy for each attribute as part of the review.

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

The program records and checks review state; it does not establish that any classification is correct, that the evidence supports it, or that the model is fit for use. Evidence entries in the reference catalog cite public sources that discuss the risk area; none of them prescribes the bundled classes or scores. Synthetic demo figures demonstrate mechanics on generated data and are not evidence of real-world performance. See [limitations.md](limitations.md) and [model-validation.md](model-validation.md).
