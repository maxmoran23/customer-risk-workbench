"""Executable synthetic behavior specifications, not a detector effectiveness study.

Each catalog entry maps to one concrete assertion. Boundary cases sharing a predicate
are reported as engineering cases, never as distinct financial-crime typologies.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, replace
from datetime import timedelta
import math
from typing import Callable

from .contracts import ContractError, Customer, Transaction, timestamp
from .features import FeatureSet, build_features
from .policy import Policy
from .scoring import score
from .synthetic import DEFAULT_AS_OF, PROFILE_KEYS

AS_OF = DEFAULT_AS_OF
CUTOFF = timestamp(AS_OF)


def _time(days: float = 0, seconds: float = 0) -> str:
    return (CUTOFF - timedelta(days=days, seconds=seconds)).isoformat().replace("+00:00", "Z")


def _customer(**changes) -> Customer:
    profile = {k: .05 for k in PROFILE_KEYS}
    profile["screening_unresolved"] = 0.0
    values = dict(customer_id="case-customer", as_of=_time(1), available_at=_time(1),
                  segment="retail", onboarded_at=_time(400), profile=profile,
                  expected_monthly_volume=6000.0, source_id="synthetic-profile",
                  history_start=_time(400), history_complete=True)
    values.update(changes)
    return Customer(**values)


def _tx(index: int, *, days: float = 1, seconds: float = 0, amount: float = 100,
        direction: str = "in", channel: str = "wire", risk: float | None = .05,
        counterparty: str | None = None, **changes) -> Transaction:
    values = dict(transaction_id=f"case-t-{index:04d}", customer_id="case-customer",
                  occurred_at=_time(days, seconds), available_at=_time(days, seconds), amount=amount,
                  direction=direction, counterparty_id=counterparty or f"case-p-{index:04d}",
                  channel=channel, jurisdiction_risk=risk, source_id="synthetic-ledger")
    values.update(changes)
    return Transaction(**values)


def _baseline() -> list[Transaction]:
    recent = [_tx(i, days=.25 + i / 2, direction="in" if i % 2 else "out") for i in range(60)]
    previous = [_tx(100 + i, days=31 + 2 * i, amount=600, direction="in" if i % 2 else "out") for i in range(10)]
    return recent + previous


def _features(events=None, customer=None) -> FeatureSet:
    return build_features(customer or _customer(), _baseline() if events is None else events, AS_OF)


def _assessment(policy, events=None, customer=None) -> dict:
    c = customer or _customer()
    return score(_features(events, c), policy, c.customer_id, AS_OF)


def _check(condition: bool, detail: str) -> None:
    if not condition:
        raise AssertionError(detail)


def _equal(actual, expected, detail: str = "") -> dict:
    if isinstance(expected, (float, int)) and not isinstance(expected, bool):
        ok = actual is not None and math.isclose(actual, expected, rel_tol=1e-10, abs_tol=1e-10)
    else:
        ok = actual == expected
    _check(ok, f"{detail}: expected {expected!r}, observed {actual!r}")
    return {"observed": actual, "expected": expected}


def _invalid(operation: Callable) -> dict:
    try:
        operation()
    except ContractError as exc:
        return {"observed": "ContractError", "detail": str(exc)}
    raise AssertionError("invalid fixture was accepted")


@dataclass(frozen=True)
class Scenario:
    id: str
    title: str
    category: str
    family: str
    rationale: str
    expected: str
    check: Callable[[Policy], dict]

    def metadata(self) -> dict:
        return {key: getattr(self, key) for key in ("id", "title", "category", "family", "rationale", "expected")}


_CASES: list[Scenario] = []


def _case(case_id, title, category, family, rationale, expected):
    def register(check):
        _CASES.append(Scenario(case_id, title, category, family, rationale, expected, check))
        return check
    return register


_CONTEXTS = [
    ("ownership_opacity", "Opaque ownership versus evidenced ownership", "ownership", "The score responds to supplied ownership evidence, not a corporate legal form."),
    ("business_complexity", "Complex activity with versus without contextual concern", "business_context", "Legal operational complexity requires proportional context; company structure alone proves no misconduct."),
    ("source_of_funds_concern", "Unexplained source of funds versus supported origin", "funding_context", "A normalized concern requires a separate evidence adapter; wealth or volume alone is not its substitute."),
    ("geography_exposure", "Elevated supplied exposure versus low supplied exposure", "geography_context", "Invented normalized exposure exercises the mapping without publishing a country blacklist."),
    ("product_complexity", "Opaque product use versus transparent product use", "product_context", "Product evidence is represented independently of transactional amount."),
    ("channel_opacity", "Opaque delivery channel versus traceable channel", "channel_context", "Cash and digital channels are not inherently synonymous with opacity."),
    ("adverse_information", "Corroborated adverse information versus absent concern", "adverse_information", "Fixture values represent assessed evidence; the engine performs no news verification."),
    ("pep_exposure", "PEP contextual exposure versus low contextual exposure", "pep_context", "PEP context has a limited weight and creates no automatic high band."),
    ("documentation_gap", "Material documentation gap versus complete documentation", "documentation", "A known evidence gap and an unknown profile field are different states."),
]
for key, title, family, rationale in _CONTEXTS:
    def context_check(policy, key=key):
        c = _customer()
        low = _assessment(policy, customer=replace(c, profile={**c.profile, key: 0}))
        high = _assessment(policy, customer=replace(c, profile={**c.profile, key: 1}))
        _check(high["provisional_index"] >= low["provisional_index"], "higher supplied concern reduced the index")
        return {"low_index": low["provisional_index"], "high_index": high["provisional_index"], "delta": high["provisional_index"] - low["provisional_index"]}
    _case("CTX-" + key, title, "paired_context", family, rationale,
          "Increasing this evidence does not reduce the index; all other evidence is held fixed.")(context_check)


@_case("CTX-pep-no-auto-high", "PEP exposure alone does not require high risk", "counterexample", "pep_context",
       "A public role by itself does not establish suspicious activity.", "Under the reference policy, PEP evidence alone remains below HIGH.")
def _pep(policy):
    c = _customer(profile={k: float(k == "pep_exposure") for k in PROFILE_KEYS})
    result = _assessment(policy, customer=c)
    _check(result["band"] == "LOW", f"unexpected PEP-only band {result['band']}")
    return {"band": result["band"], "index": result["provisional_index"]}


for segment, title, rationale in [
    ("nonprofit", "Lawful charity is not penalized by its segment label", "Charitable status is not a financial-crime predicate."),
    ("cash_business", "Cash-business label is not itself a risk trigger", "Observed cash exposure can be reviewed without treating all cash businesses as illicit."),
    ("complex_corporate", "Legal complexity label does not replace ownership evidence", "Opaque evidence must not be inferred from a business label."),
    ("digital_business", "Digital-business label is not automatically suspicious", "The engine does not equate digital services with misconduct."),
]:
    def segment_check(policy, segment=segment):
        before = _assessment(policy)
        after = _assessment(policy, customer=replace(_customer(), segment=segment))
        return _equal(after["provisional_index"], before["provisional_index"], "segment invariance")
    _case("BEN-" + segment, title, "counterexample", "segment_context", rationale,
          "Changing only the descriptive segment preserves the numerical index.")(segment_check)


@_case("BEN-treasury-balance", "Lawful treasury can have balanced aggregate flows", "counterexample", "aggregate_balance",
       "Aggregate inflow/outflow balance cannot establish tracing, layering, or a round trip.", "A legitimate treasury fixture produces flow_through=1, exposing the proxy's limited specificity.")
def _treasury(policy):
    events = [_tx(1, amount=1000, direction="in"), _tx(2, amount=1000, direction="out", counterparty="salary-account")]
    return _equal(_features(events).values["txn.30d.flow_through"], 1)


@_case("BEN-cash-share-not-structuring", "High cash share is not a structuring determination", "counterexample", "cash_exposure",
       "The ledger has no reporting threshold, intent, branch geography, or cash-deposit aggregation contract.", "A lawful cash-shop fixture has cash_share=1; no structuring label is emitted.")
def _cash_benign(policy):
    events = [_tx(i, amount=250 + 25 * i, channel="cash") for i in range(5)]
    f = _features(events)
    _equal(f.values["txn.30d.cash_share"], 1)
    _check(not any("structur" in name for name in f.values), "unsupported typology claim")
    return {"cash_share": 1, "structuring_detector": False}


_AGGREGATES = [
    ("count", "Event count", "count", [_tx(1), _tx(2)], 2, "Count observations independently of amount."),
    ("total", "Amount sum", "total", [_tx(1, amount=25), _tx(2, amount=75)], 100, "Amounts already share one declared base unit."),
    ("in-total", "Incoming amount is direction-specific", "in_total", [_tx(1, amount=25), _tx(2, amount=75, direction="out")], 25, "Outgoing activity must not inflate incoming total."),
    ("out-total", "Outgoing amount is direction-specific", "out_total", [_tx(1, amount=25), _tx(2, amount=75, direction="out")], 75, "Incoming activity must not inflate outgoing total."),
    ("cash-weighted", "Cash share uses amounts, not event counts", "cash_share", [_tx(1, amount=20, channel="cash"), _tx(2, amount=80)], .2, "One cash event among two does not imply a fifty-percent cash amount share."),
    ("digital-weighted", "Digital share uses amounts, not event counts", "digital_share", [_tx(1, amount=75, channel="digital"), _tx(2, amount=25)], .75, "Channel proportions use the declared amount denominator."),
    ("unique-counterparties", "Counterparty count deduplicates opaque identities", "counterparty_count", [_tx(1, counterparty="same"), _tx(2, counterparty="same"), _tx(3)], 2, "Repeated events are not new counterparties."),
    ("jurisdiction-weighted", "Exposure is an amount-weighted supplied value", "high_risk_share", [_tx(1, amount=25, risk=1), _tx(2, amount=75, risk=0)], .25, "This is neither a country count nor a list-screening outcome."),
    ("flow-balanced", "Balanced aggregate flows", "flow_through", [_tx(1, amount=200), _tx(2, amount=200, direction="out")], 1, "The balance proxy reaches one when inflow and outflow totals match."),
    ("flow-partial", "Partly balanced aggregate flows", "flow_through", [_tx(1, amount=400), _tx(2, amount=100, direction="out")], .25, "The ratio divides the smaller direction total by the larger."),
    ("flow-one-sided", "One-sided incoming activity", "flow_through", [_tx(1, amount=200)], 0, "Positive one-direction activity produces zero balance, not a missing denominator."),
    ("concentration-count", "Concentration measures event-count share", "concentration", [_tx(1, amount=1, counterparty="same"), _tx(2, amount=1, counterparty="same"), _tx(3, amount=998)], 2 / 3, "A high-value separate counterparty does not alter this explicitly count-based feature."),
    ("mean", "Mean amount has the observed count denominator", "mean_amount", [_tx(1, amount=10), _tx(2, amount=90)], 50, "Zero-amount records remain in the count if present."),
    ("maximum", "Maximum amount preserves the largest event", "max_amount", [_tx(1, amount=10), _tx(2, amount=90)], 90, "This statistic does not infer a transaction reporting threshold."),
    ("jurisdiction-coverage", "Jurisdiction evidence coverage is explicit", "jurisdiction_coverage", [_tx(1, risk=None), _tx(2, risk=.1)], .5, "Coverage counts mapped events and remains separate from risk exposure."),
    ("zero-volume", "Zero total has no cash-share denominator", "cash_share", [_tx(1, amount=0)], None, "A zero denominator is unknown, not a benign ratio."),
    ("empty-ratio", "Empty ledger has unknown behavioral proportions", "flow_through", [], None, "Absence of activity does not establish an observed behavioral ratio."),
    ("unmapped-jurisdiction", "One unknown jurisdiction prevents a complete exposure ratio", "high_risk_share", [_tx(1, risk=None), _tx(2, risk=1)], None, "Dropping unknown exposure from the denominator would create a misleading ratio."),
]
for case_id, title, metric, events, expected, rationale in _AGGREGATES:
    def aggregate_check(policy, metric=metric, events=events, expected=expected):
        return _equal(_features(events).values["txn.30d." + metric], expected, metric)
    _case("AGG-" + case_id, title, "arithmetic", "aggregation", rationale,
          f"30d {metric} equals {expected!r} for the explicitly specified fixture.")(aggregate_check)


for window, days in (("1d", 1), ("7d", 7), ("30d", 30), ("90d", 90), ("180d", 180), ("365d", 365)):
    def boundary_check(policy, window=window, days=days):
        events = [_tx(1, days=days, seconds=1, amount=1), _tx(2, days=days, amount=10),
                  _tx(3, days=days, seconds=-1, amount=100), _tx(4, days=0, amount=1000)]
        f = _features(events)
        _equal(f.values[f"txn.{window}.count"], 2)
        return _equal(f.values[f"txn.{window}.total"], 1100)
    _case("TIME-boundary-" + window, f"{window} cutoff excludes the exact lower boundary", "temporal", "time_windows",
          "Windows are (cutoff-duration, cutoff]; a one-second change can alter membership.",
          "Only the event one second inside the lower bound and the exact-cutoff event contribute: count=2, total=1100.")(boundary_check)


for window, n in (("last4", 4), ("last10", 10), ("last25", 25), ("last50", 50)):
    def count_window_check(policy, window=window, n=n):
        events = [_tx(i, days=n + 1 - i, amount=i + 1) for i in range(n + 1)]
        f = _features(events)
        _equal(f.values[f"txn.{window}.count"], n)
        return _equal(f.values[f"txn.{window}.total"], (n + 1) * (n + 2) / 2 - 1)
    _case("TIME-count-" + window, f"{window} retains precisely the most recent observations", "temporal", "count_windows",
          "Count windows answer a different question from elapsed-time windows.",
          f"The oldest of {n+1} sequential records is excluded, leaving {n} records and the independently computed triangular sum.")(count_window_check)


@_case("TIME-future-event", "Future event cannot leak into an earlier assessment", "temporal", "availability",
       "A later effective transaction is not part of the earlier information set.", "Adding a future event preserves feature values and index; excluded_future increments.")
def _future(policy):
    before = _features()
    after = _features(_baseline() + [_tx(999, days=-1, amount=1_000_000)])
    _equal(after.values, before.values)
    return _equal(after.quality["excluded_future"], 1)


@_case("TIME-late-arrival", "An old event received tomorrow is unavailable today", "temporal", "availability",
       "Effective time alone is insufficient for a replay-safe model.", "Feature values remain unchanged and excluded_unavailable increments.")
def _unavailable(policy):
    before = _features()
    after = _features(_baseline() + [_tx(999, days=2, amount=1_000_000, available_at=_time(-1))])
    _equal(after.values, before.values)
    return _equal(after.quality["excluded_unavailable"], 1)


@_case("TIME-available-at-cutoff", "An event received exactly at cutoff is available", "temporal", "availability",
       "Availability uses an inclusive upper boundary.", "The old event available exactly at cutoff contributes its amount.")
def _available_cutoff(policy):
    return _equal(_features([_tx(1, days=2, amount=123, available_at=AS_OF)]).values["txn.30d.total"], 123)


@_case("TIME-tie-break", "Same-time last-N selection has a stable ID tie-break", "temporal", "count_windows",
       "An input-order tie-break would make repeated ingestion change scores.", "Among five simultaneous events, last4 excludes the lexicographically smallest ID and sums to 14.")
def _ties(policy):
    events = [_tx(i, amount=i + 1) for i in range(5)]
    return _equal(_features(list(reversed(events))).values["txn.last4.total"], 14)


@_case("TIME-history-retention", "Events older than retained history do not fill a window", "temporal", "retention",
       "Declared retention is part of the observation contract.", "A 50-day-old event is excluded when retained history starts 40 days ago.")
def _retention(policy):
    c = _customer(history_start=_time(40))
    f = _features([_tx(1, days=50), _tx(2, days=1)], c)
    _equal(f.values["txn.lifetime.count"], 1)
    return _equal(f.quality["complete_windows"]["lifetime"], False)


@_case("TIME-partial-30d", "Short retained history cannot establish full-month expectation", "temporal", "retention",
       "Observed activity must not be compared as a complete month after a short observation span.", "Expected-volume ratio is None with only 20 days of retained history.")
def _short_history(policy):
    return _equal(_features([_tx(1)], _customer(history_start=_time(20))).values["txn.30d.expected_volume_ratio"], None)


@_case("TIME-growth-denominator", "Growth uses the preceding disjoint 30-day interval", "temporal", "growth",
       "Comparing an overlapping rolling window would obscure the intended growth denominator.", "Current 300 / previous 100 gives growth=3; 60-day boundary event is excluded.")
def _growth(policy):
    events = [_tx(1, days=5, amount=300), _tx(2, days=30, amount=100), _tx(3, days=60, amount=900)]
    return _equal(_features(events).values["txn.30d.growth_ratio"], 3)


@_case("TIME-growth-zero", "Growth with zero prior activity is undefined", "missing", "growth",
       "An infinite or invented growth value would encode an unsupported assumption.", "Growth is None when preceding-month total is zero.")
def _growth_zero(policy):
    return _equal(_features([_tx(1, amount=300)]).values["txn.30d.growth_ratio"], None)


@_case("QUAL-required-missing", "Missing mandatory ownership evidence requires review", "missing", "required_evidence",
       "A missing required field cannot be treated as risk-free.", "The engine returns REVIEW_REQUIRED, a null final score, and a bounded interval.")
def _required_missing(policy):
    c = _customer()
    r = _assessment(policy, customer=replace(c, profile={**c.profile, "ownership_opacity": None}))
    _equal(r["band"], "REVIEW_REQUIRED")
    _equal(r["score"], None)
    _check(r["upper_bound"] > r["lower_bound"], "missing ownership has no uncertainty allowance")
    return {"lower": r["lower_bound"], "upper": r["upper_bound"], "band": r["band"]}


@_case("QUAL-required-absent", "Absent mandatory profile key is missing evidence", "missing", "required_evidence",
       "Omitted and explicitly null mandatory evidence must both be visible.", "An omitted source-of-funds key produces required_evidence_missing.")
def _required_absent(policy):
    c = _customer()
    profile = dict(c.profile)
    del profile["source_of_funds_concern"]
    r = _assessment(policy, customer=replace(c, profile=profile))
    _check("required_evidence_missing" in r["gates"], "absent required key was silently accepted")
    return {"gates": r["gates"]}


@_case("QUAL-history-incomplete", "Unconfirmed feed completeness requires review", "missing", "retention",
       "A full-looking count of received rows does not prove that the feed is complete.", "history_complete=False produces REVIEW_REQUIRED.")
def _history_incomplete(policy):
    r = _assessment(policy, customer=replace(_customer(), history_complete=False))
    return _equal(r["band"], "REVIEW_REQUIRED")


@_case("QUAL-small-support", "Three observations do not meet four-event support", "boundary", "support",
       "A numerical ratio may exist while policy support is insufficient.", "The 7d cash factor records insufficient_events with three events.")
def _support(policy):
    r = _assessment(policy, [_tx(i, channel="cash") for i in range(3)])
    row = next(x for x in r["missing_features"] if x["factor"] == "cash_7d")
    return _equal(row["reason"], "insufficient_events")


@_case("QUAL-support-edge", "Four observations meet four-event support", "boundary", "support",
       "The minimum event-count gate is inclusive.", "The 7d cash factor is available with four events and complete history.")
def _support_edge(policy):
    r = _assessment(policy, [_tx(i, channel="cash") for i in range(4)])
    _check(not any(x["factor"] == "cash_7d" for x in r["missing_features"]), "four-event support was rejected")
    return {"cash_7d_available": True}


@_case("QUAL-zero-expectation", "Zero expected volume does not create a ratio", "missing", "expectation",
       "A zero business expectation requires a separate review hypothesis, not division by zero.", "expected_volume_ratio is None.")
def _zero_expectation(policy):
    return _equal(_features(customer=_customer(expected_monthly_volume=0)).values["txn.30d.expected_volume_ratio"], None)


@_case("QUAL-null-expectation", "Unknown expected volume remains unknown", "missing", "expectation",
       "An absent expected baseline cannot be reconstructed from observed activity without circularity.", "expected_volume_ratio is None.")
def _null_expectation(policy):
    return _equal(_features(customer=_customer(expected_monthly_volume=None)).values["txn.30d.expected_volume_ratio"], None)


_INVALID_CASES = [
    ("duplicate", "Duplicate transaction identity is rejected", "Identity collisions could double count activity.", lambda: _features([_tx(1), _tx(1)])),
    ("foreign-customer", "Another customer's transaction is rejected", "Cross-customer contamination changes both privacy scope and model evidence.", lambda: _features([_tx(1, customer_id="another-customer")])),
    ("negative-amount", "Negative normalized amount is rejected", "Direction is explicit; signed-amount ambiguity is forbidden.", lambda: _tx(1, amount=-1)),
    ("nan-amount", "Nonfinite amount is rejected", "NaN propagation can silently defeat score comparisons.", lambda: _tx(1, amount=float("nan"))),
    ("bool-amount", "Boolean amount is rejected", "Python boolean numeric coercion is not a valid ledger amount.", lambda: _tx(1, amount=True)),
    ("naive-time", "Timezone-free event time is rejected", "Local-clock ambiguity prevents reproducible point-in-time windows.", lambda: _tx(1, occurred_at="2026-09-30T12:00:00")),
    ("availability-before-event", "Availability before event is rejected", "The fixture contract does not support anticipatory or scheduled ledger records.", lambda: _tx(1, days=1, available_at=_time(2))),
    ("before-onboarding", "Pre-onboarding transaction is rejected", "Activity outside the declared relationship cannot be silently attributed.", lambda: _features([_tx(1, days=401)])),
    ("future-profile", "Future effective profile cannot be replayed today", "Later profile knowledge must not leak into earlier ratings.", lambda: _features(customer=_customer(as_of=_time(-1), available_at=_time(-1)))),
    ("late-profile", "Unavailable profile cannot be replayed today", "Profile availability is checked independently of profile effective time.", lambda: _features(customer=_customer(available_at=_time(-1)))),
    ("invalid-exposure", "Out-of-range jurisdiction evidence is rejected", "Normalized evidence must remain inside its declared 0..1 scale.", lambda: _tx(1, risk=1.01)),
    ("unknown-channel", "Undeclared channel values are rejected", "Adapter mappings must be explicit rather than silently falling into a default class.", lambda: _tx(1, channel="unmapped")),
]
for case_id, title, rationale, operation in _INVALID_CASES:
    def invalid_check(policy, operation=operation):
        return _invalid(operation)
    _case("REJECT-" + case_id, title, "invalid_input", "contract", rationale,
          "The invalid fixture raises ContractError before a rating is emitted.")(invalid_check)


@_case("INV-permutation", "Input ordering cannot change a replay", "invariance", "replay",
       "A batch file and a reordered database cursor should produce the same assessment.", "Reversing every event yields the identical assessment hash.")
def _permutation(policy):
    return _equal(_assessment(policy, list(reversed(_baseline())))["assessment_hash"], _assessment(policy)["assessment_hash"])


@_case("INV-unit-rescaling", "Consistent amount-and-expectation rescaling preserves the index", "invariance", "normalization",
       "A change of declared unit should not alter ratios when numerator and denominator change together.", "Multiplying every amount and expected volume by 100 preserves index and ratio features.")
def _rescale(policy):
    events = [replace(t, amount=t.amount * 100) for t in _baseline()]
    result = _assessment(policy, events, _customer(expected_monthly_volume=600_000))
    return _equal(result["provisional_index"], _assessment(policy)["provisional_index"])


@_case("INV-counterparty-renaming", "Bijective opaque-counterparty renaming preserves metrics", "invariance", "identity",
       "Identity equality matters; identifier spelling does not.", "Appending a fixed suffix to each counterparty preserves feature values.")
def _counterparty_renaming(policy):
    events = [replace(t, counterparty_id=t.counterparty_id + "-alias") for t in _baseline()]
    return _equal(_features(events).values, _features().values)


@_case("INV-source-renaming", "Source provenance does not silently become risk evidence", "invariance", "lineage",
       "An adapter source label can change lineage without altering observed values.", "Source renaming preserves the index but changes the assessment hash.")
def _source_rename(policy):
    events = [replace(t, source_id="alternate-source") for t in _baseline()]
    old, new = _assessment(policy), _assessment(policy, events)
    _equal(new["provisional_index"], old["provisional_index"])
    _check(new["assessment_hash"] != old["assessment_hash"], "source change disappeared from lineage")
    return {"index_unchanged": True, "hash_changed": True}


@_case("INV-timezone-equivalence", "Equivalent timezone notation preserves event membership", "invariance", "time_windows",
       "Explicit offset timestamps normalize to the same UTC instant.", "Replacing one event with equivalent -04:00 notation preserves all feature values.")
def _timezone(policy):
    events = [_tx(1, days=1)]
    equivalent = replace(events[0], occurred_at="2026-09-29T20:00:00-04:00", available_at="2026-09-29T20:00:00-04:00")
    return _equal(_features([equivalent]).values, _features(events).values)


@_case("INV-no-event-mutation", "Feature construction does not mutate caller records", "invariance", "replay",
       "Repeated assessment must be safe for reused in-memory fixtures.", "Input transaction dictionaries and list order remain unchanged.")
def _mutation(policy):
    events = list(reversed(_baseline()))
    snapshots = [t.to_dict() for t in events]
    _features(events)
    return _equal([t.to_dict() for t in events], snapshots)


@_case("SCORE-neutral-hand-calculated", "Neutral fixture reconciles to 15.75 index points", "policy_arithmetic", "scoring",
       "Reference groups contribute 1.25+0.75+0.75+12+0.50+0.50; flow balance supplies the 12 behavior points.", "Complete fixture score and sum of groups both equal 15.75.")
def _neutral_score(policy):
    r = _assessment(policy)
    _equal(r["score"], 15.75)
    return _equal(sum(g["points"] for g in r["groups"]), 15.75)


@_case("SCORE-overlap-max", "Overlapping cash windows do not each add points", "policy_arithmetic", "overlap",
       "The same events appear in 7d, 30d, 90d and last-N windows; naive addition would amplify one exposure.", "All-cash behavior contributes exactly 15 points, not five times 15.")
def _overlap(policy):
    r = _assessment(policy, [replace(t, channel="cash") for t in _baseline()])
    g = next(g for g in r["groups"] if g["id"] == "behavior")
    return _equal(g["points"], 15)


@_case("SCORE-geography-max", "Profile and activity geography are not double counted", "policy_arithmetic", "overlap",
       "Profile geography and observed exposure can represent the same underlying relationship.", "Both maximum profile and maximum observed exposure contribute 15 geography points in total.")
def _geography_max(policy):
    c = _customer()
    c = replace(c, profile={**c.profile, "geography_exposure": 1})
    r = _assessment(policy, [replace(t, jurisdiction_risk=1) for t in _baseline()], c)
    return _equal(next(g for g in r["groups"] if g["id"] == "geography")["points"], 15)


@_case("SCORE-index-bounds", "Simultaneous high evidence remains inside the 100-point cap", "policy_arithmetic", "scoring",
       "Caps make contribution limits explicit; saturation is a policy choice, not calibrated likelihood.", "All-high fixture with fivefold expected-volume excess reaches exactly 100.")
def _caps(policy):
    c = _customer(profile={k: 1.0 for k in PROFILE_KEYS}, expected_monthly_volume=1200)
    r = _assessment(policy, customer=c)
    _equal(r["score"], 100)
    return {"score": r["score"], "group_points": {g["id"]: g["points"] for g in r["groups"]}}


for label, expectation, expected_points in (("low", 4000, 12), ("mid", 6000 / 3.25, 12.5), ("high", 1200, 25)):
    def volume_edge(policy, expectation=expectation, expected_points=expected_points):
        r = _assessment(policy, customer=_customer(expected_monthly_volume=expectation))
        g = next(g for g in r["groups"] if g["id"] == "behavior")
        return _equal(g["points"], expected_points)
    _case("SCORE-volume-" + label, f"Expected-volume {label} threshold arithmetic", "policy_arithmetic", "expectation",
          "Reference severity is clipped linear interpolation from ratio 1.5 to 5; the behavior group takes the maximum including 12 flow points.",
          f"Behavior contribution equals {expected_points} for monthly expectation {expectation} and observed amount 6000.")(volume_edge)


@_case("ROUTE-screening-separate", "Unresolved screening opens a separate review route", "routing", "screening",
       "A numerical AML index neither clears nor confirms a screening match.", "Changing unresolved screening from 0 to 1 preserves index and activates the TRUE review route.")
def _screening_route(policy):
    c = _customer()
    old = _assessment(policy)
    new = _assessment(policy, customer=replace(c, profile={**c.profile, "screening_unresolved": 1}))
    _equal(new["provisional_index"], old["provisional_index"])
    return _equal(new["review_flags"][0]["state"], "TRUE")


@_case("ROUTE-screening-unknown", "Missing screening evidence is an UNKNOWN route state", "routing", "screening",
       "A missing screening observation must not look like a cleared match.", "Null screening evidence produces UNKNOWN independently of the numerical index.")
def _screening_unknown(policy):
    c = _customer()
    r = _assessment(policy, customer=replace(c, profile={**c.profile, "screening_unresolved": None}))
    return _equal(r["review_flags"][0]["state"], "UNKNOWN")


@_case("ROUTE-screening-edge", "Screening route threshold is inclusive", "routing", "screening",
       "Routing boundaries need explicit tests independently of rating bands.", "The reference route is FALSE just below 0.5 and TRUE exactly at 0.5.")
def _screening_edge(policy):
    c = _customer()
    before = _assessment(policy, customer=replace(c, profile={**c.profile, "screening_unresolved": .499999}))
    at = _assessment(policy, customer=replace(c, profile={**c.profile, "screening_unresolved": .5}))
    _equal(before["review_flags"][0]["state"], "FALSE")
    return _equal(at["review_flags"][0]["state"], "TRUE")


@_case("QUAL-optional-within-band", "Optional missing exposure can leave one bounded band", "missing", "missing_bounds",
       "Missing optional evidence can preclude an exact score without crossing the band boundary.", "With all profile concerns zero, unknown geography produces bounds [12,27], LOW band and null score.")
def _optional_bounded(policy):
    c = _customer(profile={k: 0.0 for k in PROFILE_KEYS})
    events = [replace(t, jurisdiction_risk=None) for t in _baseline()]
    r = _assessment(policy, events, c)
    _equal(r["score"], None)
    _equal(r["lower_bound"], 12)
    _equal(r["upper_bound"], 27)
    return _equal(r["band"], "LOW")


@_case("QUAL-optional-crosses-band", "Optional missing exposure crossing a band requires review", "missing", "missing_bounds",
       "A minimum possible score does not justify a final band when the upper bound reaches another band.", "Unknown geography in the neutral fixture produces bounds [15.75,30] and REVIEW_REQUIRED.")
def _optional_crosses(policy):
    events = [replace(t, jurisdiction_risk=None) for t in _baseline()]
    r = _assessment(policy, events)
    _equal(r["lower_bound"], 15.75)
    _equal(r["upper_bound"], 30)
    return _equal(r["band"], "REVIEW_REQUIRED")


@_case("QUAL-last10-incomplete", "Four events do not constitute a complete last-ten window", "boundary", "support",
       "Meeting minimum support and filling the declared observation window are separate requirements.", "The last10 cash factor is unavailable with incomplete_window despite four observed events.")
def _last10_incomplete(policy):
    r = _assessment(policy, [_tx(i, channel="cash") for i in range(4)])
    row = next(x for x in r["missing_features"] if x["factor"] == "cash_last10")
    return _equal(row["reason"], "incomplete_window")


@_case("TIME-stale-profile", "Old profile evidence contributes only through its declared policy ramp", "temporal", "profile_age",
       "Age is measured from the effective snapshot and is not confused with relationship tenure.", "A 730-day-old effective profile contributes 10 evidence points while fresh data contributes 0.5 documentation points.")
def _stale_profile(policy):
    c = _customer(as_of=_time(730), available_at=_time(730), onboarded_at=_time(900), history_start=_time(900))
    r = _assessment(policy, customer=c)
    return _equal(next(g for g in r["groups"] if g["id"] == "evidence")["points"], 10)


@_case("INV-outside-policy-windows", "An old retained event alters lineage without changing current policy index", "invariance", "retention",
       "A retained event can belong to lifetime features while lying outside every scored activity window and last-N set.", "Adding a 350-day-old record preserves index and changes the event digest.")
def _old_event(policy):
    old = _assessment(policy)
    new = _assessment(policy, _baseline() + [_tx(999, days=350, amount=1_000_000)])
    _equal(new["provisional_index"], old["provisional_index"])
    _check(new["lineage"]["event_digest"] != old["lineage"]["event_digest"], "old retained event vanished from lineage")
    return {"index_unchanged": True, "event_digest_changed": True}


@_case("SCORE-nonleading-proxy", "A weaker overlapping proxy does not add to the strongest signal", "policy_arithmetic", "overlap",
       "Maximum aggregation intentionally makes a non-leading evidence change have zero marginal group points.", "All-cash behavior remains 15 points when balanced directions are replaced by incoming-only flow.")
def _nonleading_proxy(policy):
    cash = [replace(t, channel="cash") for t in _baseline()]
    balanced = _assessment(policy, cash)
    incoming = _assessment(policy, [replace(t, direction="in") for t in cash])
    before = next(g for g in balanced["groups"] if g["id"] == "behavior")
    after = next(g for g in incoming["groups"] if g["id"] == "behavior")
    _equal(before["points"], 15)
    return _equal(after["points"], 15)


for label, cash_share, raw_points in (("low", .2, 0), ("mid", .5, 7.5), ("high", .8, 15)):
    def cash_edge(policy, cash_share=cash_share, raw_points=raw_points):
        events = [_tx(1, amount=100 * cash_share, channel="cash"),
                  _tx(2, amount=100 * (1 - cash_share)),
                  _tx(3, amount=100 * cash_share, channel="cash"),
                  _tx(4, amount=100 * (1 - cash_share))]
        r = _assessment(policy, events)
        row = next(x for x in r["reasons"] if x["factor"] == "cash_7d")
        return _equal(row["raw_points"], raw_points)
    _case("SCORE-cash-" + label, f"Cash-share {label} ramp arithmetic", "policy_arithmetic", "cash_exposure",
          "The cash factor linearly interpolates its declared share from 0.2 to 0.8; denominator and minimum support are explicit.",
          f"A cash amount share of {cash_share} contributes {raw_points} raw cash_7d points.")(cash_edge)


def scenario_catalog() -> list[dict]:
    """Return machine-readable specifications with one row per executed assertion case."""
    return [case.metadata() for case in _CASES]


def run_scenarios(policy: Policy) -> dict:
    """Run every case and retain failures instead of presenting a partial run as success.

    Policy-arithmetic and routing cases assert the bundled reference-policy v1 choices.
    A customized policy can intentionally fail those expectations; review its changes
    and author approved expectations rather than silently weakening the assertions.
    """
    results = []
    for case in _CASES:
        row = case.metadata()
        try:
            row["evidence"] = case.check(policy)
            row["passed"] = True
            row["error"] = None
        except Exception as exc:
            row["passed"] = False
            row["error"] = f"{type(exc).__name__}: {exc}"
            row["evidence"] = None
        results.append(row)
    failed = sum(not row["passed"] for row in results)
    return {"schema_version": "1.0.0", "policy_hash": policy.digest,
            "total": len(results), "passed": len(results) - failed, "failed": failed,
            "all_passed": failed == 0, "cases": len(results), "results": results,
            "errors": [{"id": r["id"], "error": r["error"]} for r in results if not r["passed"]],
            "categories": dict(sorted(Counter(r["category"] for r in results).items())),
            "families": dict(sorted(Counter(r["family"] for r in results).items())),
            "interpretation": "Synthetic executable specifications. Case count is not typology count, real-world effectiveness, or independent validation."}
