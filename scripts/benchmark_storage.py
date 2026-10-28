"""Measure the real SQLite workflow on temporary synthetic data."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
from pathlib import Path
import platform
import tempfile
import time

from crw.io import atomic_json
from crw.policy import reference_policy
from crw.storage import Store
from crw.synthetic import iter_portfolio, DEFAULT_AS_OF


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--customers", type=int, default=10000)
    parser.add_argument("--transactions", type=int, default=100)
    parser.add_argument("--out", default="evidence/benchmark-sqlite.json")
    args = parser.parse_args()
    if args.customers < 1 or args.transactions < 1:
        parser.error("positive counts required")
    policy = reference_policy()
    kwargs = dict(
        customers=args.customers, transactions_per_customer=args.transactions, seed=42, as_of=DEFAULT_AS_OF
    )
    with tempfile.TemporaryDirectory(prefix="crw-synthetic-benchmark-") as temporary:
        path = Path(temporary) / "portfolio.sqlite"
        with Store(path) as store:
            start = time.perf_counter()
            ingestion = store.ingest(
                (c for c, _ in iter_portfolio(**kwargs)),
                (t for _, events in iter_portfolio(**kwargs) for t in events),
            )
            ingested = time.perf_counter()
            run = store.score_batch(DEFAULT_AS_OF, policy, chunk_size=333)
            scored = time.perf_counter()
            bands = Counter()
            digest = hashlib.sha256()
            for record in store.results(run["run_id"]):
                bands[record["band"]] += 1
                digest.update(record["assessment_hash"].encode())
            exported = time.perf_counter()
            report = {
                "scope": "synthetic generation and real SQLite ingest, indexed feature extraction, atomic batch scoring, complete-run iteration",
                "customers": args.customers,
                "transactions": args.customers * args.transactions,
                "ingestion": ingestion,
                "ingest_seconds": ingested - start,
                "scoring_seconds": scored - ingested,
                "iteration_seconds": exported - scored,
                "total_seconds": exported - start,
                "database_bytes": path.stat().st_size,
                "database_counts": store.counts(),
                "bands": dict(bands),
                "result_digest": digest.hexdigest(),
                "policy_hash": policy.digest,
                "seed": 42,
                "as_of": DEFAULT_AS_OF,
                "python": platform.python_version(),
                "platform": platform.platform(),
                "status": run["status"],
                "chunk_size": 333,
                "limit": "One local process and one SQLite writer. No multiwriter, distributed, recovery-time or production-SLA claim. Temporary synthetic database removed after measurement.",
            }
        atomic_json(args.out, report)
    print(
        f"Measured {report['customers']} customers / {report['transactions']} transactions in {report['total_seconds']:.3f}s; {args.out}"
    )


if __name__ == "__main__":
    main()
