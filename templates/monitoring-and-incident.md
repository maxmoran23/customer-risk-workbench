# Monitoring and incident plan

**Status: worked operating design; no live monitoring or incident service is enabled.** The package does not schedule external monitoring.

## Monitoring measures

| Measure | Interpretation | Investigation evidence |
| --- | --- | --- |
| Input rejects/collisions | Data or adapter contract failure | Source changes, rejected rows, ingestion atomicity |
| Missingness and coverage | Evidence availability change | Feature/segment support and delivery watermark |
| Band and abstention migration | Changed data, policy, or population | Paired cases and reason deltas |
| Route-state distribution | Workflow evidence change | True/false/unknown counts and source mapping |
| Feature drift | Distribution difference | Fixed reference, binning, smoothing, population mix |
| Matured outcome metrics | Performance against defined target | Labels, delay, support, selection, uncertainty |
| Queue and review burden | Operational capacity | Arrivals, completion, aging, reviewer feedback |

Set thresholds, owners, and response times in the adopting environment based on use and measured baseline behavior. This template deliberately supplies no universal PSI, accuracy, or queue-size approval threshold.

## Worked incident

Synthetic incident: an adapter version changes the meaning of expected monthly volume while leaving the field name unchanged. Ratio calculations remain syntactically valid, but the prior policy interpretation becomes unreliable.

Response sequence:

1. Identify affected adapter version, records, assessments, and cutoffs; preserve original inputs and outputs.
2. Constrain the affected use and communicate the specific limitation to authorized operators.
3. Confirm old/new field meaning and source reconciliation; do not repair by arbitrary rescaling.
4. Implement and test the agreed mapping with independent examples.
5. Replay affected calculations under correct historical semantics and compare decisions.
6. Review any downstream effects in the approved environment; retain incident and decision history.
7. Close only after evidence establishes remediation, residual limitations, and monitoring changes.

## Incident record

Required fields: incident ID; detection time/method; reporter; affected versions/populations; immediate containment; evidence; root cause; corrective action; replay scope; retest; communication; owner; reviewer; closure criteria; and residual risk.

## Escalation and rollback

Define who can suspend an assessment workflow, revert policy, restore data, or authorize reprocessing. Distinguish reversible software rollback from irreversible downstream actions. Keep an approved fallback that preserves evidence and abstains where necessary. A fallback must not silently label unscored customers low risk.

**Current operational status: design only.** Actual deployment, access controls, escalation contacts, and service levels require adoption evidence.
