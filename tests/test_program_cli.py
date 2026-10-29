import json

import pytest

from crw.cli import main


def test_program_demo_end_to_end(tmp_path, capsys):
    out = tmp_path / "demo"
    assert main(["program-demo", "--parties", "4000", "--out", str(out)]) == 0
    summary = json.loads((out / "summary.json").read_text())
    assert summary["data_status"] == "synthetic"
    impact = summary["impact"]
    assert impact["sql_parity_identical"] is True
    assert impact["parity_verdict"] == "EXACT_MATCH"
    assert impact["narrative_check"] == "grounded"
    assert impact["register"] == "intact"
    assert impact["expectations_verdict"] == "consistent_with_manifest"
    assert summary["attribute_review"]["program_stages"]["value_classification"] == "in_progress"
    for path in ("impact/impact-assessment.md", "impact/impact-assessment.html", "impact/narrative-prompt.txt",
                 "attribute-review/workbook/README.md", "configs/catalog.json"):
        assert (out / path).exists(), path
    capsys.readouterr()


def test_attribute_commands(tmp_path, capsys):
    workbook = tmp_path / "wb"
    assert main(["attributes", "workbook", "--out", str(workbook)]) == 0
    assert main(["attributes", "import", "--inventory", str(workbook), "--out", str(tmp_path / "catalog.json")]) == 0
    assert json.loads((tmp_path / "catalog.changes.json").read_text()) == []
    assert main(["attributes", "validate", "--catalog", str(tmp_path / "catalog.json")]) == 0
    capsys.readouterr()


def test_impact_sql_and_narrative_rejection(tmp_path, capsys):
    sql = tmp_path / "m.sql"
    assert main(["impact", "sql", "--pre-table", "warehouse.snap_pre", "--post-table", "warehouse.snap_post",
                 "--scope-table", "warehouse.scope", "--out", str(sql)]) == 0
    text = sql.read_text()
    assert "-- matched" in text and "JOIN warehouse.scope" in text
    with pytest.raises(SystemExit) as exc:
        main(["impact", "sql", "--pre-table", "x;drop", "--post-table", "y", "--out", str(sql)])
    assert exc.value.code == 2
    pack = {"facts": {"total.moved": 5}, "allowed_numbers": [5.0], "rules": []}
    (tmp_path / "facts.json").write_text(json.dumps(pack))
    (tmp_path / "draft.txt").write_text("Seven parties moved: 7.")
    with pytest.raises(SystemExit) as exc:
        main(["impact", "narrative-check", "--facts", str(tmp_path / "facts.json"), "--draft", str(tmp_path / "draft.txt")])
    assert exc.value.code == 2
    (tmp_path / "draft.txt").write_text("5 parties moved.")
    assert main(["impact", "narrative-check", "--facts", str(tmp_path / "facts.json"), "--draft",
                 str(tmp_path / "draft.txt"), "--require", "total.moved"]) == 0
    capsys.readouterr()
