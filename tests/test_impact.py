import csv
import json
import sqlite3

import pytest

from crw.contracts import ContractError
from crw.impact import (TierScale, append_register, assess_aggregates, assess_change, baseline_outliers,
                        matrix_long_rows, reconcile_expectations, reconcile_matrices, verify_register)
from crw.impact_report import SECTIONS, render_csv, render_html, render_markdown
from crw.impact_sql import migration_sql
from crw.narrative import check_narrative, facts_pack, prompt_text
from crw.program_reference import reference_tier_scale

SCALE = TierScale(reference_tier_scale())


def config(**extra):
    base = {"assessment_id": "IA-T", "description": "test", "pre_label": "before", "post_label": "after",
            "exclude_pinned": True, "segments": {"S1": {"mode": "paired"}, "S2": {"mode": "paired"}}}
    base.update(extra)
    return base


def row(pid, segment, tier, pinned=0):
    return {"party_id": pid, "segment": segment, "tier": tier, "pinned": str(pinned)}


PRE = [row("A", "S1", "LOW"), row("B", "S1", "LOW"), row("C", "S1", "HIGH"), row("D", "S2", "MODERATE"),
       row("E", "S2", "VERY_HIGH", 1), row("F", "S2", "LOW"), row("G", "S1", "HIGH", 1)]
POST = [row("A", "S1", "LOW"), row("B", "S1", "HIGH"), row("C", "S1", "MODERATE"), row("D", "S1", "VERY_HIGH"),
        row("E", "S2", "VERY_HIGH", 1), row("H", "S2", "2"), row("G", "S1", "LOW", 1)]


def test_hand_counted_matrix_entrants_exits_and_integrity():
    result = assess_change(PRE, POST, config(), SCALE, partitions=1)
    s1 = result["segments"]["S1"]
    # Matched non-pinned: A LOW->LOW, B LOW->HIGH, C HIGH->MODERATE (S1); D MODERATE->VERY_HIGH counted in post segment S1.
    assert s1["matrix"][0][0] == 1 and s1["matrix"][0][2] == 1 and s1["matrix"][2][1] == 1 and s1["matrix"][1][3] == 1
    assert s1["matched"] == 4 and s1["up"] == 2 and s1["down"] == 1 and s1["segment_changed"] == 1
    assert s1["distance"] == {"-1": 1, "+2": 2}
    assert s1["excluded_pinned"] == 1 and s1["pinned_moved"] == 1
    s2 = result["segments"]["S2"]
    assert s2["entrants"] == [0, 1, 0, 0] and s2["exits"] == [1, 0, 0, 0] and s2["excluded_pinned"] == 1
    assert result["integrity_findings"] == ["pinned_parties_changed_tier"]
    assert result["totals"]["matched"] == 4


