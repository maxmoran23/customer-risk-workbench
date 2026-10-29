"""Render an impact assessment in a stable, familiar layout (Markdown, long CSV and standalone HTML).

The section order and matrix orientation are a contract: rows are the tier before the change, columns the tier
after, one matrix per segment, followed by annexes. New analysis goes into annexes so the core reads the same
from one release to the next.
"""

from __future__ import annotations

import csv
import html
import io

from .impact import matrix_long_rows

SECTIONS = (
    "1. Change summary",
    "2. Population and exclusions",
    "3. Tier migration by segment",
    "4. Aggregate-only segments",
    "Annex A. Expectation reconciliation",
    "Annex B. Historical comparison",
    "Annex C. Parity with the standard process",
    "Limits",
)


def _pct(value) -> str:
    return "-" if value is None else f"{100 * value:.1f}%"


def _matrix_md(data: dict) -> list[str]:
    tiers = data["tiers"]
    lines = ["| Before \\ After | " + " | ".join(tiers) + " | Total | Moved |",
             "| --- | " + " | ".join("---:" for _ in tiers) + " | ---: | ---: |"]
    for i, tier in enumerate(tiers):
        row = data["matrix"][i]
        moved = sum(row) - row[i]
        lines.append(f"| {tier} | " + " | ".join(f"{n:,}" for n in row) + f" | {sum(row):,} | {_pct(moved / sum(row) if sum(row) else None)} |")
    lines.append("| Total | " + " | ".join(f"{n:,}" for n in data["post_totals"]) + f" | {data['matched']:,} | {_pct(data['moved_share'])} |")
    return lines


