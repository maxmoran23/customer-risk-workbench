from copy import deepcopy

import pytest

from crw.attributes import (Catalog, audit_normalization, canonical_text, export_workbook, import_inventory,
                            inventory_rows, read_csv_rows, review_coverage, review_diff, scope_population,
                            validate_assignment)
from crw.contracts import ContractError
from crw.program_reference import reference_catalog, reference_party_roles

SCALE = {"minimum": 0, "maximum": 100, "neutral": 50}


@pytest.fixture
def catalog():
    return Catalog(reference_catalog())


@pytest.mark.parametrize("assignment", [
    {"class": "neutral", "score": 49},
    {"class": "elevator", "score": 50},
    {"class": "mitigator", "score": 50},
    {"class": "override_high", "score": 90},
    {"class": "elevator", "score": None},
    {"class": "unknown", "score": 60},
    {"class": "elevator", "score": 101},
])
def test_assignment_class_and_score_must_agree(assignment):
    with pytest.raises(ContractError):
        validate_assignment(assignment, SCALE, "x")


def test_valid_assignments_pass():
    for a in ({"class": "neutral", "score": 50}, {"class": "elevator", "score": 50.5},
              {"class": "mitigator", "score": 0}, {"class": "override_low", "score": None}):
        validate_assignment(a, SCALE, "x")


def _mutate(path, value):
    config = reference_catalog()
    target = config
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    return config


def test_override_without_evidence_is_rejected():
    config = reference_catalog()
    value = config["attributes"][1]["values"][12]
    assert value["id"] == "unregistered_money_transmission"
    value["evidence"] = []
    with pytest.raises(ContractError, match="evidence"):
        Catalog(config)


def test_proposal_requires_status_and_rationale():
    config = reference_catalog()
    value = config["attributes"][0]["values"][0]
    value["proposed"] = {"class": "elevator", "score": 55}
    with pytest.raises(ContractError, match="unreviewed"):
        Catalog(config)
    value["status"] = "proposed"
    with pytest.raises(ContractError, match="rationale"):
        Catalog(config)
    value["rationale"] = "test"
    with pytest.raises(ContractError, match="change of class requires"):
        Catalog(config)
    value["evidence"] = ["FATF-RBA-BANK"]
    Catalog(config)


def test_agreed_requires_complete_decision_record():
    config = reference_catalog()
    value = next(v for v in config["attributes"][1]["values"] if v["id"] == "parking_garage")
    value["status"] = "agreed"
    with pytest.raises(ContractError, match="decision"):
        Catalog(config)
    value["decision"] = {"by_role": "policy owner", "date": "2026-13-01", "reference": "REF-1"}
    with pytest.raises(ContractError, match="date"):
        Catalog(config)
    value["decision"]["date"] = "2026-11-01"
    Catalog(config)


def test_unknown_evidence_and_entity_type_rejected():
    config = reference_catalog()
    config["attributes"][0]["values"][4]["evidence"] = ["NOPE"]
    with pytest.raises(ContractError, match="unknown evidence"):
        Catalog(config)
    config = reference_catalog()
    config["attributes"][2]["applies_to"] = ["martian"]
    with pytest.raises(ContractError, match="undeclared entity"):
        Catalog(config)


def test_stage_assignment_falls_back_to_current(catalog):
    assert catalog.assignment("nature_of_business", "parking_garage", "current") == {"class": "neutral", "score": 50}
    assert catalog.assignment("nature_of_business", "parking_garage", "proposed") == {"class": "elevator", "score": 60}
    assert catalog.assignment("nature_of_business", "restaurant", "proposed") == {"class": "elevator", "score": 60}
    assert catalog.assignment("nature_of_business", "online_marketplace_seller") is None


def test_review_diff_classifies_and_orders_direction(catalog):
    diff = review_diff(catalog)
    by_id = {c["value_id"]: c for c in diff["changes"]}
    assert by_id["parking_garage"]["change"] == "reclassified" and by_id["parking_garage"]["direction"] == "up"
    assert by_id["privately_owned_atm_operator"]["direction"] == "up"
    assert by_id["virtual_asset_service_provider"]["direction"] == "down"
    assert diff["counts"]["reclassified"] == 3


def test_coverage_counts_unclassified_and_overrides(catalog):
    coverage = review_coverage(catalog)
    totals = coverage["totals"]
    assert totals["values"] == 56
    assert totals["classified"] == 55
    assert totals["overrides"] == totals["overrides_evidenced"] == 4
    nob = next(r for r in coverage["attributes"] if r["attribute_id"] == "nature_of_business")
    assert nob["unclassified"] == ["online_marketplace_seller"]


def test_canonical_text():
    assert canonical_text("  Liquor   Store ") == canonical_text("liquor-store") == "liquor store"
    assert canonical_text("Art & Antiques") == "art and antiques"
    assert canonical_text("ＡＴＭ") == "atm"


