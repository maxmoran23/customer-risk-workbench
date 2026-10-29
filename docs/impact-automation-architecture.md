# Change-impact automation: scale and compute design

**Status: reference design for a single-node implementation.** The code is tested on synthetic data and on SQLite. It has not been run against an institutional database or a production-scale population, and nothing here is a performance claim for one.

## Components

| Component | Module | Responsibility | Deterministic | Network |
| --- | --- | --- | --- | --- |
| Tier scale and snapshot reader | `crw.impact` (`TierScale`, `iter_snapshot`) | Parse labels or codes into ordered tier indexes; validate identifiers and pinned flags | Yes | None |
| Partitioned join | `crw.impact.assess_change` | Stream both snapshots into hash partitions; join partition by partition; build matrices, entrants, exits, exclusions, pin changes, integrity checks; fail if an input file changed during the run | Yes | None |
| Aggregate-only assessment | `crw.impact.assess_aggregates` | Distribution change and lower bound on movers where no rows exist | Yes | None |
| Expectation reconciliation | `crw.impact.reconcile_expectations` | Compare declared migration, population and aggregate-only effects with observations; list unexplained items by kind and overlapping expectations; reject unknown segment names | Yes | None |
| Historical comparison | `crw.impact.baseline_outliers` | Modified z-score of each rate against prior assessments | Yes | None |
| Parity | `crw.impact.reconcile_matrices` | Cell-by-cell comparison with an existing process | Yes | None |
| Register | `crw.impact.append_register`, `verify_register` | Append-only, hash-chained record of assessments and verdicts; optional external anchor to detect truncation | Yes | None |
| SQL generator | `crw.impact_sql.migration_sql` | Emit set-based statements so a database performs the join, plus a `checks` statement for input defects | Yes (text only; does not execute) | None |
| Report renderer | `crw.impact_report` | Markdown, long CSV and standalone HTML in a fixed section order | Yes | None |
| Narrative guard | `crw.narrative` | Facts pack, drafting prompt text, quantity grounding check | Yes | None |
| Command line | `crw.cli_programs` (`crw impact ...`) | Wire the above to files | Yes | None |
| Language model (optional, external) | Not part of the suite | Draft prose from a facts pack in an approved tool | No | Outside the suite |

Data flow:

```text
frozen pre snapshot  --+
                       +--> partition --> join --> assessment --+--> expectations (manifest) --+
frozen post snapshot --+                              |         +--> baseline (history) -------+--> report (md, html, csv)
                                                      |         +--> parity (standard CSV) ----+--> register (hash chain)
database snapshots --> generated SQL --> cells -------+ (parity check against the engine)      +--> facts pack
                                                                                                     |
                                     human review <-- narrative-check <-- [external approved model] <-+
```

## Memory bound of the partitioned join

`assess_change` hashes each input file, streams each snapshot once into partitions, joins one partition at a time, and hashes the files again:

1. **Hash and partition.** Each input file's SHA-256 is computed first. Each snapshot is then read one row at a time. Each row is validated and written to partition `crc32(party_id) mod P` as a tab-separated line in a temporary directory. All rows of one party land in the same partition in both snapshots. Memory during this pass is constant per row; the process holds `P` open file handles for the snapshot being partitioned.
2. **Join.** For each partition index, the pre partition is loaded into a dictionary keyed by party; the post partition is streamed against it while a set of seen post identifiers detects duplicates. Leftover pre entries are exits.
3. **Accumulate.** Results are a `k x k` matrix plus small vectors per segment, where `k` is the number of tiers.
4. **Re-hash.** Each input file's SHA-256 is computed again; a difference from step 1 fails the run.

Peak working memory is therefore approximately one pre partition's dictionary plus one post partition's identifier set plus the per-segment accumulators:

```text
peak ~ (N_pre / P) * c_pre + (N_post / P) * c_post + S * k² * c_cell + interpreter baseline
```

`c_pre` and `c_post` are per-party costs, dominated by identifier length and Python object overhead; `S` is the number of segments. The bound is one partition of each snapshot: the pre-change records and the post-change identifiers of that partition.

Disk: the temporary directory holds a full tab-separated copy of both snapshots. The Python API accepts `workdir`; the command line does not and uses the system temporary directory.

### Choosing partitions

1. Measure `c_pre` on a representative extract sample: run `assess_change` with `partitions=1` under `tracemalloc` and divide peak by rows. Repeat with realistic identifier lengths.
2. Set a memory budget well below the host limit.
3. Choose `P = ceil((N_pre * c_pre + N_post * c_post) / budget)`, then round up for headroom. The code accepts integers from 1 to 4096; the default is 16.
4. Confirm `P` is below the process open-file limit with margin.
5. Re-run the same inputs at two partition counts during adoption. `assessment_hash` must be identical; partition count is not part of the payload.

Larger `P` lowers memory and does not change results. It does not parallelize: the engine is single-threaded, and runtime is dominated by reading, validating and rewriting every row.

## When to push the join into the database

