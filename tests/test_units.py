import pytest

from crw.contracts import ContractError
from crw.features import build_features
from crw.scoring import score
from crw.storage import Store

AS_OF = "2026-10-01T00:00:00Z"


def test_explicit_units_change_lineage_and_assessment_hash(customer, events, policy):
    first = build_features(customer, events, AS_OF, base_unit="UNIT_A")
    second = build_features(customer, events, AS_OF, base_unit="UNIT_B")
    assert first.values == second.values
    assert first.quality == second.quality
    assert first.lineage["event_digest"] == second.lineage["event_digest"]
    assert first.lineage["unit"] == "UNIT_A"
    assert second.lineage["unit"] == "UNIT_B"
    assessment_a = score(first, policy, customer.customer_id, AS_OF)
    assessment_b = score(second, policy, customer.customer_id, AS_OF)
    assert assessment_a["assessment_hash"] != assessment_b["assessment_hash"]
    assert build_features(customer, events, AS_OF).lineage["unit"] == "SYNTHETIC_UNIT"


def test_store_propagates_declared_unit_into_batches(tmp_path, customer, events, policy):
    assessments = []
    for unit in ("UNIT_A", "UNIT_B"):
        with Store(tmp_path / f"{unit}.sqlite", base_unit=unit) as store:
            assert store.base_unit == unit
            store.ingest([customer], events)
            direct = store.assess(customer.customer_id, AS_OF, policy)
            assert direct["lineage"]["unit"] == unit
            run = store.score_batch(AS_OF, policy)
            exported = list(store.results(run["run_id"]))
            assert exported == [direct]
            assessments.append(direct)
    assert assessments[0]["assessment_hash"] != assessments[1]["assessment_hash"]


@pytest.mark.parametrize("base_unit", ["", "with space", "A/B", None, True, "x" * 129])
def test_feature_unit_identifier_is_validated(base_unit, customer, events):
    with pytest.raises(ContractError, match="base_unit"):
        build_features(customer, events, AS_OF, base_unit=base_unit)
