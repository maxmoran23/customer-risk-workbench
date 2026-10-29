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

**3. Value classification.** Run the normalization audit on the extract used for rating and clear blocking issues. Export the workbook; assign reviewers per attribute; collect evidence; import; obtain policy-owner decisions for agreed values; reach the coverage thresholds. See [attribute-review-playbook.md](attribute-review-playbook.md).

**4. Connections review.** Record the outcome definition and labeled share. Run the screen; record a disposition for every supported candidate and every proxy flag; test candidate combinations. See [connections-method.md](connections-method.md) and [the connections review template](../templates/connections-review.md).

**5. Rule design.** Specify each rule, simulate, resolve high UNKNOWN shares, and move every rule out of `draft`. See [rule-design.md](rule-design.md).

**6. Weighting and calibration.** Fix weights and tier minima with a documented calibration analysis and pass its reference to the gate. This program supplies no calibration method; [model-development.md](model-development.md) and [statistical-methods.md](statistical-methods.md) describe the workbench's general experiment and calibration tooling.

**7. Output validation.** Obtain independent validation of the calibrated output and change-impact evidence; pass the reference to the gate. See [model-validation.md](model-validation.md).

## Hand-off to the change-impact program

The attribute review produces proposals. Moving a proposal into force changes tiers for real parties, so its effect is measured by the change-impact program described in [impact-assessment-playbook.md](impact-assessment-playbook.md). The hand-off has three parts:

1. **Preview.** Assess a design-time population at stage `current` and stage `proposed` and count tier movements. The demo implements this as `preview_change` in `crw/program_demo.py`; it skips pinned parties and runs on a separately drawn synthetic sample (seed plus 200), not on the population later assessed, so the manifest is a forecast rather than a restatement of the outcome.
2. **Manifest.** Declare expected movement by destination tier and direction before release. The demo derives bounds of plus or minus 25% around the preview (`manifest_from_preview`).
3. **Assessment.** After release, compare pre- and post-release tier snapshots with `python -m crw impact assess` and reconcile observed movement with the manifest.

In the synthetic demo, the preview on the design-time sample estimated 549 synthetic parties moving, 313 of them MODERATE to LOW. After a simulated release with population churn, the assessment of the demo population counted 545 synthetic parties moving, and the expectation reconciliation verdict was `consistent_with_manifest`. Current figures are in `evidence/program-demo-summary.json`, regenerated at release. Stage `proposed` uses any recorded proposal regardless of its review status, so the preview included the challenged de-escalation of `source_of_funds/virtual_asset_service_provider`. Preview only the proposals intended for release.

## Synthetic demo gate state

With all attribute-review artifacts supplied, the demo gate report reads: `population_scoping` complete, `entity_segmentation` complete, `value_classification` in progress (one unclassified value, 8.9% reviewed, three open proposals, normalization audit with blocking issues), and every later stage blocked. `rule_design` also reports its own blocker (one draft rule) and a highest UNKNOWN share of 0.032, below the 0.25 default. `next_actionable` is `value_classification`. These outcomes are designed into the synthetic reference to exercise the gates.
