"""Categorical tiering model and declarative atomic/compound rules.

Assessment order for one party, deliberately simple so a reviewer can recompute it by hand:

1. Weighted mean of value scores over attributes that apply to the party's entity type. A missing value
   contributes the neutral score and is listed; under ``missing: abstain`` the score is withheld instead.
2. Score band gives the base tier.
3. Floors: any ``override_high`` value, and any rule evaluating TRUE with a floor effect.
4. ``override_low`` caps the score-derived base tier at its configured tier; floors from step 3 still apply
   on top, so an auto-low value never suppresses a trigger or a rule.
5. A rule evaluating UNKNOWN (a referenced attribute is missing) never fires; if it could have raised the
   tier, the party is flagged for review.
"""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
import json
from pathlib import Path

from .attributes import Catalog
from .contracts import ContractError, identifier, number, strict_fields
from .features import digest

REVIEW = "REVIEW_REQUIRED"


class CategoricalModel:
    def __init__(self, config: dict, catalog: Catalog):
        self._config = deepcopy(config)
        self.catalog = catalog
        self._validate()
        self.digest = digest(self._config)
        self.tiers = [t["name"] for t in self._config["tiers"]]
        self.rank = {t: i for i, t in enumerate(self.tiers)}

    @classmethod
    def load(cls, path: str | Path, catalog: Catalog) -> CategoricalModel:
        return cls(json.loads(Path(path).read_text(encoding="utf-8")), catalog)

    def to_dict(self) -> dict:
        return deepcopy(self._config)

    def _validate(self):
        c = self._config
        keys = {"model_id", "version", "description", "weights", "tiers", "missing", "override_high_tier",
                "override_low_tier"}
        strict_fields(c, keys, keys)
        identifier(c["model_id"], "model_id")
        identifier(c["version"], "version")
        if c["missing"] not in {"neutral", "abstain"}:
            raise ContractError("missing must be neutral or abstain")
        if not isinstance(c["weights"], dict) or not c["weights"]:
            raise ContractError("weights required")
        for attribute, weight in c["weights"].items():
            if not isinstance(attribute, str):
                raise ContractError("weight keys must be attribute ids")
            if attribute not in self.catalog.attributes:
                raise ContractError(f"weight for unknown attribute {attribute}")
            number(weight, f"weight {attribute}", minimum=1e-9, maximum=1e6)
        scale = self.catalog.scale
        tiers = c["tiers"]
        if not isinstance(tiers, list) or not all(isinstance(t, dict) for t in tiers):
            raise ContractError("tiers must be a list of objects")
        if len(tiers) < 2 or tiers[0].get("minimum") != scale["minimum"]:
            raise ContractError("at least two tiers required, the first starting at the scale minimum")
        previous, names = None, set()
        for t in tiers:
            strict_fields(t, {"name", "minimum"}, {"name", "minimum"})
            identifier(t["name"], "tier")
            number(t["minimum"], "tier minimum", minimum=scale["minimum"], maximum=scale["maximum"])
            if t["name"] in names or t["name"] == REVIEW or (previous is not None and t["minimum"] <= previous):
                raise ContractError("tiers need unique names and strictly ascending minima")
            names.add(t["name"])
            previous = t["minimum"]
        for key in ("override_high_tier", "override_low_tier"):
            if c[key] not in names:
                raise ContractError(f"{key} must name a configured tier")

    def applicable(self, entity_type: str) -> set[str]:
        return {a for a in self.catalog.attributes if self.catalog.applies(a, entity_type)}

    def band(self, score: float) -> str:
        return next(t["name"] for t in reversed(self._config["tiers"]) if score >= t["minimum"])

    def components(self, party: dict, stage: str = "proposed") -> dict:
        """Score, base tier and value-driven floors/caps, before rules. Rules are layered in ``assess``."""
        validate_party(party, self.catalog)
        neutral = self.catalog.scale["neutral"]
        weights = self._config["weights"]
        total_weight, total, contributions, missing = 0.0, 0.0, [], []
        triggers, caps = [], []
        for attribute in self.catalog.attributes:
            if attribute in weights or not self.catalog.applies(attribute, party["entity_type"]):
                continue
            value = party["values"].get(attribute)
            if value is None:
                continue
            assignment = self.catalog.assignment(attribute, value, stage) or {}
            if assignment.get("class") == "override_high":
                triggers.append(f"{attribute}/{value}")
            elif assignment.get("class") == "override_low":
                caps.append(f"{attribute}/{value}")
        for attribute, weight in weights.items():
            if not self.catalog.applies(attribute, party["entity_type"]):
                continue
            value = party["values"].get(attribute)
            if value is None:
                missing.append(attribute)
                score = neutral
                cls = None
            else:
                assignment = self.catalog.assignment(attribute, value, stage)
                if assignment is None:
                    raise ContractError(f"{attribute}/{value} has no classification at stage {stage}")
                cls = assignment["class"]
                score = assignment["score"] if assignment["score"] is not None else neutral
                if cls == "override_high":
                    triggers.append(f"{attribute}/{value}")
                if cls == "override_low":
                    caps.append(f"{attribute}/{value}")
            total_weight += weight
            total += weight * score
            contributions.append({"attribute": attribute, "value": value, "class": cls, "score": score,
                                  "weight": weight})
        if not total_weight:
            raise ContractError(f"no weighted attribute applies to entity type {party['entity_type']}")
        abstain = self._config["missing"] == "abstain" and bool(missing)
        # Rounded to a declared precision so a score that equals a tier minimum is not demoted by float error.
        score = None if abstain else round(total / total_weight, 9)
        return {
            "score": score,
            "base_tier": None if score is None else self.band(score),
            "triggers": triggers,
            "caps": caps,
            "missing": missing,
            "contributions": contributions,
        }

    def resolve(self, base_tier, floors: list[str], capped: bool) -> str:
        top = self.tiers[-1]
        floor = max(floors, key=self.rank.get) if floors else None
        if base_tier is None:
            return top if floor == top else REVIEW
        if capped:
            base_tier = min(base_tier, self._config["override_low_tier"], key=self.rank.get)
        return base_tier if floor is None else max(base_tier, floor, key=self.rank.get)

    def assess(self, party: dict, rules: RuleSet | None = None, stage: str = "proposed") -> dict:
        parts = self.components(party, stage)
        floors = [self._config["override_high_tier"]] if parts["triggers"] else []
        fired, unknown, routes = [], [], []
        applicable = self.applicable(party["entity_type"])
        for rule in (rules.rules if rules else []):
            if rule["status"] == "retired":
                continue
            state = evaluate(rule["condition"], party["values"], applicable)
            if state == "TRUE":
                fired.append(rule["id"])
                if rule["effect"]["type"] == "floor":
                    floors.append(rule["effect"]["tier"])
                else:
                    routes.append({"rule": rule["id"], "action": rule["effect"]["action"]})
            elif state == "UNKNOWN":
                unknown.append(rule["id"])
        tier = self.resolve(parts["base_tier"], floors, bool(parts["caps"]))
        review_flags = [f"missing_review_attribute:{a}" for a in parts["missing"]
                        if self.catalog.attributes[a]["missing"] == "review"]
        if tier != REVIEW:
            for rid in unknown:
                effect = rules.by_id[rid]["effect"]
                if effect["type"] == "floor" and self.rank[effect["tier"]] > self.rank[tier]:
                    review_flags.append(f"unknown_rule_could_raise_tier:{rid}")
        return {
            "party_id": party["party_id"],
            "segment": party.get("segment"),
            "stage": stage,
            "score": parts["score"],
            "base_tier": parts["base_tier"],
            "tier": tier,
            "triggers": parts["triggers"],
            "caps_applied": bool(parts["caps"]) and tier != REVIEW,
            "rules_fired": fired,
            "rules_unknown": unknown,
            "routes": routes,
            "review_flags": review_flags,
            "missing": parts["missing"],
            "contributions": parts["contributions"],
            "model_digest": self.digest,
            "catalog_digest": self.catalog.digest,
        }


