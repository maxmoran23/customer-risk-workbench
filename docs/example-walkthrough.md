# A compact, reproducible walkthrough

The [`examples/`](../examples/) package contains three invented customers and 240 invented transactions. It exercises the actual parsing, feature, scoring, hypothesis and monitoring APIs without a database file or additional dependencies. The expected scores are hand-reconciled below; the executable checks also verify fixture hashes and reconstruct every input record.

## Run it

From the repository root, with the project installed in the active Python environment:

```bash
python examples/walkthrough.py
```

To retain the full evidence, including active hypotheses, assessment hashes, missing-evidence bounds and monitoring diagnostics:

```bash
python examples/walkthrough.py --out runs/example-walkthrough.json
```

A checkout that has not been installed can use the source package directly:

```bash
PYTHONPATH=src python examples/walkthrough.py
```

The walkthrough always verifies its expectations. It raises an exception and exits unsuccessfully if the fixture, active policy, expected arithmetic, screening route, input-order replay or missing-evidence behavior differs. It does not silently refresh expected values from observed engine output.

## Files and intended use

| File | Role |
| --- | --- |
| [`customers.jsonl`](../examples/customers.jsonl) | Three strict normalized customer records with complete declared retained history |
| [`transactions.jsonl`](../examples/transactions.jsonl) | Eighty transactions per customer; 240 rows total |
| [`fixture-manifest.json`](../examples/fixture-manifest.json) | Explicit synthetic unit, assessment cutoff, counts, policy hash and input-file hashes |
| [`expected-summary.json`](../examples/expected-summary.json) | Independently specified score/group expectations and required review outcomes |
| [`build_fixtures.py`](../examples/build_fixtures.py) | Deterministic constructor that can reproduce the JSONL inputs without randomness |
| [`walkthrough.py`](../examples/walkthrough.py) | Runnable verification and explanation using public workbench APIs |

All amounts use `SYNTHETIC_UNIT`; these are invented amounts, not dollars or other currencies. The assessment cutoff is `2026-10-01T00:00:00Z`. The manifest's unit is passed explicitly to feature construction and recorded in assessment lineage. There are no real countries, individuals, companies, screening records or outcome labels in these fixtures.

## What the three examples represent

| Example | Complete index | Stored band | Separate screening route | Purpose |
| --- | --- | --- | --- | --- |
| `example-customer-01` | 15.75 | LOW | FALSE | Low supplied profile concerns with balanced transaction totals |
| `example-customer-02` | 48.40 | MODERATE | FALSE | Increased contextual concerns and activity above its supplied expectation |
| `example-customer-03` | 82.80 | HIGH | TRUE | Several elevated supplied concerns, a fivefold expectation ratio and unresolved screening |

The segment names are descriptive fixture fields. They do not set the scores. The reference policy uses the declared normalized evidence and supported transaction aggregates.

Each customer has sixty recent transactions of 100 units and twenty preceding-month transactions of 300 units. Thus, current-month volume is 6,000 units and preceding-month volume is also 6,000 units. The growth ratio is exactly 1. Incoming and outgoing amounts balance, producing an aggregate balance proxy of 1. This does not establish that any incoming funds financed an outgoing transaction.

The supplied monthly expectations are 6,000, 2,000 and 1,200 units. The expectation ratios are therefore 1, 3 and 5. These expectations are constructed fixture inputs; they are not independently observed business information.

## Reconcile the group arithmetic

| Group | Example 01 | Example 02 | Example 03 |
| --- | ---: | ---: | ---: |
| Customer | 1.25 | 14.50 | 22.00 |
| Geography | 0.75 | 10.50 | 12.00 |
| Product/channel | 0.75 | 6.80 | 12.80 |
| Behavior | 12.00 | 12.00 | 25.00 |
| Context | 0.50 | 2.60 | 6.00 |
| Evidence | 0.50 | 2.00 | 5.00 |
| **Total** | **15.75** | **48.40** | **82.80** |

