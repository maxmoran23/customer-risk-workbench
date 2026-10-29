"""Seeded synthetic data for the attribute-review and impact-assessment programs.

Planted structure, documented so tests can check recovery rather than assume it:

* Outcome labels (a synthetic "historical review escalation") follow a logistic model with small main effects
  for elevator values and one planted synergy: ``financial_institution_nonbank`` with
  ``third_party_unrelated`` funds. A planted null pair (``trust`` with ``inheritance_or_gift``) has elevated
  co-occurrence but no outcome interaction.
* Labels are drawn independently of the catalog's scores beyond those stated effects and are missing for 10%
  of parties, mirroring unlabeled history.
"""

from __future__ import annotations

import math
import random

from .attributes import Catalog
from .program_reference import AGGREGATE_SEGMENT, ENTITY_TYPES, SEGMENTS
from .rules import CategoricalModel, RuleSet

ENTITY_WEIGHTS = {
    "individual": 0.55, "sole_proprietor": 0.07, "private_company": 0.13, "public_company": 0.03, "trust": 0.06,
    "investment_vehicle": 0.05, "financial_institution_regulated": 0.02, "financial_institution_nonbank": 0.07,
    "government_entity": 0.02,
}
COMMON = {
    "nature_of_business": {"general_retail": 30, "manufacturing": 15, "professional_services": 20,
                           "legal_accounting_intermediary": 4, "restaurant": 5, "convenience_store": 3,
                           "liquor_store": 2, "vending_machine_operator": 1, "parking_garage": 2,
                           "privately_owned_atm_operator": 1, "precious_metals_dealer": 1, "money_services_business": 2,
                           "unregistered_money_transmission": 0.2, "import_export_trading": 5,
                           "online_marketplace_seller": 0},
    "occupation": {"salaried_employee": 50, "retired": 15, "student": 6, "not_employed": 5,
                   "self_employed_professional": 14, "cash_based_self_employment": 6, "senior_foreign_public_official": 1},
    "listed_status": {"listed_regulated_exchange": 10, "subsidiary_of_listed": 8, "unlisted_private": 70,
                      "unlisted_unregulated_structure": 12},
    "source_of_wealth": {"employment_income": 45, "business_ownership": 20, "inheritance_or_gift": 10,
                         "investment_returns": 15, "sale_of_business_or_property": 7, "undocumented": 3},
    "source_of_funds": {"own_account_same_institution": 20, "external_bank_transfer": 45, "payroll": 18,
                        "cash_deposit": 6, "third_party_unrelated": 5, "virtual_asset_service_provider": 3,
                        "unverified": 3},
    "jurisdiction_exposure": {"domestic_only": 70, "standard_international": 22, "elevated_risk": 7.5,
                              "comprehensively_sanctioned": 0.5},
    "account_purpose": {"long_term_investment": 50, "operating_or_payroll": 35, "cross_border_payments": 12,
                        "unclear_or_pass_through": 3},
}
SEGMENT_WEIGHTS = {"SEGMENT_A": 0.35, "SEGMENT_B": 0.25, "SEGMENT_C": 0.2, "SEGMENT_D": 0.2}


def _pick(rng: random.Random, weights: dict) -> str:
    items = [(k, w) for k, w in weights.items() if w > 0]
    total = sum(w for _, w in items)
    x = rng.random() * total
    for key, w in items:
        x -= w
        if x <= 0:
            return key
    return items[-1][0]


