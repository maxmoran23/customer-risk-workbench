# Contributing

Changes must improve an observable capability, test, or documented limitation. More files and generated cases alone are not evidence of improved model quality.

1. Use Python 3.12 for the pinned research environment. Install `python -m pip install '.[dev,research]'` or `uv sync --all-extras`.
2. Run `python -m pytest` and `python -m ruff check src tests scripts`.
3. Add a targeted independent expected value, boundary case, or counterexample for changed behavior. Avoid tests that simply call the same helper on both sides.
4. Run `python -m crw scenarios --out runs/scenarios.json` and a clean-directory demo. For statistical changes, preserve temporal/customer isolation and rerun all seeds, all regimes, and frozen-model stresses.
5. Record why any policy weight, threshold, feature, or source interpretation changed. Reconcile affected catalogs, documentation and evidence.
6. Keep the public-only boundary: synthetic fixtures and public references. Exclude institution names, real customer identifiers, private workflows, internal policy and credentials.

Source changes need a new release evidence manifest. Do not hand-edit a generated metric to make a gate pass. Developer checks are not institutional independent validation or approval.

The test suite runs from the source tree. A release additionally installs the built wheel into a separate environment and runs a demo there, which checks packaging independently of editable imports.
