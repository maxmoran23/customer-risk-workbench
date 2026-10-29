"""Categorical attribute catalog: value classification, evidence, normalization audit and review workbooks.

A catalog holds, per attribute, the normalized values a rating model can observe and two assignments for each
value: the one in force (``current``) and the one under review (``proposed``). An assignment is a class and, for
scored classes, a score on the catalog scale. Override classes carry no score; they act on the tier directly.
"""

from __future__ import annotations

from copy import deepcopy
import csv
from datetime import date
import io
import json
from pathlib import Path
import re
import unicodedata

from .contracts import ContractError, identifier, number, strict_fields
from .features import digest

CLASSES = ("override_low", "mitigator", "neutral", "elevator", "override_high")
SCORED = {"mitigator", "neutral", "elevator"}
STATUSES = ("unreviewed", "proposed", "challenged", "agreed", "deferred")
EVIDENCE_KINDS = (
    "regulation",
    "supervisory_guidance",
    "industry_guidance",
    "internal_policy",
    "audit_finding",
    "typology",
    "data_analysis",
)
MISSING_POLICIES = ("neutral", "review")
INVENTORY_COLUMNS = (
    "attribute_id",
    "value_id",
    "label",
    "source_values",
    "party_count",
    "current_class",
    "current_score",
    "proposed_class",
    "proposed_score",
    "evidence_ids",
    "rationale",
    "status",
    "decision_by_role",
    "decision_date",
    "decision_reference",
)


def validate_assignment(assignment, scale: dict, where: str) -> None:
    if assignment is None:
        return
    strict_fields(assignment, {"class", "score"}, {"class", "score"})
    cls, score = assignment["class"], assignment["score"]
    if cls not in CLASSES:
        raise ContractError(f"{where}: unknown class {cls!r}")
    if cls not in SCORED:
        if score is not None:
            raise ContractError(f"{where}: {cls} acts on the tier and must not carry a score")
        return
    if score is None:
        raise ContractError(f"{where}: {cls} requires a score")
    number(score, f"{where} score", minimum=scale["minimum"], maximum=scale["maximum"])
    neutral = scale["neutral"]
    if cls == "neutral" and score != neutral:
        raise ContractError(f"{where}: neutral values must score exactly {neutral}")
    if cls == "elevator" and not score > neutral:
        raise ContractError(f"{where}: elevator score must exceed neutral {neutral}")
    if cls == "mitigator" and not score < neutral:
        raise ContractError(f"{where}: mitigator score must be below neutral {neutral}")


def severity(assignment) -> tuple:
    """Ordinal key for direction of change; override_low < scored values by score < override_high."""
    if assignment is None:
        return (-1, 0.0)
    if assignment["class"] == "override_low":
        return (0, 0.0)
    if assignment["class"] == "override_high":
        return (2, 0.0)
    return (1, float(assignment["score"]))


