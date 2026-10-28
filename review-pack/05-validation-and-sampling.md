# Customer Risk Workbench / 05 validation and sampling

Public reference material. Synthetic examples and illustrative policies. No institutional approval or production-performance claim.

Source repository: https://github.com/maxmoran23/customer-risk-workbench

Attachment groups preserve full methods; source code and runnable tests remain in the repository.


---

Source: `docs/model-validation.md`


# Validation and challenge protocol

Validation asks whether the implementation, assumptions, and evidence are adequate for a stated use. A passing software test demonstrates the assertion it exercised. It does not establish real-world AML effectiveness or authorize use.

The repository's framework is informed by the current sources in [the regulatory map](https://github.com/maxmoran23/customer-risk-workbench/blob/main/docs/regulatory-map.md). The tests, formulas, review steps, and evidence thresholds described here are engineering choices, not prescriptive regulatory requirements.

For exact implemented statistical API signatures, return schemas, split rules, thresholds, and unsupported methods, read [statistical-methods.md](https://github.com/maxmoran23/customer-risk-workbench/blob/main/docs/statistical-methods.md). This chapter is a review protocol; it does not imply that every suggested analysis is automated.

## Evidence ladder

| Evidence class | Can support | Cannot establish by itself |
| --- | --- | --- |
| Hand-calculated fixture | Arithmetic, boundaries, expected behavior | Population performance |
| Property/invariant test | Broad structural guarantees over tested inputs | Correctness of the business assumptions |
| Synthetic stress experiment | Behavior under specified generated conditions | Real prevalence or unseen typology detection |
| Historical labeled evaluation | Performance for the sampled target/population/time | Causality or automatic transfer to a new population |
| Prospective shadow operation | Operational behavior without action authority | Safety of fully automated decisions |
| Authorized independent review | Findings and approval within documented scope | Immunity from future model or data failure |

Record evidence status as observed, not performed, not applicable with rationale, or failed. Do not convert missing evidence into a pass. A reviewer needs the failed and excluded tests as well as successes.

## Review workstreams

| Workstream | Concrete challenge | Required artifact |
| --- | --- | --- |
| Conceptual design | Does each signal plausibly support the intended review decision? What lawful behavior produces it? | Feature rationale and counterexamples |
| Data | Can the analyst reconstruct units, support, provenance, and availability at cutoff? | Data contract, reconciliation, lineage sample |
| Implementation | Does an independently calculated case match engine output? | Fixtures with calculations independent of engine helpers |
| Sensitivity | Can a minor input change create an unjustified policy jump? | Boundary and perturbation results |
| Missingness | Does unavailable evidence lower the score silently? | Interval, abstention, and reason-code tests |
| Outcomes | Does evaluation use an appropriate, mature target? | Label protocol, counts, selection-bias analysis |
| Operational use | Can decisions be replayed and exceptions investigated? | Assessment history, replay and rollback evidence |
| Governance | Who resolves limitations and approves the intended use? | Findings log and actual decision record |

## Metrics and undefined values

For a binary research outcome, with true positives `TP`, false positives `FP`, true negatives `TN`, and false negatives `FN`:

```text
precision   = TP / (TP + FP)
recall      = TP / (TP + FN)
specificity = TN / (TN + FP)
FPR         = FP / (FP + TN)
prevalence  = (TP + FN) / N
```

Zero denominators produce an undefined metric with a reason. They are not evidence of zero error. Always show class counts and included/excluded observations. Accuracy can look high when almost all outcomes are negative; compare with the all-negative baseline.

Rank metrics and threshold metrics answer different questions. PR-AUC depends on prevalence and the precision-recall construction; state whether reported as average precision or a trapezoidal area. ROC-AUC summarizes pair ordering and may conceal poor precision in rare-event settings. Ties need explicit treatment. Threshold selection must be separated from final evaluation.

For a genuine probability `p_i` and binary target `y_i`, Brier loss is `mean((p_i-y_i)^2)`. A reliability table compares predicted probability to observed outcome frequency within declared bins, with bin counts and uncertainty. Dividing a risk index by 100 does not make it a probability and does not justify calibration claims.

## Sampling design and precision

Choose the sampling unit to match the claim. Customer-level conclusions need customer-level support. Millions of transactions from a few customers do not create millions of independent customer observations.

For a simple random sample of independent binary observations, a planning approximation for a proportion with two-sided confidence multiplier `z` and target half-width `e` is:

```text
n0 = z^2 * p*(1-p) / e^2
n  = n0 / (1 + (n0-1)/N_population)   # finite-population approximation
```

Use `p=0.5` as a conservative variance assumption when the proportion is unknown, not as a prevalence estimate. Round sample sizes upward. This approximation is not sufficient for rare-event recall, clustered data, nonresponse, stratified oversampling, or complex selection. State assumptions and use the metric-specific method where applicable.

For recall, the effective support is the number of positive outcomes. For precision, it is the number selected positive by the decision rule. Sample planning based on total `N` alone can therefore be misleading. Rare-case enrichment helps analyze failure mechanisms, but unweighted enriched data do not reproduce population prevalence, precision, or workload.

### Zero observed failures

For `n` independent Bernoulli trials with zero failures, the exact one-sided upper bound at confidence `1-alpha` solves:

```text
(1-p_upper)^n = alpha
p_upper = 1 - alpha^(1/n)
```

For an illustrative 95% one-sided statement, use `alpha=0.05`. Zero failures does not mean zero failure probability. Repeating one fixture many times does not satisfy the independence assumption. A synthetic case suite is usually a designed coverage set, so a population failure-rate claim should not be inferred from its pass count.

### Wilson interval

For `k` successes in `n` independent Bernoulli observations, `p_hat=k/n`:

```text
denom  = 1 + z^2/n
center = (p_hat + z^2/(2*n)) / denom
half   = z/denom * sqrt(p_hat*(1-p_hat)/n + z^2/(4*n^2))
interval = [center-half, center+half]
```

Report the confidence level, unit, successes, denominator, and method. The interval addresses sampling uncertainty under its assumptions; it does not cover mislabeled outcomes, systematic selection bias, or a changed deployment population.

## Dependence, bootstrap, and repeated experiments

Resample customers or other appropriate clusters when observations within them are dependent. For temporal dependence, use a documented block or temporal evaluation design. A row bootstrap can be overconfident when the same customer contributes repeated rows. A bootstrap seed makes a result reproducible; it does not make the resampling assumptions correct.

Multiple seeds expose generator and fitting variation. Separate variation across generated worlds, training randomness, and resampling uncertainty. Do not pool them into an unlabeled confidence band. If many policies or segments are searched, disclose the search and selection process; a favorable selected result has different uncertainty from a prespecified test.

## Drift and migration

For bins with positive smoothed reference proportions `p_b` and comparison proportions `q_b`, a common PSI calculation is:

```text
PSI = sum_b((q_b-p_b) * log(q_b/p_b))
```

Declare reference population, bin edges, smoothing, sample sizes, and treatment of missingness. PSI changes with binning and is not a significance test. Conventional warning values are not universal approvals or regulatory thresholds. Compare effect size, exposure, and operating context before deciding on investigation.

A migration table compares old versus new bands for the same customer/cutoff. Include abstentions as a distinct state, retain unchanged customers in the denominator, and explain major driver changes. Report both count-weighted and appropriately defined exposure-weighted results when useful; they answer different questions.

## Minimum adversarial cases

* Event exactly at the cutoff and exactly at a lower window boundary.
* Historical event unavailable until after cutoff; future profile or event.
* Duplicate ID with identical content; duplicate ID with conflicting content; foreign-customer event.
* Empty activity, zero amount, zero expected volume, and unmapped jurisdiction evidence.
* Partial lifetime retention and sparse last-N windows.
* Input permutation, stable timestamp ties, and chunk-size changes.
* Group cap saturation, missing required factor, interval spanning a band, and threshold equality.
* Score-preserving changes to screening state and screening-preserving changes to the score.

The implemented catalog determines what is executable today. This list is a review requirement set, not a claim that every test has passed. Use generated reports and [the validation workpaper](https://github.com/maxmoran23/customer-risk-workbench/blob/main/templates/validation-workpaper.md) to connect each assertion to actual evidence.

## Finding disposition

Each finding records severity, affected use, reproducible example, root cause, proposed remedy, owner, target date, evidence of retest, and reviewer disposition. A development fix is not closed until the claimed failure is retested. Residual limitations remain visible in the model card and adoption decision. No approval is implied by completing a template.



---

Source: `templates/validation-workpaper.md`


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

For every exception, record reproducible inputs, observed versus expected behavior, severity, affected use, root cause, remediation, owner, retest, and disposition. Use [the findings log](https://github.com/maxmoran23/customer-risk-workbench/blob/main/templates/findings-and-issues.md). An unexecuted test remains unexecuted even if the expected result appears obvious from reading the source.

The conclusion must state evidence sufficiency for the named use, unresolved limitations, conditions, prohibited extensions, and next review triggers. **Current opinion: none issued.** No reviewer name, approval date, or pass conclusion is fabricated by this template.



---

Source: `templates/sampling-plan.md`


# Sampling and uncertainty plan

**Status: worked statistical design; no observed sample results.** Formulas and assumptions are developed in [the validation protocol](https://github.com/maxmoran23/customer-risk-workbench/blob/main/docs/model-validation.md).

## Define the claim

Worked estimand: the proportion of assessed synthetic customers whose engine result disagrees with an independently derived expected result in a defined generated population. This is different from the proportion of real suspicious customers identified by a review process.

| Design field | Required decision |
| --- | --- |
| Population | Frozen eligible customer set, cutoff, generator/source, version |
| Unit | Customer assessment; identify repeated-customer dependence |
| Sampling frame | Complete list and exclusions |
| Metric denominator | All sampled assessments, selected positives, or known positives as appropriate |
| Precision/confidence | Prespecified interval method and desired precision |
| Stratification | Segments, rare cases, missingness, routes, boundary cases |
| Weighting | Inclusion probabilities and population reconstruction when oversampled |

## Worked zero-failure calculation

For `n=300` independent Bernoulli trials with zero failures, a 95% one-sided upper failure bound is `1-0.05^(1/300)`, approximately `0.00994`, or `1.0%` rounded to one decimal percentage point. This is a mathematical illustration, not a report of 300 executed tests. The independence and population assumptions are essential.

A hand-picked library of difficult fixtures is not a probability sample. Its pass rate describes that library. Repeating the same fixture does not create independent observations or justify the bound above.

## Rare-event and subgroup support

If estimating recall, plan around the number of positive outcomes. If estimating precision, plan around the number selected by the rule. Predefine how to report groups with too little support: retain counts, label the estimate uncertain or undefined, and avoid ranking tiny groups as if differences were stable.

Use enriched rare-case samples for mechanism discovery and stress testing. Use appropriate sampling weights or a separate representative sample for population precision/workload claims. Record outcome maturity, nonresponse, unreviewed cases, and adjudicator disagreement.

## Evidence required before reporting

Attach sample selection code/seed, frame hash, inclusion probabilities, cluster definition, adjudication protocol, observed counts, confidence method, missing outcomes, deviations, and reproducible calculations. **Current conclusion: no empirical precision claim.**



---

Source: `templates/findings-and-issues.md`


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
