# Regulatory reference map

**Reference date: 2026-10-28.** This map supports review of a generic research workbench. It does not establish that a particular implementation satisfies law, supervisory expectations, institutional policy, or an approved use. The executable configuration contains illustrative engineering choices.

The machine-readable register is [sources.json](sources.json). It distinguishes publication dates, retrieval dates, authority, source status, and retrieval limits. A retrieved page can remain online after its guidance is superseded; availability alone does not establish currency.

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

An adopting organization must make its own classification. Names such as `score`, `model`, and `AI` are insufficient evidence. Record actual construction, assumptions, use, materiality, and reviewer rationale in [the classification template](../templates/component-classification.md).

## Change and supersession handling

For each source update, record: old source ID/version; new source; legal status; affected claim; affected configuration or document; test impact; reviewer; and effective implementation date. Never silently edit historical assessments to reflect a newer policy.

The [April 2026 AML/CFT program NPRM fact sheet](https://www.fincen.gov/system/files/2026-04/Program-NPRM-FactSheet.pdf) is a **proposal reference**. It superseded a prior proposal; this repository does not represent its proposed changes as effective law. The targeted source review did not establish a complete docket history through every later administrative action.

## Evidence limits

The FDIC announcement and FIL identification were available as official indexed text, while direct opening returned HTTP 403 during research. Substantive guidance is linked to the fully retrieved joint Federal Reserve document. The live FFIEC page did not expose a reliable revision date; its retrieval date is recorded without inventing a publication date. No regulator has reviewed or approved this repository.
