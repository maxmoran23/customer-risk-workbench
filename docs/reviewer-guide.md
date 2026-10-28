# Reviewer guide

The core proposition is inspectability: a reviewer can trace normalized evidence through time-aware features, declared policy, arithmetic bounds, and a separate review workflow. The package also provides research and testing utilities. Its acceptance case rests on executable evidence and explicit limits, not on the number of files.

## A practical review route

| Step | Inspect | Expected understanding |
| --- | --- | --- |
| 1. Purpose | [README](../README.md), [limitations](limitations.md) | What this package can support and what it cannot authorize |
| 2. One assessment | Generated assessment/reason output from the documented demo | How supplied evidence becomes group contributions, bounds, gates, and routes |
| 3. Inputs and time | [Data contract](data-contract.md), [architecture](architecture.md) | Which information was eligible at the cutoff and why |
| 4. Policy mathematics | [Development method](model-development.md), active policy file | How ramps, caps, sum/max groups, and missing evidence behave |
| 5. Challenge | [Validation](model-validation.md), [scenario design](scenario-design.md), actual test report | What was checked and what remains untested |
| 6. Evidence strength | Research/benchmark outputs and their manifests | Which claims are synthetic, measured, inferred, or unavailable |
| 7. Governance | [Regulatory map](regulatory-map.md), [governance](governance.md), [adoption](adoption-guide.md) | What an authorized evaluation would require |

Generated artifact locations and runnable commands are listed by the current README/CLI. Do not treat a static worked example in `templates/` as an executed run.

## Questions worth asking in a technical demonstration

1. **Why did this customer get this result?** Open the reasons, raw feature values, severities, weights, group aggregation, and caps. Show missing factors and the exact policy hash.
2. **What information did the process know at the time?** Show event time, availability time, profile effective/availability timestamps, cutoff, and retained-history coverage.
3. **What happens if information is missing?** Demonstrate a required missing factor, an optional missing factor with a bounded band, and an interval spanning bands.
4. **Are multiple windows double-counted?** Show the reference policy’s maximum aggregation and the factors sharing a group. Explain its trade-off against summation.
5. **Can a low score clear a screening issue?** Show the independent route state and its limited interpretation.
6. **Can the result be reproduced?** Rerun the same data, policy, and cutoff; compare hashes and explain any differences.
7. **Where can the system be wrong?** Start with the counterexamples and limitations, then the open findings and unsupported uses.
8. **Does the research result generalize?** Show target definition, generator or source, splits, support, label maturity, uncertainty, and the exact population to which the claim applies.

## Reading an assessment

| Field | Meaning | Frequent misreading |
| --- | --- | --- |
| `score` | Fully observed index when no gate is active; otherwise null | Probability or automatic disposition |
| `provisional_index` | Arithmetic lower bound from known contributions | Best guess or imputed central value |
| `lower_bound`, `upper_bound` | Missing-evidence policy envelope | Statistical confidence interval |
| `band` | Configured category or `REVIEW_REQUIRED` | A regulator-prescribed category |
| `coverage` | Fraction of configured factors usable | Verified source accuracy or independent evidence count |
| `gates` | Reasons a final category requires review | Optional presentation warnings |
| `review_flags` | Separate configured true/false/unknown route states | Confirmed legal or screening disposition |
| `lineage`, hashes | Reproduction and comparison references | Proof that the source was truthful or storage immutable |

An incomplete assessment can retain one bounded band while `score` remains null. This avoids pretending the exact index is known. A required missing factor still blocks the band even if the arithmetic range is narrow.

## Reviewing the evidence pack

An adequate pack identifies the source revision, environment, policy/config digest, input manifest, cutoff, seed where relevant, invocation, output hashes, and actual results. It distinguishes passed, failed, skipped, and not performed. Research outputs should include denominators and undefined-value reasons. Benchmarks should describe measured workload and hardware.

Trace a small number of cases end to end before reading aggregate results. Include an ordinary case, a high-contribution case, an abstention, a late-arrival case, and a benign counterexample. Verify at least one calculation independently of the engine.

## What adoption does and does not inherit

An adopter can reuse source code, interfaces, test patterns, documentation structure, and synthetic exercises subject to the license. It does not inherit an approved policy, reliable private inputs, population validation, customer-action authority, or institutional approval. Those are evidence and governance tasks in the adopting environment.

Use [the adoption decision](../templates/adoption-decision.md) to record the next defensible step. The template permits further research, restricted evaluation, rejection, and later approval by an authorized reviewer; it does not preselect success.
