# Findings and issues log

**Status: worked hypothetical findings; not a report of defects observed in the current repository.** Use actual reproduced evidence when opening a real issue.

## Severity framework

| Severity | Interpretation | Example response |
| --- | --- | --- |
| Critical | Incorrect output or authority boundary could cause immediate material harm in the stated use | Suspend affected use; preserve evidence; remediate and independently retest |
| High | Material reliability gap or unsupported intended use | Constrain use until resolved or specifically reviewed |
| Medium | Meaningful limitation with a bounded impact | Track remediation/compensating controls and review conditions |
| Low | Clarity, maintainability, or minor control issue | Correct within normal change control |

Severity is contextual; it is not a regulator-defined classification in this template. Record actual affected use and exposure rather than selecting severity from the issue title.

## Worked hypothetical finding

| Field | Illustration |
| --- | --- |
| ID | `DEMO-FINDING-001` |
| Title | Historical event incorrectly included before availability |
| Status | Hypothetical example; not observed |
| Severity if present | High for historical performance claims |
| Expected | Event unavailable at cutoff contributes nothing |
| Hypothetical actual | A flawed implementation uses occurrence time only |
| Root cause hypothesis | Eligibility filter omits availability timestamp |
| Affected claim | Point-in-time backtest validity |
| Proposed remedy | Apply both time predicates; rerun affected assessments/evaluation |
| Retest | Boundary fixture plus historical replay comparison |

## Required actual issue fields

Record source revision; policy/data hashes; reproducible steps; expected and observed result; evidence files; affected population/use; root cause; owner; target date; remediation commit; tests; residual limitations; reviewer; and closure date. If a claim cannot be reproduced, retain its status as unconfirmed and state what evidence is missing.

## Closure rules

* A proposed patch is remediation in progress, not closed.
* A passing unrelated suite does not prove that the reported failure is fixed.
* A compensating control must name its owner, scope, evidence, and duration.
* Accepted limitations remain in the model card/use restrictions and monitoring plan.
* Reopening an issue preserves earlier evidence and decisions.

**Current actual findings in this template: none recorded.** Consult the real release/review reports for observed findings; this example cannot be counted as an executed review.
