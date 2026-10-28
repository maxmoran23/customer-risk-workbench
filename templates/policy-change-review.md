# Policy change review

**Status: synthetic worked proposal; no approved parameter change.** Every threshold and weight in the example is illustrative.

## Proposed change

Worked proposal: change a behavior group from capped summation to capped maximum aggregation while leaving factors, data, cutoff, and all other groups unchanged. The proposed rationale is to reduce repeated contribution from overlapping windows. The trade-off is reduced recognition of distinct concurrent behaviors.

| Required field | Evidence request |
| --- | --- |
| Old/new policy IDs and hashes | Exact canonical configurations |
| Scope | Affected populations, factors, routes, and uses |
| Rationale | Mechanism, alternatives, assumptions, counterexamples |
| Comparison population | Frozen eligible set and data manifest |
| Predeclared acceptance criteria | Migration, abstention, workload, and failure tolerances justified for intended use |

## Worked arithmetic

Two eligible factor contributions are `12` and `8`, with group cap `15`. The old sum group contributes `15`; the maximum group contributes `12`. The total index falls by `3` if all other contributions are unchanged. This is a policy arithmetic effect, not evidence that the customer became less risky.

If the two factors represent genuinely independent mechanisms, the reduction may lose information. If both represent the same recent events, it may avoid redundant contribution. Review both cases before selecting the policy.

## Required comparison

| Analysis | Required detail |
| --- | --- |
| Paired assessment | Same customers and cutoffs; unchanged cases retained |
| Migration | Old/new bands including `REVIEW_REQUIRED`; counts and denominators |
| Score/bound changes | Fully observed scores separate from provisional bounds |
| Explanations | Changed group leaders, saturation, and dominant reasons |
| Support | Missingness and window coverage by segment |
| Workflow | Queue capacity, unresolved routes, changed review burden |
| Reversibility | Reproduce old policy and restore prior operating version |

If data also changed, use the four crossed policy/data combinations described in [governance](../docs/governance.md). Do not attribute the combined delta to policy alone.

## Decision record

Record accepted/rejected scope, evidence, reviewer, actual decision date, conditions, rollback trigger, and next review. **Current decision: proposed for evaluation only.** A new Git commit or policy hash is not policy approval.
