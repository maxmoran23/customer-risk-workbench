# Impact narrative drafter

## Purpose

Draft the plain-language narrative of a change-impact assessment for senior reviewers, using only the figures in a facts pack produced by deterministic code. The draft is then checked mechanically for unsupported quantities and reviewed by a human for meaning.

## Inputs

| Input | Source | Notes |
| --- | --- | --- |
| Drafting prompt with facts | `narrative-prompt.txt`, written by `crw impact assess` from `crw.narrative.prompt_text(facts_pack(...))` | Contains the rules and the facts JSON; paste it whole |
| Facts pack | `facts-pack.json`, same run | Kept locally for the check; review labels before pasting the prompt |
| Report | `impact-assessment.md`, same run | For the human reviewer, not for the model |

The facts pack holds totals; per-segment counts including pinned moved, pin changed and segment changed; nonzero off-diagonal cells and their row shares; aggregate-only results; expectation statuses and observed counts, including population and aggregate-only results; the number of unexplained items and of overlapping expectation pairs; baseline and parity summaries; and integrity findings. It holds no party identifiers. It does not hold the individual unexplained items, overlap pairs, baseline flags or parity differences, only their counts. Segment names, assessment ID, expectation IDs and before and after labels are copied from your configuration.

The pack separates `allowed_numbers` (count facts) from `allowed_percents` (facts whose keys end in `_pct`). The check uses that separation.

## Prompt text

Paste the following preface, then the full contents of `narrative-prompt.txt` unchanged. The generated file begins with the drafting instruction and six rules, then the facts:

```text
Formatting requirements for this draft, in addition to the rules that follow:
- Plain text, no headings, tables or bullet lists.
- Refer to sections and annexes by name, never by number.
- Write no quantity that is not copied from FACTS. No years, dates, release numbers, paragraph counts,
  ranges (400-500), ratios (3/7), shorthand (1.2k, 5M), multipliers (3x), ordinals (47th)
  or spelled-out quantities (two, half, dozen, twice).
- Write counts in digits exactly as in FACTS; thousands separators are acceptable (19,759).
- Write a percentage only for a fact whose key ends in _pct, with a percent sign (2.8%).
  Never write a count with a percent sign or a percentage without one.
- If expectations.verdict is requires_explanation, parity.verdict is MISMATCH, or integrity_findings is not empty,
  say so in the first paragraph.
- Do not add recommendations, approvals or conclusions about whether the change should be released.

<paste the full contents of narrative-prompt.txt here>
```

The generated portion starts:

```text
You are drafting the narrative section of a change-impact assessment for a customer risk rating model.
Write four short paragraphs in plain, neutral language for senior reviewers.
Rules:
- Use only figures present in facts; do not compute new totals, rates or differences.
...
- Write every quantity in digits as given (no 1.2k, 5M, 3x, ranges, fractions or spelled-out numbers).
If a figure you want is not in the facts, write 'not computed' instead of estimating it.

FACTS (JSON):
```

## Output contract

Plain text, four short paragraphs, in the standard order: change summary, population and exclusions, migration by segment, annexes. Every quantity is a count fact quoted exactly or a percentage fact quoted with a percent sign. Every integrity finding, FAIL and unexplained item count is stated.

Save the draft and run:

```bash
python -m crw impact narrative-check --facts <run>/facts-pack.json --draft <draft>.txt \
  --require total.matched total.moved expectations.verdict --out <draft>-check.json
```

What the check enforces:

| Rule | Result if broken |
| --- | --- |
| A quantity starts at the beginning of the text or after whitespace or an opening bracket; digits inside identifiers (`IA-DEMO-001`, `SEGMENT_A1`) are not quantities | Not checked |
| A bare number must exactly equal a count fact; negatives are compared with their sign | `not_in_facts` |
| A number with `%` or "percent" must be within 0.05 of a percentage fact | `not_in_facts` |
| Shorthand, exponent, ordinal or multiplier suffixes, range and ratio tails, multi-dot numbers, and spelled-out quantity words | `unverifiable_format` |
| Each `--require` key: numeric facts must appear as a whole quantity; text facts as a whole token | Listed in `missing_required_facts` |

Exit status 0 with `"status": "grounded"` passes. Exit status 2 means `rejected`; each entry in `unsupported_numbers` has the quantity, its `reason` and surrounding context. Dates are rejected (a year is not a count fact and the day and month form range tails), so leave them out of the draft. Add `--require` keys for any figure the reviewer must see, for example `parity.verdict` during a parallel run. Synthetic reference: the demo's reference draft quotes 6 quantities and is `grounded` (`narrative-check.json`).

## Required human checks

* Read every quantity against its fact key. The check confirms that a value exists among the count or percentage facts, not that it is attached to the right subject: a count equal to one segment's figure passes in a sentence about another segment, and small integers usually appear somewhere in the pack.
* Confirm percentages are quoted as given; the check accepts a difference of up to 0.05.
* Confirm nothing material is omitted: integrity findings, every FAIL, the unexplained-item count, overlapping pairs, parity differences, and any nonzero pin changed or segment changed.
* Remove any causal claim beyond the change manifest and any characterization of a finding as benign.
* A rejected draft is discarded or the affected sentences are rewritten by hand from the facts; never alter numbers until the check passes.
* Record the reviewer role and keep the unedited draft with the accepted version.

## What not to include

* Snapshot files, the long CSV, scope tables or any row-level data.
* Explanations of unexplained movements that the analyst has not established.
* Internal segment names, release names or system names in the configuration labels unless approved for the tool.
* Instructions asking the model to estimate movement for aggregate-only segments or to fill "not computed" figures.
