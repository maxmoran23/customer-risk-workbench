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

An initially low-impact tool can become material if its output determines review queues or other consequential decisions. Reassess classification when purpose, exposure, population, construction, or downstream authority changes. The source framework and scope caveats are in [the regulatory map](../docs/regulatory-map.md).

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