def generate_parties(catalog: Catalog, n: int = 20000, seed: int = 7, *, missing_rate: float = 0.03,
                     id_prefix: str = "SYN") -> list[dict]:
    if type(n) is not int or n < 1:
        raise ValueError("n must be a positive integer")
    rng = random.Random(seed)
    parties = []
    for i in range(n):
        etype = _pick(rng, ENTITY_WEIGHTS)
        values: dict[str, str | None] = {}
        for attribute in catalog.attributes:
            if not catalog.applies(attribute, etype):
                continue
            if attribute == "entity_type":
                values[attribute] = etype
                continue
            weights = dict(COMMON[attribute])
            if etype == "financial_institution_nonbank":
                if attribute == "source_of_funds":
                    weights["third_party_unrelated"] = 25
                if attribute == "listed_status":
                    weights["unlisted_unregulated_structure"] = 35
                if attribute == "nature_of_business":
                    weights = {"money_services_business": 60, "professional_services": 25,
                               "unregistered_money_transmission": 2, "import_export_trading": 13}
            if etype == "financial_institution_regulated" and attribute == "nature_of_business":
                weights = {"professional_services": 100}
            if etype == "trust" and attribute == "source_of_wealth":
                weights["inheritance_or_gift"] = 55
            values[attribute] = None if rng.random() < missing_rate else _pick(rng, weights)
        parties.append(
            {
                "party_id": f"{id_prefix}-{i:07d}",
                "entity_type": etype,
                "segment": _pick(rng, SEGMENT_WEIGHTS),
                "values": values,
                "pinned": rng.random() < 0.01,
                "outcome": _outcome(rng, catalog, values),
            }
        )
    return parties


def _outcome(rng: random.Random, catalog: Catalog, values: dict):
    if rng.random() < 0.10:
        return None
    logit = -3.2
    for attribute, value in values.items():
        if value is None:
            continue
        cls = (catalog.assignment(attribute, value, "current") or {}).get("class")
        if cls == "elevator":
            logit += 0.30
        elif cls == "override_high":
            logit += 1.2
        elif cls == "mitigator":
            logit -= 0.15
    if values.get("entity_type") == "financial_institution_nonbank" and values.get("source_of_funds") == "third_party_unrelated":
        logit += 1.9
    return int(rng.random() < 1 / (1 + math.exp(-logit)))


def role_rows(parties: list[dict], seed: int = 7, *, unmapped_role: str | None = None) -> list[dict]:
    """One account-holder row per party plus related roles; optional unmapped role for gap demonstrations."""
    rng = random.Random(seed + 1)
    rows = []
    for party in parties:
        etype = party["entity_type"]
        rows.append({"party_id": party["party_id"], "role_code": "account_holder", "entity_type": etype})
    related = 0
    for party in parties:
        etype = party["entity_type"]
        options = []
        if etype in {"private_company", "investment_vehicle", "financial_institution_nonbank"}:
            options = ["beneficial_owner_ownership", "controlling_person"]
        elif etype == "trust":
            options = ["trustee", "settlor", "contingent_beneficiary"]
        elif etype == "individual":
            options = ["attorney_in_fact", "transfer_on_death_beneficiary", "duplicate_statement_recipient"]
        for role in options:
            if rng.random() < 0.35:
                related += 1
                rows.append({"party_id": f"REL-{related:07d}", "role_code": role, "entity_type": "individual"})
    if unmapped_role:
        rows.append({"party_id": "REL-UNMAPPED", "role_code": unmapped_role, "entity_type": "individual"})
    return rows


def normalization_rows(catalog: Catalog, parties: list[dict], seed: int = 7, *, defects: bool = True) -> list[dict]:
    """Two source systems with differing spellings; optional injected defects for the audit to find."""
    rng = random.Random(seed + 2)
    counts: dict[tuple, int] = {}
    for p in parties:
        for attribute, value in p["values"].items():
            if value is not None:
                counts[(attribute, value)] = counts.get((attribute, value), 0) + 1
    rows = []
    for attribute, a in catalog.attributes.items():
        for v in a["values"]:
            total = counts.get((attribute, v["id"]), 0)
            share = rng.uniform(0.55, 0.85)
            rows.append({"attribute_id": attribute, "source_system": "SRC_A", "source_value": v["label"],
                         "value_id": v["id"], "party_count": round(total * share)})
            rows.append({"attribute_id": attribute, "source_system": "SRC_B",
                         "source_value": v["id"].upper().replace("_", " "), "value_id": v["id"],
                         "party_count": total - round(total * share)})
    if defects:
        rows += [
            {"attribute_id": "nature_of_business", "source_system": "SRC_B", "source_value": "Gas station / convenience",
             "value_id": "", "party_count": 37},
            {"attribute_id": "nature_of_business", "source_system": "SRC_C", "source_value": "Store, liquor",
             "value_id": "general_retail", "party_count": 12},
            {"attribute_id": "nature_of_business", "source_system": "SRC_C", "source_value": "Liquor Store",
             "value_id": "general_retail", "party_count": 5},
            {"attribute_id": "source_of_funds", "source_system": "SRC_A", "source_value": "Payroll",
             "value_id": "payroll", "party_count": 0},
        ]
    return rows


