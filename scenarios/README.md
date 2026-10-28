# Executable scenario library

The catalog is generated from the executable registry in [`src/crw/scenarios.py`](../src/crw/scenarios.py). Every catalog row has an ID, a concrete expected behavior, a rationale, a category, a broader family, and an executable check. The scenario runner retains failures and completes the remaining cases. It does not select passing examples or stop after the first success.

```bash
python scripts/build_scenario_catalog.py --check
python -c 'import json; from crw.policy import reference_policy; from crw.scenarios import run_scenarios; print(json.dumps(run_scenarios(reference_policy()), indent=2))'
pytest tests/test_scenarios.py tests/test_synthetic.py
```

The `case_count` and category counts in [`catalog.json`](catalog.json) come from the registry. They count engineering cases. Six duration-window boundary tests are six cases testing a common window implementation, not six independent financial-crime typologies. A synthetic test pass establishes the specified behavior on that fixture; it supplies no estimate of customer-level sensitivity, specificity, predictive value, or real-world prevalence.

## What the library exercises

| Case prefix | Evidence exercised | Interpretation |
| --- | --- | --- |
| `CTX-` | Paired profile evidence, with other observations held fixed | Nondecreasing index under supplied concern; context mapping is an adapter responsibility |
| `BEN-` | Charity, cash-business, digital-business, corporate and treasury counterexamples | Category labels and aggregate proxies cannot establish misconduct |
| `AGG-` | Independently calculated numerators and denominators | Arithmetic and explicit zero/missing behavior |
| `TIME-` | Exact cutoff boundaries, late arrivals, retention and last-N selection | Point-in-time reproducibility and declared observation limits |
| `QUAL-` | Required evidence, minimum support, completeness and expectations | Unknown values remain visible and can require abstention |
| `REJECT-` | Identity, unit-domain and timestamp contract violations | Invalid inputs fail before rating |
| `INV-` | Reordering, unit rescaling, identity renaming, offsets and immutable inputs | Expected transformations preserve results or appropriately change lineage |
| `SCORE-` | Contributions, caps, interpolation and overlapping windows | Reference-policy arithmetic, not calibrated probabilities |
| `ROUTE-` | Resolved, unresolved and unknown screening observations | Review routing remains independent of numerical AML index |

## Extending the suite

1. Describe a hypothesis and a plausible benign alternative. Identify the evidence needed to distinguish them.
2. Verify that the data contract actually represents that evidence. Add an adapter and a feature contract before claiming unsupported capabilities.
3. Create a minimal synthetic fixture with independently computed expected values. Keep the normative policy choice explicit.
4. Register the case with `_case` and return observed evidence. Assertions must fail when the behavior is wrong; avoid self-referential expected values copied from the function under test.
5. Add missing, temporal and boundary variants where they resolve a distinct failure mode. Tag their shared family rather than calling every variation a new typology.
6. Regenerate the catalog and run both the scenario suite and the application tests.

`run_scenarios(policy)` accepts a policy object. The arithmetic and routing cases intentionally assert the bundled reference policy's current choices. A customized policy can therefore fail those cases even if its arithmetic is internally consistent. Review the proposed policy and revise its approved expected behavior; do not weaken the tests to make an unexplained policy change pass.

## Synthetic population API

```python
from crw.synthetic import generate_portfolio, iter_portfolio

customers, events = generate_portfolio(
    customers=100, transactions_per_customer=40, seed=42,
    as_of="2026-10-01T00:00:00Z",
)

for customer, customer_events in iter_portfolio(
    customers=100_000, transactions_per_customer=20, seed=42,
):
    # Pass one customer's records to feature construction or a batch writer.
    pass
```

The example loop describes the API; the CLI supplies runnable ingestion and assessment workflows. `iter_portfolio` holds one customer and its events at a time. `generate_portfolio` deliberately materializes the complete output and should be reserved for appropriately sized demos. `missing_rate` is an optional number from zero to one that independently masks supplied profile values and transaction-jurisdiction evidence. It does not replace an unknown value with zero.

Reproduction requires the seed, arguments, code revision and runtime versions. Customer-specific streams preserve existing portfolio prefixes when the requested customer count increases. Changing the generator implementation can change its outputs even when the seed stays the same. The synthetic expected-volume field is deliberately engineered from the generated activity to exercise a range of ratios; it must not be treated as an independently observed business expectation in an effectiveness study.