def render_markdown(assessment: dict, *, manifest: dict | None = None, expectations: dict | None = None,
                    baseline: dict | None = None, parity: dict | None = None) -> str:
    t = assessment["totals"]
    out = [f"# Impact assessment {assessment['assessment_id']}", "",
           f"Before: {assessment['pre_label']} · After: {assessment['post_label']} · "
           f"Assessment hash `{assessment['assessment_hash'][:16]}`", "", f"## {SECTIONS[0]}", "",
           assessment["description"], ""]
    if manifest:
        out += [f"- Change `{manifest['change_id']}` ({manifest['change_type']}), release {manifest['release']}: "
                f"{manifest['description']}", ""]
    out += [f"Matched parties {t['matched']:,}; moved {t['moved']:,} ({_pct(t['moved_share'])}): "
            f"{t['up']:,} up, {t['down']:,} down.", ""]
    if assessment["integrity_findings"]:
        out += ["**Integrity findings:** " + ", ".join(assessment["integrity_findings"]), ""]
    out += [f"## {SECTIONS[1]}", "",
            "| Segment | Matched | Unchanged | Up | Down | Entrants | Exits | Excluded (pinned) | Pinned moved | Pin changed | Segment changed |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for segment, d in sorted(assessment["segments"].items()):
        out.append(f"| {segment} | {d['matched']:,} | {d['unchanged']:,} | {d['up']:,} | {d['down']:,} | "
                   f"{sum(d['entrants']):,} | {sum(d['exits']):,} | {d['excluded_pinned']:,} | {d['pinned_moved']:,} | "
                   f"{d['pin_changed']:,} | {d['segment_changed']:,} |")
    out.append(f"| **All** | {t['matched']:,} | {t['unchanged']:,} | {t['up']:,} | {t['down']:,} | "
               f"{sum(t['entrants']):,} | {sum(t['exits']):,} | {t['excluded_pinned']:,} | {t['pinned_moved']:,} | "
               f"{t['pin_changed']:,} | {t['segment_changed']:,} |")
    out += ["", f"## {SECTIONS[2]}", ""]
    for segment, d in sorted(assessment["segments"].items()):
        out += [f"### {segment}", ""] + _matrix_md(d) + [""]
    out += [f"## {SECTIONS[3]}", ""]
    if assessment["aggregate_segments"]:
        tiers = assessment["tier_scale"]["tiers"]
        out += ["| Segment | " + " | ".join(f"Net {x}" for x in tiers) + " | Population change | Minimum movers |",
                "| --- | " + " | ".join("---:" for _ in tiers) + " | ---: | ---: |"]
        for segment, d in assessment["aggregate_segments"].items():
            mm = "-" if d["minimum_movers"] is None else f"{d['minimum_movers']:,}"
            out.append(f"| {segment} | " + " | ".join(f"{n:+,}" for n in d["net_change"]) + f" | {d['population_change']:+,} | {mm} |")
    else:
        out.append("None configured.")
    if assessment["missing_aggregates"]:
        out += ["", "Aggregates not supplied for: " + ", ".join(assessment["missing_aggregates"])]
    out += ["", f"## {SECTIONS[4]}", ""]
    if expectations:
        out += [f"Verdict: **{expectations['verdict']}**", "", "| Expectation | Observed | Expected | Status |",
                "| --- | ---: | --- | --- |"]
        for e in expectations["expectations"]:
            high = "no maximum" if e["expected"]["max"] is None else f"{e['expected']['max']:,}"
            out.append(f"| {e['id']} | {e['observed']:,} | {e['expected']['min']:,} to {high} | {e['status']} |")
        if expectations["unexplained_movements"]:
            out += ["", "Unexplained movements:", ""]
            for u in expectations["unexplained_movements"]:
                out.append(f"- {u['segment']}: {u['from']} to {u['to']}, {u['count']:,} ({_pct(u['row_share'])} of row)")
    else:
        out.append("No change manifest supplied.")
    out += ["", f"## {SECTIONS[5]}", ""]
    if baseline:
        out.append(f"Compared with {baseline['history_assessments']} prior assessments; {len(baseline['flags'])} rate(s) flagged.")
        for f in baseline["flags"][:20]:
            z = "outside observed range" if f["modified_z"] is None else f"modified z {f['modified_z']:.1f}"
            out.append(f"- {f['segment']} {f['from']} to {f['to']}: rate {_pct(f['rate'])} vs median {_pct(f['history_median'])} ({z})")
        if len(baseline["flags"]) > 20:
            out.append(f"- {len(baseline['flags']) - 20} further flag(s) in the baseline JSON.")
    else:
        out.append("No history supplied.")
    out += ["", f"## {SECTIONS[6]}", ""]
    if parity:
        out.append(f"Verdict: **{parity['verdict']}** over {parity['cells_compared']} cells; {len(parity['differences'])} difference(s).")
        for d in parity["differences"][:20]:
            out.append(f"- {d['segment']} {d['pre_tier']} to {d['post_tier']}: automated {d['automated']:,}, standard {d['standard']:,}")
        if len(parity["differences"]) > 20:
            out.append(f"- {len(parity['differences']) - 20} further difference(s) in the parity JSON.")
    else:
        out.append("No standard-process output supplied.")
    out += ["", f"## {SECTIONS[7]}", ""] + [f"- {x}" for x in assessment["limits"]] + [""]
    return "\n".join(out)


def render_csv(assessment: dict) -> str:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=["segment", "pre_tier", "post_tier", "count"], lineterminator="\n")
    writer.writeheader()
    writer.writerows(matrix_long_rows(assessment))
    return buffer.getvalue()


