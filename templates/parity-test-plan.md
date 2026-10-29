# Parallel-run parity test plan

**Status: fill-in plan with guidance; no parallel run has been performed and no sign-off is recorded.** Purpose: show, release by release, that the `crw impact` engine produces the same migration counts as the existing assessment process on the same inputs before the existing process is retired.

## Scope

| Item | Entry | Guidance |
| --- | --- | --- |
| Existing process | | Describe generically: method, output shape, who runs it (role) |
| New path | | Python engine, generated SQL, or both |
| Populations and segments | | List paired and aggregate-only segments; both processes must use the same segment vocabulary |
| Outputs compared | | Matrix cells (automated); entrants, exits, exclusions (separate comparison) |
| Out of scope | | For example aggregate-only segments, report wording |

## Releases covered

| Item | Entry | Guidance |
| --- | --- | --- |
| Number of consecutive releases N | | Set before the first shadow release; justify |
| Change types to cover | | Each expected `change_type` at least once |
| Special cases to cover | | Nonzero pinned population, segment changes, aggregate-only segment, a release with no expected movement |
| Release log | | Release, date, assessment hash, verdict, defect IDs |

## Tolerance

Default: zero, meaning `EXACT_MATCH` is required. Both processes count the same parties from the same frozen snapshots, so any difference is a defect or a definitional difference.

| Item | Entry |
| --- | --- |
| `tolerance_abs` (command line `--tolerance-abs`) | |
| `tolerance_rel` (command line `--tolerance-rel`) | |
| Definitional differences that justify a nonzero tolerance | |
| Date tolerance declared (before first shadow release) | |

The per-cell allowance is `max(tolerance_abs, tolerance_rel * max(automated, standard))`. A segment present in only one output yields `MISMATCH` regardless of tolerance.

## Cell-level comparison procedure

1. Freeze pre and post snapshots once; both processes read the same frozen copies. Record SHA-256 or database checksums.
2. Run the existing process unchanged. Export its matrices as CSV `segment, pre_tier, post_tier, count`. Counts must be integers; a decimal value such as `12.0` fails rather than being truncated. Zero cells may be omitted: segments are compared by populated cells, so a configured segment with no parties need not appear. Tier codes are accepted if declared in the scale.
3. Run `crw impact assess --pre ... --post ... --config ... --scale ... --standard existing.csv --tolerance-abs <declared> --tolerance-rel <declared> --strict --out ...`. With `--strict` a `MISMATCH` exits with status 2.
4. Read `parity.json`: `verdict`, `cells_compared`, `differences`, `segments_only_in_automated`, `segments_only_in_standard`, `totals`.
5. Compare entrants, exits and excluded counts by segment from `assessment.json` against the existing process by hand or query; record the result.
6. If generated SQL is in scope, run its `checks` statement first and confirm every row reports `n = 0`; then run the remaining statements on the same tables, convert `matched` output to the CSV shape above, and pass it as `--standard` in a second run. Record that parity separately.
7. Classify every difference and log it below before the release review.

Synthetic reference: the demo runs the generated SQL on SQLite against the same synthetic snapshots and passes its cells to the engine as the standard. The result is `EXACT_MATCH` over 64 cells with 0 differences (44 nonzero cells identical in `sql-parity.json`). This is synthetic and shows the procedure only; it says nothing about agreement with any existing process.

## Defect log

| ID | Release | Segment / cell | Automated | Standard | Classification | Root cause | Owner (role) | Remediation | Retest evidence | Status |
| --- | --- | --- | ---: | ---: | --- | --- | --- | --- | --- | --- |

Classification values: `new_engine_defect`, `standard_process_defect`, `definitional_difference`, `input_difference`. A definitional difference must be resolved by agreeing one definition, not by widening tolerance after the fact.

## Exit criteria

| Criterion | Met (yes / no) | Evidence |
| --- | --- | --- |
| N consecutive releases `EXACT_MATCH`, or `WITHIN_TOLERANCE` with every difference attributed to a declared definitional cause | | |
| Entrants, exits and exclusions agree for the same releases | | |
| No open `new_engine_defect` | | |
| All required change types and special cases covered | | |
| Generated SQL parity confirmed on the target database (if used) | | |
| Reviewers have used the new report layout for a full cycle | | |
| Fallback to the existing process documented and exercised | | |

Agreement establishes that two computations match on these inputs. It does not establish that either is correct, nor that the change assessed was appropriate.

## Sign-off

| Role | Decision | Date | Conditions |
| --- | --- | --- | --- |
| Assessment owner | | | |
| Existing-process owner | | | |
| Independent reviewer | | | |
| Accountable approver | | | |

**Current status: plan not executed; no decision recorded.**
