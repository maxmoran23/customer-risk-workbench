# AI workflows under corporate constraints

**Status: tool-agnostic operating patterns; no AI service is integrated, called or endorsed.** These patterns assume an enterprise assistant or agent platform that the adopting organization has approved for the data involved. Approval of a tool, and of what may be shared with it, is the adopter's decision; this repository cannot establish it. See also [AI-assisted adaptation](ai-assistance.md), which covers adapting the code itself.

## Constraints the patterns are designed for

| Constraint | Consequence for the workflow |
| --- | --- |
| The suite makes no network calls and has no AI dependency | The model runs in a separate, approved tool. Material moves between the two by deliberate copy, never by an integration the suite opens. |
| Row-level data may not leave its approved environment | The model receives aggregates (a facts pack) and public or approved text, never snapshots or party lists. |
| Reviewers need every figure traceable to a computation | Deterministic code computes all figures; the model drafts words around them; a check rejects any number not in the facts pack. |
| Outputs feed governance records | Every model-assisted artifact is logged with its inputs, check result and the human who accepted it. |
| Model output can be fluent and wrong | A model never sets a verdict, status, tolerance, threshold or count; a human accepts or rejects each draft. |

## What may be copied in, and what never

| May be copied into an approved tool | Never paste |
| --- | --- |
| `facts-pack.json` or `narrative-prompt.txt` produced by `crw impact assess`, after review | Snapshot files, scope tables, extracts or any row-level party data |
| Public code, documentation and templates from this repository | Party identifiers, names, account numbers, or any field that identifies a customer or counterparty |
| Public regulatory or industry texts, or internal texts the tool is approved to receive | Credentials, connection strings, API keys, tokens, hostnames or database object names |
| Synthetic examples from `program-demo` | Non-public identifiers: internal system names, project codes, ticket numbers, employee names |
| A single attribute's value list and current classifications, where approved | Investigation details, override reasons, or anything describing why a party is pinned |

Review a facts pack before pasting it. It contains only aggregates and labels, but those labels come from your configuration: segment names, expectation IDs, assessment IDs and the before and after labels are copied verbatim. Use generic codes in the configuration (`SEGMENT_A`, not an internal business-line name) if the labels themselves are not approved for the tool.

## Pattern 1: grounded narrative drafting

1. Run `crw impact assess` with the manifest, history and standard inputs available. It writes `facts-pack.json` and `narrative-prompt.txt`.
2. Review the facts pack for label sensitivity, then paste `narrative-prompt.txt` into the approved tool using [the narrative drafter prompt](../prompts/impact-narrative-drafter.md).
3. Save the draft as plain text in the approved environment.
4. Run the grounding check:

   ```bash
   python -m crw impact narrative-check --facts runs/impact/this-release/facts-pack.json \
     --draft drafts/narrative.txt --require total.matched total.moved --out drafts/narrative-check.json
   ```

5. If the status is `rejected` (exit status 2), discard the draft or rewrite the affected sentences by hand from the facts. Do not adjust numbers until they pass.
6. A human reviewer reads the grounded draft against the report and confirms meaning: correct attribution of each number, every integrity finding, FAIL and unexplained movement stated, no causal claim beyond the manifest. The facts pack carries counts only for unexplained items, overlapping expectation pairs, baseline flags and parity differences; the reviewer checks the individual items in the report.

What the check does: a bare number must exactly equal a count fact (negatives with their sign); a number with a percent sign must be within 0.05 of a percentage fact; shorthand (1.2k, 5M), exponents, ordinals, multipliers (3x), ranges, ratios, multi-dot numbers and spelled-out quantity words are rejected as `unverifiable_format`; each `--require` key must appear as a whole quantity or token. Digits inside identifiers such as `IA-DEMO-001` are not treated as quantities. Dates and free-standing years are rejected, so leave them out of drafts. What it does not do: confirm that a correct number is attached to the right subject, detect omissions other than required keys, or judge tone. Details are in [the narrative drafter prompt](../prompts/impact-narrative-drafter.md).

Synthetic illustration: the demo's reference draft quotes 6 quantities, all found in the facts pack, and the check returns `grounded` (`narrative-check.json`; synthetic).

## Pattern 2: expectation wording

Expectation bounds come from a pre-deployment preview, computed by code (see the [change manifest template](../templates/change-manifest.md)). A model may help phrase the `rationale` text for each expectation from the change description and the preview cells. It must not choose `from`, `to`, `direction` or `count` values. The manifest owner edits and versions the result before deployment to test.

## Pattern 3: summarizing unexplained movement for an analyst

When reconciliation returns `requires_explanation`, an assistant may turn the `unexplained_movements` list and the relevant manifest entries into a short worklist grouped by `kind` (migration cells, aggregate-only movement, undeclared entrants or exits): which segment and cells, how many parties, which expectation came closest. The analyst then traces parties in the approved environment. The summary is a navigation aid; the explanation recorded in Annex A must come from the analyst's tracing. Use [the reviewer challenge prompt](../prompts/reviewer-challenge.md) to generate questions the explanation should answer.

## Pattern 4: classification and evidence support

For the attribute-review program, an assistant may:

* draft a proposed class and score for one attribute value with citations to evidence already in the catalog, using [the attribute classification assistant](../prompts/attribute-classification-assistant.md); the output is a JSON object that must pass catalog validation and always carries status `proposed`, never `agreed`;
* extract candidate evidence-register entries from a public or approved policy text with precise locators, using [the evidence extraction prompt](../prompts/evidence-extraction.md); each candidate is checked against the source by a human before entry.

## Agent platforms

Where the approved tool can read files or run commands:

* Give read access to the facts pack and public repository content only. Do not mount extract directories, scope tables or the register.
* Allow `narrative-check` and `verify-register --anchor`; do not allow the agent to run `assess` with a manifest it wrote, append to the register, or edit configuration.
* Treat every document the agent retrieves as data, not instructions. A policy text that contains directions to the assistant is quoted and flagged, not followed.
* Require the agent to stop and hand back on any `rejected` check rather than retry until a draft passes.

## Logging

For each model-assisted artifact, record in the approved environment:

| Field | Content |
| --- | --- |
| Artifact | Narrative draft, manifest rationale, worklist, classification proposal, evidence candidate |
| Prompt | Prompt file and its repository revision |
| Inputs | SHA-256 of the facts pack or source text supplied; never the row-level data, which was not supplied |
| Tool | The approved tool's internal inventory reference and version, as the adopter's policy defines it |
| Output | The draft as returned, before human edits |
| Checks | `narrative-check` or catalog validation result |
| Human decision | Accepted, edited or rejected; reviewer role; date; reason for edits |

Keep the unedited model output alongside the accepted version so a reviewer can see what the human changed.

## Human sign-off

A grounded narrative, a validated classification proposal or a plausible evidence candidate is a draft. The accountable reviewer accepts it by role in the adopter's own record. This repository contains no sign-off and the templates leave decision fields empty.

## Prompt library

[`prompts/`](../prompts/README.md) holds four prompts, each with purpose, inputs, prompt text, output contract, required human checks and exclusions:

| Prompt | Use |
| --- | --- |
| [Attribute classification assistant](../prompts/attribute-classification-assistant.md) | Draft a proposed class for one value with evidence citations |
| [Evidence extraction](../prompts/evidence-extraction.md) | Extract candidate evidence-register entries with locators |
| [Impact narrative drafter](../prompts/impact-narrative-drafter.md) | Draft the reviewer narrative from a facts pack |
| [Reviewer challenge](../prompts/reviewer-challenge.md) | Generate adversarial questions for a proposed reclassification or rule |
