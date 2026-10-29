import pytest

from crw.attributes import Catalog
from crw.contracts import ContractError
from crw.program import program_status
from crw.program_reference import reference_catalog, reference_model, reference_rules
from crw.rules import REVIEW, CategoricalModel, RuleSet, evaluate, simulate_rules


@pytest.fixture
def setup():
    catalog = Catalog(reference_catalog())
    model = CategoricalModel(reference_model(), catalog)
    return catalog, model, RuleSet(reference_rules(), catalog, model)


def individual(**values):
    base = {"entity_type": "individual", "occupation": "salaried_employee", "source_of_wealth": "employment_income",
            "source_of_funds": "payroll", "jurisdiction_exposure": "domestic_only", "account_purpose": "long_term_investment"}
    base.update(values)
    return {"party_id": "P1", "entity_type": "individual", "segment": "S", "values": base}


def test_hand_computed_weighted_score(setup):
    _, model, _ = setup
    party = individual(occupation="retired", source_of_funds="cash_deposit")
    # Weights for individuals: entity 1.0, occupation 1.0, wealth 1.2, funds 1.5, jurisdiction 1.5, purpose 1.0.
    expected = (50 * 1.0 + 45 * 1.0 + 50 * 1.2 + 60 * 1.5 + 50 * 1.5 + 50 * 1.0) / 7.2
    result = model.assess(party)
    assert result["score"] == pytest.approx(expected)
    assert result["base_tier"] == model.band(expected) == "MODERATE"


def test_missing_value_is_neutral_and_listed(setup):
    _, model, _ = setup
    result = model.assess(individual(occupation=None))
    assert result["missing"] == ["occupation"] and result["score"] == pytest.approx(50)
    config = reference_model() | {"missing": "abstain"}
    abstaining = CategoricalModel(config, model.catalog)
    assert abstaining.assess(individual(occupation=None))["tier"] == REVIEW


def test_trigger_floor_beats_abstention_and_cap(setup):
    catalog, _, _ = setup
    abstaining = CategoricalModel(reference_model() | {"missing": "abstain"}, catalog)
    party = individual(occupation=None, jurisdiction_exposure="comprehensively_sanctioned")
    assert abstaining.assess(party)["tier"] == "VERY_HIGH"


def test_override_low_caps_only_without_floors(setup):
    _, model, rules = setup
    gov = {"party_id": "G", "entity_type": "government_entity", "values": {
        "entity_type": "government_entity", "source_of_wealth": "undocumented", "source_of_funds": "unverified",
        "jurisdiction_exposure": "domestic_only", "account_purpose": "unclear_or_pass_through"}}
    assert model.assess(gov)["base_tier"] != "LOW" and model.assess(gov)["tier"] == "LOW"
    gov["values"]["jurisdiction_exposure"] = "elevated_risk"
    assert model.assess(gov, rules)["tier"] == "HIGH"


def test_three_valued_logic_and_applicability():
    cond = {"all": [{"attribute": "a", "in": ["x"]}, {"attribute": "b", "in": ["y"]}]}
    assert evaluate(cond, {"a": "x", "b": "y"}) == "TRUE"
    assert evaluate(cond, {"a": "x", "b": None}) == "UNKNOWN"
    assert evaluate(cond, {"a": "z", "b": None}) == "FALSE"
    assert evaluate({"any": cond["all"]}, {"a": None, "b": "y"}) == "TRUE"
    assert evaluate({"not": cond["all"][0]}, {"a": None}) == "UNKNOWN"
    assert evaluate(cond, {"a": "x"}, applicable={"a"}) == "NOT_APPLICABLE"
    assert evaluate({"not": {"attribute": "b", "in": ["y"]}}, {}, applicable={"a"}) == "NOT_APPLICABLE"
    assert evaluate(cond, {"a": "z"}, applicable={"a"}) == "FALSE"


def test_unknown_rule_that_could_raise_tier_is_flagged(setup):
    _, model, rules = setup
    party = individual(jurisdiction_exposure=None)
    result = model.assess(party, rules)
    assert "ATOM-02" in result["rules_unknown"]
    assert "unknown_rule_could_raise_tier:ATOM-02" in result["review_flags"]


def test_compound_rule_requires_every_leg(setup):
    _, model, rules = setup
    nbfi = {"party_id": "N", "entity_type": "financial_institution_nonbank", "values": {
        "entity_type": "financial_institution_nonbank", "nature_of_business": "professional_services",
        "listed_status": "unlisted_unregulated_structure", "source_of_wealth": "business_ownership",
        "source_of_funds": "third_party_unrelated", "jurisdiction_exposure": "domestic_only",
        "account_purpose": "operating_or_payroll"}}
    assert model.assess(nbfi, rules)["tier"] == "VERY_HIGH"
    assert "COMP-01" in model.assess(nbfi, rules)["rules_fired"]
    nbfi["values"]["listed_status"] = "unlisted_private"
    assert "COMP-01" not in model.assess(nbfi, rules)["rules_fired"]


def test_ruleset_validation(setup):
    catalog, model, _ = setup
    bad = reference_rules()
    bad["rules"][0]["condition"] = {"attribute": "nature_of_business", "in": ["casino_on_mars"]}
    with pytest.raises(ContractError, match="unknown value"):
        RuleSet(bad, catalog, model)
    bad = reference_rules()
    bad["rules"][0]["evidence"] = []
    with pytest.raises(ContractError, match="evidence"):
        RuleSet(bad, catalog, model)
    bad = reference_rules()
    bad["rules"][0]["effect"] = {"type": "floor", "tier": "EXTREME"}
    with pytest.raises(ContractError, match="model tier"):
        RuleSet(bad, catalog, model)