def validate_party(party: dict, catalog: Catalog) -> None:
    strict_fields(
        party,
        {"party_id", "entity_type", "segment", "values", "pinned", "outcome"},
        {"party_id", "entity_type", "values"},
    )
    identifier(party["party_id"], "party_id")
    if party["entity_type"] not in catalog.entity_types:
        raise ContractError(f"{party['party_id']}: unknown entity type {party['entity_type']}")
    if not isinstance(party["values"], dict):
        raise ContractError("party values must be an object")
    declared = party["values"].get("entity_type")
    if "entity_type" in catalog.attributes and declared is not None and declared != party["entity_type"]:
        raise ContractError(f"{party['party_id']}: entity_type value disagrees with the party's entity type")
    if "segment" in party:
        identifier(party["segment"], "segment")
    if "pinned" in party and type(party["pinned"]) is not bool:
        raise ContractError(f"{party['party_id']}: pinned must be boolean")
    if party.get("outcome") not in (None, 0, 1) or isinstance(party.get("outcome"), bool):
        raise ContractError(f"{party['party_id']}: outcome must be 0, 1 or null")
    for attribute, value in party["values"].items():
        if attribute not in catalog.attributes:
            raise ContractError(f"{party['party_id']}: unknown attribute {attribute}")
        if value is not None and not isinstance(value, str):
            raise ContractError(f"{party['party_id']}: {attribute} value must be a normalized value id or null")
        if value is not None and not catalog.applies(attribute, party["entity_type"]):
            raise ContractError(f"{party['party_id']}: {attribute} does not apply to entity type {party['entity_type']}")
        if value is not None and not catalog.has_value(attribute, value):
            raise ContractError(
                f"{party['party_id']}: {attribute} value {value!r} is not normalized; resolve it in the normalization table"
            )


