"""Local command line: generate, ingest, score, test scenarios, research and inspect."""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import platform
from pathlib import Path
import sqlite3
import sys
import time

from . import __version__
from .contracts import ContractError, Customer, Transaction
from .features import build_features, digest, feature_catalog
from .io import atomic_json, csv_transactions, json_schema, read_jsonl, write_jsonl
from .patterns import reference_patterns, evaluate_patterns
from .policy import PROFILE_KEYS, Policy, reference_policy
from .scoring import score
from .storage import Store
from .stress import stress_portfolio
from .synthetic import generate_portfolio, iter_portfolio, DEFAULT_AS_OF
from .scenarios import run_scenarios, scenario_catalog
from .cli_programs import register as register_programs


def _policy(args):
    return Policy.load(args.policy) if getattr(args, "policy", None) else reference_policy()


def _print(value):
    print(json.dumps(value, indent=2, allow_nan=False, sort_keys=True))


def generate(args):
    out = Path(args.out)
    # Two deterministic traversals keep memory bounded without holding the ledger.
    kwargs = dict(
        customers=args.customers,
        transactions_per_customer=args.transactions,
        seed=args.seed,
        as_of=args.as_of,
    )
    nc = write_jsonl(out / "customers.jsonl", (c for c, _ in iter_portfolio(**kwargs)))
    nt = write_jsonl(
        out / "transactions.jsonl", (t for _, events in iter_portfolio(**kwargs) for t in events)
    )
    manifest = {
        "data_status": "synthetic",
        "generator_version": "1",
        "base_unit": "SYNTHETIC_UNIT",
        **kwargs,
        "customers_written": nc,
        "transactions_written": nt,
        "files": {name: file_hash(out / name) for name in ("customers.jsonl", "transactions.jsonl")},
    }
    atomic_json(out / "manifest.json", manifest)
    return manifest