class Catalog:
    """Validated, immutable-by-convention catalog. Mutations go through ``with_value_updates``."""

    def __init__(self, config: dict):
        self._config = deepcopy(config)
        self._validate()
        self.digest = digest(self._config)
        self.attributes = {a["id"]: a for a in self._config["attributes"]}
        self.evidence = {e["id"]: e for e in self._config["evidence"]}
        self._values = {
            (a["id"], v["id"]): v for a in self._config["attributes"] for v in a["values"]
        }

    @classmethod
    def load(cls, path: str | Path) -> Catalog:
        return cls(json.loads(Path(path).read_text(encoding="utf-8")))

    def to_dict(self) -> dict:
        return deepcopy(self._config)

    @property
    def scale(self) -> dict:
        return dict(self._config["scale"])

    @property
    def entity_types(self) -> list[str]:
        return list(self._config["entity_types"])

    def value(self, attribute_id: str, value_id: str) -> dict:
        try:
            return self._values[(attribute_id, value_id)]
        except KeyError:
            raise ContractError(f"value {value_id!r} is not in attribute {attribute_id!r}") from None

    def has_value(self, attribute_id: str, value_id: str) -> bool:
        return (attribute_id, value_id) in self._values

    def applies(self, attribute_id: str, entity_type: str) -> bool:
        applies_to = self.attributes[attribute_id]["applies_to"]
        return applies_to == ["all"] or entity_type in applies_to

    def assignment(self, attribute_id: str, value_id: str, stage: str = "proposed"):
        """Effective assignment: ``current`` stage ignores proposals; ``proposed`` falls back to current."""
        if stage not in {"current", "proposed"}:
            raise ContractError("stage must be current or proposed")
        record = self.value(attribute_id, value_id)
        if stage == "proposed" and record["proposed"] is not None:
            return record["proposed"]
        return record["current"]

    def _validate(self):
        c = self._config
        strict_fields(
            c,
            {"catalog_id", "version", "description", "scale", "entity_types", "attributes", "evidence"},
            {"catalog_id", "version", "description", "scale", "entity_types", "attributes", "evidence"},
        )
        identifier(c["catalog_id"], "catalog_id")
        identifier(c["version"], "version")
        if not isinstance(c["description"], str) or not c["description"]:
            raise ContractError("catalog description required")
        scale = c["scale"]
        strict_fields(scale, {"minimum", "maximum", "neutral"}, {"minimum", "maximum", "neutral"})
        for key in ("minimum", "maximum", "neutral"):
            number(scale[key], "scale " + key, minimum=-1e9)
        if not scale["minimum"] < scale["neutral"] < scale["maximum"]:
            raise ContractError("scale requires minimum < neutral < maximum")
        if not isinstance(c["entity_types"], list) or not c["entity_types"]:
            raise ContractError("entity_types must be a nonempty list")
        for value in c["entity_types"]:
            identifier(value, "entity type")
        if len(set(c["entity_types"])) != len(c["entity_types"]):
            raise ContractError("duplicate entity type")
        if not isinstance(c["evidence"], list):
            raise ContractError("evidence must be a list")
        evidence_ids = set()
        for e in c["evidence"]:
            strict_fields(
                e,
                {"id", "title", "kind", "issuer", "locator", "url", "public"},
                {"id", "title", "kind", "issuer", "locator", "public"},
            )
            identifier(e["id"], "evidence id")
            if e["id"] in evidence_ids:
                raise ContractError(f"duplicate evidence id {e['id']}")
            evidence_ids.add(e["id"])
            if e["kind"] not in EVIDENCE_KINDS:
                raise ContractError(f"evidence {e['id']}: unknown kind {e['kind']!r}")
            if type(e["public"]) is not bool:
                raise ContractError(f"evidence {e['id']}: public must be boolean")
            for key in ("title", "issuer", "locator"):
                if not isinstance(e[key], str) or not e[key]:
                    raise ContractError(f"evidence {e['id']}: {key} required")
        if not isinstance(c["attributes"], list) or not c["attributes"]:
            raise ContractError("nonempty attributes required")
        attribute_ids = set()
        for a in c["attributes"]:
            strict_fields(
                a,
                {"id", "label", "category", "definition", "applies_to", "missing", "values"},
                {"id", "label", "category", "definition", "applies_to", "missing", "values"},
            )
            identifier(a["id"], "attribute id")
            identifier(a["category"], "attribute category")
            if a["id"] in attribute_ids:
                raise ContractError(f"duplicate attribute {a['id']}")
            attribute_ids.add(a["id"])
            if not isinstance(a["applies_to"], list) or not a["applies_to"]:
                raise ContractError(f"{a['id']}: applies_to must be a nonempty list")
            if a["applies_to"] != ["all"] and not set(a["applies_to"]) <= set(c["entity_types"]):
                raise ContractError(f"{a['id']}: applies_to references an undeclared entity type")
            if a["missing"] not in MISSING_POLICIES:
                raise ContractError(f"{a['id']}: missing policy must be one of {MISSING_POLICIES}")
            if not isinstance(a["values"], list) or not a["values"]:
                raise ContractError(f"{a['id']}: values required")
            value_ids = set()
            for v in a["values"]:
                self._validate_value(a["id"], v, scale, evidence_ids)
                if v["id"] in value_ids:
                    raise ContractError(f"{a['id']}: duplicate value {v['id']}")
                value_ids.add(v["id"])

    @staticmethod
    def _validate_value(attribute_id, v, scale, evidence_ids):
        where = f"{attribute_id}/{v.get('id')}"
        strict_fields(
            v,
            {"id", "label", "current", "proposed", "evidence", "rationale", "status", "decision"},
            {"id", "label", "current", "proposed", "evidence", "rationale", "status"},
        )
        identifier(v["id"], "value id")
        if not isinstance(v["label"], str) or not v["label"]:
            raise ContractError(f"{where}: label required")
        validate_assignment(v["current"], scale, where + " current")
        validate_assignment(v["proposed"], scale, where + " proposed")
        if v["status"] not in STATUSES:
            raise ContractError(f"{where}: unknown status {v['status']!r}")
        if not isinstance(v["rationale"], str):
            raise ContractError(f"{where}: rationale must be text")
        if not isinstance(v["evidence"], list) or not all(isinstance(e, str) for e in v["evidence"]) \
                or len(set(v["evidence"])) != len(v["evidence"]):
            raise ContractError(f"{where}: evidence must be a list of unique ids")
        unknown = set(v["evidence"]) - evidence_ids
        if unknown:
            raise ContractError(f"{where}: unknown evidence {sorted(unknown)}")
        if v["status"] == "unreviewed" and v["proposed"] is not None:
            raise ContractError(f"{where}: a proposal must carry a review status other than unreviewed")
        if v["status"] in {"proposed", "challenged", "agreed"}:
            if v["proposed"] is None:
                raise ContractError(f"{where}: status {v['status']} requires a proposed assignment")
            if not v["rationale"].strip():
                raise ContractError(f"{where}: a proposal requires a rationale")
        if (v["proposed"] is not None and v["current"] is not None
                and v["proposed"]["class"] != v["current"]["class"] and not v["evidence"]):
            raise ContractError(f"{where}: a change of class requires at least one evidence reference")
        effective = v["proposed"] if v["proposed"] is not None else v["current"]
        if effective is not None and effective["class"] not in SCORED and not v["evidence"]:
            raise ContractError(f"{where}: override classes require at least one evidence reference")
        decision = v.get("decision")
        if v["status"] == "agreed":
            if not isinstance(decision, dict):
                raise ContractError(f"{where}: agreed status requires a recorded decision")
            strict_fields(decision, {"by_role", "date", "reference"}, {"by_role", "date", "reference"})
            for key in ("by_role", "reference"):
                if not isinstance(decision[key], str) or not decision[key].strip():
                    raise ContractError(f"{where}: decision {key} required")
            try:
                date.fromisoformat(decision["date"])
            except (TypeError, ValueError):
                raise ContractError(f"{where}: decision date must be YYYY-MM-DD") from None
        elif decision is not None:
            raise ContractError(f"{where}: only agreed values carry a decision record")

    def with_value_updates(self, updates: dict) -> Catalog:
        """Return a new validated catalog. ``updates`` maps (attribute_id, value_id) to replacement fields."""
        config = self.to_dict()
        index = {(a["id"], v["id"]): v for a in config["attributes"] for v in a["values"]}
        for key, fields in updates.items():
            if key not in index:
                raise ContractError(f"cannot update unknown value {key}")
            index[key].update(deepcopy(fields))
            if index[key].get("decision") is None:
                index[key].pop("decision", None)
        return Catalog(config)