NA = "NOT_APPLICABLE"


def evaluate(condition: dict, values: dict, applicable: set | None = None) -> str:
    """Evaluate to TRUE, FALSE, UNKNOWN (a referenced, applicable attribute is missing) or NOT_APPLICABLE.

    A leaf on an attribute that does not apply to the party's entity type is NOT_APPLICABLE, and negation keeps
    it NOT_APPLICABLE: "not listed on an exchange" says nothing about a natural person. ``all`` is FALSE if any
    child is FALSE, else NOT_APPLICABLE if any child is; ``any`` is TRUE if any child is TRUE, else UNKNOWN if
    any child is, else NOT_APPLICABLE if any child is. A rule fires only on TRUE.
    """
    for op in ("all", "any", "not"):
        if op in condition:
            children = [condition[op]] if op == "not" else condition[op]
            states = [evaluate(child, values, applicable) for child in children]
            if op == "all":
                for state in ("FALSE", NA, "UNKNOWN"):
                    if state in states:
                        return state
                return "TRUE"
            if op == "any":
                for state in ("TRUE", "UNKNOWN", NA):
                    if state in states:
                        return state
                return "FALSE"
            return {"TRUE": "FALSE", "FALSE": "TRUE", "UNKNOWN": "UNKNOWN", NA: NA}[states[0]]
    if applicable is not None and condition["attribute"] not in applicable:
        return NA
    value = values.get(condition["attribute"])
    if value is None:
        return "UNKNOWN"
    return "TRUE" if value in condition["in"] else "FALSE"


def referenced_attributes(condition: dict) -> set[str]:
    for op in ("all", "any", "not"):
        if op in condition:
            children = [condition[op]] if op == "not" else condition[op]
            return set().union(*(referenced_attributes(c) for c in children))
    return {condition["attribute"]}


