"""Change-impact assessment: who moved between risk tiers when a model, rule or reference table changed.

Inputs are two tier snapshots of the same population (before and after a change, typically from a test
environment) with one row per party: party_id, segment, tier, pinned. ``pinned`` marks parties whose tier is
fixed by an override outside the change (for example an active-investigation override); they are excluded from
migration counts but checked: a pinned party that moved signals a data or logic defect.

The engine streams both files once into hash partitions and joins partition by partition, so memory is bounded
by one partition of each snapshot (the pre-change records and the post-change identifiers of that partition). Outputs keep the familiar matrix layout: rows are the tier before,
columns the tier after, one matrix per segment.
"""

from __future__ import annotations

from collections import Counter
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import tempfile
import zlib

from .contracts import ContractError, identifier, number, strict_fields, utc
from .features import digest

SNAPSHOT_COLUMNS = ("party_id", "segment", "tier", "pinned")
TRUE_TEXT = {"1", "true", "t", "yes", "y"}
FALSE_TEXT = {"0", "false", "f", "no", "n", ""}


class TierScale:
    """Ordered tiers, lowest first, with optional numeric codes accepted on input."""

    def __init__(self, config: dict):
        strict_fields(config, {"scale_id", "tiers", "codes"}, {"scale_id", "tiers"})
        identifier(config["scale_id"], "scale_id")
        tiers = config["tiers"]
        if not isinstance(tiers, list) or len(tiers) < 2 or len(set(tiers)) != len(tiers):
            raise ContractError("tier scale needs at least two unique tiers")
        for t in tiers:
            identifier(t, "tier")
        codes = config.get("codes", {})
        if not isinstance(codes, dict):
            raise ContractError("tier codes must be an object of tier -> code")
        if set(codes) - set(tiers) or len(set(map(str, codes.values()))) != len(codes):
            raise ContractError("tier codes must map known tiers to unique codes")
        if {str(c) for c in codes.values()} & set(tiers):
            raise ContractError("tier codes must be disjoint from tier labels")
        self.config = dict(config)
        self.tiers = list(tiers)
        self.index = {t: i for i, t in enumerate(tiers)}
        self._lookup = dict(self.index)
        for tier, code in codes.items():
            self._lookup[str(code)] = self.index[tier]

    def parse(self, value) -> int:
        key = str(value).strip()
        if key not in self._lookup:
            raise ContractError(f"unknown tier {value!r}")
        return self._lookup[key]


def _pinned(value) -> bool:
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in TRUE_TEXT:
        return True
    if text in FALSE_TEXT:
        return False
    raise ContractError(f"pinned must be a boolean flag, not {value!r}")


def iter_snapshot(source, scale: TierScale):
    """Yield (party_id, segment, tier_index, pinned) from a CSV path or an iterable of dicts."""
    if isinstance(source, (str, Path)):
        stream = Path(source).open(encoding="utf-8-sig", newline="")
        reader = csv.DictReader(stream)
        missing = set(SNAPSHOT_COLUMNS) - set(reader.fieldnames or [])
        if missing:
            stream.close()
            raise ContractError(f"snapshot missing columns {sorted(missing)}")
        rows = reader
    else:
        stream, rows = None, source
    try:
        for n, row in enumerate(rows, 1):
            try:
                if not isinstance(row, dict):
                    raise ContractError("each snapshot row must be an object with named columns")
                pid = identifier(row["party_id"], "party_id")
                segment = identifier(row["segment"], "segment")
                yield pid, segment, scale.parse(row["tier"]), _pinned(row.get("pinned", False))
            except (KeyError, ContractError) as exc:
                raise ContractError(f"snapshot row {n}: {exc}") from exc
    finally:
        if stream is not None:
            stream.close()


