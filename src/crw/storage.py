"""SQLite reference adapter with atomic ingest and immutable content identity."""

from __future__ import annotations

from contextlib import contextmanager
import json
from pathlib import Path
import sqlite3
import uuid
from typing import Iterable, Iterator

from .contracts import ContractError, Customer, Transaction, identifier, utc
from .features import build_features, digest
from .policy import Policy
from .scoring import score

SCHEMA = """
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS metadata(key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS entities(customer_id TEXT PRIMARY KEY);
CREATE TABLE IF NOT EXISTS customers(
 customer_id TEXT NOT NULL REFERENCES entities(customer_id),
 as_of TEXT NOT NULL, available_at TEXT NOT NULL, content_hash TEXT NOT NULL, payload TEXT NOT NULL,
 PRIMARY KEY(customer_id,as_of));
CREATE INDEX IF NOT EXISTS snapshot_lookup ON customers(customer_id,as_of,available_at);
CREATE TABLE IF NOT EXISTS transactions(
 transaction_id TEXT PRIMARY KEY, customer_id TEXT NOT NULL REFERENCES entities(customer_id),
 occurred_at TEXT NOT NULL, available_at TEXT NOT NULL, content_hash TEXT NOT NULL, payload TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS event_lookup ON transactions(customer_id,occurred_at,available_at);
CREATE TABLE IF NOT EXISTS runs(
 run_id TEXT PRIMARY KEY, as_of TEXT NOT NULL, policy_hash TEXT NOT NULL, status TEXT NOT NULL,
 assessed INTEGER NOT NULL DEFAULT 0, failure TEXT);
CREATE TABLE IF NOT EXISTS assessments(
 assessment_hash TEXT PRIMARY KEY, customer_id TEXT NOT NULL, as_of TEXT NOT NULL,
 policy_hash TEXT NOT NULL, payload TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS run_assessments(
 run_id TEXT NOT NULL REFERENCES runs(run_id), assessment_hash TEXT NOT NULL REFERENCES assessments(assessment_hash),
 PRIMARY KEY(run_id,assessment_hash));
"""


def encode(value) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


