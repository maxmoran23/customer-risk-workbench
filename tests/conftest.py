from datetime import datetime, timedelta, timezone
import pytest

from crw.contracts import Customer, Transaction
from crw.policy import PROFILE_KEYS, reference_policy

CUTOFF = "2026-10-01T00:00:00Z"


@pytest.fixture
def customer():
    return Customer(
        "SYN-1",
        "2026-09-01T00:00:00Z",
        "2026-09-01T00:00:00Z",
        "retail",
        "2025-01-01T00:00:00Z",
        {key: 0.1 for key in PROFILE_KEYS},
        10000,
        "synthetic",
        "2025-01-01T00:00:00Z",
        True,
    )


@pytest.fixture
def events():
    end = datetime(2026, 10, 1, tzinfo=timezone.utc)
    return [
        Transaction(
            f"T-{i}",
            "SYN-1",
            (end - timedelta(hours=12 + i * 12)).isoformat(),
            (end - timedelta(hours=12 + i * 12)).isoformat(),
            100,
            "in",
            f"P-{i % 8}",
            "wire",
            0.1,
            "synthetic",
        )
        for i in range(140)
    ]


@pytest.fixture
def policy():
    return reference_policy()
