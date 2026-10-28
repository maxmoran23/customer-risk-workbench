"""Three-valued compound hypotheses, distinct from scoring and dispositions."""

from __future__ import annotations

from .contracts import ContractError, number, identifier, strict_fields
from .features import FeatureSet, feature_catalog
from .policy import PROFILE_KEYS

OPS = {
    "gt": lambda a, b: a > b,
    "gte": lambda a, b: a >= b,
    "lt": lambda a, b: a < b,
    "lte": lambda a, b: a <= b,
    "eq": lambda a, b: a == b,
}


def validate_condition(condition: dict, depth: int = 0):
    if depth > 12 or not isinstance(condition, dict):
        raise ContractError("condition must be an object nested at most 12 levels")
    combinators = set(condition) & {"all", "any", "not"}
    if combinators:
        if len(combinators) != 1 or len(condition) != 1:
            raise ContractError("one exclusive logical operator required")
        op = next(iter(combinators))
        children = [condition[op]] if op == "not" else condition[op]
        if not isinstance(children, list) or not 1 <= len(children) <= 100:
            raise ContractError("logical operands must be a nonempty bounded list")
        for child in children:
            validate_condition(child, depth + 1)
        return
    strict_fields(
        condition, {"feature", "op", "value", "min_support", "full_window"}, {"feature", "op", "value"}
    )
    if (
        condition["feature"] not in {r["name"] for r in feature_catalog(PROFILE_KEYS)}
        or condition["op"] not in OPS
    ):
        raise ContractError("unknown feature or comparison")
    number(condition["value"], "predicate value")
    if type(condition.get("min_support", 0)) is not int or condition.get("min_support", 0) < 0:
        raise ContractError("min_support must be nonnegative integer")
    if type(condition.get("full_window", False)) is not bool:
        raise ContractError("full_window must be boolean")


def evaluate_condition(condition: dict, features: FeatureSet, *, validated: bool = False) -> dict:
    if not validated:
        validate_condition(condition)
    for op in ("all", "any", "not"):
        if op in condition:
            children = [condition[op]] if op == "not" else condition[op]
            results = [evaluate_condition(child, features, validated=True) for child in children]
            states = [r["state"] for r in results]
            if op == "all":
                state = "FALSE" if "FALSE" in states else ("UNKNOWN" if "UNKNOWN" in states else "TRUE")
            elif op == "any":
                state = "TRUE" if "TRUE" in states else ("UNKNOWN" if "UNKNOWN" in states else "FALSE")
            else:
                state = {"TRUE": "FALSE", "FALSE": "TRUE", "UNKNOWN": "UNKNOWN"}[states[0]]
            return {"operator": op, "state": state, "children": results}
    name = condition["feature"]
    value = features.values.get(name)
    why = "missing_value" if value is None else None
    if name.startswith("txn."):
        window = name.split(".")[1]
        if features.quality["support"].get(window, 0) < condition.get("min_support", 0):
            why = "insufficient_events"
        if condition.get("full_window", False) and not features.quality["complete_windows"].get(
            window, False
        ):
            why = "incomplete_window"
    if value is not None:
        number(value, name)
    state = "UNKNOWN" if why else ("TRUE" if OPS[condition["op"]](value, condition["value"]) else "FALSE")
    return {
        "feature": name,
        "op": condition["op"],
        "threshold": condition["value"],
        "value": value,
        "state": state,
        "reason": why,
    }


def evaluate_patterns(features: FeatureSet, patterns: list[dict] | None = None) -> list[dict]:
    rows = reference_patterns() if patterns is None else patterns
    ids = set()
    results = []
    for rule in rows:
        strict_fields(
            rule,
            {"id", "title", "hypothesis", "condition", "benign_explanation", "next_evidence", "limit"},
            {"id", "title", "hypothesis", "condition", "benign_explanation", "next_evidence", "limit"},
        )
        identifier(rule["id"], "pattern_id")
        if rule["id"] in ids:
            raise ContractError("duplicate pattern_id")
        ids.add(rule["id"])
        result = evaluate_condition(rule["condition"], features)
        results.append(
            {
                **rule,
                "state": result["state"],
                "evaluation": result,
                "authority": "Evidence collection hypothesis only; no automated disposition or extra score points.",
            }
        )
    return results


