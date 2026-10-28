"""Versioned, declarative scoring policy. No executable expressions or callbacks."""

from __future__ import annotations

import json
from pathlib import Path
from copy import deepcopy

from .contracts import ContractError, identifier, number, strict_fields
from .features import digest, feature_catalog

PROFILE_KEYS = (
    "ownership_opacity",
    "business_complexity",
    "geography_exposure",
    "product_complexity",
    "channel_opacity",
    "source_of_funds_concern",
    "adverse_information",
    "pep_exposure",
    "documentation_gap",
    "screening_unresolved",
    "cash_intensity",
    "cross_border_exposure",
)


class Policy:
    def __init__(self, config: dict):
        self._config = deepcopy(config)
        self._validate()
        self.digest = digest(self._config)

    def _validate(self):
        c = self._config
        strict_fields(
            c,
            {
                "policy_id",
                "version",
                "description",
                "groups",
                "factors",
                "bands",
                "routes",
                "require_complete_history",
                "profile_keys",
            },
            {
                "policy_id",
                "version",
                "description",
                "groups",
                "factors",
                "bands",
                "routes",
                "require_complete_history",
            },
        )
        identifier(c["policy_id"], "policy_id")
        identifier(c["version"], "version")
        if not isinstance(c["description"], str) or not c["description"]:
            raise ContractError("policy description required")
        if type(c["require_complete_history"]) is not bool:
            raise ContractError("require_complete_history must be boolean")
        if not isinstance(c["groups"], list) or not c["groups"]:
            raise ContractError("nonempty groups required")
        group_ids = set()
        for g in c["groups"]:
            strict_fields(
                g, {"id", "cap", "aggregation", "rationale"}, {"id", "cap", "aggregation", "rationale"}
            )
            identifier(g["id"], "group")
            if g["id"] in group_ids:
                raise ContractError("duplicate group")
            group_ids.add(g["id"])
            number(g["cap"], "cap", minimum=0.000001, maximum=100)
            if g["aggregation"] not in {"sum", "max"}:
                raise ContractError("group aggregation must be sum or max")
        if abs(sum(g["cap"] for g in c["groups"]) - 100) > 1e-9:
            raise ContractError("group caps must sum to 100")
        profile_keys = c.get("profile_keys", list(PROFILE_KEYS))
        if not isinstance(profile_keys, list) or not profile_keys or len(profile_keys) > 1000:
            raise ContractError("profile_keys must declare between 1 and 1000 normalized evidence fields")
        if len(set(profile_keys)) != len(profile_keys):
            raise ContractError("duplicate profile key")
        for key in profile_keys:
            identifier(key, "declared profile key")
        known_features = {r["name"] for r in feature_catalog(profile_keys)}
        factor_ids = set()
        if not isinstance(c["factors"], list) or not c["factors"]:
            raise ContractError("factors required")
        for f in c["factors"]:
            keys = {
                "id",
                "feature",
                "group",
                "weight",
                "low",
                "high",
                "direction",
                "required",
                "min_support",
                "require_full_window",
                "rationale",
            }
            strict_fields(f, keys, keys)
            identifier(f["id"], "factor")
            if f["id"] in factor_ids:
                raise ContractError("duplicate factor")
            factor_ids.add(f["id"])
            if f["feature"] not in known_features or f["group"] not in group_ids:
                raise ContractError("unknown feature or group")
            number(f["weight"], "weight", minimum=0.000001, maximum=100)
            number(f["low"], "low")
            number(f["high"], "high")
            if f["high"] <= f["low"]:
                raise ContractError("factor high must exceed low")
            if f["direction"] not in {"increasing", "decreasing"}:
                raise ContractError("invalid factor direction")
            if type(f["required"]) is not bool or type(f["require_full_window"]) is not bool:
                raise ContractError("required and require_full_window must be booleans")
            if type(f["min_support"]) is not int or f["min_support"] < 0:
                raise ContractError("min_support must be a nonnegative integer")
        bands = c["bands"]
        if not isinstance(bands, list) or not bands or bands[0].get("minimum") != 0:
            raise ContractError("bands must begin at zero")
        names = set()
        previous = -1
        for b in bands:
            strict_fields(b, {"name", "minimum"}, {"name", "minimum"})
            identifier(b["name"], "band")
            number(b["minimum"], "band minimum", maximum=100)
            if b["name"] in names or b["name"] == "REVIEW_REQUIRED" or b["minimum"] <= previous:
                raise ContractError("bands must have unique names and ascending minima")
            names.add(b["name"])
            previous = b["minimum"]
        route_ids = set()
        for r in c["routes"]:
            strict_fields(r, {"id", "feature", "minimum", "action"}, {"id", "feature", "minimum", "action"})
            identifier(r["id"], "route")
            if r["id"] in route_ids or r["feature"] not in known_features:
                raise ContractError("duplicate route or unknown route feature")
            route_ids.add(r["id"])
            number(r["minimum"], "route minimum")
            if not isinstance(r["action"], str) or not r["action"]:
                raise ContractError("route action required")

    @classmethod
    def from_dict(cls, config: dict) -> Policy:
        return cls(config)

    @classmethod
    def load(cls, path: str | Path) -> Policy:
        return cls(json.loads(Path(path).read_text(encoding="utf-8")))

    def to_dict(self) -> dict:
        return deepcopy(self._config)

    def band(self, value: float) -> str:
        number(value, "score", maximum=100)
        return next(b["name"] for b in reversed(self._config["bands"]) if value >= b["minimum"])


