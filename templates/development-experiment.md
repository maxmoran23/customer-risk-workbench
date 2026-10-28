# Development experiment record

**Status: worked synthetic protocol, not a completed experiment.** Register the protocol before evaluating the final holdout.

## Worked hypothesis

Hypothesis: maximum aggregation of overlapping behavior signals reduces redundant contribution relative to summation, while preserving sensitivity to the strongest observed signal. This tests a policy mechanism. It does not establish improved real-world detection.

| Protocol field | Worked specification |
| --- | --- |
| Assessment unit | Synthetic customer at a declared cutoff |
| Comparator A | Declared capped-sum behavior group |
| Candidate B | Same inputs/transforms, capped-maximum behavior group |
| Held constant | Customer population, cutoff, all other groups, data availability |
| Primary observations | Group contribution, band migration, abstention, reason changes |
| Counterexample | Two genuinely distinct behaviors may be suppressed by maximum aggregation |
| Excluded claim | Probability accuracy or criminality detection |

## Experiment design

Preserve the full configurations rather than recording only changed weights. Generate cases where overlapping windows describe the same events and cases where separate mechanisms occur in different windows. Predeclare the policy trade-off being evaluated and review the cases whose migration is largest.

For a statistical challenger, additionally define target, label availability, maturation horizon, cohort eligibility, partition scheme, training-only preprocessing, threshold selection, calibration design if applicable, and the permitted number of holdout reviews. The labels must not be derived from the comparator index.

## Required results table

| Result | Evidence required | Status in template |
| --- | --- | --- |
| Paired contribution differences | Customer-level A/B table with source/config hashes | Not run |
| Migration and abstention | Same-population denominator including unchanged cases | Not run |
| Sensitivity | Prespecified parameter ranges and failure analysis | Not run |
| Workload | Declared review capacity and queue-size interpretation | Not run |
| Counterexamples | Cases where candidate loses useful information | Not run |

## Selection decision

Record whether evidence supports continued evaluation, revision, or rejection; the reason; deviations from protocol; rejected alternatives; remaining limitations; and actual decision maker. A favorable average change is insufficient if material failure cases remain unexplained. **Current decision: pending evidence.**
