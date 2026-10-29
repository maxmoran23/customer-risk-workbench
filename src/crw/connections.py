"""Cross-attribute connection analysis for compound-rule design.

Three questions, kept separate because they need different evidence:

1. Structure: which attributes are associated at all (bias-corrected Cramer's V), and how much data supports it.
2. Synergy: for value pairs, does the outcome rate when both are present exceed what the two values predict
   separately? Measured as the interaction term of a saturated two-indicator logistic model (the interaction
   odds ratio), with Wald intervals and Benjamini-Hochberg control across every tested pair.
3. Contribution: for a proposed multi-attribute combination, does each condition add to the rate of the others?

Without outcome labels only question 1 and co-occurrence lift are answerable. Labels are adopter-defined
review outcomes, never a proxy for confirmed misconduct.
"""

from __future__ import annotations

from collections import Counter
from itertools import combinations
import math

from .contracts import ContractError, number

Z95 = 1.959963984540054


def _normal_two_sided(z: float) -> float:
    return math.erfc(abs(z) / math.sqrt(2))


def wilson(events: int, n: int, z: float = Z95) -> tuple[float, float] | None:
    if n <= 0:
        return None
    if not 0 <= events <= n:
        raise ContractError("events must lie between 0 and n")
    p = events / n
    denominator = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denominator
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denominator
    return (max(0.0, centre - half), min(1.0, centre + half))


def benjamini_hochberg(p_values: list[float]) -> list[float]:
    """Step-up adjusted q-values, monotone, in the input order."""
    m = len(p_values)
    order = sorted(range(m), key=lambda i: p_values[i])
    q = [0.0] * m
    running = 1.0
    for rank in range(m, 0, -1):
        i = order[rank - 1]
        running = min(running, p_values[i] * m / rank)
        q[i] = min(1.0, running)
    return q


def _observed(row: dict, attribute: str):
    value = row.get(attribute)
    if value in (None, ""):
        return None
    if not isinstance(value, str):
        raise ContractError(f"{attribute} values must be normalized value ids (text) or null")
    return value


def _outcome(row: dict, key: str):
    value = row.get(key)
    if value is None:
        return None
    if value not in (0, 1) or isinstance(value, bool):
        raise ContractError("outcome must be 0, 1 or null")
    return value


def cramers_v(table: Counter, n: int) -> float | None:
    """Bias-corrected Cramer's V (Bergsma 2013). None when undefined."""
    rows = Counter()
    cols = Counter()
    for (a, b), count in table.items():
        rows[a] += count
        cols[b] += count
    r, k = len(rows), len(cols)
    if n < 2 or r < 2 or k < 2:
        return None
    chi2 = 0.0
    for a, ra in rows.items():
        for b, cb in cols.items():
            expected = ra * cb / n
            chi2 += (table.get((a, b), 0) - expected) ** 2 / expected
    phi2 = chi2 / n
    phi2c = max(0.0, phi2 - (k - 1) * (r - 1) / (n - 1))
    rc = r - (r - 1) ** 2 / (n - 1)
    kc = k - (k - 1) ** 2 / (n - 1)
    denominator = min(kc - 1, rc - 1)
    return math.sqrt(phi2c / denominator) if denominator > 0 else None


def attribute_associations(rows: list[dict], attributes: list[str], min_n: int = 30) -> list[dict]:
    if type(min_n) is not int or min_n < 2:
        raise ContractError("min_n must be an integer of at least 2")
    if len(set(attributes)) != len(attributes):
        raise ContractError("attributes must be distinct")
    total = len(rows)
    results = []
    for a, b in combinations(attributes, 2):
        table = Counter()
        for row in rows:
            va, vb = _observed(row, a), _observed(row, b)
            if va is not None and vb is not None:
                table[(va, vb)] += 1
        n = sum(table.values())
        v = cramers_v(table, n) if n >= min_n else None
        results.append(
            {
                "attributes": [a, b],
                "n_both_observed": n,
                "joint_coverage": n / total if total else None,
                "cramers_v": v,
                "status": "measured" if v is not None else "insufficient_support",
            }
        )
    return sorted(results, key=lambda r: (r["cramers_v"] is None, -(r["cramers_v"] or 0)))


def _interaction(cells: dict) -> tuple[float, float]:
    """Interaction log odds ratio and Woolf standard error with Haldane-Anscombe 0.5 correction."""
    log_or = 0.0
    variance = 0.0
    for key, sign in (("11", 1), ("10", -1), ("01", -1), ("00", 1)):
        events, n = cells[key]
        e, ne = events + 0.5, n - events + 0.5
        log_or += sign * math.log(e / ne)
        variance += 1 / e + 1 / ne
    return log_or, math.sqrt(variance)