| Condition | Route |
| --- | --- |
| Snapshots already exist as database tables, and extracting tens of millions of rows to files is itself the expensive step | Generated SQL (`crw impact sql`) |
| Policy restricts moving row-level data off the database platform | Generated SQL |
| Snapshots arrive as files, or the full integrity checks are required | Python engine |
| Verifying the SQL route during adoption | Both, on the same frozen data, compared cell by cell |

The generated statements are aggregate queries. `matched` returns at most `S * k²` rows; `entrants` and `exits` at most `S * k`; `excluded_pinned` and `pinned_moved` at most `S`; `checks` returns one row per side and issue. No statement returns row-level results, which is the main defense against queries that exhaust a shared compute allocation. The work that remains is the join itself, which needs the indexes below.

Semantics match the engine on the tested cases (post-change segment for matched parties, pinned exclusion when either side is pinned, entrants and exits counted separately). Run `checks` first: it counts duplicate party identifiers on each side and pinned values outside 0, 1 or NULL, and every row must report `n = 0` before the other results are used. Pinned values are cast to integers, so text `'0'` and `'1'` work; some engines cast unparseable text to 0 rather than failing, so cleanse the column upstream. Differences an adopter must handle:

* Pinned parties are excluded by default. `exclude_pinned=False` in Python, or `crw impact sql --include-pinned`, counts them like any other party; an empty `--pinned-col` ignores pins entirely, which also disables the `pinned_moved` and invalid-pin checks.
* No `segment_changed` or `pin_changed` count, no tier validation and no aggregate-only handling. Duplicates are detected by `checks`, not prevented; a primary key on the snapshot tables prevents them. Tier codes are returned as stored and must be mapped to labels in the reporting layer.
* With a scope table, the segment for both sides comes from the scope table, so segment changes cannot appear, and parties absent from the scope table are out of scope on both sides (not entrants or exits).
* Identifiers are validated against a plain or schema-qualified identifier pattern (up to three dot-separated parts). No value is interpolated into the SQL.
* Parity is tested on SQLite only. Other databases may need dialect review; run the statements inside one read-consistent transaction or against immutable tables.

To compare database output with the engine, rename `party_count` to `count`, write `segment, pre_tier, post_tier, count` as CSV, and pass it to `crw impact assess --standard`. In the synthetic demo the SQLite statements reproduced all 44 nonzero engine cells (`sql-parity.json`; synthetic).

## Scope tables instead of list imports

A recurring cost in impact work is importing in-scope party lists into a SQL session for each run: one upload per list, session-scoped temporary tables, client upload limits, long `IN (...)` predicates that optimizers handle poorly, and no record of which list version was used.

The alternative is one scope table per assessment population with columns `(party_id, segment)`:

* Populated by set-based statements inside the database, one per segment where in-scope logic differs by segment, combined with `UNION ALL` into the table. The defining statements are version-controlled with the assessment configuration.
* Indexed on `party_id`; primary key prevents a party appearing in two segments.
* Rebuilt or versioned per release (`scope_<release>` or a release column), never edited in place after the assessment runs.
* Joined by the generated SQL (`--scope-table`), so the scope filter is applied once, inside the join, by the database.

The scope table also carries the segment assignment, which keeps segment-specific scoping logic in one reviewable place rather than in per-run spreadsheets.

## Indexing and snapshot immutability

| Object | Index | Immutability rule |
| --- | --- | --- |
| Pre snapshot table | Primary key or unique index on party identifier | Created before deployment to test; never updated afterwards |
| Post snapshot table | Primary key or unique index on party identifier | Created after deployment; never updated afterwards |
| Scope table | Primary key on party identifier | Versioned per release |
| Snapshot files | Not applicable | Written once to a frozen location; SHA-256 recorded in `assessment.json` |

The engine computes each input file's SHA-256 before partitioning and again after the join, and fails with a contract error if either changed; the recorded hashes are the pre-run values. Hashing reads each file twice more, which adds to runtime on large extracts. For the SQL route, the suite does not compute a table checksum; record row counts and a database-side checksum as adopter work.

## Aggregate-only segments

Some segments are too large or too costly to snapshot row by row. For these, the configuration declares `aggregate_only` and supplies tier counts before and after. The engine reports net change per tier, population change, and a lower bound on parties that moved. It never produces a matrix, because a matrix cannot be recovered from its margins.

**Why not.** Take two tiers. If `a` parties move LOW to HIGH and `a` other parties move HIGH to LOW, both margins are unchanged for every value of `a`, from zero to the smaller tier count. Margins fix row and column totals; any number of matrices share them.

**Lower bound.** Let the population be the same set of parties before and after. Each party that changes tier lowers one tier count by one and raises another by one, so it changes the sum of absolute per-tier differences (the L1 distance between the two count vectors) by at most two. Hence:

```text
movers >= (1/2) * Σ_t |post_t - pre_t|
```

When totals are equal, the positive and negative net changes sum to the same amount, so the L1 distance is even and the bound is an integer. The bound is attained only when no tier has offsetting inflows and outflows; actual movement can be larger by any amount the margins allow.

Synthetic illustration (`SEGMENT_E`): net changes of -462, +186, +145 and +131 across the four tiers with population change 0 give a minimum of 462 movers. The true number of movers in that synthetic segment is not computable from these figures.

