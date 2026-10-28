# Validation workpaper

**Status: synthetic worked review scope; no independent validation opinion.** Attach actual execution and reviewer evidence before using a completed version.

## Scope and independence

Record component/policy versions, input population, intended use, review period, excluded uses, reviewer qualifications, development involvement, and conflicts. Developer-authored tests remain developmental evidence even when reviewed by another automated process.

## Worked challenge matrix

| Assertion | Independent challenge | Expected evidence | Current status |
| --- | --- | --- | --- |
| Window boundary is `(cutoff-duration,cutoff]` | Hand-place events on both endpoints | Exact eligible IDs and totals | Evidence requested |
| Late data cannot leak into a historical assessment | Vary only availability timestamp | Earlier result unchanged until availability | Evidence requested |
| Missing evidence is visible | Remove required and optional features separately | Null score, bounds, gates, and routes as specified | Evidence requested |
| Maximum groups avoid repeated additive votes | Duplicate related severity across windows | Group remains strongest eligible contribution | Evidence requested |
| Screening route is independent | Hold score inputs fixed; vary route input | Route changes without index substitution | Evidence requested |
| Research partitions are valid | Inspect manifests and fitted transform lineage | No prohibited entity/time overlap or holdout fitting | Evidence requested |

## Worked arithmetic case

For a group with cap `15` and maximum aggregation, factor contributions `4`, `9`, and `7` produce `9`. If the third factor is missing and its weight is `12`, the group interval is `[9,12]`. If instead the second factor is missing with weight `20`, the interval becomes `[7,15]`. These independent calculations challenge missing-bound and cap behavior without using engine output to define expected values.

## Findings and conclusion

For every exception, record reproducible inputs, observed versus expected behavior, severity, affected use, root cause, remediation, owner, retest, and disposition. Use [the findings log](findings-and-issues.md). An unexecuted test remains unexecuted even if the expected result appears obvious from reading the source.

The conclusion must state evidence sufficiency for the named use, unresolved limitations, conditions, prohibited extensions, and next review triggers. **Current opinion: none issued.** No reviewer name, approval date, or pass conclusion is fabricated by this template.