def review_diff(catalog: Catalog) -> dict:
    """Current versus proposed, value by value, with ordinal direction."""
    changes, counts = [], {"new_classification": 0, "reclassified": 0, "rescored": 0, "unchanged": 0}
    directions = {"up": 0, "down": 0, "none": 0}
    for a in catalog.to_dict()["attributes"]:
        for v in a["values"]:
            if v["proposed"] is None:
                continue
            current, proposed = v["current"], v["proposed"]
            if current is None:
                kind = "new_classification"
            elif current["class"] != proposed["class"]:
                kind = "reclassified"
            elif current["score"] != proposed["score"]:
                kind = "rescored"
            else:
                kind = "unchanged"
            before, after = severity(current), severity(proposed)
            direction = "up" if after > before else ("down" if after < before else "none")
            if current is None:
                direction = "none"
            counts[kind] += 1
            directions[direction] += 1
            changes.append(
                {
                    "attribute_id": a["id"],
                    "value_id": v["id"],
                    "label": v["label"],
                    "change": kind,
                    "direction": direction,
                    "current": current,
                    "proposed": proposed,
                    "status": v["status"],
                    "evidence": list(v["evidence"]),
                    "rationale": v["rationale"],
                }
            )
    return {
        "catalog_id": catalog.to_dict()["catalog_id"],
        "catalog_digest": catalog.digest,
        "changes": changes,
        "counts": counts,
        "directions": directions,
        "limit": "Direction is ordinal within the catalog scale; its effect on tiers depends on weights, rules and population mix. Use the impact preview to estimate migrations.",
    }


