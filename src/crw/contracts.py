"""Strict, time-aware contracts for normalized, non-identifying research records."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import math
import re
from typing import Any


class ContractError(ValueError):
    """Input cannot be interpreted without an unsafe assumption."""


def timestamp(value: str) -> datetime:
    if not isinstance(value, str):
        raise ContractError("timestamp must be a string with an explicit timezone")
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ContractError(f"invalid timestamp: {value!r}") from exc
    if result.tzinfo is None or result.utcoffset() is None:
        raise ContractError("naive timestamps are forbidden")
    return result.astimezone(timezone.utc)


def utc(value: str) -> str:
    return timestamp(value).isoformat(timespec="microseconds").replace("+00:00", "Z")


def number(value: Any, name: str, minimum: float = 0, maximum: float | None = None) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ContractError(f"{name} must be a finite number, not a boolean")
    if value < minimum or (maximum is not None and value > maximum):
        raise ContractError(f"{name} outside [{minimum}, {maximum}]")
    return float(value)


def identifier(value: Any, name: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_.:-]{1,128}", value):
        raise ContractError(f"{name} must be an opaque identifier of 1-128 safe characters")
    return value


def strict_fields(record: dict, allowed: set[str], required: set[str]) -> None:
    if not isinstance(record, dict):
        raise ContractError("record must be an object")
    if set(record) - allowed:
        raise ContractError(f"unknown fields: {sorted(set(record) - allowed)}")
    if required - set(record):
        raise ContractError(f"missing fields: {sorted(required - set(record))}")


@dataclass(frozen=True)
class Customer:
    customer_id: str
    as_of: str
    available_at: str
    segment: str
    onboarded_at: str
    profile: dict[str, float | None]
    expected_monthly_volume: float | None
    source_id: str
    history_start: str
    history_complete: bool

    def __post_init__(self):
        for name in ("customer_id", "segment", "source_id"):
            identifier(getattr(self, name), name)
        for name in ("as_of", "available_at", "onboarded_at", "history_start"):
            object.__setattr__(self, name, utc(getattr(self, name)))
        if timestamp(self.as_of) < timestamp(self.onboarded_at):
            raise ContractError("profile predates onboarding")
        if timestamp(self.available_at) < timestamp(self.as_of):
            raise ContractError("profile available before its effective timestamp")
        if not timestamp(self.onboarded_at) <= timestamp(self.history_start) <= timestamp(self.as_of):
            raise ContractError("history_start must be between onboarding and profile as_of")
        if type(self.history_complete) is not bool:
            raise ContractError("history_complete must be explicit boolean")
        if self.expected_monthly_volume is not None:
            object.__setattr__(
                self,
                "expected_monthly_volume",
                number(self.expected_monthly_volume, "expected_monthly_volume"),
            )
        if not isinstance(self.profile, dict):
            raise ContractError("profile must be an object")
        for key, value in self.profile.items():
            identifier(key, "profile key")
            if value is not None:
                number(value, key, maximum=1)
        object.__setattr__(
            self,
            "profile",
            {key: float(value) if value is not None else None for key, value in self.profile.items()},
        )

    @classmethod
    def from_dict(cls, record: dict) -> Customer:
        fields = set(cls.__dataclass_fields__)
        strict_fields(record, fields, fields)
        return cls(**record)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class Transaction:
    transaction_id: str
    customer_id: str
    occurred_at: str
    available_at: str
    amount: float
    direction: str
    counterparty_id: str
    channel: str
    jurisdiction_risk: float | None
    source_id: str

    def __post_init__(self):
        for name in ("transaction_id", "customer_id", "counterparty_id", "source_id"):
            identifier(getattr(self, name), name)
        for name in ("occurred_at", "available_at"):
            object.__setattr__(self, name, utc(getattr(self, name)))
        if timestamp(self.available_at) < timestamp(self.occurred_at):
            raise ContractError("transaction available before it occurred")
        object.__setattr__(self, "amount", number(self.amount, "amount"))
        if self.direction not in {"in", "out"}:
            raise ContractError("direction must be in or out")
        if self.channel not in {"wire", "cash", "card", "digital", "other"}:
            raise ContractError("unknown channel")
        if self.jurisdiction_risk is not None:
            object.__setattr__(
                self, "jurisdiction_risk", number(self.jurisdiction_risk, "jurisdiction_risk", maximum=1)
            )

    @classmethod
    def from_dict(cls, record: dict) -> Transaction:
        fields = set(cls.__dataclass_fields__)
        strict_fields(record, fields, fields)
        return cls(**record)

    def to_dict(self) -> dict:
        return asdict(self)