def test_unnormalized_party_value_rejected(setup):
    _, model, _ = setup
    with pytest.raises(ContractError, match="not normalized"):
        model.assess(individual(occupation="Astronaut"))
    with pytest.raises(ContractError, match="disagrees"):
        model.assess(individual(entity_type="trust"))


def test_simulation_redundancy_and_marginal(setup):
    catalog, model, _ = setup
    config = reference_rules()
    config["rules"].append({
        "id": "ATOM-99", "title": "Subset of ATOM-01", "condition": {"attribute": "nature_of_business", "in": ["money_services_business"]},
        "effect": {"type": "floor", "tier": "MODERATE"}, "evidence": ["FFIEC-NBFI"], "rationale": "test", "status": "proposed"})
    rules = RuleSet(config, catalog, model)
    msb = {"party_id": "M", "entity_type": "private_company", "segment": "S", "values": {
        "entity_type": "private_company", "nature_of_business": "money_services_business", "listed_status": "unlisted_private",
        "source_of_wealth": "business_ownership", "source_of_funds": "external_bank_transfer",
        "jurisdiction_exposure": "domestic_only", "account_purpose": "operating_or_payroll"}}
    result = simulate_rules([msb, individual()], model, rules)
    assert {"rule": "ATOM-99", "contained_in": "ATOM-01"}.items() <= result["population_redundancy"][0].items()
    by_id = {r["rule_id"]: r for r in result["rules"]}
    assert by_id["ATOM-01"]["marginal_tier_changes"] == 1
    assert by_id["ATOM-99"]["marginal_tier_changes"] == 0 and by_id["ATOM-99"]["shadowed_share"] == 1.0
    assert by_id["ATOM-01"]["unknown"] == 0


def test_program_gates_block_downstream_stages():
    scoping = {"unresolved_share": 0.0, "unmapped_role_codes": {}, "conflicting_entity_type_parties": 0}
    coverage = {"totals": {"classified_share": 0.9, "reviewed_share": 0.5, "overrides": 2, "overrides_evidenced": 2}}
    status = program_status({"scoping": scoping, "coverage": coverage, "normalization_audit": {"status": "clean"},
                             "connections": {"outcome_status": "absent", "pairs_screened": 3}})
    states = {s["stage"]: s["status"] for s in status["stages"]}
    assert states["population_scoping"] == states["entity_segmentation"] == "complete"
    assert states["value_classification"] == "in_progress"
    assert states["connections_review"] == "blocked" and states["output_validation"] == "blocked"
    assert status["next_actionable"] == "value_classification"
    coverage["totals"].update(classified_share=1.0, reviewed_share=1.0)
    states = {s["stage"]: s["status"] for s in program_status(
        {"scoping": scoping, "coverage": coverage, "normalization_audit": {"status": "clean"},
         "connections": {"outcome_status": "absent", "pairs_screened": 3}})["stages"]}
    assert states["connections_review"] == "complete" and states["rule_design"] == "not_started"
    assert states["weighting_and_calibration"] == "blocked"
    with pytest.raises(ContractError):
        program_status({}, {"made_up": 1})


def test_override_values_apply_even_when_attribute_is_unweighted(setup):
    catalog, _, _ = setup
    config = reference_model()
    del config["weights"]["jurisdiction_exposure"]
    model = CategoricalModel(config, catalog)
    assert model.assess(individual(jurisdiction_exposure="comprehensively_sanctioned"))["tier"] == "VERY_HIGH"


def test_score_exactly_at_tier_minimum_is_not_demoted(setup):
    catalog, _, _ = setup
    config = reference_model()
    config["weights"] = {"source_of_wealth": 0.1, "source_of_funds": 0.1, "account_purpose": 0.1}
    config["tiers"] = [{"name": "LOW", "minimum": 0}, {"name": "MODERATE", "minimum": 50.5},
                       {"name": "HIGH", "minimum": 60}, {"name": "VERY_HIGH", "minimum": 90}]
    model = CategoricalModel(config, catalog)
    party = individual(source_of_wealth="undocumented", source_of_funds="unverified", account_purpose="unclear_or_pass_through")
    party["values"].update(source_of_wealth="undocumented", source_of_funds="unverified")
    for key in ("source_of_wealth", "source_of_funds", "account_purpose"):
        assert catalog.assignment(key, party["values"][key])["score"] == 70
    config["tiers"][2]["minimum"] = 70
    config["tiers"][3]["minimum"] = 90
    model = CategoricalModel(config, catalog)
    assert model.assess(party)["base_tier"] == "HIGH"


def test_malformed_party_and_rule_inputs_raise_contract_errors(setup):
    catalog, model, _ = setup
    with pytest.raises(ContractError):
        model.assess(individual(occupation=["retired"]))
    with pytest.raises(ContractError, match="does not apply"):
        model.assess(individual(listed_status="unlisted_private"))
    bad = reference_rules()
    bad["rules"][0]["effect"] = "floor HIGH"
    with pytest.raises(ContractError, match="effect must be an object"):
        RuleSet(bad, catalog, model)