class RuleSet:
    def __init__(self, config: dict, catalog: Catalog, model: CategoricalModel):
        self._config = deepcopy(config)
        self.catalog, self.model = catalog, model
        self._validate()
        self.digest = digest(self._config)
        self.rules = self._config["rules"]
        self.by_id = {r["id"]: r for r in self.rules}

    @classmethod
    def load(cls, path: str | Path, catalog: Catalog, model: CategoricalModel) -> RuleSet:
        return cls(json.loads(Path(path).read_text(encoding="utf-8")), catalog, model)

    def to_dict(self) -> dict:
        return deepcopy(self._config)

    def kind(self, rule_id: str) -> str:
        return "atomic" if len(referenced_attributes(self.by_id[rule_id]["condition"])) == 1 else "compound"

    def _condition(self, condition, depth=0):
        if depth > 8 or not isinstance(condition, dict):
            raise ContractError("condition must be an object nested at most 8 levels")
        ops = set(condition) & {"all", "any", "not"}
        if ops:
            if len(ops) != 1 or len(condition) != 1:
                raise ContractError("one exclusive logical operator required")
            op = next(iter(ops))
            children = [condition[op]] if op == "not" else condition[op]
            if not isinstance(children, list) or not 1 <= len(children) <= 50:
                raise ContractError("logical operands must be a nonempty bounded list")
            for child in children:
                self._condition(child, depth + 1)
            return
        strict_fields(condition, {"attribute", "in"}, {"attribute", "in"})
        attribute = condition["attribute"]
        if attribute not in self.catalog.attributes:
            raise ContractError(f"rule references unknown attribute {attribute}")
        if not isinstance(condition["in"], list) or not condition["in"] or not all(isinstance(v, str) for v in condition["in"]):
            raise ContractError("'in' must be a nonempty list of normalized value ids")
        for value in condition["in"]:
            if not self.catalog.has_value(attribute, value):
                raise ContractError(f"rule references unknown value {attribute}/{value}")

    def _validate(self):
        c = self._config
        strict_fields(c, {"ruleset_id", "version", "description", "rules"},
                      {"ruleset_id", "version", "description", "rules"})
        identifier(c["ruleset_id"], "ruleset_id")
        identifier(c["version"], "version")
        ids = set()
        for r in c["rules"]:
            keys = {"id", "title", "condition", "effect", "evidence", "rationale", "status"}
            strict_fields(r, keys, keys)
            identifier(r["id"], "rule id")
            if r["id"] in ids:
                raise ContractError(f"duplicate rule {r['id']}")
            ids.add(r["id"])
            self._condition(r["condition"])
            effect = r["effect"]
            if not isinstance(effect, dict):
                raise ContractError(f"{r['id']}: effect must be an object")
            if not isinstance(r["evidence"], list):
                raise ContractError(f"{r['id']}: evidence must be a list")
            if effect.get("type") == "floor":
                strict_fields(effect, {"type", "tier"}, {"type", "tier"})
                if effect["tier"] not in self.model.rank:
                    raise ContractError(f"{r['id']}: floor tier must be a model tier")
            elif effect.get("type") == "route":
                strict_fields(effect, {"type", "action"}, {"type", "action"})
                if not isinstance(effect["action"], str) or not effect["action"]:
                    raise ContractError(f"{r['id']}: route action required")
            else:
                raise ContractError(f"{r['id']}: effect type must be floor or route")
            if not r["evidence"] or set(r["evidence"]) - set(self.catalog.evidence):
                raise ContractError(f"{r['id']}: at least one registered evidence reference required")
            if not isinstance(r["rationale"], str) or not r["rationale"].strip():
                raise ContractError(f"{r['id']}: rationale required")
            if r["status"] not in {"draft", "proposed", "challenged", "agreed", "retired"}:
                raise ContractError(f"{r['id']}: unknown status")