def reference_patterns() -> list[dict]:
    def p(feature, value, op="gte", support=4):
        result = {"feature": feature, "op": op, "value": value}
        if feature.startswith("txn."):
            result.update(min_support=support, full_window=True)
        return result

    specifications = [
        (
            "cash_volume",
            "Cash volume above declared activity",
            [p("txn.30d.cash_share", 0.6), p("txn.30d.expected_volume_ratio", 2)],
            "Cash-dependent seasonal trade",
            "Seasonal sales, deposits, and declared expected activity",
        ),
        (
            "cash_growth",
            "Growing cash concentration",
            [p("txn.30d.cash_share", 0.6), p("txn.30d.growth_ratio", 3)],
            "Holiday retail demand",
            "Comparable seasonal history and revenue corroboration",
        ),
        (
            "geography_volume",
            "Elevated geography exposure and volume",
            [p("txn.30d.high_risk_share", 0.6), p("txn.30d.expected_volume_ratio", 2)],
            "Documented international supply chain",
            "Counterparty locations, actual purpose, source mapping",
        ),
        (
            "geography_opacity",
            "Geography exposure with opaque ownership",
            [p("profile.geography_exposure", 0.6), p("profile.ownership_opacity", 0.6)],
            "Complex lawful multinational structure",
            "Verified ownership and business explanation",
        ),
        (
            "flow_growth",
            "Balanced flows with activity growth",
            [p("txn.30d.flow_through", 0.85), p("txn.30d.growth_ratio", 3)],
            "Treasury sweeps or settlement",
            "Account purpose and actual linked transfer tracing",
        ),
        (
            "flow_concentration",
            "Balanced flows concentrated in counterparties",
            [p("txn.30d.flow_through", 0.85), p("txn.30d.concentration", 0.5)],
            "Single merchant acquirer or payroll provider",
            "Counterparty identity and contractual relationship",
        ),
        (
            "digital_volume",
            "Digital channel with elevated volume",
            [p("txn.30d.digital_share", 0.7), p("txn.30d.expected_volume_ratio", 2)],
            "Lawful digital asset settlement",
            "Platform purpose, source and destination evidence",
        ),
        (
            "digital_geography",
            "Digital channel and geography exposure",
            [p("txn.30d.digital_share", 0.7), p("txn.30d.high_risk_share", 0.6)],
            "Authorized international service",
            "Mapped jurisdictions and transaction purpose",
        ),
        (
            "ownership_funds",
            "Opaque ownership and source-of-funds concerns",
            [p("profile.ownership_opacity", 0.7), p("profile.source_of_funds_concern", 0.5)],
            "Incomplete onboarding documentation",
            "Ownership chain and independently corroborated funds",
        ),
        (
            "complexity_docs",
            "Complex structure with documentation gaps",
            [p("profile.business_complexity", 0.7), p("profile.documentation_gap", 0.6)],
            "Legitimate multi-entity enterprise",
            "Entity purpose, operational footprint, legal structure",
        ),
        (
            "pep_corroboration",
            "PEP exposure with separate adverse information",
            [p("profile.pep_exposure", 0.5), p("profile.adverse_information", 0.6)],
            "Name ambiguity or unrelated allegations",
            "Identity resolution, source reliability and relevant chronology",
        ),
        (
            "channel_funds",
            "Opaque channel and funds concerns",
            [p("profile.channel_opacity", 0.7), p("profile.source_of_funds_concern", 0.5)],
            "Documented intermediary service",
            "Intermediary controls and underlying transaction purpose",
        ),
        (
            "recent_cash",
            "Recent-event cash concentration",
            [p("txn.last4.cash_share", 0.8), p("txn.last10.cash_share", 0.6)],
            "One recurring cash deposit pattern",
            "Longer history and customer business context",
        ),
        (
            "recent_balanced",
            "Balanced recent incoming and outgoing amounts",
            [p("txn.last4.flow_through", 0.9), p("txn.last10.flow_through", 0.8)],
            "Ordinary payment settlement",
            "Time-ordered linkage; aggregates do not establish pass-through",
        ),
        (
            "short_long_cash",
            "Short and long cash exposure",
            [p("txn.7d.cash_share", 0.7), p("txn.90d.cash_share", 0.6)],
            "Stable cash-intensive business",
            "Consistency with nature and purpose of relationship",
        ),
        (
            "volume_adverse",
            "Volume change with corroborated adverse information",
            [p("txn.30d.expected_volume_ratio", 3), p("profile.adverse_information", 0.6)],
            "Business expansion and unrelated adverse item",
            "Relevance, reliability, event chronology",
        ),
        (
            "stale_complex",
            "Stale profile for complex activity",
            [p("profile_age_days", 365), p("profile.business_complexity", 0.7)],
            "Unchanged business with delayed documentation",
            "Refresh triggered by material changes, policy context",
        ),
        (
            "product_ownership",
            "Complex product and opaque ownership",
            [p("profile.product_complexity", 0.7), p("profile.ownership_opacity", 0.7)],
            "Lawful specialized investment structure",
            "Product use rationale and beneficial ownership evidence",
        ),
        (
            "concentrated_cash",
            "Cash activity concentrated in counterparties",
            [p("txn.30d.cash_share", 0.6), p("txn.30d.concentration", 0.7)],
            "Cash logistics service",
            "Economic counterparty definition and operating model",
        ),
        (
            "large_funds_gap",
            "Elevated activity with weak funds evidence",
            [p("txn.30d.expected_volume_ratio", 4), p("profile.source_of_funds_concern", 0.6)],
            "Documented asset sale",
            "Sale proceeds and source-of-wealth corroboration",
        ),
    ]
    return [
        {
            "id": code,
            "title": title,
            "hypothesis": title + " merits contextual evidence collection.",
            "condition": {"all": conditions},
            "benign_explanation": benign,
            "next_evidence": evidence,
            "limit": "Illustrative thresholds; pattern presence does not establish suspicious activity or customer misconduct.",
        }
        for code, title, conditions, benign, evidence in specifications
    ]