_STYLE = (
    ":root{--bg:#111f30;--panel:#182b3e;--border:#34495e;--text:#edf3f8;--muted:#bac8d5;--teal:#86d4c2;--amber:#edc485}"
    "@media (prefers-color-scheme: light){:root{--bg:#f6f7f9;--panel:#ffffff;--border:#cfd6de;--text:#142436;--muted:#40556b;--teal:#286f65;--amber:#8a5a12}}"
    "body{margin:0;background:var(--bg);color:var(--text);font:15px/1.55 -apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif}"
    "main{max-width:1100px;margin:auto;padding:32px 16px}h1{font-size:28px}h2{font-size:20px;margin-top:32px}"
    "table{border-collapse:collapse;width:100%;font-size:13px;margin:12px 0;display:block;overflow-x:auto}"
    "th,td{border-bottom:1px solid var(--border);padding:8px;text-align:right;white-space:nowrap}"
    "th:first-child,td:first-child{text-align:left}th{color:var(--muted);font-weight:500}"
    ".diag{color:var(--teal)}.moved{color:var(--amber);font-weight:600}.note{color:var(--muted);font-size:13px}"
)


def render_html(assessment: dict, **annexes) -> str:
    """Standalone page: summary and matrices as HTML tables, annexes as escaped preformatted Markdown."""
    esc = html.escape
    t = assessment["totals"]
    parts = [f"<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1'>"
             f"<title>Impact assessment {esc(assessment['assessment_id'])}</title><style>{_STYLE}</style></head><body><main>",
             f"<h1>Impact assessment {esc(assessment['assessment_id'])}</h1>",
             f"<p class='note'>Before: {esc(assessment['pre_label'])} · After: {esc(assessment['post_label'])} · hash {esc(assessment['assessment_hash'][:16])}</p>",
             f"<p>{esc(assessment['description'])}</p>",
             f"<p>Matched {t['matched']:,}; moved {t['moved']:,} ({_pct(t['moved_share'])}): {t['up']:,} up, {t['down']:,} down.</p>"]
    if assessment["integrity_findings"]:
        parts.append(f"<p class='moved'>Integrity findings: {esc(', '.join(assessment['integrity_findings']))}</p>")
    parts.append("<h2>Population and exclusions</h2><table><tr><th>Segment</th><th>Matched</th><th>Unchanged</th>"
                 "<th>Up</th><th>Down</th><th>Entrants</th><th>Exits</th><th>Excluded (pinned)</th><th>Pinned moved</th>"
                 "<th>Pin changed</th><th>Segment changed</th></tr>")
    for segment, d in sorted(assessment["segments"].items()) + [("All", t)]:
        parts.append(f"<tr><td>{esc(segment)}</td><td>{d['matched']:,}</td><td>{d['unchanged']:,}</td><td>{d['up']:,}</td>"
                     f"<td>{d['down']:,}</td><td>{sum(d['entrants']):,}</td><td>{sum(d['exits']):,}</td>"
                     f"<td>{d['excluded_pinned']:,}</td><td>{d['pinned_moved']:,}</td><td>{d['pin_changed']:,}</td>"
                     f"<td>{d['segment_changed']:,}</td></tr>")
    parts.append("</table>")
    parts.append("<h2>Tier migration by segment</h2>")
    for segment, d in sorted(assessment["segments"].items()):
        tiers = d["tiers"]
        rows = [f"<tr><th>Before \\ After</th>{''.join(f'<th>{esc(x)}</th>' for x in tiers)}<th>Total</th></tr>"]
        for i, tier in enumerate(tiers):
            cells = "".join(
                f"<td class='{'diag' if i == j else ('moved' if n else '')}'>{n:,}</td>" for j, n in enumerate(d["matrix"][i])
            )
            rows.append(f"<tr><td>{esc(tier)}</td>{cells}<td>{sum(d['matrix'][i]):,}</td></tr>")
        parts.append(f"<h3>{esc(segment)}</h3><table>{''.join(rows)}</table>"
                     f"<p class='note'>Entrants {sum(d['entrants']):,} · exits {sum(d['exits']):,} · excluded (pinned) {d['excluded_pinned']:,}</p>")
    markdown = render_markdown(assessment, **annexes)
    annex = markdown[markdown.index("## " + SECTIONS[3]):]
    parts.append(f"<h2>Annexes</h2><pre style='white-space:pre-wrap'>{esc(annex)}</pre></main></body></html>")
    return "".join(parts)