def file_hash(path):
    h = hashlib.sha256()
    with open(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def ingest(args):
    events = csv_transactions(args.transactions) if args.csv else read_jsonl(args.transactions, Transaction)
    with Store(args.db, args.base_unit) as store:
        return store.ingest(read_jsonl(args.customers, Customer), events)


def batch_score(args):
    with Store(args.db, args.base_unit) as store:
        run = store.score_batch(args.as_of, _policy(args), args.chunk_size)
        written = write_jsonl(args.out, store.results(run["run_id"]))
        return {**run, "exported": written, "output": str(args.out)}


def benchmark(args):
    policy = _policy(args)
    counts = Counter()
    checksum = hashlib.sha256()
    started = time.perf_counter()
    n = 0
    for customer, events in iter_portfolio(args.customers, args.transactions, args.seed, args.as_of):
        result = score(build_features(customer, events, args.as_of), policy, customer.customer_id, args.as_of)
        counts[result["band"]] += 1
        checksum.update(result["assessment_hash"].encode())
        n += 1
    seconds = time.perf_counter() - started
    try:
        import resource

        usage = resource.getrusage(resource.RUSAGE_SELF)
        peak_bytes = usage.ru_maxrss if sys.platform == "darwin" else usage.ru_maxrss * 1024
    except ImportError:
        peak_bytes = None
    report = {
        "scope": "streamed synthetic generation + temporal features + policy scoring; excludes database, report rendering and supervised learning",
        "customers": n,
        "transactions": n * args.transactions,
        "elapsed_seconds": seconds,
        "customers_per_second": n / seconds,
        "process_peak_rss_bytes": peak_bytes,
        "memory_limit": "Process high-water mark includes interpreter and imported modules; not isolated incremental allocation.",
        "python": platform.python_version(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "seed": args.seed,
        "as_of": args.as_of,
        "policy_hash": policy.digest,
        "assessment_stream_sha256": checksum.hexdigest(),
        "bands": dict(counts),
        "limits": "Single process, local hardware, synthetic input. No distributed throughput, concurrency, SLA or production capacity claim.",
    }
    atomic_json(args.out, report)
    return report


def demo(args):
    policy = _policy(args)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    customers, transactions = generate_portfolio(args.customers, args.transactions, args.seed, args.as_of)
    by_customer = {c.customer_id: [] for c in customers}
    for event in transactions:
        by_customer[event.customer_id].append(event)
    write_jsonl(out / "customers.jsonl", customers)
    write_jsonl(out / "transactions.jsonl", transactions)
    with Store(out / "portfolio.sqlite") as store:
        ingestion = store.ingest(customers, transactions)
        run = store.score_batch(args.as_of, policy)
        assessments = list(store.results(run["run_id"]))
        write_jsonl(out / "assessments.jsonl", assessments)
        replay = store.score_batch(args.as_of, policy, chunk_size=73)
        replay_results = list(store.results(replay["run_id"]))
        if assessments != replay_results:
            raise RuntimeError("chunk-size replay invariant failed")
        counts = store.counts()
    scenario_results = run_scenarios(policy)
    if scenario_results["failed"]:
        raise RuntimeError("scenario failures prevent demo release")
    # A deterministic spread across sorted scores provides readable review examples.
    ordered = sorted(assessments, key=lambda r: (r["provisional_index"], r["customer_id"]))
    indices = sorted(
        {
            round(i * (len(ordered) - 1) / max(1, min(60, len(ordered)) - 1))
            for i in range(min(60, len(ordered)))
        }
    )
    selected = [ordered[i] for i in indices]
    profiles = {c.customer_id: c for c in customers}
    cases = []
    feature_rows = []
    for result in selected:
        cid = result["customer_id"]
        f = build_features(profiles[cid], by_customer[cid], args.as_of)
        feature_rows.append((cid, f))
        cases.append(
            {
                "customer": profiles[cid].to_dict(),
                "assessment": result,
                "features": f.to_dict(),
                "patterns": evaluate_patterns(f),
            }
        )
    summary = {
        "bands": dict(Counter(r["band"] for r in assessments)),
        "mean_index": sum(r["provisional_index"] for r in assessments) / len(assessments),
        "mean_coverage": sum(r["coverage"] for r in assessments) / len(assessments),
        "incomplete_scores": sum(r["score"] is None for r in assessments),
        "screening_reviews": sum(
            any(flag["state"] == "TRUE" for flag in r["review_flags"]) for r in assessments
        ),
        "selected_customer_examples": len(cases),
    }
    report = {
        "meta": {
            "version": __version__,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "as_of": args.as_of,
            "seed": args.seed,
            "data_status": "SYNTHETIC REFERENCE DEMONSTRATION",
            "customers": len(customers),
            "transactions": len(transactions),
            "unit": "SYNTHETIC_UNIT",
            "policy_hash": policy.digest,
            "result_digest": digest(assessments),
        },
        "summary": summary,
        "policy": policy.to_dict(),
        "catalog": feature_catalog(PROFILE_KEYS),
        "scenarios": scenario_results,
        "scenario_catalog": scenario_catalog(),
        "patterns_catalog": reference_patterns(),
        "customers": cases,
        "stress": stress_portfolio(feature_rows, policy, args.as_of),
        "operational": {
            "ingest": ingestion,
            "counts": counts,
            "chunk_replay_identical": True,
            "end_to_end_seconds": time.perf_counter() - started,
            "measurement_scope": "generate, write fixtures, SQLite ingest, two score/export passes, scenario and selected-example assembly; excludes research and HTML rendering",
        },
        "research": None,
        "limits": [
            "Illustrative policy has not been calibrated on an operational population.",
            "Synthetic scenario coverage does not estimate detection effectiveness.",
            "No real customer data, employer processes or private regulatory interpretations are included.",
            "Independent institutional validation and approved-environment integration remain necessary.",
        ],
    }
    if args.research:
        from .learning import run_research_experiment

        report["research"] = run_research_experiment(n=args.research_rows, seeds=(7, 19, 41))
        atomic_json(out / "research.json", report["research"])
    atomic_json(out / "demo-report.json", report)
    atomic_json(out / "scenario-results.json", scenario_results)
    atomic_json(out / "stress-results.json", report["stress"])
    from .render import render_workbench

    render_workbench(report, out / "workbench.html")
    return {
        "output": str(out.resolve()),
        "summary": summary,
        "scenarios": {k: scenario_results[k] for k in ("total", "passed", "failed")},
        "replay_identical": True,
        "research_included": bool(report["research"]),
        "elapsed_seconds": time.perf_counter() - started,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="crw", description="Customer Risk Workbench: public reference tools and synthetic evidence."
    )
    parser.add_argument("--version", action="version", version=__version__)
    subs = parser.add_subparsers(dest="command", required=True)
    p = subs.add_parser("generate", help="Write seeded synthetic JSONL inputs")
    p.set_defaults(func=generate)
    p = subs.add_parser("demo", help="Rebuild SQLite replay, scenario evidence and offline workbench")
    p.set_defaults(func=demo)
    p.add_argument("--research", action="store_true")
    p.add_argument("--research-rows", type=int, default=3000)
    p.add_argument("--policy")
    p = subs.add_parser("benchmark", help="Measure streamed generation, features and scoring")
    p.set_defaults(func=benchmark)
    p.add_argument("--policy")
    for name in ("generate", "demo", "benchmark"):
        p = subs.choices[name]
        p.add_argument("--customers", type=int, default=1000 if name != "benchmark" else 10000)
        p.add_argument("--transactions", type=int, default=80 if name != "benchmark" else 10)
        p.add_argument("--seed", type=int, default=42)
        p.add_argument("--as-of", default=DEFAULT_AS_OF)
        p.add_argument("--out", default="runs/benchmark.json" if name == "benchmark" else "runs/" + name)
    p = subs.add_parser("ingest", help="Atomic ingestion of normalized JSONL or transaction CSV")
    p.add_argument("--db", required=True)
    p.add_argument("--customers", required=True)
    p.add_argument("--transactions", required=True)
    p.add_argument("--csv", action="store_true")
    p.add_argument("--base-unit", default="SYNTHETIC_UNIT")
    p.set_defaults(func=ingest)
    p = subs.add_parser("score", help="Score an as-of portfolio and export complete run")
    p.add_argument("--db", required=True)
    p.add_argument("--as-of", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--policy")
    p.add_argument("--base-unit", default="SYNTHETIC_UNIT")
    p.add_argument("--chunk-size", type=int, default=500)
    p.set_defaults(func=batch_score)
    p = subs.add_parser("scenarios", help="Execute the expected-behavior case library")
    p.add_argument("--policy")
    p.add_argument("--out", default="runs/scenarios.json")
    p.set_defaults(func=lambda a: _save_scenarios(a))
    p = subs.add_parser("research", help="Run isolated supervised-learning experiments on synthetic outcomes")
    p.add_argument("--rows", type=int, default=3000)
    p.add_argument("--seeds", nargs="+", type=int, default=[7, 19, 41])
    p.add_argument("--out", default="runs/research.json")
    p.set_defaults(func=_research)
    p = subs.add_parser("catalog", help="Export reference policy, JSON Schemas, feature and pattern catalogs")
    p.add_argument("--out", default="runs/catalog")
    p.set_defaults(func=_catalog)
    register_programs(subs)
    args = parser.parse_args(argv)
    try:
        if hasattr(args, "customers") and isinstance(args.customers, int) and args.customers < 1:
            raise ContractError("customers must be positive")
        result = args.func(args)
        _print(result)
        return 0
    except (ValueError, OSError, ImportError, sqlite3.Error) as exc:
        parser.exit(2, f"crw: {exc}\n")
    except (TypeError, KeyError, AttributeError) as exc:
        parser.exit(2, f"crw: malformed input ({type(exc).__name__}: {exc}); check the file against the documented contract\n")


def _save_scenarios(args):
    result = run_scenarios(_policy(args))
    atomic_json(args.out, result)
    if result["failed"]:
        raise ContractError(f"{result['failed']} scenario assertions failed; inspect {args.out}")
    return {k: result[k] for k in ("total", "passed", "failed")}


def _research(args):
    from .learning import run_research_experiment

    result = run_research_experiment(n=args.rows, seeds=tuple(args.seeds))
    atomic_json(args.out, result)
    return {"out": args.out, "summary": result["summary"]}


def _catalog(args):
    out = Path(args.out)
    atomic_json(out / "reference-policy.json", reference_policy().to_dict())
    atomic_json(out / "features.json", feature_catalog(PROFILE_KEYS))
    atomic_json(out / "patterns.json", reference_patterns())
    atomic_json(out / "customer.schema.json", json_schema(Customer))
    atomic_json(out / "transaction.schema.json", json_schema(Transaction))
    return {
        "output": str(out),
        "features": len(feature_catalog(PROFILE_KEYS)),
        "patterns": len(reference_patterns()),
    }
