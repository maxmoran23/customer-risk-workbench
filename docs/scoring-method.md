# Scoring method and worked arithmetic

The reference policy produces an explainable priority index, an arithmetic envelope for missing evidence, a band or review state, and separate screening-workflow routes. It does not estimate the probability of financial crime. Policy coefficients express illustrative judgments, not fitted or regulator-prescribed parameters.

## Normalization

For an increasing factor with observation `x`, lower transition `l`, upper transition `h` and weight `w`:

```text
severity(x) = min(1, max(0, (x-l)/(h-l)))
raw_points  = w * severity(x)
```

A decreasing factor uses `1-severity(x)`. The policy rejects nonfinite values, nonpositive transition widths, unknown feature references, duplicate IDs and invalid caps. Profile evidence must already have a documented `[0,1]` mapping. Raw activity features retain their units until the factor transformation.

For example, an expected-volume ratio of 3.25 with transitions 1.5 and 5 has severity `(3.25-1.5)/(5-1.5)=0.5`. With weight 25, its raw contribution is 12.5. This calculation says where the observation lies on the illustrative scale; it does not establish suspiciousness or calibrated risk.

## Group aggregation

| Group | Cap | Method | Reason for grouping |
| --- | ---: | --- | --- |
| Customer | 25 | Capped sum | Ownership, complexity and source-of-funds evidence |
| Geography | 15 | Capped maximum | Profile and transaction geography can represent the same exposure |
| Product/channel | 15 | Capped sum | Distinct product and delivery-channel dimensions |
| Behavior | 25 | Capped maximum | Overlapping windows and related activity proxies should not each get a full vote |
| Context | 10 | Capped sum | Adverse information and contextual PEP exposure |
| Evidence | 10 | Capped maximum | Documentation and profile-age signal |

For a sum group, `points=min(cap,sum(raw_points))`. For a max group, `points=min(cap,max(raw_points))`. The complete index is the sum of group points. Raw factor points do not necessarily sum to the index; the interface presents group contributions and labels raw points separately.

If five overlapping cash windows each produce 15 raw points, the behavior group receives 15 points, not 75. If another behavior factor produces 20, the group receives 20. This is an intentional conservative aggregation choice with a tradeoff: joint moderate signals are not reinforced within max groups. A different interaction design needs explicit justification, tests, and validation.

## Missing evidence and abstention

Each unavailable factor is allowed to range from zero to its full weight. Apply the same sum/max/cap operation to known and possible values to obtain group lower and upper bounds. Add the group bounds to obtain the portfolio-independent customer envelope. These are worst-case arithmetic bounds; they are neither confidence intervals nor a probability distribution.

- `provisional_index` is the known-evidence lower bound.
- `score` is null unless every configured factor is available and no hard gate applies.
- Missing required evidence forces `REVIEW_REQUIRED` even if its range falls within one band.
- Unconfirmed required history completeness forces review.
- Optional missing evidence whose envelope crosses a band boundary forces review.
- If optional missing evidence stays entirely within one band, the band may be retained with `band_basis=bounded_incomplete_evidence`; the complete score is still null.

Reference band minima are 0, 30 and 60. The comparison is inclusive at each minimum. An envelope `[12,27]` may retain LOW if no hard gate applies. `[15.75,30]` spans LOW and MODERATE and requires review. A null ratio caused by no prior-period activity is not replaced with zero or infinity.

## Screening and compound patterns

An unresolved screening flag produces a separate TRUE/FALSE/UNKNOWN route. It does not change the priority index and cannot be cancelled by a low index. A FALSE route means only that the supplied predicate did not fire; it is not sanctions clearance. Missing screening input remains UNKNOWN.

Compound hypotheses in `patterns.py` use three-valued logic and retain their predicate tree, benign explanation, and next evidence. They add no score points. The balance proxy `min(in,out)/max(in,out)` is not traced pass-through, and a digital-channel ratio is not evidence of illicit activity.

## Extending normalized evidence

The default catalog includes the declared reference profile keys. A custom policy can supply an explicit `profile_keys` list of up to 1,000 normalized fields and reference them as `profile.<key>`. Declare each mapping's source, effective date, unit, missing treatment, monotonicity and rationale. Extra undeclared profile keys are rejected during scoring so spelling errors cannot silently disappear. Keep unused reference keys declared when the input schema still supplies them.

Normalization does not make heterogeneous evidence scientifically commensurate. Calibration, factor dependence, segment effects, missingness, qualitative judgment, and intended use still require challenge. Adding more factors or more decimal places cannot substitute for that evidence.

## Change attribution

`monitoring.attribute_change` evaluates old/new data under old/new policies, producing four results. It averages the two orderings to allocate total provisional movement between data and policy effects, and exposes the interaction. This is an arithmetic decomposition. It does not isolate causal effects, and changes in missingness or elapsed time remain part of the data effect.

Sensitivity output labels changes in provisional lower bounds explicitly. Removing evidence can lower a bound while increasing uncertainty and suppressing the final score; this is not evidence of a risk reduction. Complete-score deltas are calculated only for pairs with two complete scores, with the paired denominator retained.