def review_coverage(catalog: Catalog) -> dict:
    """Review progress per attribute. Coverage is about review state, not correctness."""
    rows, totals = [], {"values": 0, "classified": 0, "reviewed": 0, "overrides": 0, "overrides_evidenced": 0,
                        "open_proposals": 0, "agreed": 0}
    for a in catalog.to_dict()["attributes"]:
        n = len(a["values"])
        classified = sum((v["proposed"] or v["current"]) is not None for v in a["values"])
        reviewed = sum(v["status"] != "unreviewed" for v in a["values"])
        overrides = [
            v for v in a["values"] if (v["proposed"] or v["current"] or {}).get("class") in {"override_high", "override_low"}
        ]
        evidenced = sum(bool(v["evidence"]) for v in overrides)
        by_class = {c: 0 for c in CLASSES}
        by_class["unclassified"] = 0
        for v in a["values"]:
            effective = v["proposed"] or v["current"]
            by_class[effective["class"] if effective else "unclassified"] += 1
        rows.append(
            {
                "attribute_id": a["id"],
                "values": n,
                "classified_share": classified / n,
                "reviewed_share": reviewed / n,
                "by_effective_class": by_class,
                "status_counts": {s: sum(v["status"] == s for v in a["values"]) for s in STATUSES},
                "unclassified": [v["id"] for v in a["values"] if (v["proposed"] or v["current"]) is None],
            }
        )
        totals["values"] += n
        totals["classified"] += classified
        totals["reviewed"] += reviewed
        totals["overrides"] += len(overrides)
        totals["overrides_evidenced"] += evidenced
        totals["open_proposals"] += sum(v["status"] in {"proposed", "challenged"} for v in a["values"])
        totals["agreed"] += sum(v["status"] == "agreed" for v in a["values"])
    totals["classified_share"] = totals["classified"] / totals["values"]
    totals["reviewed_share"] = totals["reviewed"] / totals["values"]
    return {"catalog_digest": catalog.digest, "attributes": rows, "totals": totals,
            "note": "reviewed counts any status other than unreviewed; open_proposals counts proposed and challenged values awaiting decision."}


_PUNCT = re.compile(r"[^\w]+", re.UNICODE)


def canonical_text(value: str) -> str:
    """Comparison key for source strings: NFKC, casefold, '&' as 'and', punctuation and spacing collapsed."""
    if not isinstance(value, str):
        raise ContractError("source value must be text")
    text = unicodedata.normalize("NFKC", value).casefold().replace("&", " and ")
    return " ".join(_PUNCT.sub(" ", text).split())


def _tokens(text: str) -> set[str]:
    return set(text.split())