def test_normalization_audit_finds_each_defect(catalog):
    rows = [
        {"attribute_id": "nature_of_business", "source_system": "S1", "source_value": "Liquor store", "value_id": "liquor_store", "party_count": "10"},
        {"attribute_id": "nature_of_business", "source_system": "S2", "source_value": "LIQUOR-STORE", "value_id": "general_retail", "party_count": "5"},
        {"attribute_id": "nature_of_business", "source_system": "S2", "source_value": "Gas station", "value_id": "", "party_count": "5"},
        {"attribute_id": "nature_of_business", "source_system": "S1", "source_value": "Store, liquor", "value_id": "restaurant", "party_count": "0"},
        {"attribute_id": "nature_of_business", "source_system": "S1", "source_value": "Liquor store", "value_id": "liquor_store", "party_count": "1"},
        {"attribute_id": "made_up", "source_system": "S1", "source_value": "x", "value_id": "y"},
        {"attribute_id": "occupation", "source_system": "S1", "source_value": "x", "value_id": "astronaut"},
    ]
    audit = audit_normalization(catalog, rows)
    counts = audit["issue_counts"]
    assert counts["conflicting_mapping"] == 1
    assert counts["unmapped"] == 1
    assert counts["duplicate_rows"] == 1
    assert counts["unknown_attribute"] == 1
    assert counts["unknown_value"] == 1
    assert counts["fragmentation_candidates"] >= 1
    assert audit["status"] == "blocking_issues"
    assert audit["party_coverage"] == pytest.approx(15 / 20)
    assert counts["orphan_catalog_values"] == 56 - 3


def test_workbook_round_trip_applies_only_review_fields(tmp_path, catalog):
    result = export_workbook(catalog, tmp_path)
    assert "README.md" in result["files"] and len(result["files"]) == 2 * len(catalog.attributes) + 2
    sheet = (tmp_path / "02-nature_of_business.md").read_text(encoding="utf-8")
    for heading in ("1. Instructions", "2. Attribute profile", "3. Research evidence", "4. Value inventory"):
        assert heading in sheet
    rows = read_csv_rows(tmp_path / "02-nature_of_business-inventory.csv")
    target = next(r for r in rows if r["value_id"] == "online_marketplace_seller")
    target.update(proposed_class="elevator", proposed_score="55", evidence_ids="FATF-RBA-BANK",
                  rationale="Marketplace sellers can mix third-party receipts.", status="proposed")
    updated, log = import_inventory(catalog, rows)
    assert len(log) == 1 and log[0]["value_id"] == "online_marketplace_seller"
    assert updated.assignment("nature_of_business", "online_marketplace_seller") == {"class": "elevator", "score": 55}
    assert updated.digest != catalog.digest


def test_import_rejects_current_edits_and_invalid_scores(catalog):
    rows = inventory_rows(catalog)
    tampered = deepcopy(rows)
    tampered[0]["current_score"] = "55"
    with pytest.raises(ContractError, match="read-only"):
        import_inventory(catalog, tampered)
    bad = deepcopy(rows)
    row = next(r for r in bad if r["value_id"] == "restaurant")
    row.update(proposed_class="mitigator", proposed_score="60", rationale="x", status="proposed")
    with pytest.raises(ContractError, match="below neutral"):
        import_inventory(catalog, bad)


def test_unchanged_inventory_imports_without_changes(catalog):
    updated, log = import_inventory(catalog, inventory_rows(catalog))
    assert log == [] and updated.digest == catalog.digest


def test_scoping_precedence_and_gaps():
    rows = [
        {"party_id": "P1", "role_code": "account_holder", "entity_type": "individual"},
        {"party_id": "P1", "role_code": "contingent_beneficiary", "entity_type": "individual"},
        {"party_id": "P2", "role_code": "contingent_beneficiary", "entity_type": "individual"},
        {"party_id": "P3", "role_code": "trustee", "entity_type": "individual"},
        {"party_id": "P4", "role_code": "mystery_role", "entity_type": "individual"},
        {"party_id": "P5", "role_code": "trustee", "entity_type": "individual"},
        {"party_id": "P5", "role_code": "mystery_role", "entity_type": "trust"},
    ]
    result = scope_population(reference_party_roles(), rows)
    assert result["scope_counts"] == {"customer": 1, "related_with_influence": 2, "related_without_influence": 1,
                                      "unresolved": 1}
    assert result["rated_population"] == 3
    assert result["unmapped_role_codes"] == {"mystery_role": 2}
    assert result["multi_role_parties"] == 2
    assert result["partially_unmapped_parties"] == 1
    assert result["conflicting_entity_type_parties"] == 1