For example 01, the customer group is `10×0.05 + 5×0.05 + 10×0.05 = 1.25`. Profile geography and observed geography both contribute 0.75, but the geography group takes their maximum rather than their sum. Product and channel contribute `8×0.05 + 7×0.05 = 0.75`. Context contributes `8×0.05 + 2×0.05 = 0.50`. Documentation contributes `10×0.05 = 0.50`; the one-day profile age adds no points.

The balanced-flow proxy supplies 12 behavior points to the first two examples. For example 02, the volume factor's raw contribution is `25×(3−1.5)/(5−1.5) = 10.7142857`; maximum aggregation therefore retains 12. For example 03, ratio 5 supplies 25 points, the behavior-group cap. Overlapping time and event-count windows do not each add another copy of their contributions.

These are policy-arithmetic expectations. They do not imply criminality probabilities, empirical calibration or a recommended institutional risk appetite.

## Follow the executable steps

1. **Verify provenance and parse.** The walkthrough checks input-file SHA-256 values, parses every JSONL row through `Customer.from_dict` or `Transaction.from_dict`, and compares the parsed records with the independent fixture constructor.
2. **Build available-at-cutoff features.** Each customer receives only its own records. `build_features(..., base_unit=manifest["base_unit"])` preserves time, support, retention and unit information.
3. **Score and reconcile.** `score(...)` runs the reference policy. The walkthrough compares every group contribution, complete score, band and screening route with the committed expectations.
4. **Verify replay.** Reversing the input transaction order must reproduce the same assessment hash.
5. **Inspect hypotheses.** `evaluate_patterns(...)` returns contextual review questions. The evidence output retains TRUE hypotheses with their lawful alternatives and next-evidence requirements.
6. **Remove mandatory evidence in a copy.** `dataclasses.replace(...)` creates an altered profile with unknown ownership opacity. The original customer and checked-in records remain unchanged.
7. **Monitor the change with its actual sample size.** `monitor_portfolios(...)` compares the three baseline assessments with the altered portfolio while retaining its illustrative minimum population of 50. It reports insufficient population support instead of treating three examples as adequate monitoring evidence.

## The missing-evidence result is deliberately instructive

| Measure | Complete example 01 | Ownership evidence removed |
| --- | ---: | ---: |
| Final score | 15.75 | `null` |
| Lower bound | 15.75 | 15.25 |
| Upper bound | 15.75 | 25.25 |
| Band | LOW | REVIEW_REQUIRED |
| Mandatory gate | None | `required_evidence_missing` |

Removing the known ownership contribution subtracts 0.50 from the provisional lower bound. The upper bound permits the full 10 ownership points, producing `[15.25,25.25]`. Although that interval remains within the reference LOW band, the mandatory-evidence gate still requires review. The lower-bound decrease is not evidence that the customer's risk declined.

The script preserves both complete-score availability and the interval in its output. It labels the comparison's numerical delta as provisional and reports that the policy stayed fixed while data changed.

## Expected console result

The console summary includes these values:

```text
status: verified
customers: 3
transactions: 240
complete scores: 15.75, 48.40, 82.80
stored bands: LOW, MODERATE, HIGH
missing ownership: score=null; REVIEW_REQUIRED; bounds=[15.25,25.25]
monitoring signal: insufficient_population_support
```

The actual output is valid JSON. The optional evidence file adds full explanatory details. Fixture hashes and the active policy hash are retained so the same result can be tied to the inputs used.

To reproduce the fixture files themselves:

```bash
python examples/build_fixtures.py
python examples/walkthrough.py
```

The constructor rebuilds only the two JSONL files and their manifest. It does not rewrite the hand-specified expected scores. If the active reference policy changes, review its intended effect and update the example's expectations through normal code review; do not treat an unexplained difference as a successful reproduction.

Three engineered examples cannot establish sampling adequacy, detection performance, fairness or portfolio calibration. They make the software's behavior inspectable before a reviewer invests in the larger synthetic run or an independently governed evaluation.
