# Development rules

This repository is a public, generic reference implementation using synthetic examples and public sources only.
Never add employer names, internal processes, customer data, work credentials, private identifiers, or real screening lists.
All weights, thresholds, generators, and policy examples are illustrative unless explicitly sourced otherwise.
Do not describe synthetic performance as real-world effectiveness, certification, regulatory approval, or production readiness.
Preserve separate risk index, data completeness, screening workflow, and probability concepts.
Use UTC-aware event and availability timestamps. Fail invalid input; abstain when required evidence is unavailable.
Tests must use real SQLite databases and independently derived expected values where possible.
Do not add network calls, AI API dependencies, telemetry, scheduling, automatic decisions, or deployments.
Run pytest and the reproducible demo before release. Keep source counts and evidence claims generated, not hand-maintained.
No emojis in repository content. No placeholder implementations or fabricated validation sign-offs.

Program kits (attributes, connections, rules, program, impact, impact_sql, impact_report, narrative):
Keep class, score, weight, tier and rule values illustrative and evidence entries public. Policy decisions belong to adopters.
Never let generated text carry a figure the deterministic code did not compute; route drafts through narrative.check_narrative.
Keep the impact report section order and matrix orientation stable; new analysis goes into annexes.
Regenerate configs/programs and examples/programs from code (`--check` in CI); never hand-edit them.
Run `python scripts/public_boundary_check.py --private-terms <private file>` before every push. The terms file stays outside the published tree.