def reference_policy() -> Policy:
    groups = [
        {
            "id": "customer",
            "cap": 25,
            "aggregation": "sum",
            "rationale": "Contextual ownership, business and source-of-funds evidence; cap limits accumulation.",
        },
        {
            "id": "geography",
            "cap": 15,
            "aggregation": "max",
            "rationale": "Profile and observed exposure overlap; strongest normalized signal only.",
        },
        {
            "id": "product_channel",
            "cap": 15,
            "aggregation": "sum",
            "rationale": "Separate product and delivery-channel exposures.",
        },
        {
            "id": "behavior",
            "cap": 25,
            "aggregation": "max",
            "rationale": "Overlapping windows describe related activity; no multiple votes for the same period.",
        },
        {
            "id": "context",
            "cap": 10,
            "aggregation": "sum",
            "rationale": "Corroborated contextual evidence, not automatic categorical classification.",
        },
        {
            "id": "evidence",
            "cap": 10,
            "aggregation": "max",
            "rationale": "Documentation and stale-profile uncertainty; completeness also has a separate gate.",
        },
    ]
    factors = []

    def add(
        name,
        feature,
        group,
        weight,
        low=0,
        high=1,
        required=False,
        min_support=0,
        full=False,
        rationale="Illustrative hypothesis; requires approved local calibration.",
    ):
        factors.append(
            {
                "id": name,
                "feature": feature,
                "group": group,
                "weight": weight,
                "low": low,
                "high": high,
                "direction": "increasing",
                "required": required,
                "min_support": min_support,
                "require_full_window": full,
                "rationale": rationale,
            }
        )

    for name, weight in [
        ("ownership_opacity", 10),
        ("business_complexity", 5),
        ("source_of_funds_concern", 10),
    ]:
        add(name, "profile." + name, "customer", weight, required=True)
    add("geography_profile", "profile.geography_exposure", "geography", 15, required=True)
    add("geography_activity", "txn.30d.high_risk_share", "geography", 15, min_support=4, full=True)
    add("product", "profile.product_complexity", "product_channel", 8, required=True)
    add("channel", "profile.channel_opacity", "product_channel", 7, required=True)
    for w in ("7d", "30d", "90d", "last4", "last10"):
        add("cash_" + w, f"txn.{w}.cash_share", "behavior", 15, low=0.2, high=0.8, min_support=4, full=True)
        add(
            "flow_" + w,
            f"txn.{w}.flow_through",
            "behavior",
            12,
            low=0.7,
            high=1,
            min_support=4,
            full=True,
            rationale="Aggregate balance proxy only; lawful treasury/payroll activity can produce the same value.",
        )
    add(
        "expected_volume",
        "txn.30d.expected_volume_ratio",
        "behavior",
        25,
        low=1.5,
        high=5,
        min_support=4,
        full=True,
    )
    add("growth", "txn.30d.growth_ratio", "behavior", 20, low=2, high=8, min_support=4, full=True)
    add("adverse_information", "profile.adverse_information", "context", 8, required=True)
    add(
        "pep_context",
        "profile.pep_exposure",
        "context",
        2,
        required=True,
        rationale="Contextual exposure only; PEP status alone does not impose a high band or adverse action.",
    )
    add("documentation", "profile.documentation_gap", "evidence", 10, required=True)
    add("profile_age", "profile_age_days", "evidence", 10, low=180, high=730)
    return Policy(
        {
            "policy_id": "generic-reference",
            "version": "1.0.0",
            "description": "Illustrative policy for synthetic research. Weights, thresholds and bands are not empirically calibrated or regulator-prescribed.",
            "groups": groups,
            "factors": factors,
            "bands": [
                {"name": "LOW", "minimum": 0},
                {"name": "MODERATE", "minimum": 30},
                {"name": "HIGH", "minimum": 60},
            ],
            "require_complete_history": True,
            "routes": [
                {
                    "id": "screening_review",
                    "feature": "profile.screening_unresolved",
                    "minimum": 0.5,
                    "action": "Refer unresolved screening evidence to the separate screening workflow. No clearance or legal disposition is produced.",
                }
            ],
        }
    )
