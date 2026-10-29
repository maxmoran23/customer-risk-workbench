"""Grounding guard for AI-drafted impact narratives.

Division of labor: deterministic code computes every figure; a language model (any approved tool) may draft
the prose from a facts pack; ``check_narrative`` then rejects any number in the draft that the facts pack does
not contain. No model is called here and no network access is needed.
"""

from __future__ import annotations

import json
import re

from .contracts import ContractError

_SEP = "\u00a0\u2009\u202f"
# A quantity token starts at the beginning of text or after whitespace or an opening bracket, so digits inside
# identifiers (SEGMENT_A1, IA-001, r-2) are not quantities. Range and ratio tails (400-500, 3/7) are separate.
_NUMBER = re.compile(
    r"(?:(?<=^)|(?<=[\s(\[]))(?P<sign>[-+\u2212])?(?P<body>\d[\d," + _SEP + r"]*(?:\.\d+)*|\.\d+)"
    r"(?P<pct>\s?(?:%|percent\b))?(?P<tail>[A-Za-z\u00d7]+)?"
)
_TAIL = re.compile(r"(?<=\d)[-\u2013/](?P<body>\d[\d,]*(?:\.\d+)?)(?P<pct>\s?%)?")
_WORDS = re.compile(
    r"\b(two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|"
    r"eighteen|nineteen|twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety|hundred|hundreds|thousand|thousands|"
    r"million|millions|billion|dozen|dozens|half|third|thirds|quarter|quarters|double|doubled|triple|tripled|twice)\b",
    re.I,
)


def facts_pack(assessment: dict, *, expectations: dict | None = None, baseline: dict | None = None,
               parity: dict | None = None) -> dict:
    facts: dict[str, object] = {
        "assessment_id": assessment["assessment_id"],
        "pre_label": assessment["pre_label"],
        "post_label": assessment["post_label"],
        "tiers": assessment["tier_scale"]["tiers"],
        "total.matched": assessment["totals"]["matched"],
        "total.moved": assessment["totals"]["moved"],
        "total.up": assessment["totals"]["up"],
        "total.down": assessment["totals"]["down"],
        "total.unchanged": assessment["totals"]["unchanged"],
        "total.excluded_pinned": assessment["totals"]["excluded_pinned"],
        "total.entrants": sum(assessment["totals"]["entrants"]),
        "total.exits": sum(assessment["totals"]["exits"]),
        "total.moved_share_pct": _pct(assessment["totals"]["moved_share"]),
        "integrity_findings": assessment["integrity_findings"],
    }
    tiers = assessment["tier_scale"]["tiers"]
    for segment, data in sorted(assessment["segments"].items()):
        prefix = f"segment.{segment}"
        for key in ("matched", "moved", "up", "down", "unchanged", "excluded_pinned", "pinned_moved", "pin_changed",
                    "segment_changed"):
            facts[f"{prefix}.{key}"] = data[key]
        facts[f"{prefix}.moved_share_pct"] = _pct(data["moved_share"])
        facts[f"{prefix}.entrants"] = sum(data["entrants"])
        facts[f"{prefix}.exits"] = sum(data["exits"])
        for i, row in enumerate(data["matrix"]):
            for j, count in enumerate(row):
                if i != j and count:
                    facts[f"{prefix}.cell.{tiers[i]}->{tiers[j]}"] = count
                    facts[f"{prefix}.cell.{tiers[i]}->{tiers[j]}.row_share_pct"] = _pct(count / sum(row))
    for segment, data in sorted(assessment["aggregate_segments"].items()):
        facts[f"aggregate.{segment}.population_change"] = data["population_change"]
        facts[f"aggregate.{segment}.minimum_movers"] = data["minimum_movers"]
        for i, tier in enumerate(tiers):
            facts[f"aggregate.{segment}.net_change.{tier}"] = data["net_change"][i]
    if expectations:
        facts["expectations.verdict"] = expectations["verdict"]
        for e in expectations["expectations"]:
            facts[f"expectation.{e['id']}.observed"] = e["observed"]
            facts[f"expectation.{e['id']}.status"] = e["status"]
        facts["expectations.unexplained_cells"] = len(expectations["unexplained_movements"])
        facts["expectations.overlapping_pairs"] = len(expectations["overlapping_expectations"])
    if baseline:
        facts["baseline.history_assessments"] = baseline["history_assessments"]
        facts["baseline.flags"] = len(baseline["flags"])
    if parity:
        facts["parity.verdict"] = parity["verdict"]
        facts["parity.differences"] = len(parity["differences"])
    numeric = {k: v for k, v in facts.items() if isinstance(v, (int, float)) and not isinstance(v, bool)}
    counts = sorted({float(v) for k, v in numeric.items() if not k.endswith("_pct")})
    percents = sorted({float(v) for k, v in numeric.items() if k.endswith("_pct")})
    return {
        "facts": facts,
        "allowed_numbers": counts,
        "allowed_percents": percents,
        "rules": [
            "Use only figures present in facts; do not compute new totals, rates or differences.",
            "Keep the standard section order: change summary, population and exclusions, migration by segment, annexes.",
            "State every integrity finding and every FAIL or unexplained movement; do not characterize them as benign.",
            "Do not attribute cause beyond the change manifest; say 'requires explanation' where the facts do.",
            "Percentages are given to one decimal place; quote them as given, with a percent sign.",
            "Write every quantity in digits as given (no 1.2k, 5M, 3x, ranges, fractions or spelled-out numbers).",
        ],
    }


