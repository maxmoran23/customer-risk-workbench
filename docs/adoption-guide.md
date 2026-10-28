# Adoption guide

The package is a generic reference implementation for controlled evaluation. Its public inputs, generated portfolios, score policy, and outcomes are synthetic or illustrative. A useful adoption outcome is an evidence-based decision about a narrow approved evaluation, not a claim that downloaded code is production-ready.

## Reader routes

| Reader | Begin with | Review question |
| --- | --- | --- |
| Business/compliance reviewer | [Reviewer guide](reviewer-guide.md), [scenario design](scenario-design.md) | Does this make the reasoning and limits clearer? |
| Data engineer | [Data contract](data-contract.md), [architecture](architecture.md) | Can approved data be mapped without inventing meaning or history? |
| Quantitative reviewer | [Development](model-development.md), [validation](model-validation.md) | Are objectives, measurements, comparisons, and uncertainty defensible? |
| Governance reviewer | [Regulatory map](regulatory-map.md), [governance](governance.md) | What review, authority, and controls are still required? |

## Phase 1: reproduce the public demonstration

Use the installation, test, and demo commands in [README](../README.md), which are maintained alongside the CLI. Run in an isolated local environment. Preserve the source revision, interpreter and dependency versions, command, seed, policy digest, output manifest, and failures. Open the resulting evidence before accepting claims in a screenshot.

Expected review evidence includes a feature catalog, generated scenario results, assessment explanations, and measured runtime or research outputs for the commands actually run. A generated artifact must identify its inputs and run context. If a command is unavailable or fails, record the failure and stop the dependent claim; do not substitute a static example and call it executed.

## Phase 2: agree a narrow intended use

Choose one decision process and population for evaluation. Define the current comparator and the cost of each error. Clarify whether the purpose is review prioritization, changed-behavior investigation, policy comparison, or research. Decide what the output cannot authorize.

Complete the scope sections in [the adoption decision](../templates/adoption-decision.md). Required inputs include eligible population, assessment unit, outcome/feedback mechanism, review capacity, use restrictions, responsible owner, and decision criteria. A fully customized institution-wide risk program is not a prerequisite for a meaningful narrow experiment.

## Phase 3: map data in an approved environment

An adopting organization must conduct its own review of open-source licensing, software security, privacy, architecture, model/tool classification, and permitted integration. Those reviews are not performed by this repository. Keep private data, mappings, policy settings, internal labels, and credentials in that approved environment. Do not send them back to the public project.

| Mapping decision | Evidence request | Reject or constrain use when |
| --- | --- | --- |
| Identity | Customer/account relationship and duplicate rules | Different customers can be joined silently |
| Units | Currency/base-unit transformation and reconciliation | Amounts mix incompatible units |
| Time | Event and availability meaning with historical support | Historical knowledge time is fabricated |
| Coverage | Retention boundary, source totals, delivery watermark | Incomplete history is represented as complete |
| Profile evidence | Provenance, effective dates, transformation rationale | Numbers have no interpretable source |
| Outcomes | Label definition, maturity, adjudication, selection | The outcome reproduces the score itself |

Use [the adapter review](../templates/data-adapter-review.md). Mapping from a convenient existing column to a similarly named feature is insufficient if the units or meaning differ.

## Phase 4: calibrate local policy transparently

Review each feature, weight, ramp, group, cap, band, support requirement, and route. The reference policy is a worked design, not a recommended calibration. Remove unsupported features rather than populating them with invented defaults. Distinguish an omitted feature by deliberate design from a required feature that is missing at runtime.

Prespecify sensitivity ranges and a comparison population. Review band migration, abstention, workload, and reason changes. A threshold chosen to fit available review capacity is an operational decision; record that purpose rather than presenting it as a discovered natural risk boundary.

## Phase 5: objective challenge and restricted shadow evaluation

Resolve material calculation and data defects before interpreting effectiveness. Then evaluate the proposed process without giving it customer-action authority. Compare decisions at the same cutoffs and preserve divergent cases for review. Include low scores and abstentions in sampling so the exercise does not examine only the selected queue.

Record disagreement reasons, missing information, analyst burden, and any downstream data leakage. Agreement with the existing process is not automatically correctness; disagreement is not automatically improvement. The reviewer must examine evidence and the intended target.

## Phase 6: a documented decision

The decision record should state: approved scope, rejected scope, outstanding limitations, conditions, monitoring, authority, rollback, re-review triggers, and expiry. A defensible outcome may be further research, a restricted pilot, or rejection. The package does not prefill approval.

Changes in population, source semantics, transaction coverage, target, feature logic, or use require reconsideration. A model validated for one segment does not inherit evidence for a new segment simply because the API accepts it.

## Private customization boundary

Public contributions may include generic bug fixes, synthetic fixtures, and non-sensitive design improvements. Institution-specific policy, outcome labels, real screening hits, customer records, access details, and internal review findings must remain outside the public repository. A generic adapter interface can be published without its private mapping implementation.

## Adoption deliverable

The handoff should contain a pinned source version, environment manifest, public demonstration evidence, mapping review, local policy rationale, development/validation results, limitations, unresolved findings, and the actual authorized decision. Keep the evidence linked and reproducible. File volume is not an acceptance criterion.