def value_pair_screen(
    rows: list[dict],
    attributes: list[str],
    *,
    outcome: str | None = "outcome",
    min_support: int = 30,
    min_events: int = 5,
    alpha: float = 0.05,
    catalog=None,
    stage: str = "proposed",
) -> dict:
    """Screen all cross-attribute value pairs for co-occurrence and, when labeled, outcome synergy."""
    for name, value in (("min_support", min_support), ("min_events", min_events)):
        if type(value) is not int or value < 1:
            raise ContractError(f"{name} must be a positive integer")
    number(alpha, "alpha", minimum=1e-9, maximum=0.5)
    if len(set(attributes)) != len(attributes):
        raise ContractError("attributes must be distinct")
    labeled = outcome is not None and any(row.get(outcome) is not None for row in rows)
    candidates, tested_p = [], []
    for a, b in combinations(attributes, 2):
        joint = Counter()
        joint_events = Counter()
        for row in rows:
            va, vb = _observed(row, a), _observed(row, b)
            if va is None or vb is None:
                continue
            y = _outcome(row, outcome) if labeled else None
            if labeled and y is None:
                continue
            joint[(va, vb)] += 1
            joint_events[(va, vb)] += y or 0
        n_total = sum(joint.values())
        e_total = sum(joint_events.values())
        if not n_total:
            continue
        na, nb, ea, eb = Counter(), Counter(), Counter(), Counter()
        for (va, vb), n in joint.items():
            na[va] += n
            nb[vb] += n
            ea[va] += joint_events[(va, vb)]
            eb[vb] += joint_events[(va, vb)]
        for (va, vb), n11 in joint.items():
            if n11 < min_support:
                continue
            lift = n11 * n_total / (na[va] * nb[vb])
            item = {
                "a": {"attribute": a, "value": va},
                "b": {"attribute": b, "value": vb},
                "support": n11,
                "support_share": n11 / n_total,
                "cooccurrence_lift": lift,
                "n_pair_observed": n_total,
            }
            if catalog is not None:
                triggered = [
                    f"{x}/{y}"
                    for x, y in ((a, va), (b, vb))
                    if (catalog.assignment(x, y, stage) or {}).get("class") == "override_high"
                ]
                item["already_triggered_by"] = triggered
            if labeled:
                e11 = joint_events[(va, vb)]
                n10, e10 = na[va] - n11, ea[va] - e11
                n01, e01 = nb[vb] - n11, eb[vb] - e11
                n00 = n_total - n11 - n10 - n01
                e00 = e_total - e11 - e10 - e01
                cells = {"11": (e11, n11), "10": (e10, n10), "01": (e01, n01), "00": (e00, n00)}
                rates = {k: (e / n if n else None) for k, (e, n) in cells.items()}
                item.update(
                    events=e11,
                    rate_both=rates["11"],
                    rate_both_interval=wilson(e11, n11),
                    rate_a_without_b=rates["10"],
                    rate_b_without_a=rates["01"],
                    rate_neither=rates["00"],
                )
                if e11 < min_events or min(n10, n01, n00) == 0:
                    item["grade"] = "insufficient_support"
                else:
                    log_or, se = _interaction(cells)
                    z = log_or / se
                    item.update(
                        interaction_odds_ratio=math.exp(log_or),
                        interaction_log_or_interval=(log_or - Z95 * se, log_or + Z95 * se),
                        p_value=_normal_two_sided(z),
                    )
                    item["_test_index"] = len(tested_p)
                    tested_p.append(item["p_value"])
            candidates.append(item)
    q_values = benjamini_hochberg(tested_p) if tested_p else []
    for item in candidates:
        index = item.pop("_test_index", None)
        if index is None:
            continue
        item["q_value"] = q_values[index]
        if item["q_value"] <= alpha:
            item["grade"] = "supported_synergy" if item["interaction_odds_ratio"] > 1 else "supported_antagonism"
        elif item["p_value"] <= alpha:
            item["grade"] = "unadjusted_signal_only"
        else:
            item["grade"] = "not_supported"
    if labeled:
        order = {"supported_synergy": 0, "supported_antagonism": 1, "unadjusted_signal_only": 2,
                 "not_supported": 3, "insufficient_support": 4}
        candidates.sort(key=lambda r: (order[r["grade"]], r.get("q_value", 1), -r["support"]))
        _annotate_proxies(candidates)
    else:
        candidates.sort(key=lambda r: (-r["cooccurrence_lift"], -r["support"]))
    grades = Counter(c.get("grade", "structural_only") for c in candidates)
    return {
        "outcome_status": "labeled" if labeled else "absent",
        "attributes": list(attributes),
        "settings": {"min_support": min_support, "min_events": min_events, "alpha": alpha},
        "pairs_screened": len(candidates),
        "hypotheses_tested": len(tested_p),
        "grade_counts": dict(grades),
        "candidates": candidates,
        "method": (
            "Interaction odds ratio from the four cells (both, a only, b only, neither) among rows with both "
            "attributes and the outcome observed; Woolf standard error with 0.5 cell correction; two-sided Wald "
            "test; Benjamini-Hochberg false-discovery control across all tested pairs."
            if labeled
            else "Co-occurrence lift only: observed joint frequency divided by the product of marginals."
        ),
        "limits": [
            "Associations and interactions are descriptive and population-specific; they do not establish causation or misconduct.",
            "Outcome labels inherit the selection and review practices that produced them; a synergy may reflect past review focus.",
            "Pairs below support thresholds are not evidence of no connection; they are unmeasured.",
            "Values already carrying an override_high class cannot raise the tier further through a compound rule.",
        ],
    }


