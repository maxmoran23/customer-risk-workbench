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