def file_sha256(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def validate_config(config: dict, scale: TierScale) -> None:
    strict_fields(
        config,
        {"assessment_id", "description", "pre_label", "post_label", "exclude_pinned", "segments",
         "unknown_segments", "aggregates"},
        {"assessment_id", "description", "pre_label", "post_label", "exclude_pinned", "segments"},
    )
    identifier(config["assessment_id"], "assessment_id")
    if type(config["exclude_pinned"]) is not bool:
        raise ContractError("exclude_pinned must be boolean")
    if not isinstance(config["segments"], dict) or not isinstance(config.get("aggregates", {}), dict):
        raise ContractError("segments and aggregates must be objects keyed by segment")
    if config.get("unknown_segments", "error") not in {"error", "include"}:
        raise ContractError("unknown_segments must be error or include")
    for segment, spec in config["segments"].items():
        identifier(segment, "segment")
        strict_fields(spec, {"mode", "description"}, {"mode"})
        if spec["mode"] not in {"paired", "aggregate_only"}:
            raise ContractError(f"segment {segment}: mode must be paired or aggregate_only")
    for segment, agg in config.get("aggregates", {}).items():
        if config["segments"].get(segment, {}).get("mode") != "aggregate_only":
            raise ContractError(f"aggregates supplied for {segment}, which is not aggregate_only")
        strict_fields(agg, {"pre", "post"}, {"pre", "post"})
        for side in ("pre", "post"):
            if not isinstance(agg[side], dict):
                raise ContractError("aggregate counts must be an object of tier -> count")
            if len({scale.parse(t) for t in agg[side]}) != len(agg[side]):
                raise ContractError(f"aggregate {segment}/{side} names a tier twice (label and code)")
            for tier, count in agg[side].items():
                scale.parse(tier)
                if type(count) is not int or count < 0:
                    raise ContractError("aggregate counts must be nonnegative integers")


def _blank(k: int) -> dict:
    return {
        "matrix": [[0] * k for _ in range(k)],
        "entrants": [0] * k,
        "exits": [0] * k,
        "excluded_pinned": 0,
        "pinned_moved": 0,
        "segment_changed": 0,
        "pin_changed": 0,
    }


def _partition(source, scale, k, directory, label, segments, unknown) -> tuple[list[Path], int]:
    paths = [Path(directory) / f"{label}-{i:04d}.tsv" for i in range(k)]
    handles = [p.open("w", encoding="utf-8", newline="\n") for p in paths]
    rows = 0
    try:
        for pid, segment, tier, pinned in iter_snapshot(source, scale):
            if segment not in segments and unknown == "error":
                raise ContractError(f"{label} snapshot: segment {segment} is not configured")
            if segments.get(segment, {}).get("mode") == "aggregate_only":
                raise ContractError(f"{label} snapshot: segment {segment} is aggregate_only; supply aggregates, not rows")
            handles[zlib.crc32(pid.encode()) % k].write(f"{pid}\t{segment}\t{tier}\t{int(pinned)}\n")
            rows += 1
    finally:
        for h in handles:
            h.close()
    return paths, rows


def _read_partition(path: Path):
    with path.open(encoding="utf-8") as stream:
        for line in stream:
            pid, segment, tier, pinned = line.rstrip("\n").split("\t")
            yield pid, segment, int(tier), pinned == "1"


def assess_change(pre, post, config: dict, scale: TierScale, *, partitions: int = 16,
                  workdir: str | Path | None = None) -> dict:
    """Join two snapshots and compute per-segment migration matrices, entrants, exits and integrity checks."""
    validate_config(config, scale)
    hashes_before = {side: file_sha256(src) if isinstance(src, (str, Path)) else None
                     for side, src in (("pre", pre), ("post", post))}
    if type(partitions) is not int or not 1 <= partitions <= 4096:
        raise ContractError("partitions must be an integer between 1 and 4096")
    k = len(scale.tiers)
    segments = config["segments"]
    unknown = config.get("unknown_segments", "error")
    results: dict[str, dict] = {}
    exclude = config["exclude_pinned"]
    with tempfile.TemporaryDirectory(dir=workdir) as directory:
        pre_parts, pre_rows = _partition(pre, scale, partitions, directory, "pre", segments, unknown)
        post_parts, post_rows = _partition(post, scale, partitions, directory, "post", segments, unknown)
        for pre_path, post_path in zip(pre_parts, post_parts):
            before: dict[str, tuple] = {}
            for pid, segment, tier, pinned in _read_partition(pre_path):
                if pid in before:
                    raise ContractError(f"pre snapshot: duplicate party {pid}")
                before[pid] = (segment, tier, pinned)
            seen_post: set[str] = set()
            for pid, segment, tier, pinned in _read_partition(post_path):
                if pid in seen_post:
                    raise ContractError(f"post snapshot: duplicate party {pid}")
                seen_post.add(pid)
                bucket = results.setdefault(segment, _blank(k))
                old = before.pop(pid, None)
                if old is None:
                    if exclude and pinned:
                        bucket["excluded_pinned"] += 1
                    else:
                        bucket["entrants"][tier] += 1
                    continue
                old_segment, old_tier, old_pinned = old
                if old_segment != segment:
                    bucket["segment_changed"] += 1
                if old_pinned and pinned and old_tier != tier:
                    bucket["pinned_moved"] += 1
                if old_pinned != pinned:
                    bucket["pin_changed"] += 1
                if exclude and (old_pinned or pinned):
                    bucket["excluded_pinned"] += 1
                    continue
                bucket["matrix"][old_tier][tier] += 1
            for pid, (segment, tier, pinned) in before.items():
                bucket = results.setdefault(segment, _blank(k))
                if exclude and pinned:
                    bucket["excluded_pinned"] += 1
                else:
                    bucket["exits"][tier] += 1
    paired = {seg: _summarize(results.get(seg, _blank(k)), scale) for seg in sorted(set(results) | {
        s for s, spec in segments.items() if spec["mode"] == "paired"})}
    aggregate = {seg: assess_aggregates(agg["pre"], agg["post"], scale)
                 for seg, agg in sorted(config.get("aggregates", {}).items())}
    missing_aggregates = sorted(s for s, spec in segments.items()
                                if spec["mode"] == "aggregate_only" and s not in aggregate)
    totals = _summarize(_combine(list(results.values()), k), scale)
    hashes_after = {side: file_sha256(src) if isinstance(src, (str, Path)) else None
                    for side, src in (("pre", pre), ("post", post))}
    if hashes_after != hashes_before:
        raise ContractError("an input snapshot changed during the assessment; rerun against immutable files")
    integrity = []
    if sum(v["pinned_moved"] for v in paired.values()):
        integrity.append("pinned_parties_changed_tier")
    if missing_aggregates:
        integrity.append("aggregate_only_segments_without_aggregates")
    payload = {
        "assessment_id": config["assessment_id"],
        "description": config["description"],
        "pre_label": config["pre_label"],
        "post_label": config["post_label"],
        "tier_scale": scale.config,
        "config_digest": digest(config),
        "inputs": {
            "pre_rows": pre_rows,
            "post_rows": post_rows,
            "pre_sha256": hashes_before["pre"],
            "post_sha256": hashes_before["post"],
        },
        "segments": paired,
        "aggregate_segments": aggregate,
        "missing_aggregates": missing_aggregates,
        "totals": totals,
        "integrity_findings": integrity,
        "limits": [
            "Migration counts describe the supplied snapshots; they do not establish that a change is correct or desirable.",
            "Segment assignment uses the post-change snapshot; parties that changed segment are counted there and reported.",
            "Aggregate-only segments report distribution change and a lower bound on movers, never a migration matrix.",
        ],
    }
    payload["assessment_hash"] = digest(payload)
    return payload


def _combine(buckets: list[dict], k: int) -> dict:
    total = _blank(k)
    for b in buckets:
        for i in range(k):
            for j in range(k):
                total["matrix"][i][j] += b["matrix"][i][j]
            total["entrants"][i] += b["entrants"][i]
            total["exits"][i] += b["exits"][i]
        for key in ("excluded_pinned", "pinned_moved", "segment_changed", "pin_changed"):
            total[key] += b[key]
    return total


def _summarize(bucket: dict, scale: TierScale) -> dict:
    m = bucket["matrix"]
    k = len(scale.tiers)
    matched = sum(map(sum, m))
    up = sum(m[i][j] for i in range(k) for j in range(k) if j > i)
    down = sum(m[i][j] for i in range(k) for j in range(k) if j < i)
    distance = Counter()
    for i in range(k):
        for j in range(k):
            if i != j and m[i][j]:
                distance[j - i] += m[i][j]
    return {
        "tiers": list(scale.tiers),
        "matrix": [row[:] for row in m],
        "pre_totals": [sum(row) for row in m],
        "post_totals": [sum(m[i][j] for i in range(k)) for j in range(k)],
        "matched": matched,
        "unchanged": sum(m[i][i] for i in range(k)),
        "up": up,
        "down": down,
        "moved": up + down,
        "moved_share": (up + down) / matched if matched else None,
        "distance": {f"{d:+d}": n for d, n in sorted(distance.items())},
        "entrants": bucket["entrants"][:],
        "exits": bucket["exits"][:],
        "excluded_pinned": bucket["excluded_pinned"],
        "pinned_moved": bucket["pinned_moved"],
        "segment_changed": bucket["segment_changed"],
        "pin_changed": bucket["pin_changed"],
    }


def assess_aggregates(pre: dict, post: dict, scale: TierScale) -> dict:
    """Distribution change for populations without row-level snapshots, plus the implied minimum movers."""
    k = len(scale.tiers)
    before, after = [0] * k, [0] * k
    for tier, n in pre.items():
        before[scale.parse(tier)] += n
    for tier, n in post.items():
        after[scale.parse(tier)] += n
    n_pre, n_post = sum(before), sum(after)
    result = {
        "tiers": list(scale.tiers),
        "pre_counts": before,
        "post_counts": after,
        "net_change": [after[i] - before[i] for i in range(k)],
        "population_change": n_post - n_pre,
        "method": "aggregate_only",
    }
    if n_pre == n_post:
        result["minimum_movers"] = sum(abs(after[i] - before[i]) for i in range(k)) // 2
        result["minimum_movers_note"] = ("Lower bound on parties that changed tier, valid only if membership is unchanged; "
                                         "equal totals do not prove that no parties entered and left.")
    else:
        result["minimum_movers"] = None
        result["minimum_movers_note"] = "Population size changed; movers cannot be bounded from marginals alone."
    return result


def validate_manifest(manifest: dict, scale: TierScale) -> None:
    strict_fields(
        manifest,
        {"change_id", "release", "description", "change_type", "expected_effects", "unexplained_tolerance",
         "expected_population", "expected_aggregate"},
        {"change_id", "release", "description", "change_type", "expected_effects"},
    )
    if "expected_population" in manifest:
        population = manifest["expected_population"]
        strict_fields(population, {"entrants", "exits", "rationale"}, {"entrants", "exits", "rationale"})
        for key in ("entrants", "exits"):
            _bounds(population[key], f"expected_population.{key}")
    aggregate = manifest.get("expected_aggregate", {})
    if not isinstance(aggregate, dict):
        raise ContractError("expected_aggregate must be an object keyed by aggregate-only segment")
    for segment, spec in aggregate.items():
        strict_fields(spec, {"minimum_movers", "rationale"}, {"minimum_movers", "rationale"})
        _bounds(spec["minimum_movers"], f"expected_aggregate.{segment}.minimum_movers")
    identifier(manifest["change_id"], "change_id")
    if manifest["change_type"] not in {"value_classification", "rule", "weight_or_threshold",
                                       "reference_data", "population_scope", "logic"}:
        raise ContractError("unknown change_type")
    ids = set()
    for e in manifest["expected_effects"]:
        strict_fields(e, {"id", "segments", "from", "to", "direction", "count", "rationale"},
                      {"id", "segments", "from", "to", "direction", "count", "rationale"})
        identifier(e["id"], "expectation id")
        if e["id"] in ids:
            raise ContractError("duplicate expectation id")
        ids.add(e["id"])
        for key in ("segments", "from", "to"):
            if not isinstance(e[key], list) or not e[key] or not all(isinstance(x, str) for x in e[key]):
                raise ContractError(f"expectation {e['id']}: {key} must be a nonempty list (use [\"*\"] for all)")
        for key in ("from", "to"):
            if e[key] != ["*"]:
                for tier in e[key]:
                    if tier not in scale.index:
                        raise ContractError(f"expectation {e['id']}: unknown tier {tier}")
        if e["direction"] not in {"up", "down", "any"}:
            raise ContractError("direction must be up, down or any")
        _bounds(e["count"], f"expectation {e['id']} count")
    tolerance = manifest.get("unexplained_tolerance", {"min_count": 1, "min_share": 0.0})
    strict_fields(tolerance, {"min_count", "min_share"}, {"min_count", "min_share"})
    if type(tolerance["min_count"]) is not int or tolerance["min_count"] < 1:
        raise ContractError("unexplained_tolerance.min_count must be a positive integer")
    number(tolerance["min_share"], "min_share", maximum=1)


def _bounds(count, where: str) -> None:
    strict_fields(count, {"min", "max"}, {"min", "max"})
    low, high = count["min"], count["max"]
    if type(low) is not int or low < 0 or (high is not None and (type(high) is not int or high < low)):
        raise ContractError(f"{where} needs integer min <= max (max may be null)")


def _within(observed: int, count: dict) -> bool:
    return observed >= count["min"] and (count["max"] is None or observed <= count["max"])


def _cell_matches(e: dict, segment: str, i: int, j: int, scale: TierScale) -> bool:
    if e["segments"] != ["*"] and segment not in e["segments"]:
        return False
    if e["from"] != ["*"] and scale.tiers[i] not in e["from"]:
        return False
    if e["to"] != ["*"] and scale.tiers[j] not in e["to"]:
        return False
    return {"up": j > i, "down": j < i, "any": True}[e["direction"]]


def reconcile_expectations(assessment: dict, manifest: dict) -> dict:
    """Declared expectations versus observed movement; any movement no expectation explains is surfaced."""
    scale = TierScale(assessment["tier_scale"])
    validate_manifest(manifest, scale)
    known = set(assessment["segments"]) | set(assessment["aggregate_segments"])
    for e in manifest["expected_effects"]:
        unknown = [s for s in e["segments"] if s != "*" and s not in known]
        if unknown:
            raise ContractError(f"expectation {e['id']} names segments not in the assessment: {unknown}")
    k = len(scale.tiers)
    tolerance = manifest.get("unexplained_tolerance", {"min_count": 1, "min_share": 0.0})
    results = []
    for e in manifest["expected_effects"]:
        observed = sum(
            data["matrix"][i][j]
            for segment, data in assessment["segments"].items()
            for i in range(k) for j in range(k)
            if i != j and _cell_matches(e, segment, i, j, scale)
        )
        passed = _within(observed, e["count"])
        results.append({"id": e["id"], "observed": observed, "expected": e["count"],
                        "status": "PASS" if passed else "FAIL", "rationale": e["rationale"]})
    unexplained = []
    for segment, data in assessment["segments"].items():
        for i in range(k):
            row_total = sum(data["matrix"][i])
            for j in range(k):
                count = data["matrix"][i][j]
                if i == j or not count:
                    continue
                if any(_cell_matches(e, segment, i, j, scale) for e in manifest["expected_effects"]):
                    continue
                share = count / row_total
                if count >= tolerance["min_count"] and share >= tolerance["min_share"]:
                    unexplained.append({"segment": segment, "from": scale.tiers[i], "to": scale.tiers[j],
                                        "count": count, "row_share": share, "kind": "migration"})
    declared = manifest.get("expected_aggregate", {})
    for segment in declared:
        if segment not in assessment["aggregate_segments"]:
            raise ContractError(f"expected_aggregate names {segment}, which has no aggregates in the assessment")
    for segment, data in assessment["aggregate_segments"].items():
        moved = data["minimum_movers"]
        if segment in declared:
            spec = declared[segment]
            passed = moved is not None and _within(moved, spec["minimum_movers"])
            results.append({"id": f"AGGREGATE-{segment}", "observed": moved, "expected": spec["minimum_movers"],
                            "status": "PASS" if passed else "FAIL", "rationale": spec["rationale"]})
        elif moved is None or moved > 0:
            unexplained.append({"segment": segment, "from": "*", "to": "*", "count": moved,
                                "row_share": None, "kind": "aggregate_only_movement"})
    entrants, exits = sum(assessment["totals"]["entrants"]), sum(assessment["totals"]["exits"])
    population = manifest.get("expected_population")
    if population is None:
        for kind, n in (("entrants", entrants), ("exits", exits)):
            if n >= tolerance["min_count"]:
                unexplained.append({"segment": "*", "from": "*", "to": "*", "count": n, "row_share": None,
                                    "kind": f"undeclared_{kind}"})
    else:
        for kind, n in (("entrants", entrants), ("exits", exits)):
            results.append({"id": f"POPULATION-{kind.upper()}", "observed": n, "expected": population[kind],
                            "status": "PASS" if _within(n, population[kind]) else "FAIL",
                            "rationale": population["rationale"]})
    consistent = all(r["status"] == "PASS" for r in results) and not unexplained and not assessment["integrity_findings"]
    return {
        "change_id": manifest["change_id"],
        "assessment_hash": assessment["assessment_hash"],
        "expectations": results,
        "unexplained_movements": sorted(unexplained, key=lambda u: -(u["count"] if u["count"] is not None else 10**18)),
        "integrity_findings": list(assessment["integrity_findings"]),
        "overlapping_expectations": _overlaps(assessment, manifest, scale),
        "verdict": "consistent_with_manifest" if consistent else "requires_explanation",
        "limit": "A consistent verdict means observed movement matched declared expectations; it does not validate the expectations themselves.",
    }


def _overlaps(assessment: dict, manifest: dict, scale: TierScale) -> list[list[str]]:
    """Expectation pairs that both claim at least one nonzero cell; such cells count toward both."""
    k = len(scale.tiers)
    claims: dict[str, set] = {e["id"]: set() for e in manifest["expected_effects"]}
    for segment, data in assessment["segments"].items():
        for i in range(k):
            for j in range(k):
                if i != j and data["matrix"][i][j]:
                    for e in manifest["expected_effects"]:
                        if _cell_matches(e, segment, i, j, scale):
                            claims[e["id"]].add((segment, i, j))
    ids = sorted(claims)
    return [[a, b] for x, a in enumerate(ids) for b in ids[x + 1:] if claims[a] & claims[b]]


def _rates(assessment: dict) -> dict:
    out = {}
    tiers = assessment["tier_scale"]["tiers"]
    for segment, data in assessment["segments"].items():
        for i, row in enumerate(data["matrix"]):
            total = sum(row)
            if not total:
                continue
            for j, count in enumerate(row):
                if i != j:
                    out[(segment, tiers[i], tiers[j])] = count / total
        if data["matched"]:
            out[(segment, "*", "*")] = data["moved_share"]
    return out


def baseline_outliers(history: list[dict], assessment: dict, *, min_history: int = 5, z_threshold: float = 3.5) -> dict:
    """Compare migration rates with prior assessments using median and MAD (modified z-score)."""
    if type(min_history) is not int or min_history < 3:
        raise ContractError("min_history must be an integer of at least 3")
    number(z_threshold, "z_threshold", minimum=0.5)
    tiers = assessment["tier_scale"]["tiers"]
    for h in history:
        if h["tier_scale"]["tiers"] != tiers:
            raise ContractError("history must share the current tier scale")
    past = [_rates(h) for h in history]
    flags, insufficient = [], 0
    for key, value in sorted(_rates(assessment).items()):
        series = sorted(p[key] for p in past if key in p)
        if len(series) < min_history:
            insufficient += 1
            continue
        median = _median(series)
        mad = _median([abs(x - median) for x in series])
        if mad == 0:
            if value > series[-1] or value < series[0]:
                flags.append({"segment": key[0], "from": key[1], "to": key[2], "rate": value,
                              "history_median": median, "modified_z": None, "reason": "outside_observed_range",
                              "history_n": len(series)})
            continue
        z = 0.6745 * (value - median) / mad
        if abs(z) >= z_threshold:
            flags.append({"segment": key[0], "from": key[1], "to": key[2], "rate": value, "history_median": median,
                          "modified_z": z, "reason": "modified_z_exceeds_threshold", "history_n": len(series)})
    return {
        "history_assessments": len(history),
        "cells_without_sufficient_history": insufficient,
        "flags": sorted(flags, key=lambda f: -(abs(f["modified_z"]) if f["modified_z"] is not None else math.inf)),
        "settings": {"min_history": min_history, "z_threshold": z_threshold},
        "method": "Iglewicz-Hoaglin modified z-score of each off-diagonal row rate and segment moved share against prior assessments.",
        "limit": "Historical changes differ in kind; an unusual rate is a prompt for explanation, not evidence of error.",
    }


def _median(values: list[float]) -> float:
    s = sorted(values)
    n = len(s)
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2


def matrix_long_rows(assessment: dict) -> list[dict]:
    tiers = assessment["tier_scale"]["tiers"]
    rows = []
    for segment, data in sorted(assessment["segments"].items()):
        for i, row in enumerate(data["matrix"]):
            for j, count in enumerate(row):
                rows.append({"segment": segment, "pre_tier": tiers[i], "post_tier": tiers[j], "count": count})
    return rows


def reconcile_matrices(assessment: dict, standard_rows: list[dict], *, tolerance_abs: int = 0,
                       tolerance_rel: float = 0.0) -> dict:
    """Cell-by-cell parity between this engine and an existing (standard) process output."""
    scale = TierScale(assessment["tier_scale"])
    if type(tolerance_abs) is not int or tolerance_abs < 0:
        raise ContractError("tolerance_abs must be a nonnegative integer")
    number(tolerance_rel, "tolerance_rel", maximum=1)
    auto = {(r["segment"], r["pre_tier"], r["post_tier"]): r["count"] for r in matrix_long_rows(assessment)}
    standard: dict[tuple, int] = {}
    for n, row in enumerate(standard_rows, 1):
        strict_fields(row, {"segment", "pre_tier", "post_tier", "count"}, {"segment", "pre_tier", "post_tier", "count"})
        key = (row["segment"], scale.tiers[scale.parse(row["pre_tier"])], scale.tiers[scale.parse(row["post_tier"])])
        raw = row["count"]
        if isinstance(raw, bool) or not (isinstance(raw, int) or (isinstance(raw, str) and raw.strip().isdigit())):
            raise ContractError(f"standard row {n}: count must be a nonnegative integer, not {raw!r}")
        count = int(raw)
        if key in standard:
            raise ContractError(f"standard row {n}: duplicate cell {key}")
        standard[key] = count
    differences = []
    for key in sorted(set(auto) | set(standard)):
        a, s = auto.get(key, 0), standard.get(key, 0)
        if a == s:
            continue
        allowed = max(tolerance_abs, tolerance_rel * max(a, s))
        differences.append({"segment": key[0], "pre_tier": key[1], "post_tier": key[2], "automated": a,
                            "standard": s, "difference": a - s, "within_tolerance": abs(a - s) <= allowed})
    # Segments compare by populated cells, so an empty configured segment omitted by a nonzero-only export
    # is not a mismatch.
    auto_segments = {k[0] for k, v in auto.items() if v}
    standard_segments = {k[0] for k, v in standard.items() if v}
    if not differences and auto_segments == standard_segments:
        verdict = "EXACT_MATCH"
    elif all(d["within_tolerance"] for d in differences) and auto_segments == standard_segments:
        verdict = "WITHIN_TOLERANCE"
    else:
        verdict = "MISMATCH"
    return {
        "assessment_hash": assessment["assessment_hash"],
        "verdict": verdict,
        "cells_compared": len(set(auto) | set(standard)),
        "differences": sorted(differences, key=lambda d: -abs(d["difference"])),
        "segments_only_in_automated": sorted(auto_segments - standard_segments),
        "segments_only_in_standard": sorted(standard_segments - auto_segments),
        "totals": {"automated": sum(auto.values()), "standard": sum(standard.values())},
        "settings": {"tolerance_abs": tolerance_abs, "tolerance_rel": tolerance_rel},
        "limit": "Parity shows two computations agree on these inputs; agreement with a flawed standard is still agreement.",
    }


def append_register(path: str | Path, entry: dict) -> dict:
    """Append a hash-chained record of an assessment and its verdicts. Tamper-evident, not tamper-proof."""
    strict_fields(entry, {"assessment_id", "assessment_hash", "recorded_at", "verdicts", "notes"},
                  {"assessment_id", "assessment_hash", "recorded_at", "verdicts"})
    entry = {**entry, "recorded_at": utc(entry["recorded_at"])}
    path = Path(path)
    previous, sequence = None, 0
    if path.exists():
        lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        if lines:
            last = json.loads(lines[-1])
            previous, sequence = last["entry_hash"], last["sequence"]
    record = {**entry, "sequence": sequence + 1, "previous_entry_hash": previous}
    record["entry_hash"] = digest(record)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(record, sort_keys=True) + "\n")
        stream.flush()
        os.fsync(stream.fileno())
    return record