def _pct(value):
    return None if value is None else round(100 * value, 1)


def prompt_text(pack: dict) -> str:
    """Vendor-neutral drafting prompt. Paste into an approved assistant with the facts JSON appended."""
    rules = "\n".join(f"- {r}" for r in pack["rules"])
    return (
        "You are drafting the narrative section of a change-impact assessment for a customer risk rating model.\n"
        "Write four short paragraphs in plain, neutral language for senior reviewers.\n"
        f"Rules:\n{rules}\n"
        "If a figure you want is not in the facts, write 'not computed' instead of estimating it.\n\n"
        "FACTS (JSON):\n" + json.dumps(pack["facts"], indent=2, sort_keys=True)
    )


def _value(body: str) -> float | None:
    cleaned = body
    for ch in "," + _SEP:
        cleaned = cleaned.replace(ch, "")
    if cleaned.count(".") > 1:
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def _quantities(text: str) -> list[dict]:
    found = []
    for m in _NUMBER.finditer(text):
        value = _value(m.group("body"))
        sign = m.group("sign")
        if value is not None and sign in ("-", "\u2212"):
            value = -value
        found.append({"text": m.group(0).strip(), "value": value, "percent": bool(m.group("pct")),
                      "format_issue": bool(m.group("tail")) or value is None, "start": m.start(), "end": m.end()})
    for m in _TAIL.finditer(text):
        found.append({"text": m.group(0), "value": _value(m.group("body")), "percent": bool(m.group("pct")),
                      "format_issue": True, "start": m.start(), "end": m.end()})
    for m in _WORDS.finditer(text):
        found.append({"text": m.group(0), "value": None, "percent": False, "format_issue": True,
                      "start": m.start(), "end": m.end()})
    return sorted(found, key=lambda q: q["start"])


def check_narrative(text: str, pack: dict, *, required: list[str] | None = None) -> dict:
    """Reject drafts quoting any quantity the facts pack does not contain.

    Counts must equal a count fact exactly; a percentage must match a percentage fact (to 0.05). Shorthand,
    exponents, ordinals, multipliers, ranges, ratios and spelled-out quantities are rejected as unverifiable
    formats. Required facts must appear as a whole quantity, not as a substring of another number.
    """
    if not isinstance(text, str):
        raise ContractError("narrative must be text")
    counts = pack["allowed_numbers"]
    percents = pack.get("allowed_percents", counts)
    unsupported = []
    quantities = _quantities(text)
    for q in quantities:
        context = text[max(0, q["start"] - 40):q["end"] + 40]
        if q["format_issue"]:
            unsupported.append({"number": q["text"], "reason": "unverifiable_format", "context": context})
            continue
        pool, tolerance = (percents, 0.05) if q["percent"] else (counts, 0.0)
        if not any(abs(q["value"] - a) <= tolerance + 1e-9 for a in pool):
            unsupported.append({"number": q["text"], "reason": "not_in_facts", "context": context})
    quoted = {q["value"] for q in quantities if not q["format_issue"]}
    missing = []
    for key in required or []:
        if key not in pack["facts"]:
            raise ContractError(f"required fact {key} is not in the pack")
        value = pack["facts"][key]
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            if not any(abs(float(value) - v) <= 1e-9 for v in quoted):
                missing.append(key)
        elif not re.search(r"(?<![\w-])" + re.escape(str(value)) + r"(?![\w-])", text):
            missing.append(key)
    return {
        "numbers_checked": len(quantities),
        "unsupported_numbers": unsupported,
        "missing_required_facts": missing,
        "status": "grounded" if not unsupported and not missing else "rejected",
        "limit": "Numeric grounding only: a quantity that equals some fact may still be attached to the wrong subject. Human review remains required.",
    }
