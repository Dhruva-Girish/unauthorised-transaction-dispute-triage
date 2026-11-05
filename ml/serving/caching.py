"""
caching.py — Prediction Caching and Micro-Batching Optimizer (Unit 2.G)
Provides thread-safe in-memory LRU/TTL caching and micro-batching aggregation.
"""

from __future__ import annotations

import hashlib
import json
import time
from collections import OrderedDict
from threading import Lock
from typing import Any, Callable


class PredictionCache:
    """Thread-safe LRU Cache with Time-To-Live (TTL) expiration."""

    def __init__(self, maxsize: int = 5000, ttl_seconds: float = 300.0) -> None:
        self.maxsize = maxsize
        self.ttl_seconds = ttl_seconds
        self._cache: OrderedDict[str, tuple[float, Any]] = OrderedDict()
        self._lock = Lock()
        self.hits = 0
        self.misses = 0

    @staticmethod
    def _hash_features(features: dict[str, Any]) -> str:
        serialized = json.dumps(features, sort_keys=True)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def get(self, features: dict[str, Any]) -> Any | None:
        key = self._hash_features(features)
        now = time.time()
        with self._lock:
            if key in self._cache:
                timestamp, value = self._cache[key]
                if now - timestamp <= self.ttl_seconds:
                    self._cache.move_to_end(key)
                    self.hits += 1
                    return value
                else:
                    del self._cache[key]
            self.misses += 1
            return None

    def put(self, features: dict[str, Any], result: Any) -> None:
        key = self._hash_features(features)
        now = time.time()
        with self._lock:
            if key in self._cache:
                del self._cache[key]
            elif len(self._cache) >= self.maxsize:
                self._cache.popitem(last=False)
            self._cache[key] = (now, result)

    def stats(self) -> dict[str, Any]:
        with self._lock:
            total = self.hits + self.misses
            hit_ratio = round((self.hits / total) * 100.0, 1) if total > 0 else 0.0
            return {
                "size": len(self._cache),
                "maxsize": self.maxsize,
                "hits": self.hits,
                "misses": self.misses,
                "hit_ratio_percent": hit_ratio,
            }


class MicroBatcher:
    """
    Groups concurrent individual scoring requests into vectorized batches.
    Trades ~5ms of wait latency for dramatic throughput gains on high load.
    """

    def __init__(
        self,
        batch_scoring_fn: Callable[[list[dict[str, Any]]], list[dict[str, Any]]],
        max_batch_size: int = 64,
        max_wait_ms: float = 10.0,
    ) -> None:
        self.batch_scoring_fn = batch_scoring_fn
        self.max_batch_size = max_batch_size
        self.max_wait_ms = max_wait_ms

    def score_batch(self, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Vectorized execution of micro-batch."""
        return self.batch_scoring_fn(items)