def audit_normalization(catalog: Catalog, rows: list[dict], similarity: float = 0.8) -> dict:
    """Audit a source-value to normalized-value mapping table against the catalog.

    Each row: attribute_id, source_system, source_value, value_id (empty when unmapped), optional party_count.
    """
    number(similarity, "similarity", minimum=0.5, maximum=1)
    issues = {"unknown_attribute": [], "unknown_value": [], "unmapped": [], "conflicting_mapping": [],
              "fragmentation_candidates": [], "orphan_catalog_values": [], "duplicate_rows": []}
    seen_rows, by_canonical, mapped_values = set(), {}, set()
    party_total, party_mapped, counts_present = 0, 0, False
    for n, row in enumerate(rows, 1):
        strict_fields(
            row,
            {"attribute_id", "source_system", "source_value", "value_id", "party_count"},
            {"attribute_id", "source_system", "source_value", "value_id"},
        )
        attribute, system, source, value = (
            row["attribute_id"], row["source_system"], row["source_value"], row["value_id"] or ""
        )
        if not all(isinstance(x, str) for x in (attribute, value)):
            raise ContractError(f"row {n}: attribute_id and value_id must be text")
        identifier(system, f"row {n} source_system")
        if not isinstance(source, str) or not source.strip():
            raise ContractError(f"row {n}: source_value required")
        key = (attribute, system, source)
        if key in seen_rows:
            issues["duplicate_rows"].append({"row": n, "attribute_id": attribute, "source_value": source})
            continue
        seen_rows.add(key)
        count = row.get("party_count")
        if count not in (None, ""):
            if isinstance(count, bool) or not (isinstance(count, int) or (isinstance(count, str) and count.strip().isdigit())):
                raise ContractError(f"row {n}: party_count must be a nonnegative integer, not {count!r}")
            count = int(count)
            counts_present = True
            party_total += count
        if attribute not in catalog.attributes:
            issues["unknown_attribute"].append({"row": n, "attribute_id": attribute})
            continue
        if not value:
            issues["unmapped"].append(
                {"row": n, "attribute_id": attribute, "source_system": system, "source_value": source,
                 "party_count": count if counts_present else None}
            )
            continue
        if not catalog.has_value(attribute, value):
            issues["unknown_value"].append({"row": n, "attribute_id": attribute, "value_id": value})
            continue
        mapped_values.add((attribute, value))
        if isinstance(count, int):
            party_mapped += count
        by_canonical.setdefault((attribute, canonical_text(source)), []).append(
            {"row": n, "source_system": system, "source_value": source, "value_id": value}
        )
    for (attribute, canonical), entries in sorted(by_canonical.items()):
        if len({e["value_id"] for e in entries}) > 1:
            issues["conflicting_mapping"].append(
                {"attribute_id": attribute, "canonical": canonical, "entries": entries}
            )
    for attribute in catalog.attributes:
        keys = [(c, entries) for (a, c), entries in by_canonical.items() if a == attribute]
        inverted: dict[str, list[int]] = {}
        for i, (canonical, _) in enumerate(keys):
            for token in _tokens(canonical):
                inverted.setdefault(token, []).append(i)
        compared = set()
        for i, (canonical, entries) in enumerate(keys):
            candidates = {j for token in _tokens(canonical) for j in inverted[token] if j > i}
            for j in sorted(candidates):
                if (i, j) in compared:
                    continue
                compared.add((i, j))
                other, other_entries = keys[j]
                a_tokens, b_tokens = _tokens(canonical), _tokens(other)
                jaccard = len(a_tokens & b_tokens) / len(a_tokens | b_tokens)
                left = {e["value_id"] for e in entries}
                right = {e["value_id"] for e in other_entries}
                if jaccard >= similarity and left != right:
                    issues["fragmentation_candidates"].append(
                        {"attribute_id": attribute, "similarity": round(jaccard, 4),
                         "a": {"canonical": canonical, "value_ids": sorted(left)},
                         "b": {"canonical": other, "value_ids": sorted(right)}}
                    )
    for attribute, a in catalog.attributes.items():
        for v in a["values"]:
            if (attribute, v["id"]) not in mapped_values:
                issues["orphan_catalog_values"].append({"attribute_id": attribute, "value_id": v["id"]})
    blocking = sum(len(issues[k]) for k in ("unknown_attribute", "unknown_value", "unmapped", "conflicting_mapping"))
    return {
        "rows": len(rows),
        "catalog_digest": catalog.digest,
        "issues": issues,
        "issue_counts": {k: len(v) for k, v in issues.items()},
        "party_coverage": (party_mapped / party_total if party_total else None) if counts_present else None,
        "status": "blocking_issues" if blocking else (
            "review_candidates" if issues["fragmentation_candidates"] or issues["duplicate_rows"] else "clean"
        ),
        "limits": [
            "Fragmentation candidates are lexical similarities for human review, not proof that two values mean the same thing.",
            "Orphan catalog values may be legitimate (defined ahead of source adoption) or stale; both need a decision.",
            "Party coverage weights rows by the supplied counts; it is not a data-quality certification.",
        ],
    }


def _source_lookup(normalization_rows: list[dict] | None) -> dict:
    lookup: dict[tuple, dict] = {}
    for row in normalization_rows or []:
        if not row.get("value_id"):
            continue
        entry = lookup.setdefault((row["attribute_id"], row["value_id"]), {"sources": [], "count": 0, "counted": False})
        source = f"{row['source_system']}:{row['source_value']}"
        if source in entry["sources"]:
            continue
        entry["sources"].append(source)
        if row.get("party_count") not in (None, ""):
            entry["count"] += int(row["party_count"])
            entry["counted"] = True
    return lookup


