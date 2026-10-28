import json
from dataclasses import replace
import pytest
from crw.cli import main
from crw.contracts import ContractError, Customer
from crw.io import read_jsonl, write_jsonl, atomic_json
from crw.features import build_features
from crw.scoring import score
from crw.policy import Policy, PROFILE_KEYS


def test_atomic_json_rejects_nonfinite_without_replacing(tmp_path):
    path = tmp_path / "report.json"
    atomic_json(path, {"valid": 1})
    with pytest.raises(ValueError):
        atomic_json(path, {"invalid": float("nan")})
    assert json.loads(path.read_text()) == {"valid": 1}
    assert not list(tmp_path.glob("*.tmp"))


def test_jsonl_error_context(tmp_path, customer):
    path = tmp_path / "customers.jsonl"
    write_jsonl(path, [customer])
    assert list(read_jsonl(path, Customer)) == [customer]
    path.write_text(path.read_text() + "{invalid}\n")
    with pytest.raises(ContractError, match="line 2"):
        list(read_jsonl(path, Customer))


def test_cli_pipeline(tmp_path):
    inputs = tmp_path / "inputs"
    db = tmp_path / "portfolio.sqlite"
    assert main(["generate", "--customers", "4", "--transactions", "16", "--out", str(inputs)]) == 0
    assert (
        main(
            [
                "ingest",
                "--db",
                str(db),
                "--customers",
                str(inputs / "customers.jsonl"),
                "--transactions",
                str(inputs / "transactions.jsonl"),
            ]
        )
        == 0
    )
    output = tmp_path / "results.jsonl"
    assert main(["score", "--db", str(db), "--as-of", "2026-10-01T00:00:00Z", "--out", str(output)]) == 0
    assert len(output.read_text().splitlines()) == 4


def test_customer_binding(customer, events, policy):
    f = build_features(customer, events, "2026-10-01T00:00:00Z")
    with pytest.raises(ContractError, match="customer"):
        score(f, policy, "another_customer", "2026-10-01T00:00:00Z")


def test_custom_normalized_evidence_extension(customer, events, policy):
    c = policy.to_dict()
    c["profile_keys"] = [*PROFILE_KEYS, "custom_evidence"]
    c["factors"][0]["feature"] = "profile.custom_evidence"
    custom_policy = Policy.from_dict(c)
    custom_customer = replace(customer, profile={**customer.profile, "custom_evidence": 0.6})
    f = build_features(custom_customer, events, "2026-10-01T00:00:00Z")
    result = score(f, custom_policy, customer.customer_id, "2026-10-01T00:00:00Z")
    assert result["reasons"][0]["raw_points"] == 6
