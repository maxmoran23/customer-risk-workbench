# Verification dossier — research release 0.1.0

**Observed on October 28, 2026.** This dossier reports reproducible software behavior on synthetic fixtures. It is not institutional independent model validation, certification, or evidence of effectiveness on real financial-crime outcomes. Machine-readable counts, versions and scope are retained in [verification.json](../evidence/verification.json); file hashes are in the [release manifest](../evidence/source-manifest.json).

## Executed evidence

| Check | Observed result | Scope and reproducible source |
| --- | --- | --- |
| Automated suite | 230 passed; zero failures, errors or skips | Python contracts, arithmetic, temporal behavior, research, real SQLite, review history, renderer escaping and JavaScript helper checks; `python -m pytest` |
| Statement coverage | 2,022 / 2,265 statements, 89.3% | Python statement coverage only; excludes manual demonstration execution; rendering a template is not complete browser coverage |
| Named executable cases | 96 / 96 passed | [Expected/observed case results](../evidence/scenario-results.json); this is partly overlapping evidence with parameterized tests, not 326 independent validations |
| Demonstration | 1,000 customers; 80,000 transactions; two chunk sizes give identical assessments | Real SQLite; [retained summary](../evidence/demo-summary.json) and [standalone viewer](../web/workbench.html) |
| Numerical cross-check | 785 finite comparisons over 100 seeded cases; 15 explicit undefined checks | scikit-learn/SciPy reference results; maximum absolute discrepancy `1.454392162258955e-14`, below `1e-12`; [evidence](../evidence/numerical-crosscheck.json) |
| Research | 12 refitted experiments, each using 3,000 synthetic customers; three seeds | Four regimes per seed; 36 paired fixed-model stress comparisons across nine model/seed combinations; [full results](../evidence/research.json) |
| Installed package | Fresh wheel installation, no optional dependencies, outside source checkout | 12 customers / 960 transactions; 96 cases; identical chunk replay; HTML written; [wheel evidence](../evidence/wheel-check.json) |
| Portable walkthrough | Three customers / 240 transactions; expected scores 15.75, 48.40 and 82.80 | Hand-reconciled group contributions, missing-evidence abstention and replay; [worked example](example-walkthrough.md) |
| Desktop interface | Selected Safari interactions observed | Overview, customer search/selection, stress null-score/bounds details, threshold control and research/frozen-model views; not exhaustive accessibility or browser coverage |

The numerical comparison includes tied and constant probabilities, imbalanced and single-class labels, shifted distributions, and Wilson interval endpoints. It verifies finite-sample arithmetic, not empirical interval coverage or the appropriateness of a metric for a business decision. Source and script hashes are retained with the numerical evidence.

