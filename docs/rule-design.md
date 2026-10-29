# Rule design for the categorical model

Rules in `crw/rules.py` act on a categorical model's tier after the weighted score is banded. A rule either sets a minimum tier (a floor) or requests a review action without changing the tier (a route). Rules exist because some conclusions should not depend on how a weighted mean happens to land, and because some values matter only in combination. Every rule, weight and tier threshold in the reference configuration is an illustrative assumption.

## Atomic and compound rules

A rule is **atomic** when its condition references exactly one attribute and **compound** when it references two or more. `RuleSet.kind` computes this from the condition, so a rule over one attribute with an `any` of several values is still atomic.

| Question | Atomic rule | Compound rule |
| --- | --- | --- |
| When it is the right tool | A single value should set a minimum tier or a review action regardless of everything else, but an override class is too strong or too broad | A combination of values warrants a tier the weighted mean would not reach, and no single value does |
| Alternative to consider first | Reclassify the value (for example elevator to `override_high`) | Raise a component value's score, if the effect is not specific to the combination |
| Evidence expected | Evidence for the value alone | Evidence for the combination, a connections screen result, and a leg-contribution result |
| Typical failure | Duplicates an override class or another atomic rule | A leg adds parties but not discrimination; the combination is a proxy for a stronger pair |

## Rule record and grammar

A rule set is a JSON object with `ruleset_id`, `version`, `description` and `rules`. Each rule has exactly these fields:

| Field | Requirement |
| --- | --- |
| `id` | Opaque identifier, unique in the set |
| `title` | Text |
| `condition` | Condition object (below) |
| `effect` | `{"type": "floor", "tier": <model tier>}` or `{"type": "route", "action": <nonempty text>}` |
| `evidence` | Nonempty list; every id must exist in the catalog's evidence register |
| `rationale` | Nonblank text |
| `status` | `draft`, `proposed`, `challenged`, `agreed` or `retired` |

A condition is either a leaf or one logical operator:

```json
{"attribute": "source_of_wealth", "in": ["undocumented"]}
{"all": [<condition>, <condition>, ...]}
{"any": [<condition>, <condition>, ...]}
{"not": <condition>}
```

A leaf's attribute must be a catalog attribute and every value in `in` must be one of its normalized values; `in` must be nonempty. An operator object carries exactly one key. `all` and `any` take 1 to 50 operands. The validator rejects conditions nested more than eight levels below the root. Unknown fields anywhere fail validation.

## Four-state evaluation

`evaluate(condition, values, applicable)` returns `TRUE`, `FALSE`, `UNKNOWN` or `NOT_APPLICABLE`. Only `TRUE` fires a rule.

| Construct | Result |
| --- | --- |
| Leaf, attribute not applicable to the party's entity type | `NOT_APPLICABLE` |
| Leaf, applicable attribute missing (null or absent) | `UNKNOWN` |
| Leaf, value present | `TRUE` if the value is in `in`, else `FALSE` |
| `all` | `FALSE` if any operand is `FALSE`; else `NOT_APPLICABLE` if any is; else `UNKNOWN` if any is; else `TRUE` |
| `any` | `TRUE` if any operand is `TRUE`; else `UNKNOWN` if any is; else `NOT_APPLICABLE` if any is; else `FALSE` |
| `not` | Swaps `TRUE` and `FALSE`; `UNKNOWN` and `NOT_APPLICABLE` are preserved |

A business-type condition says nothing about a natural person, so it is `NOT_APPLICABLE` rather than false or unknown, and negation preserves that: `not (listed_status in [listed_regulated_exchange])` does not fire for an individual. In an `all`, a `FALSE` operand still decides the result, so a compound rule whose entity-type leaf is false for a party evaluates `FALSE` for it even when another leg is not applicable. A non-applicable leg never makes a rule fire and never raises an UNKNOWN review flag.

The connections screen's `evaluate_combination` excludes the same parties instead: a non-applicable attribute has no value there, so the row is unobserved ([connections-method.md](connections-method.md)). Leg-contribution figures therefore describe only parties to which every leg applies, while rule simulation counts every party in one of the four states.

## Assessment precedence

`CategoricalModel.assess(party, rules, stage)` applies a fixed order that a reviewer can recompute by hand:

1. **Validate the party.** The entity type must be a catalog entity type; every attribute must be a catalog attribute; every non-null value must be text, a normalized catalog value, and on an attribute that applies to the entity type; an `entity_type` value, if present, must agree with the party's entity type; `pinned`, if present, must be boolean; `outcome`, if present, must be 0, 1 or null.
2. **Weighted mean.** Over weighted attributes that apply to the entity type, each value contributes its score at the chosen stage (`proposed` uses a value's proposal where one exists, else its current assignment). Override classes contribute the scale neutral. A missing value contributes the neutral and is listed. A value with no assignment at the stage fails the assessment. Catalog attributes without a weight do not enter the score but remain available to rules, and their override classes still act in steps 5 and 6. The mean is rounded to nine decimal places before banding, so a score equal to a tier minimum is not demoted by floating-point error.
3. **Abstention.** If the model's `missing` setting is `abstain` and any applicable weighted attribute is missing, the score is withheld (`null`). The catalog's per-attribute `missing` policy does not change the score; it controls the review flag in step 8.
4. **Base tier.** The highest tier whose minimum is at or below the score.
5. **Floors.** Any `override_high` value on an applicable attribute, weighted or not, adds the model's `override_high_tier`. Each non-retired rule evaluating `TRUE` with a floor effect adds its tier. Route rules evaluating `TRUE` are listed in `routes` and do not touch the tier.
6. **Cap.** If any applicable value, weighted or not, is `override_low`, the base tier is capped at the model's `override_low_tier`. Floors from step 5 then apply on top, so an auto-low value never suppresses a trigger or a rule.
7. **Resolution.** The final tier is the higher of the (capped) base tier and the highest floor. If the score was withheld, the final tier is the top tier when the highest floor is the top tier, and `REVIEW_REQUIRED` otherwise.
8. **Review flags.** Each missing applicable weighted attribute whose catalog missing policy is `review` adds `missing_review_attribute:<attribute>`, whatever the tier; under policy `neutral` no flag is added. A rule evaluating `UNKNOWN` never fires. If the final tier is not `REVIEW_REQUIRED` and an UNKNOWN floor rule's tier is above the final tier, the party carries `unknown_rule_could_raise_tier:<rule id>`. Neither flag changes the tier.

`caps_applied` is true whenever an `override_low` value is present and the tier is not `REVIEW_REQUIRED`, including when the cap did not bind. Retired rules are skipped in assessment and in simulation.

## Worked arithmetic

Reference weights: entity type 1.0, nature of business 1.5, occupation 1.0, listed status 1.0, source of wealth 1.2, source of funds 1.5, jurisdiction exposure 1.5, account purpose 1.0. Tier minima: LOW 0, MODERATE 50.5, HIGH 54, VERY_HIGH 58. These are illustrative. The values below were calculated by hand from the reference configuration; the engine returned the same results.

**Case 1, compound floor binds.** A nonbank financial institution (elevator 70) in professional services (neutral 50), unlisted unregulated structure (elevator 65), business-ownership wealth (neutral 50), unrelated third-party funds (elevator 65), domestic only (neutral 50), operating account (neutral 50). Occupation does not apply. Weighted sum `70 + 75 + 65 + 60 + 97.5 + 75 + 50 = 492.5` over weight 8.7 gives 56.609, base tier HIGH. `COMP-01` evaluates TRUE with a VERY_HIGH floor; final tier VERY_HIGH.

**Case 2, missing leg.** The same party with listed status missing. Listed status now contributes neutral 50: `477.5 / 8.7 = 54.885`, base tier HIGH. `COMP-01` is UNKNOWN and does not fire. Final tier HIGH with flags `missing_review_attribute:listed_status` (the reference policy for listed status is `review`) and `unknown_rule_could_raise_tier:COMP-01`. Under `missing: abstain` the same party has a null score; no floor reaches the top tier, so the result is `REVIEW_REQUIRED`, and only the missing-attribute flag is added. An individual missing occupation, whose reference policy is `neutral`, receives no flag.

**Case 3, cap and floor together.** A domestic governmental entity (`override_low`, contributes neutral 50) with employment-income wealth (50), external bank transfer (50), elevated-risk jurisdiction (elevator 70) and operating account (50). Nature of business, occupation and listed status do not apply. `(50 + 60 + 75 + 105 + 50) / 6.2 = 54.839`, base tier HIGH, capped to LOW. `ATOM-02` fires with a HIGH floor; final tier HIGH. With a standard international jurisdiction instead, the score is exactly 50.0, base LOW, final LOW, and `caps_applied` is still true.

**Case 4, floor and route.** An individual who is a senior foreign public official (elevator 65) with undocumented wealth (elevator 70), external bank transfer (50), domestic only (50), and unclear account purpose (elevator 70). Score 58.194, base VERY_HIGH. `COMP-02` fires but changes nothing; `ROUTE-01` fires and adds a purpose-clarification route without affecting the tier.

## Simulation

`simulate_rules(parties, model, rules, stage)` (CLI: `python -m crw attributes rules`) evaluates every non-retired rule on every party and reports:

| Output | Definition | How to read it |
| --- | --- | --- |
| `tier_distribution_without_rules` | Tiers from score, value triggers and caps only | Baseline that rules modify |
| `tier_distribution_with_rules` | Tiers with every floor rule applied | Combined effect of the rule set |
| `true`, `unknown`, `not_applicable`, `false` | Evaluation counts per rule | High `unknown` is a data-quality finding first; `not_applicable` shows how much of the population the rule cannot address |
| `marginal_tier_changes` (floors) | Parties whose final tier changes when only this rule is removed | The rule's unique effect given all others; not effectiveness |
| `shadowed_share` (floors) | Share of firing parties already at or above the floor tier without this rule | Near 1 means the rule mostly restates other logic |
| `shadowed_by_triggers` (floors) | Firing parties that also hold an `override_high` value | Overlap with value triggers |
| `overlaps` | Rule pairs, routes included, firing together, with Jaccard similarity and joint count | Candidates for consolidation or ordering review |
| `population_redundancy` | Floor rule whose firing set is contained in another floor rule's set with an equal or higher tier | Removable on this population; may not hold on another |

Simulation does not compute review flags; use `assess` on individual parties for those. Routes have no marginal or shadowing statistics because they do not change tiers.

Synthetic demo results (20,000 synthetic parties, seed 11, stage `proposed`; the release summary is regenerated at `evidence/program-demo-summary.json`):

| Rule | Kind | Effect | TRUE | UNKNOWN | NOT_APPLICABLE | Marginal changes | Shadowed share |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| `ATOM-01` | atomic | floor HIGH | 966 | 222 | 12,577 | 111 | 0.885 |
| `ATOM-02` | atomic | floor HIGH | 1,473 | 580 | 0 | 426 | 0.711 |
| `COMP-01` | compound | floor VERY_HIGH | 74 | 23 | 0 | 20 | 0.730 |
| `COMP-02` | compound | floor VERY_HIGH | 7 | 25 | 455 | 6 | 0.143 |
| `COMP-03` | compound | floor HIGH (draft) | 2 | 7 | 148 | 1 | 0.500 |
| `ROUTE-01` | atomic | route | 583 | 638 | 0 | n/a | n/a |

Reading these synthetic figures: `ATOM-01` fires often but changes few tiers because 88.5% of its firing parties already reach HIGH without it, through their scores, value triggers or other rules; its large `NOT_APPLICABLE` count is the natural persons and other entity types to which nature of business does not apply. `COMP-01` has no `NOT_APPLICABLE` parties because its entity-type leg is `FALSE` for every other entity type. `COMP-02` is UNKNOWN for more parties than it fires on, so its practical reach depends on wealth documentation. `COMP-03` remains `draft`, which blocks the rule-design gate. The `COMP-01` leg test in [connections-method.md](connections-method.md) found that its listed-status leg adds no discrimination in this synthetic population, which is a reason to revisit that leg before agreement. Tier distributions with and without rules, overlaps and redundancy are in `rule-simulation.json`.

## Rule lifecycle

| Status | Effect in assessment and simulation | Effect on the rule-design gate |
| --- | --- | --- |
| `draft` | Evaluated | Blocks the gate |
| `proposed` | Evaluated | None |
| `challenged` | Evaluated | None |
| `agreed` | Evaluated | None |
| `retired` | Skipped | Excluded from the simulation, so not counted |

Unlike catalog values, rule statuses carry no decision record in the rule-set contract, and no status sequence is enforced. Record the policy owner's decision, date and reference on [the rule specification card](../templates/rule-specification.md). A simulation of `proposed` or `challenged` rules describes candidate behavior, not an approved position.

## Design checklist

1. State the conclusion the rule encodes and why a value class or score change cannot express it.
2. For a compound rule, cite the connections screen candidate and its grade, and confirm it is not flagged as a proxy.
3. Run `evaluate_combination` and drop or justify any leg whose complement rate is close to the full rate.
4. Choose floor or route. A route is the honest effect when the condition marks missing information rather than a risk conclusion, as `ROUTE-01` does.
5. Simulate; record UNKNOWN share, marginal changes, shadowing and overlaps; investigate any UNKNOWN share near the gate threshold.
6. Check the `NOT_APPLICABLE` count and confirm that the entity types it covers are meant to be outside the rule.
7. Record evidence, rationale and status; obtain the policy owner's decision outside the rule file.

## Limits

Simulation describes one population. Marginal changes count tier dependence, not detection value, and a rule with few marginal changes can still matter for a future population. UNKNOWN behavior depends on missing data. Rule floors are set by judgment; nothing here estimates their correctness. See [program-sequencing.md](program-sequencing.md) for where rule design sits relative to calibration and validation.
