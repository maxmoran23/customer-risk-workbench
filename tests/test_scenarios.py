import json
from pathlib import Path

import pytest

from crw.policy import Policy, reference_policy
from crw.scenarios import run_scenarios, scenario_catalog


@pytest.fixture(scope="module")
def report():
    return run_scenarios(reference_policy())


@pytest.mark.parametrize("case_id", [row["id"] for row in scenario_catalog()])
def test_executable_scenario(case_id, report):
    result = next(row for row in report["results"] if row["id"] == case_id)
    assert result["passed"], f"{case_id}: {result['error']}"
    assert result["evidence"] is not None


def test_catalog_has_unique_substantive_and_executable_entries(report):
    catalog = scenario_catalog()
    assert len({row["id"] for row in catalog}) == len(catalog)
    assert len(catalog) == report["total"] == report["passed"]
    assert report["failed"] == 0
    assert report["errors"] == []
    assert report["all_passed"] is True
    assert sum(report["categories"].values()) == len(catalog)
    assert sum(report["families"].values()) == len(catalog)
    for row in catalog:
        assert len(row["rationale"]) > 30
        assert row["expected"].strip()


def test_catalog_file_matches_executable_registry():
    path = Path(__file__).resolve().parents[1] / "scenarios" / "catalog.json"
    payload = json.loads(path.read_text())
    assert payload["cases"] == scenario_catalog()
    assert payload["case_count"] == len(scenario_catalog())


def test_custom_policy_changes_are_visible_as_failed_expectations():
    config = reference_policy().to_dict()
    factor = next(f for f in config["factors"] if f["id"] == "expected_volume")
    factor["high"] = 100
    changed = run_scenarios(Policy(config))
    assert changed["failed"] > 0
    assert changed["all_passed"] is False
    assert any(row["id"] == "SCORE-volume-high" for row in changed["errors"])
    assert len(changed["results"]) == len(scenario_catalog())
    assert changed["passed"] + changed["failed"] == changed["total"]
