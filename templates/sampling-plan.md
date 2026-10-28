# Sampling and uncertainty plan

**Status: worked statistical design; no observed sample results.** Formulas and assumptions are developed in [the validation protocol](../docs/model-validation.md).

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
