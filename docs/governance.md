# Governance and decision authority

The workbench calculates and records evidence for review. It does not grant approval to deploy, clear sanctions, file a report, or take an adverse customer action. Governance artifacts in this repository are worked examples and evidence requests. They contain no fictional approvals.

## Responsibilities

| Role | Responsibility | Evidence of completion |
| --- | --- | --- |
| Business owner | Define intended use, eligible population, error costs, and review capacity | Signed scope and use restrictions in an approved environment |
| Data owner | Establish field meaning, completeness, availability, retention, and source controls | Adapter reconciliation and lineage evidence |
| Developer | Implement and test the declared design; disclose limitations | Reproducible build and developmental testing |
| Objective reviewer | Challenge design, implementation, and evidence with sufficient independence | Findings, retests, unresolved limitations, disposition |
| Policy approver | Decide parameters, workflow, exceptions, and use conditions | Versioned policy decision with evidence references |
| Operator | Execute the approved process, investigate failures, preserve records | Run manifests, incidents, reconciliation, replay |
| Audit function, if applicable | Assess whether governance and controls operate as designed | Scope-specific assessment; not a substitute for model validation |

Roles describe functions, not mandatory organization charts. Where one person performs multiple functions, disclose the conflict and establish a compensating review. A second automated agent is useful developer challenge; it does not establish institutional reviewer independence.

## Lifecycle and release state

Use explicit states such as research, development, review pending, restricted evaluation, approved for stated use, suspended, and retired. A Git tag or passing test run is a software release, not a governance approval. Approval applies to a particular code/config/data/use combination with conditions and an expiry or review trigger.

| Change | Example | Review considerations |
| --- | --- | --- |
| Data meaning | Adapter changes expected volume from gross to net | Target/features affected; backtest and denominator meaning |
| Feature calculation | Change a window boundary or counterparty mapping | Historical comparability, replay, affected cases |
| Policy | Change a weight, band, group aggregation, or required-evidence flag | Paired migration, sensitivity, workload, justification |
| Model | New target, algorithm, calibration, or training population | Conceptual review, leakage, outcomes, limitations |
| Workflow | Change referral handling or review priority | Authority, escalation, operational burden, failure paths |
| Packaging | Dependency or runtime change | Reproducibility, security, numerical differences |

Classify by impact rather than line count. A one-line boundary change can alter many decisions. A documentation clarification may have no runtime impact but can change how users interpret output.

## Policy provenance

Each policy needs an identifier, version, rationale, owner, declared use, source/assumption register, and a canonical digest. Preserve the exact policy used by each historical assessment. New policy versions should be assessed on the same data/cutoff as the old version before comparing results.

To separate a policy change from a data change, compute the four combinations:

| | Old data | New data |
| --- | --- | --- |
| Old policy | A | B |
| New policy | C | D |

`C-A` isolates policy effect on old data; `B-A` isolates data effect under the old policy. `D-C-B+A` expresses their interaction for a numeric output. A simple `D-A` cannot establish which change caused the difference. For abstentions, compare states and bounds separately rather than subtracting null scores.

## Screening and decisions

Review flags have `TRUE`, `FALSE`, or `UNKNOWN` states. `FALSE` means the configured supplied value did not trigger that route; it is not a sanctions clearance. `UNKNOWN` requires its own operational handling. The reference screening route cannot be neutralized by a lower risk index.

The runtime’s assessment record must remain separate from any later human decision. A decision record should identify the assessment hash, requested action, evidence, accountable actor, reviewer, time, expiry, and any superseded decision. Preserve the original score and policy. A decision cannot retroactively make unavailable evidence observed.

The implemented `ReviewDecision` in [workflow.py](../src/crw/workflow.py) requires different requester/reviewer identifiers, a substantive rationale, evidence references, a creation time, and a later expiry. Allowed dispositions are `retain`, `escalate_review`, and `return_for_evidence`. It does not support clearance, closure, or report filing. Its `active(as_of)` check uses `[created_at, expires_at)`.

`DecisionLog.append` stores a linked content hash in SQLite, rejects changed content under an existing decision ID, and reuses the existing hash for an identical retry. Database triggers reject ordinary update/delete operations; `verify` checks the local chain. These are inspectable local controls, not authenticated approval. String identifiers do not prove distinct people, and a database owner can change storage or controls. The host system must authenticate actors, verify assessment/evidence references, check decision validity before use, and establish any required external integrity assurance.

Governance templates describe the complete review record even where an adopting environment must supply access control, approval workflow, or records management. Do not infer those properties from a completed template or the presence of a local SQLite file.

## Exceptions and unresolved findings

An exception must name the specific control or limitation, reason, affected population, compensating control, authorized duration, and trigger for termination. “Business accepted” without scope or evidence does not resolve a technical failure. High-severity correctness findings should constrain use until addressed; documented acceptance does not change the nature of the defect.

Use [the decision/exception template](../templates/decision-exception.md) and [the finding log](../templates/findings-and-issues.md). Every finding has one of: open, remediation in progress, retest pending, closed with evidence, or accepted limitation with use conditions. Closure needs a reviewer and retest evidence; initial synthetic examples remain unapproved.

## Operating controls outside the package

The adopting environment must establish authentication, authorization, segregation of duties, privacy controls, retention, incident response, deployment security, and institutional approval. Local content hashes and append-only application behavior are useful evidence controls; a user with filesystem/database authority can still alter artifacts. If stronger integrity is needed, use independently governed storage, signed manifests, or another approved control and validate it.

External data feeds and rule changes need explicit ownership, source validation, effective dates, rollback, and historical reproducibility. This repository does not download live screening lists or operate scheduled monitoring.

## Governance evidence pack

The pack should contain scope, component classification, policy decision, adapter review, developmental tests, objective challenge, open findings, release/replay manifest, monitoring plan, and adoption decision. Link existing evidence rather than copying outcomes into multiple documents that can drift apart. The [reviewer guide](reviewer-guide.md) provides an ordered reading route.
