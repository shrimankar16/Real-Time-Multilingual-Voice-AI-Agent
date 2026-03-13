"""Latency tracker for measuring pipeline stage durations."""
import time
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class LatencyTracker:
    """Records start/stop timestamps for named pipeline stages and reports durations."""

    _starts: dict[str, float] = field(default_factory=dict)
    _durations: dict[str, float] = field(default_factory=dict)

    def start(self, label: str) -> None:
        """Mark the start of a pipeline stage."""
        self._starts[label] = time.perf_counter()

    def stop(self, label: str) -> None:
        """Mark the end of a pipeline stage and compute duration in milliseconds."""
        if label in self._starts:
            elapsed = (time.perf_counter() - self._starts[label]) * 1000
            self._durations[label] = round(elapsed, 2)
            logger.info("⏱ %s: %.2f ms", label, elapsed)

    def report(self) -> dict[str, float]:
        """Return all recorded durations plus a computed total."""
        total = sum(self._durations.values())
        return {**self._durations, "total_ms": round(total, 2)}