def test_partitioned_join_equals_single_partition(tmp_path):
    import random

    rng = random.Random(3)
    tiers = SCALE.tiers
    pre = [row(f"P{i}", rng.choice(["S1", "S2"]), rng.choice(tiers), int(rng.random() < 0.02)) for i in range(5000)]
    post = [dict(r, tier=rng.choice(tiers)) if rng.random() < 0.1 else dict(r) for r in pre[:4900]]
    post += [row(f"N{i}", "S2", "LOW") for i in range(50)]
    for path, rows in ((tmp_path / "pre.csv", pre), (tmp_path / "post.csv", post)):
        with path.open("w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["party_id", "segment", "tier", "pinned"])
            w.writeheader()
            w.writerows(rows)
    one = assess_change(tmp_path / "pre.csv", tmp_path / "post.csv", config(), SCALE, partitions=1)
    many = assess_change(tmp_path / "pre.csv", tmp_path / "post.csv", config(), SCALE, partitions=37)
    assert one["segments"] == many["segments"] and one["assessment_hash"] == many["assessment_hash"]
    assert one["inputs"]["pre_sha256"] and one["inputs"]["pre_rows"] == 5000


def test_contract_failures():
    with pytest.raises(ContractError, match="duplicate party"):
        assess_change(PRE + [row("A", "S1", "LOW")], POST, config(), SCALE, partitions=1)
    with pytest.raises(ContractError, match="not configured"):
        assess_change(PRE + [row("Z", "S9", "LOW")], POST, config(), SCALE, partitions=1)
    with pytest.raises(ContractError, match="unknown tier"):
        assess_change([row("A", "S1", "EXTREME")], POST, config(), SCALE, partitions=1)
    with pytest.raises(ContractError, match="pinned"):
        assess_change([row("A", "S1", "LOW", "maybe")], POST, config(), SCALE, partitions=1)
    agg = config(segments={"S1": {"mode": "paired"}, "S2": {"mode": "aggregate_only"}})
    with pytest.raises(ContractError, match="aggregate_only"):
        assess_change(PRE, POST, agg, SCALE, partitions=1)


def test_aggregate_only_minimum_movers():
    result = assess_aggregates({"LOW": 100, "MODERATE": 50}, {"LOW": 90, "MODERATE": 55, "HIGH": 5}, SCALE)
    assert result["net_change"] == [-10, 5, 5, 0] and result["minimum_movers"] == 10
    grown = assess_aggregates({"LOW": 100}, {"LOW": 101}, SCALE)
    assert grown["minimum_movers"] is None


def test_missing_aggregates_is_an_integrity_finding():
    cfg = config(segments={"S1": {"mode": "paired"}, "S2": {"mode": "paired"}, "S3": {"mode": "aggregate_only"}})
    result = assess_change(PRE, POST, cfg, SCALE, partitions=1)
    assert "aggregate_only_segments_without_aggregates" in result["integrity_findings"]
    cfg["aggregates"] = {"S3": {"pre": {"LOW": 10}, "post": {"LOW": 9, "HIGH": 1}}}
    result = assess_change(PRE, POST, cfg, SCALE, partitions=1)
    assert result["aggregate_segments"]["S3"]["minimum_movers"] == 1


def manifest(effects, **extra):
    return {"change_id": "CHG-T", "release": "r1", "description": "t", "change_type": "value_classification",
            "expected_effects": effects, **extra}


def effect(eid, direction, to=("*",), lo=0, hi=None, segments=("*",)):
    return {"id": eid, "segments": list(segments), "from": ["*"], "to": list(to), "direction": direction,
            "count": {"min": lo, "max": hi}, "rationale": "t"}


def test_expectation_reconciliation():
    clean_pre = [r for r in PRE if r["party_id"] != "G"]
    clean_post = [r for r in POST if r["party_id"] != "G"]
    result = assess_change(clean_pre, clean_post, config(), SCALE, partitions=1)
    population = {"entrants": {"min": 1, "max": 1}, "exits": {"min": 1, "max": 1}, "rationale": "t"}
    undeclared = reconcile_expectations(result, manifest([effect("UP", "up", lo=2, hi=2), effect("DOWN", "down", lo=1, hi=1)]))
    assert {u["kind"] for u in undeclared["unexplained_movements"]} == {"undeclared_entrants", "undeclared_exits"}
    ok = reconcile_expectations(result, manifest([effect("UP", "up", lo=2, hi=2), effect("DOWN", "down", lo=1, hi=1)],
                                                 expected_population=population))
    assert ok["verdict"] == "consistent_with_manifest"
    partial = reconcile_expectations(result, manifest([effect("UP", "up", to=["HIGH"], lo=1, hi=1)],
                                                      expected_population=population))
    assert partial["verdict"] == "requires_explanation"
    assert {(u["from"], u["to"]) for u in partial["unexplained_movements"]} == {("MODERATE", "VERY_HIGH"), ("HIGH", "MODERATE")}
    with pytest.raises(ContractError, match="not in the assessment"):
        reconcile_expectations(result, manifest([effect("UP", "up", segments=["S9"])]))
    with pytest.raises(ContractError, match="nonempty list"):
        reconcile_expectations(result, manifest([effect("UP", "up", segments=[])]))
    overlap = reconcile_expectations(result, manifest([effect("A", "up"), effect("B", "any")], expected_population=population))
    assert overlap["overlapping_expectations"] == [["A", "B"]]
    failed = reconcile_expectations(result, manifest([effect("UP", "up", lo=5)]))
    assert failed["expectations"][0]["status"] == "FAIL"
    with pytest.raises(ContractError):
        reconcile_expectations(result, manifest([effect("UP", "sideways")]))


def _assessment_with_rate(moved, n=100):
    pre = [row(f"P{i}", "S1", "LOW") for i in range(n)]
    post = [row(f"P{i}", "S1", "MODERATE" if i < moved else "LOW") for i in range(n)]
    return assess_change(pre, post, config(segments={"S1": {"mode": "paired"}}), SCALE, partitions=1)


def test_baseline_flags_outlier_and_respects_history_minimum():
    history = [_assessment_with_rate(m) for m in (2, 3, 2, 4, 3, 2)]
    flags = baseline_outliers(history, _assessment_with_rate(30))["flags"]
    assert any(f["from"] == "LOW" and f["to"] == "MODERATE" for f in flags)
    assert baseline_outliers(history, _assessment_with_rate(3))["flags"] == []
    thin = baseline_outliers(history[:2], _assessment_with_rate(30), min_history=3)
    assert thin["flags"] == [] and thin["cells_without_sufficient_history"] > 0


def test_parity_verdicts():
    result = assess_change(PRE, POST, config(), SCALE, partitions=1)
    rows = matrix_long_rows(result)
    assert reconcile_matrices(result, rows)["verdict"] == "EXACT_MATCH"
    coded = [dict(r, pre_tier=str(SCALE.index[r["pre_tier"]] + 1), post_tier=str(SCALE.index[r["post_tier"]] + 1)) for r in rows]
    assert reconcile_matrices(result, coded)["verdict"] == "EXACT_MATCH"
    off = [dict(r) for r in rows]
    off[0]["count"] += 1
    assert reconcile_matrices(result, off)["verdict"] == "MISMATCH"
    assert reconcile_matrices(result, off, tolerance_abs=1)["verdict"] == "WITHIN_TOLERANCE"
    assert reconcile_matrices(result, [r for r in rows if r["count"]])["verdict"] == "EXACT_MATCH"
    assert reconcile_matrices(result, [r for r in rows if r["segment"] != "S1"])["verdict"] == "MISMATCH"
    with pytest.raises(ContractError, match="integer"):
        reconcile_matrices(result, [dict(rows[0], count="1.9")])


def _load(con, table, rows):
    con.execute(f"CREATE TABLE {table} (party_id TEXT PRIMARY KEY, segment TEXT, tier TEXT, pinned INTEGER)")
    con.executemany(f"INSERT INTO {table} VALUES (?,?,?,?)",
                    [(r["party_id"], r["segment"], SCALE.tiers[SCALE.parse(r["tier"])], int(r["pinned"])) for r in rows])


def test_generated_sql_matches_engine_on_sqlite():
    result = assess_change(PRE, POST, config(), SCALE, partitions=1)
    con = sqlite3.connect(":memory:")
    _load(con, "pre", PRE)
    _load(con, "post", POST)
    sql = migration_sql("pre", "post")
    cells = {(s, a, b): n for s, a, b, n in con.execute(sql["matched"])}
    engine = {(r["segment"], r["pre_tier"], r["post_tier"]): r["count"] for r in matrix_long_rows(result) if r["count"]}
    assert cells == engine
    entrants = {(s, t): n for s, t, n in con.execute(sql["entrants"])}
    exits = {(s, t): n for s, t, n in con.execute(sql["exits"])}
    assert entrants == {("S2", "MODERATE"): 1} and exits == {("S2", "LOW"): 1}
    excluded = dict(con.execute(sql["excluded_pinned"]).fetchall())
    assert excluded == {s: d["excluded_pinned"] for s, d in result["segments"].items() if d["excluded_pinned"]}
    assert dict(con.execute(sql["pinned_moved"]).fetchall()) == {"S1": 1}


def test_scope_table_sql_and_identifier_guard():
    con = sqlite3.connect(":memory:")
    _load(con, "pre", PRE)
    _load(con, "post", POST)
    con.execute("CREATE TABLE scope (party_id TEXT PRIMARY KEY, segment TEXT)")
    con.executemany("INSERT INTO scope VALUES (?, ?)", [("A", "X"), ("B", "X"), ("C", "Y")])
    sql = migration_sql("pre", "post", scope_table="scope")
    assert sorted(con.execute(sql["matched"]).fetchall()) == [("X", "LOW", "HIGH", 1), ("X", "LOW", "LOW", 1), ("Y", "HIGH", "MODERATE", 1)]
    for bad in ("pre; DROP TABLE x", "pre--", "1pre", "a.b.c.d"):
        with pytest.raises(ContractError):
            migration_sql(bad, "post")


def test_register_chain_detects_tampering(tmp_path):
    path = tmp_path / "register.jsonl"
    for i in range(3):
        append_register(path, {"assessment_id": f"IA-{i}", "assessment_hash": "h", "recorded_at": "2026-01-01T00:00:00Z",
                               "verdicts": {}})
    intact = verify_register(path)
    assert intact["entries"] == 3 and intact["status"] == "intact" and intact["problems"] == []
    anchor = {"entries": 3, "last_entry_hash": intact["last_entry_hash"]}
    assert verify_register(path, anchor)["status"] == "intact"
    with pytest.raises(ContractError):
        append_register(path, {"assessment_id": "X", "assessment_hash": "h", "recorded_at": "yesterday", "verdicts": {}})
    truncated = tmp_path / "truncated.jsonl"
    truncated.write_text("\n".join(path.read_text().splitlines()[:2]) + "\n")
    assert verify_register(truncated)["status"] == "intact"
    assert verify_register(truncated, anchor)["status"] == "broken"
    lines = path.read_text().splitlines()
    record = json.loads(lines[1])
    record["verdicts"] = {"parity": "EXACT_MATCH"}
    lines[1] = json.dumps(record, sort_keys=True)
    path.write_text("\n".join(lines) + "\n")
    assert verify_register(path)["status"] == "broken"


def test_report_layout_contract_and_escaping():
    cfg = config()
    cfg["description"] = "<script>alert(1)</script>"
    result = assess_change(PRE, POST, cfg, SCALE, partitions=1)
    md = render_markdown(result)
    positions = [md.index("## " + s) for s in SECTIONS]
    assert positions == sorted(positions)
    assert "| Before \\ After | LOW | MODERATE | HIGH | VERY_HIGH | Total | Moved |" in md
    page = render_html(result)
    assert "<script>alert" not in page and "&lt;script&gt;" in page
    assert render_csv(result).splitlines()[0] == "segment,pre_tier,post_tier,count"


def test_narrative_guard_accepts_grounded_and_rejects_invented_numbers():
    result = assess_change(PRE, POST, config(), SCALE, partitions=1)
    pack = facts_pack(result)
    t = pack["facts"]
    good = f"Of {t['total.matched']} matched parties, {t['total.moved']} moved ({t['total.moved_share_pct']}%). Release r-2 in segment S1."
    assert check_narrative(good, pack, required=["total.moved"])["status"] == "grounded"
    bad = good + " Roughly 1,250 parties are expected next sprint, a 12.5% increase."
    verdict = check_narrative(bad, pack)
    assert verdict["status"] == "rejected"
    assert {u["number"] for u in verdict["unsupported_numbers"]} == {"1,250", "12.5%"}
    assert check_narrative("Nothing quoted.", pack, required=["total.moved"])["missing_required_facts"] == ["total.moved"]
    assert "Use only figures present in facts" in prompt_text(pack)


def test_tier_codes_must_not_shadow_labels():
    with pytest.raises(ContractError, match="disjoint"):
        TierScale({"scale_id": "x", "tiers": ["LOW", "HIGH"], "codes": {"LOW": "HIGH", "HIGH": "LOW"}})
    with pytest.raises(ContractError):
        TierScale({"scale_id": "x", "tiers": ["LOW", "HIGH"], "codes": ["LOW"]})


def test_aggregate_movement_requires_a_named_expectation():
    cfg = config(segments={"S1": {"mode": "paired"}, "S2": {"mode": "paired"}, "S3": {"mode": "aggregate_only"}},
                 aggregates={"S3": {"pre": {"LOW": 100}, "post": {"LOW": 50, "VERY_HIGH": 50}}})
    clean = [r for r in PRE if r["party_id"] in "ABC"], [r for r in POST if r["party_id"] in "ABC"]
    result = assess_change(*clean, cfg, SCALE, partitions=1)
    verdict = reconcile_expectations(result, manifest([effect("ALL", "any")]))
    assert verdict["verdict"] == "requires_explanation"
    assert [u["kind"] for u in verdict["unexplained_movements"]] == ["aggregate_only_movement"]
    declared = {"S3": {"minimum_movers": {"min": 40, "max": 60}, "rationale": "t"}}
    named = reconcile_expectations(result, manifest([effect("ALL", "any")], expected_aggregate=declared))
    assert named["verdict"] == "consistent_with_manifest"
    declared["S3"]["minimum_movers"] = {"min": 0, "max": 10}
    assert reconcile_expectations(result, manifest([effect("ALL", "any")], expected_aggregate=declared))["verdict"] == "requires_explanation"
    with pytest.raises(ContractError, match="twice"):
        assess_aggregates_config = config(segments={"S3": {"mode": "aggregate_only"}},
                                          aggregates={"S3": {"pre": {"LOW": 5, "1": 5}, "post": {"LOW": 10}}})
        assess_change([], [], assess_aggregates_config, SCALE, partitions=1)


def test_sql_handles_text_pins_and_reports_contract_violations():
    con = sqlite3.connect(":memory:")
    for table, rows in (("pre", PRE), ("post", POST)):
        con.execute(f"CREATE TABLE {table} (party_id TEXT, segment TEXT, tier TEXT, pinned TEXT)")
        con.executemany(f"INSERT INTO {table} VALUES (?,?,?,?)",
                        [(r["party_id"], r["segment"], SCALE.tiers[SCALE.parse(r["tier"])], r["pinned"]) for r in rows])
    sql = migration_sql("pre", "post")
    result = assess_change(PRE, POST, config(), SCALE, partitions=1)
    engine = {(r["segment"], r["pre_tier"], r["post_tier"]): r["count"] for r in matrix_long_rows(result) if r["count"]}
    assert {(s, a, b): n for s, a, b, n in con.execute(sql["matched"])} == engine
    assert all(n == 0 for _, _, n in con.execute(sql["checks"]))
    con.execute("INSERT INTO pre VALUES ('A', 'S1', 'LOW', '2')")
    issues = {(side, issue): n for side, issue, n in con.execute(sql["checks"])}
    assert issues[("pre", "duplicate_party")] == 1 and issues[("pre", "invalid_pinned")] == 1
    included = migration_sql("pre", "post", exclude_pinned=False)
    con.execute("DELETE FROM pre WHERE pinned = '2'")
    total = sum(n for *_, n in con.execute(included["matched"]))
    assert total == 6


def test_narrative_guard_rejects_unverifiable_formats_and_unit_confusion():
    result = assess_change(PRE, POST, config(), SCALE, partitions=1)
    pack = facts_pack(result)
    moved = pack["facts"]["total.moved"]
    for bad in ("About 1.2k parties.", "Net change of -347.", "Between 400-500 parties.", "Twelve hundred parties.",
                f"{moved}% of parties moved.", "A ratio of 3/7.", "Up 3x."):
        assert check_narrative(bad, pack)["status"] == "rejected", bad
    assert check_narrative(f"Of these, 1{moved} moved down.", pack, required=["total.moved"])["missing_required_facts"] == ["total.moved"]