class Store:
    def __init__(self, path: str | Path, base_unit: str = "SYNTHETIC_UNIT"):
        identifier(base_unit, "base_unit")
        self.path = str(path)
        self.db = sqlite3.connect(self.path)
        self.db.row_factory = sqlite3.Row
        self.db.executescript(SCHEMA)
        with self.db:
            self.db.execute("INSERT OR IGNORE INTO metadata VALUES ('schema_version','1')")
            self.db.execute("INSERT OR IGNORE INTO metadata VALUES ('base_unit',?)", (base_unit,))
        if self.db.execute("SELECT value FROM metadata WHERE key='base_unit'").fetchone()[0] != base_unit:
            self.db.close()
            raise ContractError("base unit mismatch; normalize amounts before ingestion")
        self.base_unit = base_unit

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.db.close()

    @contextmanager
    def atomic(self):
        try:
            self.db.execute("BEGIN IMMEDIATE")
            yield
            self.db.commit()
        except BaseException:
            self.db.rollback()
            raise

    @contextmanager
    def read_snapshot(self):
        owned = not self.db.in_transaction
        if owned:
            self.db.execute("BEGIN")
        try:
            yield
        except BaseException:
            if owned:
                self.db.rollback()
            raise
        else:
            if owned:
                self.db.commit()

    def ingest(self, customers: Iterable[Customer], transactions: Iterable[Transaction]) -> dict:
        counts = {
            "customers_inserted": 0,
            "customers_unchanged": 0,
            "transactions_inserted": 0,
            "transactions_unchanged": 0,
        }
        with self.atomic():
            for customer in customers:
                content = customer.to_dict()
                h = digest(content)
                existing = self.db.execute(
                    "SELECT content_hash FROM customers WHERE customer_id=? AND as_of=?",
                    (customer.customer_id, customer.as_of),
                ).fetchone()
                if existing:
                    if existing[0] != h:
                        raise ContractError(
                            "conflicting customer snapshot; preserve history with a new effective timestamp"
                        )
                    counts["customers_unchanged"] += 1
                    continue
                previous = self.db.execute(
                    "SELECT payload FROM customers WHERE customer_id=? ORDER BY as_of LIMIT 1",
                    (customer.customer_id,),
                ).fetchone()
                if previous is not None and json.loads(previous[0])["onboarded_at"] != customer.onboarded_at:
                    raise ContractError("onboarded_at is immutable across customer snapshots")
                self.db.execute("INSERT OR IGNORE INTO entities VALUES (?)", (customer.customer_id,))
                self.db.execute(
                    "INSERT INTO customers VALUES (?,?,?,?,?)",
                    (customer.customer_id, customer.as_of, customer.available_at, h, encode(content)),
                )
                counts["customers_inserted"] += 1
            for event in transactions:
                content = event.to_dict()
                h = digest(content)
                existing = self.db.execute(
                    "SELECT content_hash FROM transactions WHERE transaction_id=?", (event.transaction_id,)
                ).fetchone()
                if existing:
                    if existing[0] != h:
                        raise ContractError(
                            "conflicting transaction ID; mutation of an ingested event is forbidden"
                        )
                    counts["transactions_unchanged"] += 1
                    continue
                customer = self.db.execute(
                    "SELECT payload FROM customers WHERE customer_id=? ORDER BY as_of LIMIT 1",
                    (event.customer_id,),
                ).fetchone()
                if customer is None:
                    raise ContractError("orphan transaction")
                if event.occurred_at < json.loads(customer[0])["onboarded_at"]:
                    raise ContractError("transaction predates onboarding")
                self.db.execute(
                    "INSERT INTO transactions VALUES (?,?,?,?,?,?)",
                    (
                        event.transaction_id,
                        event.customer_id,
                        event.occurred_at,
                        event.available_at,
                        h,
                        encode(content),
                    ),
                )
                counts["transactions_inserted"] += 1
        return counts

    def customer(self, customer_id: str, as_of: str) -> Customer:
        cutoff = utc(as_of)
        row = self.db.execute(
            "SELECT payload FROM customers WHERE customer_id=? AND as_of<=? AND available_at<=? ORDER BY as_of DESC LIMIT 1",
            (customer_id, cutoff, cutoff),
        ).fetchone()
        if row is None:
            raise ContractError("no customer snapshot available at cutoff")
        return Customer.from_dict(json.loads(row[0]))

    def events(self, customer_id: str, as_of: str) -> Iterator[Transaction]:
        cutoff = utc(as_of)
        for row in self.db.execute(
            "SELECT payload FROM transactions WHERE customer_id=? AND occurred_at<=? AND available_at<=? ORDER BY occurred_at,transaction_id",
            (customer_id, cutoff, cutoff),
        ):
            yield Transaction.from_dict(json.loads(row[0]))

    def assess(self, customer_id: str, as_of: str, policy: Policy) -> dict:
        # Both queries must share one snapshot even when called outside a batch.
        with self.read_snapshot():
            customer = self.customer(customer_id, as_of)
            return score(
                build_features(customer, self.events(customer_id, as_of), as_of, base_unit=self.base_unit),
                policy,
                customer_id,
                as_of,
            )

    def score_batch(self, as_of: str, policy: Policy, chunk_size: int = 500) -> dict:
        if type(chunk_size) is not int or chunk_size < 1:
            raise ContractError("chunk_size must be a positive integer")
        cutoff = utc(as_of)
        run_id = uuid.uuid4().hex
        with self.db:
            self.db.execute(
                "INSERT INTO runs(run_id,as_of,policy_hash,status) VALUES (?,?,?,'running')",
                (run_id, cutoff, policy.digest),
            )
        n = 0
        last = ""
        try:
            # One transaction freezes the portfolio for the entire run. Chunking
            # bounds retrieval memory; it must not create moving input snapshots.
            with self.atomic():
                while True:
                    rows = self.db.execute(
                        "SELECT e.customer_id FROM entities e WHERE e.customer_id>? "
                        "AND EXISTS (SELECT 1 FROM customers c WHERE c.customer_id=e.customer_id "
                        "AND c.as_of<=? AND c.available_at<=?) ORDER BY e.customer_id LIMIT ?",
                        (last, cutoff, cutoff, chunk_size),
                    ).fetchall()
                    if not rows:
                        break
                    for row in rows:
                        result = self.assess(row[0], cutoff, policy)
                        self.db.execute(
                            "INSERT OR IGNORE INTO assessments VALUES (?,?,?,?,?)",
                            (result["assessment_hash"], row[0], cutoff, policy.digest, encode(result)),
                        )
                        self.db.execute(
                            "INSERT INTO run_assessments VALUES (?,?)", (run_id, result["assessment_hash"])
                        )
                        n += 1
                    self.db.execute("UPDATE runs SET assessed=? WHERE run_id=?", (n, run_id))
                    last = rows[-1][0]
                if n == 0:
                    raise ContractError("no eligible customer population at the assessment cutoff")
                self.db.execute("UPDATE runs SET status='complete' WHERE run_id=?", (run_id,))
        except BaseException as exc:
            with self.db:
                self.db.execute(
                    "UPDATE runs SET status='failed',failure=? WHERE run_id=?", (type(exc).__name__, run_id)
                )
            raise
        return dict(self.db.execute("SELECT * FROM runs WHERE run_id=?", (run_id,)).fetchone())

    def results(self, run_id: str) -> Iterator[dict]:
        row = self.db.execute("SELECT status FROM runs WHERE run_id=?", (run_id,)).fetchone()
        if row is None or row[0] != "complete":
            raise ContractError("only complete runs may be exported")
        for result in self.db.execute(
            "SELECT a.payload FROM assessments a JOIN run_assessments r USING(assessment_hash) WHERE r.run_id=? ORDER BY a.customer_id",
            (run_id,),
        ):
            yield json.loads(result[0])

    def counts(self) -> dict:
        return {
            table: self.db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in ("entities", "customers", "transactions", "assessments", "runs")
        }
