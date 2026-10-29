from collections import Counter
import math

import pytest

from crw.connections import (attribute_associations, benjamini_hochberg, cramers_v, evaluate_combination,
                             value_pair_screen, wilson)
from crw.contracts import ContractError


def test_benjamini_hochberg_matches_textbook_example():
    p = [0.01, 0.04, 0.03, 0.005]
    # Sorted: 0.005, 0.01, 0.03, 0.04 -> raw m*p/rank = 0.02, 0.02, 0.04, 0.04
    assert benjamini_hochberg(p) == pytest.approx([0.02, 0.04, 0.04, 0.02])


def test_wilson_interval_known_value():
    low, high = wilson(10, 100)
    assert low == pytest.approx(0.0552, abs=1e-4)
    assert high == pytest.approx(0.1744, abs=1e-4)
    assert wilson(0, 0) is None


def test_cramers_v_perfect_and_independent():
    perfect = Counter({("a", "x"): 50, ("b", "y"): 50})
    assert cramers_v(perfect, 100) == pytest.approx(1.0, abs=0.02)
    independent = Counter({("a", "x"): 25, ("a", "y"): 25, ("b", "x"): 25, ("b", "y"): 25})
    assert cramers_v(independent, 100) == 0.0
    assert cramers_v(Counter({("a", "x"): 10}), 10) is None


def _rows(spec):
    rows = []
    for (a, b, y), n in spec.items():
        rows += [{"A": a, "B": b, "outcome": y} for _ in range(n)]
    return rows


def test_interaction_odds_ratio_matches_hand_calculation():
    # Cells (A=a1,B=b1), (a1,b0), (a0,b1), (a0,b0) with events/non-events.
    spec = {("a1", "b1", 1): 40, ("a1", "b1", 0): 60, ("a1", "b0", 1): 10, ("a1", "b0", 0): 90,
            ("a0", "b1", 1): 10, ("a0", "b1", 0): 90, ("a0", "b0", 1): 10, ("a0", "b0", 0): 90}
    screen = value_pair_screen(_rows(spec), ["A", "B"], min_support=50, min_events=5)
    pair = next(c for c in screen["candidates"] if c["a"]["value"] == "a1" and c["b"]["value"] == "b1")
    expected = math.log(40.5 / 60.5) - math.log(10.5 / 90.5) - math.log(10.5 / 90.5) + math.log(10.5 / 90.5)
    assert math.log(pair["interaction_odds_ratio"]) == pytest.approx(expected)
    se = math.sqrt(sum(1 / x for x in (40.5, 60.5, 10.5, 90.5, 10.5, 90.5, 10.5, 90.5)))
    low, high = pair["interaction_log_or_interval"]
    assert high - low == pytest.approx(2 * 1.959963984540054 * se)
    assert pair["rate_both"] == 0.4 and pair["rate_a_without_b"] == 0.1
    assert pair["grade"] == "supported_synergy"


def test_additive_log_odds_gives_no_synergy():
    # Odds: base 1/9; a alone 3/9 (x3); b alone 3/9 (x3); both 9/9 (x9) -> interaction OR = 1.
    spec = {("a1", "b1", 1): 500, ("a1", "b1", 0): 500, ("a1", "b0", 1): 250, ("a1", "b0", 0): 750,
            ("a0", "b1", 1): 250, ("a0", "b1", 0): 750, ("a0", "b0", 1): 100, ("a0", "b0", 0): 900}
    screen = value_pair_screen(_rows(spec), ["A", "B"], min_support=50)
    pair = next(c for c in screen["candidates"] if c["a"]["value"] == "a1" and c["b"]["value"] == "b1")
    assert pair["interaction_odds_ratio"] == pytest.approx(1.0, abs=0.02)
    assert pair["grade"] == "not_supported"


def test_unlabeled_screen_is_structural_only():
    rows = [{"A": "a1", "B": "b1"}] * 40 + [{"A": "a0", "B": "b0"}] * 60
    screen = value_pair_screen(rows, ["A", "B"], min_support=10)
    assert screen["outcome_status"] == "absent" and screen["hypotheses_tested"] == 0
    top = screen["candidates"][0]
    assert top["cooccurrence_lift"] == pytest.approx(100 / 40) or top["cooccurrence_lift"] == pytest.approx(100 / 60)
    assert "grade" not in top


