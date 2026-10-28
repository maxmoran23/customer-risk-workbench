# Local operation, reproduction and extension

## Execution contract

The core is a local Python package and SQLite adapter. It starts no scheduler, network service, collector, AI API, or telemetry process. The optional HTML file is a read-only synthetic review artifact. The optional HTTP command below serves only the specified directory on loopback.

```bash
python -m pip install '.[dev,research]'
python -m pytest
python -m crw catalog --out runs/catalog
python -m crw demo --research --out runs/reference-demo
python -m http.server 3046 --bind 127.0.0.1 --directory runs/reference-demo
```

Alternatively open the HTML directly. Python 3.12 and `uv.lock` define the pinned reference environment. Core requires Python 3.11+; live verification and CI platform results are recorded separately in the evidence dossier. On Windows use the Python executable belonging to the intended virtual environment; the commands above do not require a shell activation script. Peak-memory measurement is null on platforms without the standard-library `resource` module.

## Ingestion and identity

`generate` writes JSONL and a source-file hash manifest. `ingest` reads customers before transactions in one transaction. Customer identity and effective timestamp identify a snapshot; transaction ID identifies an event. Repeated identical content is idempotent. Conflicting content with an existing ID fails and rolls back the whole ingestion. A later legitimate profile change needs a new effective timestamp. Onboarding time is immutable for a customer in this reference adapter.

`--base-unit` is explicit on ingest and score. All amounts and expected volumes must already share that unit. The stored unit cannot be changed by reopening with a different argument. Unit declarations remain in exported assessment lineage. The adapter cannot detect mislabeled source units; upstream reconciliation must establish the assertion.

For transaction CSV, pass `--csv`; headers must match the complete Transaction contract. Blank jurisdiction exposure becomes null. Negative amounts and reversals are rejected; an adopting adapter must define economic-event normalization rather than coerce them.

## Assessment consistency

A batch selects customer snapshots effective and available at the requested cutoff. Future-only profiles do not enter the historical population. An empty eligible population is an explicit failed run, not a silent zero-result success.

The batch holds one SQLite transaction across its full assessment population. Chunking bounds retrieval memory; it does not commit a sequence of moving input snapshots. Standalone `Store.assess` opens a read transaction when it does not already participate in one. Concurrent source updates therefore cannot mix an old profile with new events in one assessment.

Only complete runs can be exported. An exception rolls back assessment writes for the batch and records a failed run. Interrupted processes can leave a `running` record; the software does not falsely promote that state to complete. An operator should preserve evidence, investigate, and rerun as a new run. Automatic crash recovery, stale-run repair, distributed scheduling and resumable multiwriter execution are not implemented.

SQLite is a local reference adapter. Long scoring runs hold a writer reservation. Production architectures may need immutable extract snapshots, partitioning, a warehouse or a governed job service; those are separate implementations whose equivalence must be tested. Benchmark results do not prove those designs.

## Monitoring and sampling APIs

```python
import json
from crw.monitoring import monitor_portfolios, review_sample
from crw.io import atomic_json

with open("runs/assessments.jsonl", encoding="utf-8") as stream:
    assessments = [json.loads(line) for line in stream if line.strip()]
atomic_json("runs/review-sample.json", review_sample(assessments, per_band=20, seed=7))
atomic_json("runs/replay-monitor.json", monitor_portfolios(assessments, assessments))
```

Monitoring validates content hashes, rejects duplicate customer IDs and inconsistent within-population cutoffs/policies/units, and rejects incompatible units between populations. It reports entrants/exits alongside matched-customer migration. Abstention is not an ordinal band above HIGH. PSI and effect diagnostics have explicit support and missingness; default investigation settings are examples, not statistical or regulatory standards.

Sampling retains stratum populations, selection probabilities and design weights. The supplied per-band allocation is a review design; an unweighted pooled error rate from disproportionate sampling is not a population estimate. See [statistical methods](statistical-methods.md) and [sampling plan](../templates/sampling-plan.md).

## Decision history

`workflow.ReviewDecision` records retain, escalate-review, or return-for-evidence actions. It requires separate requester/reviewer strings, substantive rationale, evidence references, and a bounded validity period. `DecisionLog` appends to SQLite and verifies a local hash chain. These checks do not authenticate people, establish approval authority, or prevent a privileged database owner from rewriting storage. No action changes the original risk calculation or executes a screening disposition.

## Build and transfer

```bash
python -m build
python scripts/build_review_pack.py --out review-pack
python scripts/public_boundary_check.py
```

The wheel includes the core and the embedded HTML renderer; the full repository/release archive includes catalogs, documentation, templates, tests and prebuilt evidence. The eight review packs aggregate complete methods for approved manual review; they are not a replacement for executable verification. Follow the adopter's repository access, dependency approval and data-handling processes.

## Failure investigation

| Symptom | Inspect | Preserve |
| --- | --- | --- |
| Contract rejection | File/line diagnostic, field type, timezone, source mapping | Rejected source reference; do not repair by guessing |
| ID collision | Same ID with different content, adapter version, source correction | Both source records and reconciliation decision |
| Historical replay difference | Cutoff, availability, source/unit/policy hashes, code version | Both complete artifacts and crossed comparison |
| Review queue growth | Factor coverage, retention, entrants, source delivery, bands | Missingness and bounded scores alongside workload |
| Research metric undefined | Class support, maturity, censoring, segment gates | Null reason and denominators |
| Frozen stress failure | Fixed model/threshold hashes, paired inputs, changed probabilities | Original failing result; do not retune on holdout |

For release, rebuild evidence after code changes, rerun targeted regressions and then the full checks, install the wheel into a fresh environment, and verify the same demo there. See [verification](verification.md).
