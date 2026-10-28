# Customer Risk Workbench / 06 governance and regulation

Public reference material. Synthetic examples and illustrative policies. No institutional approval or production-performance claim.

Source repository: https://github.com/maxmoran23/customer-risk-workbench

Attachment groups preserve full methods; source code and runnable tests remain in the repository.


---

Source: `docs/regulatory-map.md`


# Regulatory reference map

**Reference date: 2026-10-28.** This map supports review of a generic research workbench. It does not establish that a particular implementation satisfies law, supervisory expectations, institutional policy, or an approved use. The executable configuration contains illustrative engineering choices.

The machine-readable register is [sources.json](https://github.com/maxmoran23/customer-risk-workbench/blob/main/docs/sources.json). It distinguishes publication dates, retrieval dates, authority, source status, and retrieval limits. A retrieved page can remain online after its guidance is superseded; availability alone does not establish currency.

## Current reference frame

| Reference | Verified source point | Application to this repository |
| --- | --- | --- |
| [SR 26-2](https://www.federalreserve.gov/supervisionreg/srletters/sr2602.htm), April 2026 | Replaces SR 11-7 and SR 21-8. | Historical references must be marked superseded. |
| [Joint model-risk guidance](https://www.federalreserve.gov/supervisionreg/srletters/SR2602a1.pdf) | Discusses purpose, testing, validation, monitoring, governance, and third-party products. | A review framework; no assertion of certification. |
| [OCC Bulletin 2026-13](https://www.occ.gov/news-issuances/bulletins/2026/bulletin-2026-13.html) | Scope excludes some deterministic tools and generative/agentic AI; guidance is non-prescriptive. | Classify components by actual design and use. Scope exclusion does not remove software controls. |
| [FFIEC CDD overview](https://bsaaml.ffiec.gov/manual/AssessingComplianceWithBSARegulatoryRequirements/02) | Customer profiles should reflect pertinent information and material variation. | Preserve context and evidence quality alongside the index. |
| [2022 joint CDD statement](https://www.federalreserve.gov/frrs/regulations/joint-statement-on-the-risk-based-approach-to-assessing-customer-relationships-and-conducting-customer-due-diligence.htm) | Customer types do not imply uniform risk. | Test benign cases and combinations, not type-based exclusion. |
| [FinCEN CDD FAQs](https://www.fincen.gov/resources/statutes-and-regulations/cdd-rule-faqs), including 2026 updates | No prescribed scoring categories or categorical update schedule. | Bands and intervals are local policy choices. |
| [FIN-2026-R001](https://www.fincen.gov/system/files/2026-02/FinCEN-Order-CCDExceptiveRelief.pdf) | Optional relief changes repeated-account ownership collection triggers. | Ownership workflow must preserve ongoing risk-based review. |
| [2026 CTA final rule](https://www.govinfo.gov/content/pkg/FR-2026-08-14/pdf/2026-16576.pdf) | Corporate reporting and financial-institution CDD serve different purposes. | Never derive a CDD exemption from CTA reporting status. |
| [FATF Recommendations, June 2026](https://www.fatf-gafi.org/content/dam/fatf-gafi/recommendations/fatf-recommendations-2012.pdf) | International standards address proportionate measures and CDD. | Local law and approved policy determine implementation. |
| [FATF banking guidance](https://www.fatf-gafi.org/en/publications/Fatfrecommendations/Risk-based-approach-banking-sector.html), 2014 | Live page warns that later revisions are not incorporated. | Background reference, supplemented by current standards. |
| [FATF financial-inclusion guidance](https://www.fatf-gafi.org/en/publications/Financialinclusionandnpoissues/guidance-financial-inclusion-aml-tf-measures.html), 2025 | Addresses proportionality and financial inclusion. | Review unjustified exclusion and weak proxies. |
| [OFAC framework](https://ofac.treasury.gov/media/16331/download?inline=) and [FAQ 401](https://ofac.treasury.gov/faqs/401) | Sanctions controls and ownership analysis are distinct considerations. | A customer index cannot resolve sanctions permissibility. |

## Interpretation boundaries

These are original design decisions for the workbench:

* A score in `[0,100]` is an index for comparing configured evidence. It is neither a probability nor a legal finding.
* Data completeness describes the evidence available to the calculation. It does not certify that an upstream source is accurate.
* A high score is a reason to review the supporting facts. A low score does not clear sanctions, settle a suspicion, or establish that a customer is safe.
* A rule mapping may be inspired by public typology material without being a regulator-prescribed threshold.
* Human review is part of the intended workflow, but adding a reviewer does not repair an invalid calculation or poor evidence.

## Component classification worksheet

| Component | Preliminary technical characterization | Review question |
| --- | --- | --- |
| Contract and timestamp validation | Deterministic software control | Are all accepted records unambiguous enough to calculate? |
| Window aggregation | Deterministic transformation | Are event time, availability time, coverage, units, and ties correct? |
| Configured additive index | Policy-based decision support | Does the actual design involve statistical/economic/financial theory, and how is it used? |
| Trained statistical challenger | Statistical research model | Is the target meaningful, observable, and appropriate for intended use? |
| Score-to-workflow mapping | Operational policy | Could the action be harmful despite a mathematically correct index? |
| Optional future narrative assistant | Separate AI tool, not implemented scoring authority | What controls prevent unsupported facts or autonomous decisions? |

An adopting organization must make its own classification. Names such as `score`, `model`, and `AI` are insufficient evidence. Record actual construction, assumptions, use, materiality, and reviewer rationale in [the classification template](https://github.com/maxmoran23/customer-risk-workbench/blob/main/templates/component-classification.md).

## Change and supersession handling

For each source update, record: old source ID/version; new source; legal status; affected claim; affected configuration or document; test impact; reviewer; and effective implementation date. Never silently edit historical assessments to reflect a newer policy.

The [April 2026 AML/CFT program NPRM fact sheet](https://www.fincen.gov/system/files/2026-04/Program-NPRM-FactSheet.pdf) is a **proposal reference**. It superseded a prior proposal; this repository does not represent its proposed changes as effective law. The targeted source review did not establish a complete docket history through every later administrative action.

## Evidence limits

The FDIC announcement and FIL identification were available as official indexed text, while direct opening returned HTTP 403 during research. Substantive guidance is linked to the fully retrieved joint Federal Reserve document. The live FFIEC page did not expose a reliable revision date; its retrieval date is recorded without inventing a publication date. No regulator has reviewed or approved this repository.



---

Source: `docs/governance.md`


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

The implemented `ReviewDecision` in [workflow.py](https://github.com/maxmoran23/customer-risk-workbench/blob/main/src/crw/workflow.py) requires different requester/reviewer identifiers, a substantive rationale, evidence references, a creation time, and a later expiry. Allowed dispositions are `retain`, `escalate_review`, and `return_for_evidence`. It does not support clearance, closure, or report filing. Its `active(as_of)` check uses `[created_at, expires_at)`.

`DecisionLog.append` stores a linked content hash in SQLite, rejects changed content under an existing decision ID, and reuses the existing hash for an identical retry. Database triggers reject ordinary update/delete operations; `verify` checks the local chain. These are inspectable local controls, not authenticated approval. String identifiers do not prove distinct people, and a database owner can change storage or controls. The host system must authenticate actors, verify assessment/evidence references, check decision validity before use, and establish any required external integrity assurance.

Governance templates describe the complete review record even where an adopting environment must supply access control, approval workflow, or records management. Do not infer those properties from a completed template or the presence of a local SQLite file.

## Exceptions and unresolved findings

An exception must name the specific control or limitation, reason, affected population, compensating control, authorized duration, and trigger for termination. “Business accepted” without scope or evidence does not resolve a technical failure. High-severity correctness findings should constrain use until addressed; documented acceptance does not change the nature of the defect.

Use [the decision/exception template](https://github.com/maxmoran23/customer-risk-workbench/blob/main/templates/decision-exception.md) and [the finding log](https://github.com/maxmoran23/customer-risk-workbench/blob/main/templates/findings-and-issues.md). Every finding has one of: open, remediation in progress, retest pending, closed with evidence, or accepted limitation with use conditions. Closure needs a reviewer and retest evidence; initial synthetic examples remain unapproved.

## Operating controls outside the package

The adopting environment must establish authentication, authorization, segregation of duties, privacy controls, retention, incident response, deployment security, and institutional approval. Local content hashes and append-only application behavior are useful evidence controls; a user with filesystem/database authority can still alter artifacts. If stronger integrity is needed, use independently governed storage, signed manifests, or another approved control and validate it.

External data feeds and rule changes need explicit ownership, source validation, effective dates, rollback, and historical reproducibility. This repository does not download live screening lists or operate scheduled monitoring.

## Governance evidence pack

The pack should contain scope, component classification, policy decision, adapter review, developmental tests, objective challenge, open findings, release/replay manifest, monitoring plan, and adoption decision. Link existing evidence rather than copying outcomes into multiple documents that can drift apart. The [reviewer guide](https://github.com/maxmoran23/customer-risk-workbench/blob/main/docs/reviewer-guide.md) provides an ordered reading route.



---

Source: `templates/component-classification.md`


# Component classification and inventory record

**Status: worked illustration; no classification approval.** Replace the example only in an approved adopting environment. Retain the reasoning, evidence, and actual reviewer decision.

## Worked component

| Field | Synthetic example |
| --- | --- |
| Inventory ID | `DEMO-COMP-001` |
| Component | Configured customer review-priority index |
| Construction | Piecewise-linear severity transforms; capped sum/max groups |
| Inputs | Normalized profile evidence and time-window aggregates |
| Output | Index bounds, band/gates, contribution record, separate routes |
| Intended use | Compare synthetic cases and evaluate review-priority logic |
| Prohibited use | Automatic adverse action, sanctions clearance, criminality probability |
| Technical classification | Deterministic policy calculation; institutional classification unassessed |
| Downstream dependency | Human review demonstration; no external execution |
| Materiality in this exercise | Synthetic research only; no customer impact |

## Classification reasoning

The calculation is deterministic once inputs and policy are fixed. That fact alone does not settle model classification: a deterministic implementation can embody statistical assumptions or fitted parameters. Review actual design history, parameter derivation, and use. A later trained or calibrated version may require a different classification.

An initially low-impact tool can become material if its output determines review queues or other consequential decisions. Reassess classification when purpose, exposure, population, construction, or downstream authority changes. The source framework and scope caveats are in [the regulatory map](https://github.com/maxmoran23/customer-risk-workbench/blob/main/docs/regulatory-map.md).

## Required evidence

| Question | Evidence requested | Decision condition |
| --- | --- | --- |
| What is implemented? | Source revision, policy digest, architecture, feature formulas | Classification reflects actual code and parameters |
| What decisions depend on it? | Use map, output consumers, permitted actions | No undisclosed customer-action authority |
| How were parameters selected? | Expert rationale, experiment history, fitted parameter lineage | Statistical and judgmental elements distinguished |
| What can fail together? | Shared input/feature/model dependency inventory | Aggregate dependencies considered |
| Who owns review? | Named owner and actual authorized reviewer in approved environment | Accountability accepted, not inferred |

## Review result fields

Record final classification, rationale, applicable policy, scope restrictions, materiality, review triggers, actual reviewer identity, decision date, and evidence links. **Current result: not assessed.** The worked classification is not a substitute for that decision.



---

Source: `templates/policy-change-review.md`


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

If data also changed, use the four crossed policy/data combinations described in [governance](https://github.com/maxmoran23/customer-risk-workbench/blob/main/docs/governance.md). Do not attribute the combined delta to policy alone.

## Decision record

Record accepted/rejected scope, evidence, reviewer, actual decision date, conditions, rollback trigger, and next review. **Current decision: proposed for evaluation only.** A new Git commit or policy hash is not policy approval.



---

Source: `templates/decision-exception.md`


# Decision and exception record

**Status: synthetic worked record; no approval or operational exception is granted.** Preserve the original assessment separately.

## Worked situation

A synthetic assessment has `score=null`, provisional index `22`, and bounds `[22,28]`. One optional factor is unavailable, but the interval lies in one illustrative band. A reviewer may decide to request evidence or conduct a scoped manual review. They must not rewrite the score to `22` and describe it as fully observed.

| Field | Required content |
| --- | --- |
| Decision ID | Unique opaque reference |
| Assessment reference | Exact assessment hash, customer ID, cutoff, policy hash |
| Requested action | Concrete review action within the authorized scope |
| Reason | Facts and evidence supporting the action |
| Unresolved information | Missing factors, source issues, assumptions |
| Requester and reviewer | Actual accountable identities in approved environment |
| Decision time | Timezone-aware timestamp |
| Validity/expiry | Explicit period or event trigger |
| Supersession | Previous decision reference and reason, preserving history |

## Exception analysis

| Question | Worked interpretation |
| --- | --- |
| What is being excepted? | No exception is needed merely to acknowledge an incomplete bounded band; an exception would need a specific control/use being bypassed |
| What remains unknown? | The missing optional factor and any source-quality limitation |
| What cannot be changed by approval? | Historical evidence availability, arithmetic result, or legal obligations |
| What is the compensating control? | Defined additional review with evidence and accountable owner, if authorized |
| What ends the exception? | Expiry, evidence arrival, changed risk, or explicit superseding decision |

## Screening boundary

An unresolved screening route must be handled through the separate authorized screening process. A customer-risk exception cannot clear a hit, determine a license, or change a legal disposition. `FALSE` and `UNKNOWN` route values are also not clearance statements.

## Recording and integrity

Store the decision alongside, not inside, the original calculation. A later record can supersede an earlier decision without deleting it. Application-level append behavior alone does not provide authenticated approval or tamper-proof storage; adopting controls must establish those properties where needed.

**Current decision: not made.** Required completion evidence: actual authority, supporting documents, timestamp, conditions, expiry, and record-integrity control.
