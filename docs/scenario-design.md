# Scenario design and coverage

A scenario is a falsifiable statement about behavior under specified inputs. A typology is a hypothesis about a pattern requiring context. Neither is evidence that a named individual committed an offense. Public examples remain synthetic and use no real customer or live screening data.

## Case anatomy

Each case should specify an ID, purpose, input fixture, cutoff, source provenance, expected calculation or relation, expected gates/routes, lawful counterexample, missing evidence, and failure interpretation. An expected result should be independent of the function being tested. Copying the engine output into the expected field creates a regression snapshot, not independent correctness evidence.

| Case family | What it tests | Example question |
| --- | --- | --- |
| Positive mechanism | Signal responds to a constructed condition | Does a configured cash-share ramp change severity as declared? |
| Benign counterexample | Same observable pattern with lawful explanation | Does balanced treasury activity get described as a proxy rather than traced laundering? |
| Missing evidence | Incomplete data remains visible | Does unmapped exposure become unknown rather than zero? |
| Temporal adversary | Information unavailable at cutoff is excluded | Can a late-arriving event leak into a backtest? |
| Boundary | Exact threshold and window semantics | Which band contains a value exactly at its minimum? |
| Structural invariant | Behavior preserved under irrelevant changes | Does permutation or chunk size change the assessment? |
| Cross-control | One workflow cannot neutralize another | Does a low index suppress an unresolved screening referral? |
| Operational fault | Invalid input is handled predictably | Is a conflicting duplicate rejected without partial success? |

## Worked behavioral example: balanced flows

Synthetic events total 120 incoming units and 120 outgoing units in a complete window. The balance proxy is `min(120,120)/max(120,120)=1`. A policy ramp from `0.7` to `1` produces maximum severity for that feature.

This establishes an aggregate numerical pattern. It does not show that the outgoing events used the incoming funds, occurred after them, involved the same counterparties, or lacked an economic purpose. A legitimate settlement business can produce the same proxy. The case should therefore assert arithmetic and reason wording, while recording the contextual questions necessary for review.

Counterexample variations include incoming-only activity, no activity, equal flows with a documented expected business pattern, and equal flows with incomplete history. Empty activity should produce an undefined ratio. Incomplete history should affect eligibility according to the declared policy; it should not be relabeled complete for convenience.

## Worked temporal example

Let cutoff be `2026-10-28T12:00:00Z`. Event A occurred one hour earlier and was available at `11:30Z`. Event B occurred one day earlier but was available the next day. Both amounts are 100 synthetic units.

At cutoff, the eligible total is 100. Replaying after B becomes available can produce 200 for a sufficiently broad window. The two results are both correct for their knowledge cutoffs. Replacing B’s availability with occurrence time would erase the difference and contaminate a historical evaluation.

## Worked missing-evidence example

Suppose observed groups contribute a lower bound of 22 and optional unknown evidence could add up to 12 after group caps. The interval is `[22,34]`. With illustrative band minima at 0, 30, and 60, it crosses a boundary and must produce `REVIEW_REQUIRED`. This is arithmetic uncertainty about a configured index, not statistical uncertainty about criminal behavior.

If optional unknown evidence can increase 22 only to 28, the interval remains within one band. The engine may report that bounded band while keeping `score=null`. If the missing factor is mandatory, it still abstains. Fixtures must exercise these distinct paths.

## Coverage dimensions

Build a coverage matrix across mechanisms and dimensions, rather than creating many nearly identical scenarios:

| Dimension | Variations worth covering |
| --- | --- |
| History | New relationship, full retention, truncated retention, late arrivals |
| Activity | Empty, zero-value, sparse, concentrated, diverse, one-way, balanced |
| Expectation | Known positive, zero, missing, stale meaning |
| Jurisdiction evidence | Complete mapping, partially missing, all missing, changed version |
| Profile | Observed low/high severity, missing required, missing optional, stale |
| Policy | Sum/max aggregation, saturation, increasing/decreasing ramp, threshold equality |
| Review route | True, false, unknown; all independent of index band |
| Data integrity | Duplicate, collision, foreign customer, future row, malformed numeric value |

Pairwise combinations can uncover interactions economically, but do not guarantee coverage of all higher-order failures. Reserve explicit cases for critical combinations such as missing required evidence plus a low provisional index, or an unresolved screening route plus a high-confidence observed score.

## Metamorphic relations

Useful relations include: permuting eligible input rows preserves the result; adding an unavailable event does not change eligible aggregates; changing only an opaque identifier should not change arithmetic unless it changes grouping/tie semantics; and increasing an observed severity cannot reduce a nonnegative monotone group contribution under fixed data and policy. A comparison that changes eligibility, missingness, or a denominator needs a more careful relation.

For a maximum group, increasing a non-leading factor may leave the group contribution unchanged until it exceeds the leader. For a saturated sum group, increases can have no effect. These are declared policy properties, not bugs. Explanation tests should make that behavior visible.

## Compound hypotheses and unknown evidence

[patterns.py](../src/crw/patterns.py) evaluates declarative conditions using `all`, `any`, and `not`. Leaves compare a known feature with a declared threshold and can require event support and full history. Missing or ineligible evidence evaluates as `UNKNOWN`. Conditions do not execute arbitrary code and do not add score points or authorize an action.

| A | B | `all(A,B)` | `any(A,B)` |
| --- | --- | --- | --- |
| TRUE | TRUE | TRUE | TRUE |
| TRUE | FALSE | FALSE | TRUE |
| TRUE | UNKNOWN | UNKNOWN | TRUE |
| FALSE | FALSE | FALSE | FALSE |
| FALSE | UNKNOWN | FALSE | UNKNOWN |
| UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |

Negation swaps TRUE/FALSE and preserves UNKNOWN. For example, a known false cash-exposure predicate makes an `all` hypothesis false even when volume evidence is unknown. That conclusion means the specified compound condition is not established under its definition; it does not establish low customer risk. A true `any` hypothesis similarly does not make every underlying predicate known.

Each reference hypothesis carries a benign explanation, next evidence to obtain, and an interpretation limit. Review those fields alongside the evaluation tree. A pattern name is a concise search aid, not a typology finding or a case conclusion.

## Coverage reporting and interpretation

Report generated case counts and outcomes from the actual run. Include case IDs, assertion types, failures, skipped cases and reasons, and code/policy hashes. A large case count is not a claim of exhaustive typology coverage. Repeated amounts or permutations expand structural testing but do not add distinct real-world risk mechanisms.

Use [the scenario workpaper](../templates/scenario-workpaper.md). A new typology should bring a falsifiable mechanism, a benign counterexample, a missing-evidence case, and a clear boundary on what the observable pattern can establish.