def _annotate_proxies(candidates: list[dict], min_lift: float = 2.0) -> None:
    """Flag supported pairs that may restate a stronger supported pair through a correlated value.

    A pair sharing one value with a stronger supported pair, whose other value co-occurs with the stronger
    pair's other value at lift >= ``min_lift``, is marked ``possible_proxy_of``. Confirm with a stratified or
    multivariable analysis before designing a rule on it.
    """
    lift = {}
    for c in candidates:
        key = frozenset([(c["a"]["attribute"], c["a"]["value"]), (c["b"]["attribute"], c["b"]["value"])])
        lift[key] = c["cooccurrence_lift"]
    supported = [c for c in candidates if c.get("grade", "").startswith("supported")]
    for i, c in enumerate(supported):
        mine = {(c["a"]["attribute"], c["a"]["value"]), (c["b"]["attribute"], c["b"]["value"])}
        for stronger in supported[:i]:
            theirs = {(stronger["a"]["attribute"], stronger["a"]["value"]),
                      (stronger["b"]["attribute"], stronger["b"]["value"])}
            shared = mine & theirs
            if len(shared) != 1:
                continue
            (x,), (y,) = mine - shared, theirs - shared
            if x[0] != y[0] and lift.get(frozenset([x, y]), 0) >= min_lift:
                c["possible_proxy_of"] = sorted(f"{a}/{v}" for a, v in theirs)
                break


def _matches(row: dict, conditions: dict) -> bool | None:
    for attribute, allowed in conditions.items():
        value = _observed(row, attribute)
        if value is None:
            return None
        if value not in allowed:
            return False
    return True


def _two_proportion_p(e1: int, n1: int, e2: int, n2: int) -> float | None:
    if not n1 or not n2:
        return None
    pooled = (e1 + e2) / (n1 + n2)
    se = math.sqrt(pooled * (1 - pooled) * (1 / n1 + 1 / n2))
    if se == 0:
        return None
    return _normal_two_sided((e1 / n1 - e2 / n2) / se)


def evaluate_combination(rows: list[dict], conditions: dict, *, outcome: str = "outcome") -> dict:
    """Does every condition of a proposed compound rule contribute?

    For each condition, compare the full combination's outcome rate with rows meeting all other conditions
    but not this one. A condition whose complement has a similar rate adds support, not discrimination.
    """
    if not isinstance(conditions, dict) or len(conditions) < 2:
        raise ContractError("a combination needs at least two attribute conditions")
    for attribute, allowed in conditions.items():
        if not isinstance(allowed, list) or not allowed or not all(isinstance(v, str) for v in allowed):
            raise ContractError(f"{attribute}: allowed values must be a nonempty list of value ids")
    conditions = {a: set(v) for a, v in conditions.items()}
    attributes = sorted(conditions)
    observed = [r for r in rows if all(_observed(r, a) is not None for a in attributes)
                and _outcome(r, outcome) is not None]
    full = [r for r in observed if _matches(r, conditions)]
    e_full = sum(r[outcome] for r in full)
    base_e = sum(r[outcome] for r in observed)
    legs = []
    for attribute in attributes:
        others = {a: v for a, v in conditions.items() if a != attribute}
        complement = [r for r in observed if _matches(r, others) and _observed(r, attribute) not in conditions[attribute]]
        e_c = sum(r[outcome] for r in complement)
        legs.append(
            {
                "condition": attribute,
                "complement_support": len(complement),
                "complement_rate": e_c / len(complement) if complement else None,
                "complement_interval": wilson(e_c, len(complement)),
                "p_value_vs_full": _two_proportion_p(e_full, len(full), e_c, len(complement)),
            }
        )
    return {
        "conditions": {a: sorted(v) for a, v in conditions.items()},
        "rows_fully_observed": len(observed),
        "support": len(full),
        "events": e_full,
        "rate": e_full / len(full) if full else None,
        "rate_interval": wilson(e_full, len(full)),
        "base_rate": base_e / len(observed) if observed else None,
        "legs": legs,
        "limit": "Unadjusted per-leg comparisons for design discussion. Pre-register combinations or adjust for multiplicity before treating any as confirmed.",
    }