When totals differ, the engine returns no bound. Equal totals are necessary but not sufficient: if parties both entered and left in equal numbers, the bound is not valid, and the code cannot detect that from counts alone. The engine's `minimum_movers_note` states this. Confirm unchanged membership by other means before quoting the bound. Aggregate-only segments are reconciled only through the manifest's `expected_aggregate` bounds on minimum movers; an undeclared segment with movement is reported as unexplained. They are excluded from historical comparison and parity.

## Report layout contract

`impact_report.SECTIONS` fixes the order: change summary; population and exclusions; tier migration by segment; aggregate-only segments; Annex A expectation reconciliation; Annex B historical comparison; Annex C parity; limits. Matrices always have the tier before as rows and the tier after as columns, lowest tier first, with totals and row moved share. A test asserts the order and the matrix header.

The rationale is reviewer trust. Senior reviewers who have read migration matrices for years distrust output that looks unfamiliar, and a layout that changes between releases forces re-learning and hides comparisons. New analysis (expectations, history, parity) goes into annexes so the core sections read the same every release. The long CSV gives the same cells in a shape any spreadsheet or database can pivot.

Current rendering detail: the Markdown report contains every section. The HTML page renders the summary, the population and exclusions table, and the matrices as tables, and embeds Section 4 onward as escaped preformatted text. Both population tables carry the same columns and an all-segments row. In Markdown, Annex B and Annex C list at most 20 items and state how many further items are in `baseline.json` or `parity.json`.

## Historical comparison method

For each off-diagonal cell, the row rate (cell count divided by the pre-tier row total) is compared with the same cell's rates in prior assessments, plus each segment's overall moved share. With at least `min_history` prior values (default 5, minimum 3), the Iglewicz-Hoaglin modified z-score `0.6745 * (x - median) / MAD` is computed and flagged at `|z| >= 3.5` by default. Where the median absolute deviation is zero (at least half the prior rates are identical), a z-score is undefined; the rate is flagged with reason `outside_observed_range` and `modified_z` null only if it lies below the minimum or above the maximum of the prior rates.

Synthetic illustration (`baseline.json`): against 8 prior assessments, 10 rates were flagged, 5 by modified z-score and 5 as outside the observed range. The largest is `SEGMENT_A` `MODERATE` to `LOW` at 5.1% against a history median of 0.1% (modified z 43.5). The demo's history consists of synthetic rescorings unrelated to this change, so the flags show the mechanics, not a meaningful comparison. History should be drawn from prior changes of similar type; a flag prompts explanation and is not evidence of error.

## Where AI fits and where it must not

| Task | Owner | Control |
| --- | --- | --- |
| Every count, rate, bound, verdict, flag and hash | Deterministic code | Tests with independently derived values; reproducible hash |
| Narrative prose for reviewers | Language model may draft | Facts pack only; `narrative-check` rejects unsupported numbers; human review of meaning |
| Wording of expectation rationales | Language model may suggest | Bounds come from the preview, not the model; human edits and owns the manifest |
| Summary of unexplained movements for an investigating analyst | Language model may summarize the cells listed in `expectations.json` | Analyst traces parties in the approved environment; the summary is not an explanation |
| Deciding whether a movement is explained | Human | Recorded in Annex A commentary |
| Setting verdicts, tolerances, thresholds | Code and predeclared configuration | Never set or overridden by a model |
| Computing counts, filling missing figures, estimating aggregate-only movement | Never a model | Prompt rule; grounding check |

The suite makes no network call and has no AI dependency. A model, if used, runs in an approved tool outside the suite and sees only the facts pack. The grounding check treats each quantity token in a draft (at the start of the text or after whitespace or a bracket) as a claim: a bare number must exactly equal a count fact, a percentage must be within 0.05 of a percentage fact, and shorthand, multipliers, ordinals, ranges, ratios and spelled-out quantities are rejected as unverifiable. It does not confirm that a correct number is attached to the right subject, that the prose is accurate, or that nothing material is omitted. See [AI workflows](ai-workflows.md).

## Limits

* Single process on a single node. No parallelism, distributed execution, retry or resumption; a failed run is re-run from the start.
* No scheduling, orchestration, job service or release integration. An operator runs the commands.
* No authentication, authorization or access control. File and database permissions are the adopter's.
* The generated SQL is text; the suite does not connect to any database except the local SQLite file in the demo's parity step.
* The register is a local append-only file without locking; concurrent writers can corrupt it. It detects edits and reordering; deletion of trailing entries is detected only against an anchor (`entries`, `last_entry_hash`) kept elsewhere and updated after each append.
* The generated SQL has no segment-changed or pin-changed count, relies on the operator to run `checks` before using results, and with a scope table uses the scope table's segment for both sides.
* The narrative check accepts any count present anywhere among the count facts, and any percentage within 0.05 of a percentage fact; it cannot verify that a correct number is attached to the right subject.
* Tested on synthetic populations of the demo's size. Behavior at tens of millions of rows follows from the design above but has not been measured here.
