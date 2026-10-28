"""Append-only review decision examples; identity authorization belongs to a host system."""

from __future__ import annotations

from dataclasses import dataclass, asdict
import sqlite3
import json

from .contracts import ContractError, identifier, timestamp, utc
from .features import digest


@dataclass(frozen=True)
class ReviewDecision:
    decision_id: str
    assessment_hash: str
    requested_by: str
    reviewed_by: str
    reason: str
    evidence_ids: list[str]
    disposition: str
    created_at: str
    expires_at: str

    def __post_init__(self):
        for field in ("decision_id", "assessment_hash", "requested_by", "reviewed_by"):
            identifier(getattr(self, field), field)
        if self.requested_by == self.reviewed_by:
            raise ContractError("requester and reviewer identifiers must differ")
        if self.disposition not in {"retain", "escalate_review", "return_for_evidence"}:
            raise ContractError("unsupported disposition; no automatic clearance/closure/SAR decision")
        if not isinstance(self.reason, str) or len(self.reason.strip()) < 20:
            raise ContractError("substantive decision rationale required")
        if not isinstance(self.evidence_ids, list) or not self.evidence_ids:
            raise ContractError("evidence references required")
        for evidence in self.evidence_ids:
            identifier(evidence, "evidence_id")
        object.__setattr__(self, "created_at", utc(self.created_at))
        object.__setattr__(self, "expires_at", utc(self.expires_at))
        if timestamp(self.expires_at) <= timestamp(self.created_at):
            raise ContractError("decision expiry must follow creation")

    def active(self, as_of: str) -> bool:
        return timestamp(self.created_at) <= timestamp(as_of) < timestamp(self.expires_at)


class DecisionLog:
    def __init__(self, db: sqlite3.Connection):
        self.db = db
        db.execute(
            "CREATE TABLE IF NOT EXISTS decisions(seq INTEGER PRIMARY KEY, decision_id TEXT UNIQUE NOT NULL, payload TEXT NOT NULL, previous_hash TEXT NOT NULL, record_hash TEXT NOT NULL)"
        )
        db.execute(
            "CREATE TRIGGER IF NOT EXISTS decisions_no_update BEFORE UPDATE ON decisions BEGIN SELECT RAISE(ABORT,'append only'); END"
        )
        db.execute(
            "CREATE TRIGGER IF NOT EXISTS decisions_no_delete BEFORE DELETE ON decisions BEGIN SELECT RAISE(ABORT,'append only'); END"
        )
        db.commit()

    def append(self, decision: ReviewDecision) -> str:
        payload = asdict(decision)
        self.db.execute("BEGIN IMMEDIATE")
        try:
            old = self.db.execute(
                "SELECT payload, record_hash FROM decisions WHERE decision_id=?", (decision.decision_id,)
            ).fetchone()
            if old:
                if json.loads(old[0]) != payload:
                    raise ContractError("decision identifier collision")
                self.db.commit()
                return old[1]
            last = self.db.execute("SELECT record_hash FROM decisions ORDER BY seq DESC LIMIT 1").fetchone()
            previous = last[0] if last else "0" * 64
            record_hash = digest({"previous_hash": previous, "decision": payload})
            self.db.execute(
                "INSERT INTO decisions(decision_id,payload,previous_hash,record_hash) VALUES (?,?,?,?)",
                (decision.decision_id, json.dumps(payload, sort_keys=True), previous, record_hash),
            )
            self.db.commit()
            return record_hash
        except BaseException:
            self.db.rollback()
            raise

    def verify(self) -> dict:
        previous = "0" * 64
        count = 0
        for payload, parent, record_hash in self.db.execute(
            "SELECT payload,previous_hash,record_hash FROM decisions ORDER BY seq"
        ):
            if parent != previous or record_hash != digest(
                {"previous_hash": parent, "decision": json.loads(payload)}
            ):
                return {"valid": False, "verified_records": count}
            previous = record_hash
            count += 1
        return {
            "valid": True,
            "verified_records": count,
            "head": previous,
            "limit": "Local integrity chain only. Database owners can rewrite storage; external attestation and authenticated identities are not implemented.",
        }
