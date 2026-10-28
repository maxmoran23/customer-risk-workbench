"""Streaming adapters and atomic artifacts, with explicit import diagnostics."""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path
import tempfile
from typing import Iterable

from .contracts import ContractError, Customer, Transaction


def read_jsonl(path: str | Path, kind: type):
    with Path(path).open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
                yield kind.from_dict(record)
            except (ValueError, TypeError) as exc:
                raise ContractError(f"{Path(path).name}, line {line_number}: {exc}") from exc


def atomic_json(path: str | Path, value) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(value, stream, sort_keys=True, indent=2, allow_nan=False)
            stream.write("\n")
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def write_jsonl(path: str | Path, rows: Iterable) -> int:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    n = 0
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            for row in rows:
                data = row.to_dict() if hasattr(row, "to_dict") else row
                stream.write(json.dumps(data, sort_keys=True, allow_nan=False) + "\n")
                n += 1
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return n


def csv_transactions(path: str | Path):
    """Strict transaction CSV; blank jurisdiction risk is unknown, never zero."""
    with Path(path).open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        expected = set(Transaction.__dataclass_fields__)
        if (
            reader.fieldnames is None
            or len(reader.fieldnames) != len(set(reader.fieldnames))
            or set(reader.fieldnames) != expected
        ):
            raise ContractError("CSV headers must exactly match the Transaction contract")
        for line, row in enumerate(reader, 2):
            try:
                row["amount"] = float(row["amount"])
                row["jurisdiction_risk"] = (
                    float(row["jurisdiction_risk"]) if row["jurisdiction_risk"] != "" else None
                )
                yield Transaction.from_dict(row)
            except (ValueError, TypeError) as exc:
                raise ContractError(f"transaction CSV line {line}: {exc}") from exc


def json_schema(kind: type) -> dict:
    if kind not in {Customer, Transaction}:
        raise ValueError("unsupported schema")
    fields = kind.__dataclass_fields__
    properties = {name: {"type": "string"} for name in fields}
    for name in ("as_of", "available_at", "onboarded_at", "history_start", "occurred_at"):
        if name in fields:
            properties[name] = {
                "type": "string",
                "format": "date-time",
                "description": "Explicit timezone required; canonicalized to UTC.",
            }
    if kind is Customer:
        properties["profile"] = {
            "type": "object",
            "additionalProperties": {"type": ["number", "null"], "minimum": 0, "maximum": 1},
        }
        properties["expected_monthly_volume"] = {"type": ["number", "null"], "minimum": 0}
        properties["history_complete"] = {"type": "boolean"}
    else:
        properties["amount"] = {"type": "number", "minimum": 0}
        properties["jurisdiction_risk"] = {"type": ["number", "null"], "minimum": 0, "maximum": 1}
        properties["direction"] = {"enum": ["in", "out"]}
        properties["channel"] = {"enum": ["wire", "cash", "card", "digital", "other"]}
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": kind.__name__,
        "type": "object",
        "required": list(fields),
        "additionalProperties": False,
        "properties": properties,
        "$comment": "Python contract additionally enforces cross-field chronology, finite numbers and opaque identifier format.",
    }