def simulate_rules(parties: list[dict], model: CategoricalModel, rules: RuleSet, stage: str = "proposed") -> dict:
    """Population effect of each rule: firing, unknowns, overlap, redundancy, shadowing, marginal migration."""
    active = [r for r in rules.rules if r["status"] != "retired"]
    floor_rules = [r for r in active if r["effect"]["type"] == "floor"]
    states: dict[str, list[str]] = {r["id"]: [] for r in active}
    base = []
    for party in parties:
        parts = model.components(party, stage)
        base.append((parts["base_tier"], [model.to_dict()["override_high_tier"]] if parts["triggers"] else [],
                     bool(parts["caps"])))
        applicable = model.applicable(party["entity_type"])
        for r in active:
            states[r["id"]].append(evaluate(r["condition"], party["values"], applicable))

    def tiers(excluded: str | None = None) -> list[str]:
        out = []
        for i, (base_tier, trigger_floors, capped) in enumerate(base):
            floors = list(trigger_floors) + [
                r["effect"]["tier"] for r in floor_rules if r["id"] != excluded and states[r["id"]][i] == "TRUE"
            ]
            out.append(model.resolve(base_tier, floors, capped))
        return out

    with_rules = tiers()
    without = []
    for i, (base_tier, trigger_floors, capped) in enumerate(base):
        without.append(model.resolve(base_tier, list(trigger_floors), capped))
    true_sets = {rid: {i for i, s in enumerate(v) if s == "TRUE"} for rid, v in states.items()}
    report = []
    for r in active:
        rid = r["id"]
        fired = true_sets[rid]
        row = {
            "rule_id": rid,
            "kind": rules.kind(rid),
            "effect": r["effect"],
            "status": r["status"],
            "true": len(fired),
            "unknown": sum(s == "UNKNOWN" for s in states[rid]),
            "false": sum(s == "FALSE" for s in states[rid]),
            "not_applicable": sum(s == NA for s in states[rid]),
        }
        if r["effect"]["type"] == "floor":
            leave_out = tiers(excluded=rid)
            changed = [i for i in range(len(parties)) if leave_out[i] != with_rules[i]]
            target = model.rank[r["effect"]["tier"]]
            already = sum(1 for i in fired if leave_out[i] != REVIEW and model.rank[leave_out[i]] >= target)
            row.update(
                marginal_tier_changes=len(changed),
                shadowed_share=already / len(fired) if fired else None,
                shadowed_by_triggers=sum(1 for i in fired if base[i][1]),
            )
        report.append(row)
    overlaps = []
    for x in range(len(active)):
        for y in range(x + 1, len(active)):
            a, b = active[x]["id"], active[y]["id"]
            union = true_sets[a] | true_sets[b]
            if not union:
                continue
            inter = true_sets[a] & true_sets[b]
            if inter:
                overlaps.append({"rules": [a, b], "jaccard": len(inter) / len(union), "both": len(inter)})
    redundancy = []
    for a in floor_rules:
        for b in floor_rules:
            if a is b or not true_sets[a["id"]]:
                continue
            if true_sets[a["id"]] <= true_sets[b["id"]] and model.rank[a["effect"]["tier"]] <= model.rank[b["effect"]["tier"]]:
                redundancy.append({"rule": a["id"], "contained_in": b["id"],
                                   "note": "On this population every party firing the rule also fires a rule with an equal or higher floor."})
    return {
        "parties": len(parties),
        "stage": stage,
        "ruleset_digest": rules.digest,
        "model_digest": model.digest,
        "catalog_digest": model.catalog.digest,
        "tier_distribution_without_rules": dict(Counter(without)),
        "tier_distribution_with_rules": dict(Counter(with_rules)),
        "rules": report,
        "overlaps": sorted(overlaps, key=lambda o: -o["jaccard"]),
        "population_redundancy": redundancy,
        "limits": [
            "Simulation describes this population only; redundancy observed here may not hold for future populations.",
            "Marginal tier changes count parties whose final tier depends on the rule given all other rules; they are not effectiveness.",
            "UNKNOWN counts depend on missing data; high UNKNOWN shares are a data-quality finding before they are a rule-design finding.",
        ],
    }