def inventory_rows(catalog: Catalog, normalization_rows: list[dict] | None = None) -> list[dict]:
    lookup = _source_lookup(normalization_rows)
    rows = []
    for a in catalog.to_dict()["attributes"]:
        for v in a["values"]:
            source = lookup.get((a["id"], v["id"]), {"sources": [], "count": 0, "counted": False})
            decision = v.get("decision") or {}
            rows.append(
                {
                    "attribute_id": a["id"],
                    "value_id": v["id"],
                    "label": v["label"],
                    "source_values": " | ".join(sorted(source["sources"])),
                    "party_count": source["count"] if source["counted"] else "",
                    "current_class": (v["current"] or {}).get("class", ""),
                    "current_score": _fmt((v["current"] or {}).get("score")),
                    "proposed_class": (v["proposed"] or {}).get("class", ""),
                    "proposed_score": _fmt((v["proposed"] or {}).get("score")),
                    "evidence_ids": ";".join(v["evidence"]),
                    "rationale": v["rationale"],
                    "status": v["status"],
                    "decision_by_role": decision.get("by_role", ""),
                    "decision_date": decision.get("date", ""),
                    "decision_reference": decision.get("reference", ""),
                }
            )
    return rows


def _fmt(value) -> str:
    if value is None:
        return ""
    return str(int(value)) if float(value).is_integer() else repr(float(value))