def test_support_gates_and_invalid_outcomes():
    rows = _rows({("a1", "b1", 1): 3, ("a1", "b0", 0): 50, ("a0", "b1", 0): 50, ("a0", "b0", 0): 50})
    screen = value_pair_screen(rows, ["A", "B"], min_support=3, min_events=5)
    pair = next(c for c in screen["candidates"] if c["a"]["value"] == "a1" and c["b"]["value"] == "b1")
    assert pair["grade"] == "insufficient_support"
    with pytest.raises(ContractError):
        value_pair_screen([{"A": "x", "B": "y", "outcome": 2}], ["A", "B"])


def test_associations_report_support():
    rows = [{"A": "x", "B": "x"}] * 20 + [{"A": "y", "B": "y"}] * 20 + [{"A": None, "B": "x"}]
    result = attribute_associations(rows, ["A", "B"], min_n=10)
    assert result[0]["n_both_observed"] == 40 and result[0]["cramers_v"] > 0.9


def test_combination_legs_show_which_condition_contributes():
    rows = []
    rows += [{"A": "a", "B": "b", "C": "c", "outcome": 1}] * 30 + [{"A": "a", "B": "b", "C": "c", "outcome": 0}] * 20
    rows += [{"A": "a", "B": "b", "C": "x", "outcome": 1}] * 28 + [{"A": "a", "B": "b", "C": "x", "outcome": 0}] * 22
    rows += [{"A": "z", "B": "b", "C": "c", "outcome": 1}] * 5 + [{"A": "z", "B": "b", "C": "c", "outcome": 0}] * 45
    rows += [{"A": "a", "B": "z", "C": "c", "outcome": 1}] * 5 + [{"A": "a", "B": "z", "C": "c", "outcome": 0}] * 45
    result = evaluate_combination(rows, {"A": ["a"], "B": ["b"], "C": ["c"]})
    legs = {leg["condition"]: leg for leg in result["legs"]}
    assert result["rate"] == pytest.approx(0.6)
    assert legs["C"]["complement_rate"] == pytest.approx(0.56)
    assert legs["C"]["p_value_vs_full"] > 0.5
    assert legs["A"]["p_value_vs_full"] < 0.001 and legs["B"]["p_value_vs_full"] < 0.001


def test_planted_synergy_recovered_and_null_not(tmp_path):
    from crw.attributes import Catalog
    from crw.program_reference import reference_catalog
    from crw.synthetic_program import generate_parties

    catalog = Catalog(reference_catalog())
    parties = generate_parties(catalog, 20000, 11)
    rows = [{**p["values"], "outcome": p["outcome"]} for p in parties]
    screen = value_pair_screen(rows, list(catalog.attributes), catalog=catalog)
    grade = {frozenset([c["a"]["value"], c["b"]["value"]]): c.get("grade") for c in screen["candidates"]}
    assert grade[frozenset(["financial_institution_nonbank", "third_party_unrelated"])] == "supported_synergy"
    assert grade[frozenset(["trust", "inheritance_or_gift"])] == "not_supported"
    proxies = [c for c in screen["candidates"] if c.get("possible_proxy_of")]
    assert any("money_services_business" in (c["a"]["value"], c["b"]["value"]) for c in proxies)


def test_combination_and_screen_input_validation():
    rows = [{"A": "a1", "B": "b", "outcome": 1}] * 5
    with pytest.raises(ContractError, match="nonempty list"):
        evaluate_combination(rows, {"A": "a1", "B": ["b"]})
    with pytest.raises(ContractError, match="nonempty list"):
        evaluate_combination(rows, {"A": [], "B": ["b"]})
    with pytest.raises(ContractError, match="distinct"):
        value_pair_screen(rows, ["A", "A"])
    with pytest.raises(ContractError, match="value ids"):
        value_pair_screen([{"A": ["x"], "B": "b", "outcome": 1}], ["A", "B"])
    with pytest.raises(ContractError):
        wilson(5, 3)
