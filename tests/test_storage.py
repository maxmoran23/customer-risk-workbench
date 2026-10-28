from dataclasses import replace
import sqlite3
import pytest
from crw.contracts import ContractError
from crw.storage import Store
from crw.workflow import DecisionLog, ReviewDecision

AS_OF = "2026-10-01T00:00:00Z"


def test_atomic_idempotent_ingest(tmp_path, customer, events):
    with Store(tmp_path / "actual.sqlite") as store:
        first = store.ingest([customer], events)
        second = store.ingest([customer], events)
        assert first["transactions_inserted"] == len(events)
        assert second["transactions_unchanged"] == len(events)
        with pytest.raises(ContractError):
            store.ingest([replace(customer, customer_id="SYN-2")], [replace(events[0], amount=1000)])
        assert store.counts()["entities"] == 1
        assert store.counts()["transactions"] == len(events)


def test_orphans_snapshot_collision_and_units(tmp_path, customer, events):
    path = tmp_path / "actual.sqlite"
    with Store(path) as store:
        with pytest.raises(ContractError):
            store.ingest([], events)
        store.ingest([customer], [])
        with pytest.raises(ContractError):
            store.ingest([replace(customer, segment="different")], [])
    with pytest.raises(ContractError):
        Store(path, base_unit="OTHER")


def test_replay_and_chunks(tmp_path, customer, events, policy):
    with Store(tmp_path / "actual.sqlite") as store:
        store.ingest([customer], events)
        a = store.score_batch(AS_OF, policy, chunk_size=1)
        b = store.score_batch(AS_OF, policy, chunk_size=50)
        assert list(store.results(a["run_id"])) == list(store.results(b["run_id"]))
        assert store.counts()["assessments"] == 1
        assert a["status"] == b["status"] == "complete"


def test_asof_snapshot_and_late_data(tmp_path, customer, events, policy):
    with Store(tmp_path / "actual.sqlite") as store:
        store.ingest([customer], events)
        base = store.assess(customer.customer_id, AS_OF, policy)
        late = replace(events[0], transaction_id="late", available_at="2026-10-02T00:00:00Z")
        store.ingest([], [late])
        assert store.assess(customer.customer_id, AS_OF, policy) == base
        new = replace(customer, as_of="2026-10-03T00:00:00Z", available_at="2026-10-03T00:00:00Z")
        store.ingest([new], [])
        assert store.customer(customer.customer_id, AS_OF).as_of == customer.as_of


def test_failed_batch_cannot_export(tmp_path, customer, policy):
    with Store(tmp_path / "actual.sqlite") as store:
        store.ingest([customer], [])
        with pytest.raises(ContractError):
            store.score_batch("2026-08-01T00:00:00Z", policy)
        run = store.db.execute("SELECT run_id,status FROM runs").fetchone()
        assert run[1] == "failed"
        with pytest.raises(ContractError):
            list(store.results(run[0]))


def test_future_only_customer_does_not_contaminate_historical_population(tmp_path, customer, events, policy):
    with Store(tmp_path / "actual.sqlite") as store:
        store.ingest([customer], events)
        first = store.score_batch(AS_OF, policy)
        historical = list(store.results(first["run_id"]))
        future = replace(customer, customer_id="FUTURE", onboarded_at="2026-11-01T00:00:00Z",
                         history_start="2026-11-01T00:00:00Z", as_of="2026-12-01T00:00:00Z",
                         available_at="2026-12-01T00:00:00Z")
        delayed = replace(customer, customer_id="DELAYED", available_at="2026-12-01T00:00:00Z")
        store.ingest([future, delayed], [])
        second = store.score_batch(AS_OF, policy, chunk_size=1)
        assert second["assessed"] == 1
        assert historical == list(store.results(second["run_id"]))


def decision():
    return ReviewDecision(
        "D-1",
        "a" * 64,
        "requester",
        "reviewer",
        "Synthetic evidence supports another manual review.",
        ["E-1"],
        "escalate_review",
        AS_OF,
        "2026-11-01T00:00:00Z",
    )


def test_decision_log_real_sqlite(tmp_path):
    db = sqlite3.connect(tmp_path / "decisions.sqlite")
    log = DecisionLog(db)
    d = decision()
    h = log.append(d)
    assert log.append(d) == h
    assert log.verify()["verified_records"] == 1
    assert log.verify()["valid"]
    with pytest.raises(sqlite3.IntegrityError):
        db.execute("DELETE FROM decisions")
    db.rollback()
    with pytest.raises(ContractError):
        log.append(replace(d, reason="Different substantive decision record."))
    assert d.active(AS_OF)
    assert not d.active("2026-11-01T00:00:00Z")
    with pytest.raises(ContractError):
        replace(d, reviewed_by="requester")
    db.close()