The reference environment is Python 3.12.14 on macOS arm64, with NumPy 2.5.4, SciPy 1.18.1 and scikit-learn 1.9.1. `uv.lock` records resolved dependencies. The core declares Python 3.11 or later; the retained reference evidence uses 3.12. Continuous integration is configured for Ubuntu and Windows with Python 3.12. **A configured workflow is not evidence of a successful run**; current external outcomes are visible in [Actions](https://github.com/maxmoran23/customer-risk-workbench/actions).

## Scale measurements

| Workload | Population | Observed wall time | Included / excluded |
| --- | --- | --- | --- |
| Streaming feature and policy pipeline | 100,000 customers / 1,000,000 events | 51.61 seconds; 1,937.7 customers/second | Includes synthetic generation, temporal features and scoring; excludes database, HTML and supervised learning |
| Real SQLite pipeline | 10,000 customers / 1,000,000 events | 63.21 seconds total | Generation/ingest 39.09 seconds; indexed scoring 23.58 seconds; complete-result iteration 0.54 seconds |
| Reference demonstration operations | 1,000 customers / 80,000 events | 6.02 seconds | Fixture writing, ingest, two score/export passes, cases and selected-example assembly; excludes research and rendering |

[Streaming measurement](../evidence/benchmark-100k.json) · [SQLite measurement](../evidence/benchmark-sqlite.json)

These are single observations on a development machine with concurrent activity. They do not establish a throughput distribution, latency percentile, service level, distributed scaling, multiwriter capacity, recovery objective or production sizing. Streaming process peak RSS was 24,526,848 bytes; this includes the interpreter/imports and is not incremental memory or SQLite memory. The SQLite file measured 745,103,360 bytes and was removed after its temporary benchmark.

The streaming benchmark deliberately uses only ten events per customer: 55,579 of 100,000 assessments require review (55.6%). This exposes insufficient support under the configured policy. In the denser demonstration, 60 of 1,000 require review, while 92 have no complete point score. These differ because an incomplete score can retain a stable band when required evidence is present and its bounds remain within that band. No comparison between these synthetic populations is an efficacy claim.

## Retained stress failure

In the base seed-7 logistic model, 132 of 630 synthetic holdout observations exceed the frozen calibration-selected threshold. Masking the two behavior features reduces that count to **zero**, while model parameters, preprocessing and threshold remain unchanged. The reported mean absolute probability movement is approximately 0.1308. This is a retained model vulnerability under the specified perturbation, not a successful robustness result.

The experiment is useful because it separates a changed input from a retrained model. Whether this failure represents a real operational concern depends on source coverage, model use, outcomes, controls and approved-environment evaluation. [Exact paired outputs and integrity hashes](../evidence/research.json).

## Review findings closed before release

AI-assisted adversarial and compliance reviews produced concrete fixes:

1. **Historical population:** a future-only or not-yet-available customer could previously contaminate a historical batch. Eligibility now requires an effective, available snapshot; a real-database replay regression preserves the original result.
2. **Concurrent evidence reads:** standalone assessments now own a read snapshot unless a caller already owns the transaction. A two-connection WAL test commits a profile and transaction between reads; the in-flight assessment remains identical to the prior snapshot and the next sees both updates.
3. **Amount-unit lineage:** actual declared units now enter feature lineage and assessment hashes. Monitoring, attribution and portfolio stress reject inconsistent units.
4. **Duplicate stress identities:** duplicate customer IDs could overwrite paired baselines. The stress entry point now rejects them before calculation; the original screening-only false-change reproduction is a regression test.
5. **Missing-evidence interpretation:** stress output now labels lower-bound movement, retains before/after scores, bounds and gates, and computes complete-score changes only for complete pairs with their denominator.

These are bounded implementation reviews by AI agents, supported by execution evidence. They are not independent institutional validation, legal advice, regulator endorsement, external penetration testing or third-party assurance.

## Reproduce and challenge

From the repository, after installing `.[dev,research]`:

```bash
python -m pytest --cov=crw --cov-report=json:runs/coverage.json --junitxml=runs/pytest.xml
python scripts/build_scenario_catalog.py --check
python scripts/check_numerics.py
python examples/walkthrough.py --out runs/example-walkthrough.json
python -m crw demo --customers 1000 --transactions 80 --research --out runs/fresh-demo
python -m crw benchmark --customers 100000 --transactions 10 --out runs/benchmark-100k.json
python scripts/benchmark_storage.py --out runs/benchmark-sqlite.json
python -m build
python scripts/check_wheel.py --out runs/wheel-check.json
python scripts/public_boundary_check.py
python scripts/source_manifest.py --check
```

Use a fresh demonstration directory. Wall time and generated timestamps vary; deterministic assessment content should reproduce with unchanged inputs/configuration/runtime assumptions. Library upgrades can change numerical training results. The source-manifest check verifies the bundled release files; it intentionally fails after those public files are changed until a new manifest is generated and reviewed.

For technical challenge, begin with the [three-customer walkthrough](example-walkthrough.md), then inspect missing-evidence propagation, availability-time leakage tests, concurrency regressions, numerical cross-checks, held-out research and fixed-model failures. Remaining adoption work is itemized in [limitations](limitations.md), [operations](operations.md) and the [adoption guide](adoption-guide.md).