def verify_register(path: str | Path, anchor: dict | None = None) -> dict:
    """Recompute the chain. Without an external ``anchor`` ({"entries", "last_entry_hash"}) recorded elsewhere,
    truncation of trailing entries is undetectable: an unanchored chain proves internal consistency only."""
    previous, problems, n = None, [], 0
    for n, line in enumerate((x for x in Path(path).read_text(encoding="utf-8").splitlines() if x.strip()), 1):
        try:
            record = json.loads(line)
            claimed = record.pop("entry_hash")
        except (ValueError, KeyError, AttributeError):
            problems.append({"sequence": n, "issue": "unreadable entry"})
            previous = None
            continue
        if digest(record) != claimed:
            problems.append({"sequence": record.get("sequence"), "issue": "entry hash mismatch"})
        if record.get("previous_entry_hash") != previous or record.get("sequence") != n:
            problems.append({"sequence": record.get("sequence"), "issue": "chain break"})
        previous = claimed
    if anchor is not None:
        if anchor.get("entries") != n or anchor.get("last_entry_hash") != previous:
            problems.append({"sequence": n, "issue": "does not match external anchor (truncated or replaced)"})
    return {"entries": n, "last_entry_hash": previous, "anchored": anchor is not None,
            "status": "intact" if not problems else "broken", "problems": problems}