def test_standalone_assessment_keeps_one_wal_snapshot(tmp_path, customer, events, policy, monkeypatch):
    path = tmp_path / "concurrent.sqlite"
    with Store(path) as reader, Store(path) as writer:
        assert reader.db.execute("PRAGMA journal_mode=WAL").fetchone()[0] == "wal"
        assert writer.db.execute("PRAGMA journal_mode=WAL").fetchone()[0] == "wal"
        reader.ingest([customer], events)
        historical_before = reader.assess(customer.customer_id, AS_OF, policy)
        original_customer = reader.customer
        newer = replace(customer, as_of="2026-09-15T00:00:00Z", available_at="2026-09-15T00:00:00Z")
        extra = replace(events[0], transaction_id="WAL-INSERT", amount=12345)
        commits = []

        def customer_then_concurrent_commit(customer_id, as_of):
            retrieved = original_customer(customer_id, as_of)
            assert reader.db.in_transaction
            writer.ingest([newer], [extra])
            commits.append(True)
            return retrieved

        monkeypatch.setattr(reader, "customer", customer_then_concurrent_commit)
        during_commit = reader.assess(customer.customer_id, AS_OF, policy)
        assert commits == [True]
        assert during_commit == historical_before
        assert not reader.db.in_transaction
        monkeypatch.setattr(reader, "customer", original_customer)
        after_commit = reader.assess(customer.customer_id, AS_OF, policy)
        assert after_commit["lineage"]["customer_snapshot"] != historical_before["lineage"]["customer_snapshot"]
        assert after_commit["lineage"]["event_digest"] != historical_before["lineage"]["event_digest"]
        assert after_commit["assessment_hash"] != historical_before["assessment_hash"]


def test_assess_preserves_callers_transaction_and_rolls_back_own_failure(tmp_path, customer, events, policy):
    with Store(tmp_path / "transaction.sqlite") as store:
        store.ingest([customer], events)
        with pytest.raises(RuntimeError, match="rollback caller"):
            with store.atomic():
                store.db.execute("INSERT INTO entities VALUES ('UNCOMMITTED')")
                store.assess(customer.customer_id, AS_OF, policy)
                assert store.db.in_transaction
                raise RuntimeError("rollback caller")
        assert store.counts()["entities"] == 1
        assert not store.db.in_transaction
        with pytest.raises(ContractError, match="no customer snapshot"):
            store.assess(customer.customer_id, "2026-08-01T00:00:00Z", policy)
        assert not store.db.in_transaction
        assert store.assess(customer.customer_id, AS_OF, policy)["customer_id"] == customer.customer_id


def test_onboarding_is_immutable_across_snapshots_and_ingest_rolls_back(tmp_path, customer, events):
    with Store(tmp_path / "onboarding.sqlite") as store:
        store.ingest([customer], events)
        initial_counts = store.counts()
        changed_onboarding = replace(customer, as_of="2026-09-15T00:00:00Z",
                                     available_at="2026-09-15T00:00:00Z",
                                     onboarded_at="2025-02-01T00:00:00Z",
                                     history_start="2025-02-01T00:00:00Z")
        with pytest.raises(ContractError, match="onboarded_at is immutable"):
            store.ingest([replace(customer, customer_id="ROLLBACK"), changed_onboarding], [])
        assert store.counts() == initial_counts
        equivalent_onboarding = replace(customer, as_of="2026-09-15T00:00:00Z",
                                        available_at="2026-09-15T00:00:00Z",
                                        onboarded_at="2024-12-31T19:00:00-05:00")
        assert store.ingest([equivalent_onboarding], [])["customers_inserted"] == 1
        assert store.customer(customer.customer_id, AS_OF).onboarded_at == customer.onboarded_at


def test_conflicting_onboarding_in_first_ingest_is_atomic(tmp_path, customer):
    conflicting = replace(customer, as_of="2026-09-15T00:00:00Z", available_at="2026-09-15T00:00:00Z",
                          onboarded_at="2024-01-01T00:00:00Z")
    with Store(tmp_path / "new-onboarding.sqlite") as store:
        with pytest.raises(ContractError, match="onboarded_at is immutable"):
            store.ingest([customer, conflicting], [])
        assert store.counts()["customers"] == store.counts()["entities"] == 0