def write_inventory_csv(path: str | Path, rows: list[dict]) -> None:
    """UTF-8 with byte-order mark so spreadsheet tools open it without an import wizard."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=INVENTORY_COLUMNS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    path.write_text("﻿" + buffer.getvalue(), encoding="utf-8", newline="")


def read_csv_rows(path: str | Path) -> list[dict]:
    with Path(path).open(encoding="utf-8-sig", newline="") as stream:
        return [dict(row) for row in csv.DictReader(stream)]


def _parse_assignment(cls: str, score: str, where: str):
    cls, score = (cls or "").strip(), (score or "").strip()
    if not cls:
        if score:
            raise ContractError(f"{where}: score supplied without a class")
        return None
    if cls not in SCORED:
        if score:
            raise ContractError(f"{where}: {cls} must not carry a score")
        return {"class": cls, "score": None}
    try:
        value = float(score)
    except ValueError:
        raise ContractError(f"{where}: {cls} requires a numeric score") from None
    return {"class": cls, "score": int(value) if value.is_integer() else value}


def import_inventory(catalog: Catalog, rows: list[dict]) -> tuple[Catalog, list[dict]]:
    """Apply reviewer edits from inventory rows. Only proposals, evidence, rationale, status and decision change.

    Current assignments are read-only here: the in-force classification changes through the adopter's
    approved release process, not through a spreadsheet edit.
    """
    updates, log, seen = {}, [], set()
    for n, row in enumerate(rows, 2):
        missing = set(INVENTORY_COLUMNS) - set(row)
        if missing:
            raise ContractError(f"inventory row {n}: missing columns {sorted(missing)}")
        key = (row["attribute_id"], row["value_id"])
        if key in seen:
            raise ContractError(f"inventory row {n}: duplicate value {key}")
        seen.add(key)
        record = catalog.value(*key)
        where = f"inventory row {n} {key[0]}/{key[1]}"
        if row["label"] != record["label"]:
            raise ContractError(f"{where}: label is read-only in review imports; change labels in the catalog")
        current = _parse_assignment(row["current_class"], row["current_score"], where + " current")
        if current != record["current"]:
            raise ContractError(f"{where}: current assignment is read-only in review imports")
        proposed = _parse_assignment(row["proposed_class"], row["proposed_score"], where + " proposed")
        evidence = [e.strip() for e in row["evidence_ids"].split(";") if e.strip()]
        decision = None
        if any(row[k].strip() for k in ("decision_by_role", "decision_date", "decision_reference")):
            decision = {
                "by_role": row["decision_by_role"].strip(),
                "date": row["decision_date"].strip(),
                "reference": row["decision_reference"].strip(),
            }
        fields = {
            "proposed": proposed,
            "evidence": evidence,
            "rationale": row["rationale"],
            "status": row["status"].strip(),
            "decision": decision,
        }
        before = {k: record.get(k) for k in fields}
        if before != fields:
            updates[key] = fields
            log.append(
                {"attribute_id": key[0], "value_id": key[1],
                 "fields": sorted(k for k in fields if before[k] != fields[k]), "before": before, "after": fields}
            )
    return catalog.with_value_updates(updates), log


def attribute_sheet(catalog: Catalog, attribute_id: str, normalization_rows: list[dict] | None = None,
                    diff: dict | None = None) -> str:
    """One self-contained Markdown review sheet per attribute: instructions, profile, evidence, inventory."""
    a = catalog.attributes[attribute_id]
    scale = catalog.scale
    rows = [r for r in inventory_rows(catalog, normalization_rows) if r["attribute_id"] == attribute_id]
    cited = sorted({e for v in a["values"] for e in v["evidence"]})
    changes = [c for c in (diff or review_diff(catalog))["changes"] if c["attribute_id"] == attribute_id]
    lines = [
        f"# Attribute review: {a['label']}",
        "",
        f"Catalog `{catalog.to_dict()['catalog_id']}` version `{catalog.to_dict()['version']}` "
        f"(digest `{catalog.digest[:12]}`). Attribute `{a['id']}`; category `{a['category']}`.",
        "",
        "## 1. Instructions",
        "",
        "1. Confirm every source value in the inventory maps to the right normalized value. Record mapping defects in the normalization audit, not here.",
        f"2. For each normalized value, record a proposed class: `override_high`, `elevator`, `neutral`, `mitigator` or `override_low`. Scored classes use the {scale['minimum']:g}-{scale['maximum']:g} scale with neutral fixed at {scale['neutral']:g}.",
        "3. Cite at least one evidence identifier for every override class and for any change of class. Evidence identifiers resolve to the register in section 3.",
        "4. Note values that are unremarkable alone but may matter in combination; they feed the connections review and compound-rule design.",
        "5. Leave `current_*` columns untouched. Edit the CSV inventory, then re-import it with `crw attributes import` to validate.",
        "",
        "## 2. Attribute profile",
        "",
        f"- Definition: {a['definition']}",
        f"- Applies to entity types: {', '.join(a['applies_to'])}",
        f"- Missing-value policy: `{a['missing']}`",
        f"- Normalized values: {len(a['values'])}",
        "",
        "## 3. Research evidence",
        "",
    ]
    if cited:
        lines += ["| Evidence | Kind | Issuer | Locator |", "| --- | --- | --- | --- |"]
        for eid in cited:
            e = catalog.evidence[eid]
            title = f"[{e['title']}]({e['url']})" if e.get("url") else e["title"]
            lines.append(f"| `{eid}` {title} | {e['kind']} | {e['issuer']} | {e['locator']} |")
    else:
        lines.append("No evidence cited yet.")
    lines += [
        "",
        "## 4. Value inventory",
        "",
        "| Value | Source values | Parties | Current | Proposed | Evidence | Status |",
        "| --- | --- | ---: | --- | --- | --- | --- |",
    ]
    for r in rows:
        current = f"{r['current_class']} {r['current_score']}".strip() or "unclassified"
        proposed = f"{r['proposed_class']} {r['proposed_score']}".strip() or "-"
        sources = r["source_values"].replace("|", "\\|") if r["source_values"] else "-"
        parties = "-" if r["party_count"] == "" else r["party_count"]
        lines.append(
            f"| `{r['value_id']}` {r['label']} | {sources} | {parties} | "
            f"{current} | {proposed} | {r['evidence_ids'] or '-'} | {r['status']} |"
        )
    lines += ["", "## 5. Proposed changes", ""]
    if changes:
        for ch in changes:
            lines.append(
                f"- `{ch['value_id']}`: {ch['change']}, direction {ch['direction']} ({ch['status']}). {ch['rationale']}"
            )
    else:
        lines.append("No proposals recorded.")
    lines += [
        "",
        "## 6. Combination notes and open questions",
        "",
        "- Values that may matter in combination with other attributes:",
        "- Questions for policy owners:",
        "",
        "Review state only. Recording a proposal does not change the in-force classification.",
        "",
    ]
    return "\n".join(lines)


def export_workbook(catalog: Catalog, out_dir: str | Path, normalization_rows: list[dict] | None = None) -> dict:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    diff = review_diff(catalog)
    coverage = review_coverage(catalog)
    files = []
    all_rows = inventory_rows(catalog, normalization_rows)
    for i, attribute_id in enumerate(catalog.attributes, 1):
        stem = f"{i:02d}-{attribute_id}"
        (out / f"{stem}.md").write_text(
            attribute_sheet(catalog, attribute_id, normalization_rows, diff), encoding="utf-8", newline="\n"
        )
        write_inventory_csv(out / f"{stem}-inventory.csv", [r for r in all_rows if r["attribute_id"] == attribute_id])
        files += [f"{stem}.md", f"{stem}-inventory.csv"]
    write_inventory_csv(out / "all-values-inventory.csv", all_rows)
    files.append("all-values-inventory.csv")
    index = ["# Attribute review workbook", "",
             f"Catalog `{catalog.to_dict()['catalog_id']}` digest `{catalog.digest[:12]}`.", "",
             "| Attribute | Values | Classified | Reviewed | Sheet | Inventory |",
             "| --- | ---: | ---: | ---: | --- | --- |"]
    for i, row in enumerate(coverage["attributes"], 1):
        stem = f"{i:02d}-{row['attribute_id']}"
        index.append(
            f"| `{row['attribute_id']}` | {row['values']} | {row['classified_share']:.0%} | {row['reviewed_share']:.0%} "
            f"| [{stem}.md]({stem}.md) | [{stem}-inventory.csv]({stem}-inventory.csv) |"
        )
    index += ["", "Edit inventories, then validate with `crw attributes import`. All values are illustrative.", ""]
    (out / "README.md").write_text("\n".join(index), encoding="utf-8", newline="\n")
    files.append("README.md")
    return {"directory": out.name, "files": files, "coverage": coverage["totals"], "diff_counts": diff["counts"]}


def scope_population(config: dict, rows: list[dict]) -> dict:
    """Resolve each party's rating scope from its role codes; most-precedent scope wins.

    ``config``: scope_classes (ordered most to least precedent, each with id/rated/description) and roles
    mapping role codes to scope ids. ``rows``: party_id, role_code, entity_type (one row per role held).
    """
    strict_fields(config, {"config_id", "version", "description", "scope_classes", "roles"},
                  {"config_id", "version", "scope_classes", "roles"})
    order, rated = [], set()
    for s in config["scope_classes"]:
        strict_fields(s, {"id", "rated", "description"}, {"id", "rated", "description"})
        identifier(s["id"], "scope class")
        if type(s["rated"]) is not bool:
            raise ContractError("scope rated flag must be boolean")
        order.append(s["id"])
        if s["rated"]:
            rated.add(s["id"])
    if len(set(order)) != len(order):
        raise ContractError("duplicate scope class")
    rank = {s: i for i, s in enumerate(order)}
    if not isinstance(config["roles"], dict):
        raise ContractError("roles must be an object of role code -> scope class")
    for role, scope in config["roles"].items():
        identifier(role, "role code")
        if scope not in rank:
            raise ContractError(f"role {role} maps to unknown scope {scope}")
    parties: dict[str, dict] = {}
    unmapped: dict[str, int] = {}
    for n, row in enumerate(rows, 1):
        strict_fields(row, {"party_id", "role_code", "entity_type"}, {"party_id", "role_code", "entity_type"})
        pid = identifier(row["party_id"], f"row {n} party_id")
        entry = parties.setdefault(pid, {"roles": set(), "entity_types": set()})
        entry["roles"].add(row["role_code"])
        entry["entity_types"].add(row["entity_type"])
        if row["role_code"] not in config["roles"]:
            unmapped[row["role_code"]] = unmapped.get(row["role_code"], 0) + 1
    counts = {s: 0 for s in order}
    counts["unresolved"] = 0
    by_entity: dict[str, dict[str, int]] = {}
    multi_role, conflicting_entity, partially_unmapped = 0, 0, 0
    for pid, entry in parties.items():
        mapped = [config["roles"][r] for r in entry["roles"] if r in config["roles"]]
        if len(entry["roles"]) > 1:
            multi_role += 1
        if len(mapped) < len(entry["roles"]) and mapped:
            partially_unmapped += 1
        if len(entry["entity_types"]) > 1:
            conflicting_entity += 1
        scope = min(mapped, key=rank.get) if mapped else "unresolved"
        counts[scope] += 1
        etype = sorted(entry["entity_types"])[0] if len(entry["entity_types"]) == 1 else "conflicting"
        by_entity.setdefault(scope, {}).setdefault(etype, 0)
        by_entity[scope][etype] += 1
    total = len(parties)
    return {
        "parties": total,
        "scope_counts": counts,
        "rated_population": sum(counts[s] for s in rated),
        "by_scope_and_entity_type": by_entity,
        "unmapped_role_codes": dict(sorted(unmapped.items())),
        "unresolved_share": counts["unresolved"] / total if total else None,
        "multi_role_parties": multi_role,
        "partially_unmapped_parties": partially_unmapped,
        "conflicting_entity_type_parties": conflicting_entity,
        "precedence": order,
        "limits": [
            "Precedence resolves a party holding several roles to its most-precedent scope; adopters must confirm that rule against policy.",
            "Partially unmapped parties resolved through another role still carry an unmapped role that needs a mapping decision.",
        ],
    }
