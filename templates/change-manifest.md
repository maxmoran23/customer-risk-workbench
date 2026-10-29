# Change manifest

**Status: fill-in template with a synthetic worked example; no actual change is declared.** The manifest states, before deployment to test, which tier movements and population changes a change is expected to cause. `crw impact assess --manifest` reconciles it against what was observed. Complete and version it before the post-change snapshot exists.

## Fields

The JSON fields below mirror `crw.impact.validate_manifest` and `reconcile_expectations`. Unknown fields fail validation.

| Field | Required | Contract | Guidance |
| --- | --- | --- | --- |
| `change_id` | Yes | Identifier, 1-128 of `A-Z a-z 0-9 _ . : -` | Stable reference used in the report and register |
| `release` | Yes | Free value | Release or deployment label as the adopter's change process names it |
| `description` | Yes | Free text | What changes, in one or two sentences, without internal system names |
| `change_type` | Yes | One of `value_classification`, `rule`, `weight_or_threshold`, `reference_data`, `population_scope`, `logic` | Choose the dominant type; split combined changes into separate manifests where they can be assessed separately |
| `expected_effects` | Yes | List of migration expectations (below); may be empty | An empty list declares that no tier movement is expected; any movement then appears as unexplained |
| `expected_population` | No | `{"entrants": {"min", "max"}, "exits": {"min", "max"}, "rationale"}` | Declares the expected number of parties entering and leaving between snapshots. Without it, total entrants or exits at or above `min_count` are reported as unexplained (`undeclared_entrants`, `undeclared_exits`) |
| `expected_aggregate` | No | Object keyed by aggregate-only segment: `{"minimum_movers": {"min", "max"}, "rationale"}` | Declares the expected lower bound on movers for each aggregate-only segment. A declared segment must have aggregates in the assessment. An undeclared segment with movement, or with an unbounded mover count, is reported as unexplained (`aggregate_only_movement`) |
| `unexplained_tolerance` | No | `{"min_count": n, "min_share": s}` with `n` a positive integer and `0 <= s <= 1`; default `{"min_count": 1, "min_share": 0.0}` | Unexplained migration cells are reported only when count `>= min_count` and row share `>= min_share`; undeclared entrants and exits use `min_count`. The default reports every unexplained party. Set looser values only with a written reason |

All `min` and `max` bounds are integers with `min >= 0` and `max >= min`, or `max` null for no maximum.

Each migration expectation:

| Field | Contract | Guidance |
| --- | --- | --- |
| `id` | Identifier, unique within the manifest | For example `EXP-DOWN-TO-LOW` |
| `segments` | Nonempty list of segment names, or exactly `["*"]` for all segments | Reconciliation fails if a named segment is not in the assessment. Only paired segments have cells; naming an aggregate-only segment matches nothing |
| `from` | Nonempty list of tier labels, or exactly `["*"]` | Tier before. Labels must exist in the scale; codes are not accepted here |
| `to` | Nonempty list of tier labels, or exactly `["*"]` | Tier after |
| `direction` | `up`, `down` or `any` | A cell must also satisfy the direction: `up` means the tier after is higher |
| `count` | Bounds as above | Bounds on the total of all matching off-diagonal cells |
| `rationale` | Text | Why this movement follows from the change, and where the bound came from |

Matching rules: a migration cell is explained if any expectation matches it. Observed counts are summed per expectation across matching cells in all paired segments; a cell matching two expectations counts toward both, and `expectations.json` lists each such pair under `overlapping_expectations`. Declared population and aggregate bounds appear as results `POPULATION-ENTRANTS`, `POPULATION-EXITS` and `AGGREGATE-<segment>`, with PASS or FAIL like any expectation. Each unexplained item carries a `kind`: `migration`, `aggregate_only_movement`, `undeclared_entrants` or `undeclared_exits`.

## Deriving bounds from a preview

Expectations should come from a computation made before deployment, not from the observed result.

1. Run the current and proposed logic on a design-time sample drawn separately from the population that will be assessed, excluding pinned parties. `crw.program_demo.preview_change(parties, model, rules)` does this for the reference categorical model and returns moved cells `{from, to, count}`.
2. Group cells into expectations. `crw.program_demo.manifest_from_preview(preview, scale, change_id, band=0.25, population=..., aggregate=...)` groups by destination tier and direction, with `from` and `segments` set to `["*"]`. It scales each preview count to the assessed population (`n = round(raw * population / preview_parties)`), then sets `slack = max(band * n, 3 * sqrt(n) + 3)`, `min = max(0, floor(n - slack))` and `max = floor(n + slack) + 1`. The square-root term keeps bounds on small counts from being overconfident. It also writes a synthetic `release`, `description` and `expected_population` (0 to 1% of the population); replace them with values justified for the change.
3. Narrow where the preview supports it. Grouping only by destination means a movement from an unexpected source tier in the same direction is still treated as explained. Listing `from` tiers and segments explicitly makes the reconciliation more sensitive.
4. Declare population movement from ordinary onboarding and closure rates for the snapshot interval, and aggregate-only bounds from whatever estimate exists for those segments. State the basis in each rationale.
5. Choose and record the band and slack rule before deployment. Wider bounds tolerate more preview error and detect less.

## Synthetic worked example

From `program-demo` (seed 11; synthetic). The preview ran on a separate design-time sample of 20,000 synthetic parties and estimated 549 movers (`preview.json`), including 313 `MODERATE` to `LOW`. The assessed population is also 20,000, so no scaling applied. That cell became:

```json
{
  "id": "EXP-DOWN-TO-LOW",
  "segments": ["*"],
  "from": ["*"],
  "to": ["LOW"],
  "direction": "down",
  "count": {"min": 234, "max": 392},
  "rationale": "Pre-deployment preview on a separate design-time sample estimated 313 of 20000 parties moving down to LOW; scaled to the assessed population."
}
```

Observed: 329, PASS. A small cell shows the square-root allowance at work: the preview estimated 8 parties moving down to `HIGH`, giving bounds 0 to 20, and the observed count was 20, at the upper bound. The manifest also declared entrants and exits of 0 to 200 each (observed 80 and 63) and minimum movers of 0 to 2,500 for the aggregate-only `SEGMENT_E` (observed 462). All nine results passed with no unexplained items and no overlapping expectations; the verdict was `consistent_with_manifest`. Agreement on synthetic data from one generator does not indicate how a real preview would perform.

## Manifest record

| Field | Entry |
| --- | --- |
| Manifest file and version | |
| Date written (before deployment to test) | |
| Preview method, sample, size and date | |
| Band, slack rule and reason | |
| Population and aggregate-only bounds and basis | |
| Prepared by (role) | |
| Reviewed by (role) | |
| Later corrections (new version, reason, date; original retained) | |

**Current manifest decision: none recorded.** A manifest edited after the post-change snapshot is visible must be recorded as a correction, with the original reconciliation retained.
