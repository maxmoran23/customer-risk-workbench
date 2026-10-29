"""Generate set-based SQL for an impact matrix so the database does the join, not a workstation.

The generated statements mirror ``impact.assess_change`` semantics (post-change segment, pinned exclusion when
either side is pinned, entrants and exits counted separately) and are tested for parity against it on SQLite.
Identifiers are validated, never quoted from user text, and no values are interpolated.

Population lists: instead of importing in-scope party lists into the session for every run, maintain one scope
table (party_id, segment) per assessment population and join it. The join is set-based and indexable; repeated
list imports are not.
"""

from __future__ import annotations

import re

from .contracts import ContractError

_IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]{0,62}(\.[A-Za-z_][A-Za-z0-9_]{0,62}){0,2}")


def _ident(value: str, name: str) -> str:
    if not isinstance(value, str) or not _IDENT.fullmatch(value):
        raise ContractError(f"{name} must be a plain SQL identifier (optionally schema-qualified)")
    return value


def migration_sql(
    pre_table: str,
    post_table: str,
    *,
    id_col: str = "party_id",
    segment_col: str = "segment",
    tier_col: str = "tier",
    pinned_col: str | None = "pinned",
    scope_table: str | None = None,
    scope_id_col: str = "party_id",
    scope_segment_col: str = "segment",
    exclude_pinned: bool = True,
) -> dict:
    """Return ANSI SQL statements: matched (matrix cells), entrants, exits and excluded counts.

    Pinned values are cast to integers (1 = pinned, 0 or NULL = not pinned); the ``checks`` statement counts
    duplicate identifiers and pinned values outside 0/1/NULL, and must return zero rows before the other results
    are used. With ``scope_table`` the segment comes from the scope table and parties absent from it are out of
    scope on both sides. ``exclude_pinned=False`` counts pinned parties like any other.
    """
    if type(exclude_pinned) is not bool:
        raise ContractError("exclude_pinned must be boolean")
    pre, post = _ident(pre_table, "pre_table"), _ident(post_table, "post_table")
    pid, seg, tier = _ident(id_col, "id_col"), _ident(segment_col, "segment_col"), _ident(tier_col, "tier_col")
    pin = _ident(pinned_col, "pinned_col") if pinned_col else None
    raw_pin = pin
    if scope_table:
        scope = _ident(scope_table, "scope_table")
        sid, sseg = _ident(scope_id_col, "scope_id_col"), _ident(scope_segment_col, "scope_segment_col")
        pre_src = f"(SELECT p.{pid} AS party_id, s.{sseg} AS segment, p.{tier} AS tier, " \
                  f"{'CAST(p.' + pin + ' AS INTEGER)' if pin else '0'} AS pinned FROM {pre} p JOIN {scope} s ON s.{sid} = p.{pid})"
        post_src = f"(SELECT p.{pid} AS party_id, s.{sseg} AS segment, p.{tier} AS tier, " \
                   f"{'CAST(p.' + pin + ' AS INTEGER)' if pin else '0'} AS pinned FROM {post} p JOIN {scope} s ON s.{sid} = p.{pid})"
        pid_a, seg_a, tier_a, pin_a = "party_id", "segment", "tier", "pinned"
    else:
        pre_src, post_src = pre, post
        pid_a, seg_a, tier_a, pin_a = pid, seg, tier, pin

    def p(alias):
        return f"COALESCE(CAST({alias}.{pin_a} AS INTEGER), 0) = 1" if pin_a else "1 = 0"

    def np(alias):
        return f"COALESCE(CAST({alias}.{pin_a} AS INTEGER), 0) = 0" if pin_a and exclude_pinned else "1 = 1"

    invalid_pin = (f"{raw_pin} IS NOT NULL AND CAST({raw_pin} AS INTEGER) NOT IN (0, 1)" if raw_pin else "1 = 0")
    checks = (
        f"SELECT 'pre' AS side, 'duplicate_party' AS issue, COUNT(*) AS n FROM "
        f"(SELECT {pid} FROM {pre} GROUP BY {pid} HAVING COUNT(*) > 1) d\n"
        f"UNION ALL SELECT 'post', 'duplicate_party', COUNT(*) FROM "
        f"(SELECT {pid} FROM {post} GROUP BY {pid} HAVING COUNT(*) > 1) d\n"
        f"UNION ALL SELECT 'pre', 'invalid_pinned', COUNT(*) FROM {pre} WHERE {invalid_pin}\n"
        f"UNION ALL SELECT 'post', 'invalid_pinned', COUNT(*) FROM {post} WHERE {invalid_pin}"
    )

    matched = (
        f"SELECT b.{seg_a} AS segment, a.{tier_a} AS pre_tier, b.{tier_a} AS post_tier, COUNT(*) AS party_count\n"
        f"FROM {pre_src} a\nJOIN {post_src} b ON b.{pid_a} = a.{pid_a}\n"
        f"WHERE {np('a')} AND {np('b')}\n"
        f"GROUP BY b.{seg_a}, a.{tier_a}, b.{tier_a}"
    )
    entrants = (
        f"SELECT b.{seg_a} AS segment, b.{tier_a} AS post_tier, COUNT(*) AS party_count\n"
        f"FROM {post_src} b\nLEFT JOIN {pre_src} a ON a.{pid_a} = b.{pid_a}\n"
        f"WHERE a.{pid_a} IS NULL AND {np('b')}\n"
        f"GROUP BY b.{seg_a}, b.{tier_a}"
    )
    exits = (
        f"SELECT a.{seg_a} AS segment, a.{tier_a} AS pre_tier, COUNT(*) AS party_count\n"
        f"FROM {pre_src} a\nLEFT JOIN {post_src} b ON b.{pid_a} = a.{pid_a}\n"
        f"WHERE b.{pid_a} IS NULL AND {np('a')}\n"
        f"GROUP BY a.{seg_a}, a.{tier_a}"
    )
    excluded = (
        "SELECT segment, COUNT(*) AS party_count FROM (\n"
        f"  SELECT b.{seg_a} AS segment FROM {post_src} b LEFT JOIN {pre_src} a ON a.{pid_a} = b.{pid_a}\n"
        f"  WHERE {p('b')} OR (a.{pid_a} IS NOT NULL AND {p('a')})\n"
        "  UNION ALL\n"
        f"  SELECT a.{seg_a} AS segment FROM {pre_src} a LEFT JOIN {post_src} b ON b.{pid_a} = a.{pid_a}\n"
        f"  WHERE b.{pid_a} IS NULL AND {p('a')}\n"
        ") x GROUP BY segment"
    )
    pinned_moved = (
        f"SELECT b.{seg_a} AS segment, COUNT(*) AS party_count\n"
        f"FROM {pre_src} a\nJOIN {post_src} b ON b.{pid_a} = a.{pid_a}\n"
        f"WHERE {p('a')} AND {p('b')} AND a.{tier_a} <> b.{tier_a}\n"
        f"GROUP BY b.{seg_a}"
    )
    if not exclude_pinned:
        excluded = "SELECT NULL AS segment, 0 AS party_count WHERE 1 = 0"
    return {
        "checks": checks,
        "matched": matched,
        "entrants": entrants,
        "exits": exits,
        "excluded_pinned": excluded,
        "pinned_moved": pinned_moved,
        "notes": [
            "Run `checks` first: every row must report n = 0 (no duplicate identifiers, pinned only 0/1/NULL).",
            "Some engines cast unparseable text to 0 instead of failing; cleanse pinned to integers upstream.",
            "Create indexes on the party identifier of both snapshots (and the scope table) before running.",
            "Tier values must already be the scale's labels or codes; map codes to labels in the reporting layer.",
            "Run all statements inside one read-consistent transaction or against immutable snapshot tables.",
        ],
    }


def rows_to_assessment_inputs(matched_rows, entrants_rows, exits_rows) -> dict:
    """Shape SQL result rows for comparison with the Python engine (used by parity tests and adapters)."""
    cells = {}
    for segment, pre_tier, post_tier, count in matched_rows:
        cells[(segment, str(pre_tier), str(post_tier))] = int(count)
    entrants = {(segment, str(tier)): int(count) for segment, tier, count in entrants_rows}
    exits = {(segment, str(tier)): int(count) for segment, tier, count in exits_rows}
    return {"cells": cells, "entrants": entrants, "exits": exits}
