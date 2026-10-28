# Model or decision-tool card

**Status: worked card for the generic reference design; no institutional approval.** Replace versions and evidence references from the actual release under review.

## Identity and purpose

| Field | Reference-design description |
| --- | --- |
| Name | Generic customer review-priority workbench |
| Component type | Deterministic feature/policy engine with separate optional research tools |
| Intended use | Synthetic experimentation, transparent arithmetic, review preparation |
| Assessment unit | Customer at a declared information cutoff |
| Outputs | Index/bounds, bands or review gates, explanations, lineage, separate routes |
| Action authority | None for customer actions, sanctions disposition, or reporting |
| Inputs | Strict normalized profile and transaction records |
| Parameter origin | Illustrative policy choices; not empirically calibrated |

## Construction

Features use event and availability timestamps, retained-history indicators, duration and last-N windows. Policy factors use declared ramps, weights, support requirements, and group sum/max aggregation with caps. Missing factors produce arithmetic bounds; required missing evidence can prevent a final band. Exact runtime details belong in the source revision and policy being reviewed.

## Evidence summary to complete from artifacts

| Evidence | Required reference | Current status |
| --- | --- | --- |
| Software tests | Actual command, environment, revision, results | Refer to release artifact; not asserted here |
| Scenario coverage | Generated case matrix and failures/skips | Refer to executed run |
| Synthetic research | Generator, target, partitions, metrics, uncertainty | Research only if executed |
| Performance | Hardware, workload, runtime, memory, failures | Measured benchmark only if executed |
| Objective review | Actual reviewer, scope, findings, retests | Not granted by this card |
| Operational outcomes | Representative approved evaluation | Not established by public synthetic examples |

## Known limitations

The score is not a probability. The balance proxy does not trace funds. Supplied completeness does not prove source delivery. Normalized profile values require upstream evidence. Synthetic outcomes do not establish real effectiveness. The package lacks the surrounding institutional approval, security, records, and operating controls required for consequential use.

## Conditions and review triggers

Record permitted population, target, environment, workflow, policy version, expiry, and actual authorized owner. Reassess when data meaning, availability, population, algorithm, parameters, label process, dependencies, or downstream authority changes.

Link [limitations](../docs/limitations.md), open findings, the monitoring plan, and the actual adoption decision. **Approval state: not approved by this template.**