def snapshot_rows(parties: list[dict], model: CategoricalModel, rules: RuleSet | None, stage: str) -> list[dict]:
    top = model.tiers[-1]
    rows = []
    for p in parties:
        tier = top if p.get("pinned") else model.assess(p, rules, stage)["tier"]
        rows.append({"party_id": p["party_id"], "segment": p["segment"], "tier": tier,
                     "pinned": "1" if p.get("pinned") else "0"})
    return rows


def change_snapshots(parties: list[dict], model_pre: CategoricalModel, model_post: CategoricalModel,
                     rules: RuleSet | None, seed: int = 7, *, churn: float = 0.004,
                     pinned_defect: bool = False) -> tuple[list[dict], list[dict]]:
    """Before/after snapshots with small population churn (exits and entrants)."""
    rng = random.Random(seed + 3)
    pre = snapshot_rows(parties, model_pre, rules, "current")
    post = snapshot_rows(parties, model_post, rules, "proposed")
    keep = [rng.random() >= churn for _ in post]
    post = [row for row, k in zip(post, keep) if k]
    entrants = generate_parties(model_post.catalog, max(1, round(len(parties) * churn)), seed + 4, id_prefix="NEW")
    post += snapshot_rows(entrants, model_post, rules, "proposed")
    if pinned_defect:
        for row in post:
            if row["pinned"] == "1":
                row["tier"] = model_post.tiers[0]
                break
    return pre, post


def aggregate_counts(n: int, seed: int, shift: float) -> dict:
    """Aggregate-only segment: pre/post tier counts for a fixed population with a small upward shift."""
    rng = random.Random(seed + 5)
    base = [0.52, 0.28, 0.14, 0.06]
    pre = [round(n * b) for b in base]
    pre[0] += n - sum(pre)
    moved = [round(pre[i] * shift * rng.uniform(0.6, 1.4)) for i in range(3)]
    post = pre[:]
    for i in range(3):
        post[i] -= moved[i]
        post[i + 1] += moved[i]
    tiers = ["LOW", "MODERATE", "HIGH", "VERY_HIGH"]
    return {"pre": dict(zip(tiers, pre)), "post": dict(zip(tiers, post))}


def history_catalogs(catalog: Catalog, releases: int = 8, seed: int = 7) -> list[Catalog]:
    """Prior synthetic releases: each rescored one or two elevator values by a few points."""
    rng = random.Random(seed + 6)
    elevators = [(a, v["id"]) for a, attr in catalog.attributes.items() for v in attr["values"]
                 if (v["current"] or {}).get("class") == "elevator"]
    out = []
    for _ in range(releases):
        config = catalog.to_dict()
        index = {(a["id"], v["id"]): v for a in config["attributes"] for v in a["values"]}
        for v in index.values():
            v.pop("decision", None)
            v["proposed"], v["status"] = None, "unreviewed"
        for key in rng.sample(elevators, rng.choice([1, 2])):
            score = index[key]["current"]["score"]
            index[key]["proposed"] = {"class": "elevator", "score": max(51, min(95, score + rng.choice([-10, -5, 5, 10, 15])))}
            index[key]["status"] = "proposed"
            index[key]["rationale"] = "Synthetic prior release."
        out.append(Catalog(config))
    return out


__all__ = ["ENTITY_TYPES", "SEGMENTS", "AGGREGATE_SEGMENT", "generate_parties", "role_rows", "normalization_rows",
           "snapshot_rows", "change_snapshots", "aggregate_counts", "history_catalogs"]
