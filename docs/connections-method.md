# Connections screen: statistical method

The connections screen in `crw/connections.py` helps reviewers find attribute values that may matter in combination, before compound rules are designed. It answers three separate questions because each needs different evidence:

1. **Structure.** Which attributes are associated at all, and how much jointly observed data supports the measurement?
2. **Synergy.** For a pair of values from different attributes, is the outcome rate when both are present different from what the two values predict separately?
3. **Contribution.** For a proposed multi-attribute combination, does each condition add to the outcome rate of the others?

Results are descriptive statistics on one population. They do not establish causation, misconduct, or the correctness of a rule. Outcome labels are adopter-defined review outcomes (for example a historical escalation decision), never a proxy for confirmed misconduct. Exact signatures are in the source; this document states the arithmetic and its interpretation limits.

## Rows, observation, and labels

Each row is one party's normalized values, plus an optional `outcome` that is `0`, `1` or null. Any other outcome value, including a boolean, fails. Attribute values must be text value ids or null; other types fail, and an attribute list naming the same attribute twice fails. A value is observed when it is neither null nor an empty string. An attribute that does not apply to a party's entity type has no value and is therefore unobserved here; rule evaluation instead classes such a leaf `NOT_APPLICABLE`, which never fires ([rule-design.md](rule-design.md)).

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
