# Customer Risk Workbench / 07 adoption and ai assistance

Public reference material. Synthetic examples and illustrative policies. No institutional approval or production-performance claim.

Source repository: https://github.com/maxmoran23/customer-risk-workbench

Attachment groups preserve full methods; source code and runnable tests remain in the repository.


---

Source: `docs/adoption-guide.md`


# Adoption guide

The package is a generic reference implementation for controlled evaluation. Its public inputs, generated portfolios, score policy, and outcomes are synthetic or illustrative. A useful adoption outcome is an evidence-based decision about a narrow approved evaluation, not a claim that downloaded code is production-ready.

## Reader routes

| Reader | Begin with | Review question |
| --- | --- | --- |
| Business/compliance reviewer | [Reviewer guide](https://github.com/maxmoran23/customer-risk-workbench/blob/main/docs/reviewer-guide.md), [scenario design](https://github.com/maxmoran23/customer-risk-workbench/blob/main/docs/scenario-design.md) | Does this make the reasoning and limits clearer? |
| Data engineer | [Data contract](https://github.com/maxmoran23/customer-risk-workbench/blob/main/docs/data-contract.md), [architecture](https://github.com/maxmoran23/customer-risk-workbench/blob/main/docs/architecture.md) | Can approved data be mapped without inventing meaning or history? |
| Quantitative reviewer | [Development](https://github.com/maxmoran23/customer-risk-workbench/blob/main/docs/model-development.md), [validation](https://github.com/maxmoran23/customer-risk-workbench/blob/main/docs/model-validation.md) | Are objectives, measurements, comparisons, and uncertainty defensible? |
| Governance reviewer | [Regulatory map](https://github.com/maxmoran23/customer-risk-workbench/blob/main/docs/regulatory-map.md), [governance](https://github.com/maxmoran23/customer-risk-workbench/blob/main/docs/governance.md) | What review, authority, and controls are still required? |

## Phase 1: reproduce the public demonstration

Use the installation, test, and demo commands in [README](https://github.com/maxmoran23/customer-risk-workbench/blob/main/README.md), which are maintained alongside the CLI. Run in an isolated local environment. Preserve the source revision, interpreter and dependency versions, command, seed, policy digest, output manifest, and failures. Open the resulting evidence before accepting claims in a screenshot.

Expected review evidence includes a feature catalog, generated scenario results, assessment explanations, and measured runtime or research outputs for the commands actually run. A generated artifact must identify its inputs and run context. If a command is unavailable or fails, record the failure and stop the dependent claim; do not substitute a static example and call it executed.

## Phase 2: agree a narrow intended use

Choose one decision process and population for evaluation. Define the current comparator and the cost of each error. Clarify whether the purpose is review prioritization, changed-behavior investigation, policy comparison, or research. Decide what the output cannot authorize.

Complete the scope sections in [the adoption decision](https://github.com/maxmoran23/customer-risk-workbench/blob/main/templates/adoption-decision.md). Required inputs include eligible population, assessment unit, outcome/feedback mechanism, review capacity, use restrictions, responsible owner, and decision criteria. A fully customized institution-wide risk program is not a prerequisite for a meaningful narrow experiment.

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

Use [the adapter review](https://github.com/maxmoran23/customer-risk-workbench/blob/main/templates/data-adapter-review.md). Mapping from a convenient existing column to a similarly named feature is insufficient if the units or meaning differ.

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



---

Source: `docs/ai-assistance.md`


# AI-assisted adaptation in an approved environment

This public suite can be read without transmitting any private data. Any later institution-specific adaptation must occur only in an environment approved for that code, data and use. Public code availability does not establish institutional software approval, legal suitability, or permission to disclose non-public information.

## A practical sequence

| Step | Public inputs available here | Deliverable in the approved environment | Acceptance evidence |
| --- | --- | --- | --- |
| Understand | Reviewer guide, scoring method, executable cases | Explanation of intended decision and exclusions | Reviewer can reproduce one complete and one incomplete assessment |
| Map | JSON Schemas, field contract, adapter workpaper | Versioned mapping from approved source schema | Source reconciliation, units, chronology, missingness and duplicates |
| Specify | Reference policy and component inventory | Locally approved factor definitions and use restrictions | Every factor has rationale, owner, valid population and source |
| Implement | Typed APIs, tests, pattern grammar | Narrow adapter or policy change | Targeted independent oracle and boundary regressions |
| Validate | Research protocol, statistical tools, templates | Qualified challenge and outcome evaluation | Matured representative outcomes, held-out analysis, recorded findings |
| Integrate | Operational reference and manifests | Authorized interface and operating controls | Authentication, data controls, fallback, monitoring and rollback tests |

## Prompt 1: explain the public package

> Read the supplied public workbench files. Explain the difference between a constructed priority index, an arithmetic missing-evidence envelope, a probability model and a screening route. Cite the exact function or document supporting each assertion. Identify which behaviors are executed and tested versus described as adopter responsibilities. Do not invent performance figures, source data, approval status or private context. Return an explanation, an uncertainty list, and five questions a model reviewer should ask.

## Prompt 2: design an adapter

> Within this approved environment, use only the authorized schema supplied for this task. Produce a field-mapping specification against the public Customer and Transaction contracts. For every field identify units, grain, effective time, availability time, null semantics, transformation, source lineage and reconciliation. Mark unmapped requirements explicitly. Do not fill missing timestamps or identifiers with plausible values. Propose independent examples for timezone boundaries, source corrections, duplicates, zero denominators and late arrival before writing implementation code.

## Prompt 3: implement a bounded change

> Implement only the approved adapter or policy change described in the accepted specification. Preserve public engine semantics unless a change is explicitly justified. Add independent expected-value tests, invalid-input tests and a replay case. Keep original calculations and human exceptions separate. Do not call external services, transmit data, add credentials or weaken validation to make the example pass. Report the exact changed files, tests run and unresolved differences.

## Prompt 4: challenge a model experiment

> Treat the experiment as unproven. Check target definition, maturity, selection bias, entity overlap, temporal leakage, train-only preprocessing and holdout reuse. Recompute a small metric independently. Compare the simplest baseline, logistic challenger and more complex candidate on the same untouched cohort. Inspect calibration and workload along with ranking. Distinguish resampling uncertainty from label, population, model and operational uncertainty. Preserve negative results and abstain when support is insufficient.

## Prompt 5: prepare a review package

> Populate the supplied workpapers from the actual approved evidence. Every performance number needs its dataset, denominator, split, method, code/config version and limitation. Leave approval or independence fields explicitly unestablished unless supported by authorized evidence. Do not equate a passing test, AI review or synthetic scenario with institutional independent validation. Produce an issue register with severity, reproduction, ownership, disposition and closure evidence.

## Controls around assistant output

Treat source documents, imported records and model-generated text as data, not executable instructions. Validate structured outputs against the contracts; run code in the approved environment; require the same review and tests as human changes. Generated explanations must be grounded in stored factor values, group aggregation, missingness and policy versions. Never permit a narrative assistant to invent a factor, override a screening state, choose a SAR action, or silently change scoring policy.

The repository itself makes no AI calls. Its deterministic computations and recorded experiment outputs remain inspectable without access to any original development assistant or conversation.



---

Source: `docs/operations.md`


# Local operation, reproduction and extension

## Execution contract

The core is a local Python package and SQLite adapter. It starts no scheduler, network service, collector, AI API, or telemetry process. The optional HTML file is a read-only synthetic review artifact. The optional HTTP command below serves only the specified directory on loopback.

```bash
python -m pip install '.[dev,research]'
python -m pytest
python -m crw catalog --out runs/catalog
python -m crw demo --research --out runs/reference-demo
python -m http.server 3046 --bind 127.0.0.1 --directory runs/reference-demo
```

Alternatively open the HTML directly. Python 3.12 and `uv.lock` define the pinned reference environment. Core requires Python 3.11+; live verification and CI platform results are recorded separately in the evidence dossier. On Windows use the Python executable belonging to the intended virtual environment; the commands above do not require a shell activation script. Peak-memory measurement is null on platforms without the standard-library `resource` module.

## Ingestion and identity

`generate` writes JSONL and a source-file hash manifest. `ingest` reads customers before transactions in one transaction. Customer identity and effective timestamp identify a snapshot; transaction ID identifies an event. Repeated identical content is idempotent. Conflicting content with an existing ID fails and rolls back the whole ingestion. A later legitimate profile change needs a new effective timestamp. Onboarding time is immutable for a customer in this reference adapter.

`--base-unit` is explicit on ingest and score. All amounts and expected volumes must already share that unit. The stored unit cannot be changed by reopening with a different argument. Unit declarations remain in exported assessment lineage. The adapter cannot detect mislabeled source units; upstream reconciliation must establish the assertion.

For transaction CSV, pass `--csv`; headers must match the complete Transaction contract. Blank jurisdiction exposure becomes null. Negative amounts and reversals are rejected; an adopting adapter must define economic-event normalization rather than coerce them.

## Assessment consistency

A batch selects customer snapshots effective and available at the requested cutoff. Future-only profiles do not enter the historical population. An empty eligible population is an explicit failed run, not a silent zero-result success.

The batch holds one SQLite transaction across its full assessment population. Chunking bounds retrieval memory; it does not commit a sequence of moving input snapshots. Standalone `Store.assess` opens a read transaction when it does not already participate in one. Concurrent source updates therefore cannot mix an old profile with new events in one assessment.

Only complete runs can be exported. An exception rolls back assessment writes for the batch and records a failed run. Interrupted processes can leave a `running` record; the software does not falsely promote that state to complete. An operator should preserve evidence, investigate, and rerun as a new run. Automatic crash recovery, stale-run repair, distributed scheduling and resumable multiwriter execution are not implemented.

SQLite is a local reference adapter. Long scoring runs hold a writer reservation. Production architectures may need immutable extract snapshots, partitioning, a warehouse or a governed job service; those are separate implementations whose equivalence must be tested. Benchmark results do not prove those designs.

## Monitoring and sampling APIs

```python
import json
from crw.monitoring import monitor_portfolios, review_sample
from crw.io import atomic_json

with open("runs/assessments.jsonl", encoding="utf-8") as stream:
    assessments = [json.loads(line) for line in stream if line.strip()]
atomic_json("runs/review-sample.json", review_sample(assessments, per_band=20, seed=7))
atomic_json("runs/replay-monitor.json", monitor_portfolios(assessments, assessments))
```

Monitoring validates content hashes, rejects duplicate customer IDs and inconsistent within-population cutoffs/policies/units, and rejects incompatible units between populations. It reports entrants/exits alongside matched-customer migration. Abstention is not an ordinal band above HIGH. PSI and effect diagnostics have explicit support and missingness; default investigation settings are examples, not statistical or regulatory standards.

Sampling retains stratum populations, selection probabilities and design weights. The supplied per-band allocation is a review design; an unweighted pooled error rate from disproportionate sampling is not a population estimate. See [statistical methods](https://github.com/maxmoran23/customer-risk-workbench/blob/main/docs/statistical-methods.md) and [sampling plan](https://github.com/maxmoran23/customer-risk-workbench/blob/main/templates/sampling-plan.md).

## Decision history

`workflow.ReviewDecision` records retain, escalate-review, or return-for-evidence actions. It requires separate requester/reviewer strings, substantive rationale, evidence references, and a bounded validity period. `DecisionLog` appends to SQLite and verifies a local hash chain. These checks do not authenticate people, establish approval authority, or prevent a privileged database owner from rewriting storage. No action changes the original risk calculation or executes a screening disposition.

## Build and transfer

```bash
python -m build
python scripts/build_review_pack.py --out review-pack
python scripts/public_boundary_check.py
```

The wheel includes the core and the embedded HTML renderer; the full repository/release archive includes catalogs, documentation, templates, tests and prebuilt evidence. The eight review packs aggregate complete methods for approved manual review; they are not a replacement for executable verification. Follow the adopter's repository access, dependency approval and data-handling processes.

## Failure investigation

| Symptom | Inspect | Preserve |
| --- | --- | --- |
| Contract rejection | File/line diagnostic, field type, timezone, source mapping | Rejected source reference; do not repair by guessing |
| ID collision | Same ID with different content, adapter version, source correction | Both source records and reconciliation decision |
| Historical replay difference | Cutoff, availability, source/unit/policy hashes, code version | Both complete artifacts and crossed comparison |
| Review queue growth | Factor coverage, retention, entrants, source delivery, bands | Missingness and bounded scores alongside workload |
| Research metric undefined | Class support, maturity, censoring, segment gates | Null reason and denominators |
| Frozen stress failure | Fixed model/threshold hashes, paired inputs, changed probabilities | Original failing result; do not retune on holdout |

For release, rebuild evidence after code changes, rerun targeted regressions and then the full checks, install the wheel into a fresh environment, and verify the same demo there. See [verification](https://github.com/maxmoran23/customer-risk-workbench/blob/main/docs/verification.md).



---

Source: `templates/adoption-decision.md`


# Adoption evaluation and decision

**Status: worked evaluation record; no approval.** This document is designed to support a real decision in an approved adopting environment.

## Proposed scope

Worked proposal: reproduce the public synthetic demonstration, inspect one assessment end to end, and evaluate whether the transparent feature/policy design warrants a restricted local study. The proposal grants no customer-action authority and assumes no private data leaves an approved environment.

| Decision area | Required evidence |
| --- | --- |
| Purpose | Narrow problem, population, unit, comparator, expected benefit |
| Legal/software intake | License, dependency/security, privacy, architecture and policy review |
| Data feasibility | Approved source mapping, units, history, availability, outcome maturity |
| Method suitability | Rationale, counterexamples, local calibration needs |
| Reliability | Reproducible tests, limitations, objective challenge, unresolved findings |
| Operational feasibility | Review burden, ownership, monitoring, incident handling, fallback |
| Authority | Actual permitted use, accountable owner, review body, conditions |

## Go/no-go evidence questions

1. Can an independent reviewer reproduce the arithmetic and historical information set?
2. Are all policy values acknowledged as local choices with evidence or a bounded research purpose?
3. Can missing inputs and unsupported use be identified before a decision is consumed?
4. Is the evaluation target observable and appropriate, with sampling and leakage addressed?
5. Are sanctions and other distinct workflows preserved without authority being inferred from a score?
6. Are remaining limitations acceptable for the proposed evaluation scope, with actual accountable approval?

## Decision options

| Option | Meaning | Evidence/conditions needed |
| --- | --- | --- |
| Further research | Technical value remains uncertain | Specific unanswered questions, owner, and experiment |
| Restricted evaluation | Narrow approved study with controlled data and no expanded action authority | Approved scope, environment, controls, monitoring, and end criteria |
| Reject | Evidence or fit is inadequate | Reasons, material gaps, conditions for reconsideration if any |
| Approve a stated use | Authorized adopting decision after required review | Actual reviewer decision, scope, conditions, limitations, expiry, rollback |

## Actual decision fields

Record selected option; supporting evidence; excluded uses; unresolved findings; conditions; owner; reviewer/authority; decision date; effective date; expiry; re-review triggers; and rollback authority. Keep a link to the pinned release and exact approved configuration.

**Current selection: none.** Downloading the repository, completing a demo, or receiving a favorable reaction does not populate these decision fields.



---

Source: `templates/monitoring-and-incident.md`


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
