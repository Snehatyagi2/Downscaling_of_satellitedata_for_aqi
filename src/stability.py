"""Utilities for deterministic, time-bucketed randomness."""

from __future__ import annotations

import hashlib
import time


def city_hour_bucket(city: str, bucket_seconds: int = 1800) -> int:
    """Return a coarse time bucket for the current wall clock."""
    return int(time.time() // bucket_seconds)


def stable_seed(city: str, bucket_seconds: int = 1800, salt: str = "") -> int:
    """Build a deterministic seed for a city within a time bucket."""
    city_key = city.lower().strip()
    bucket = city_hour_bucket(city_key, bucket_seconds)
    payload = f"{city_key}|{bucket}|{salt}".encode("utf-8")
    digest = hashlib.sha256(payload).hexdigest()
    return int(digest[:16], 16)
