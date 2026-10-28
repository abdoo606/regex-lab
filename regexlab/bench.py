"""Micro-benchmarking with stdlib only (time.perf_counter)."""

from __future__ import annotations

import re
import time
from dataclasses import dataclass

from .engine import compile_pattern


@dataclass(slots=True, frozen=True)
class Benchmark:
    expression: str
    subject_length: int
    runs: int
    best_us: float
    mean_us: float

    def __str__(self) -> str:
        return (
            f"{self.expression:<40} n={self.subject_length:<7} "
            f"best={self.best_us:8.2f}us mean={self.mean_us:8.2f}us"
        )


def benchmark(expression: str, subject: str, *, runs: int = 50) -> Benchmark:
    pattern = compile_pattern(expression)
    pattern.search(subject)  # warm the regex cache before timing
    samples: list[float] = []
    for _ in range(max(runs, 1)):
        start = time.perf_counter()
        pattern.search(subject)
        samples.append((time.perf_counter() - start) * 1_000_000)
    return Benchmark(expression, len(subject), runs, min(samples), sum(samples) / len(samples))


def compare(expressions: dict[str, str], subject: str, *, runs: int = 50) -> list[Benchmark]:
    results = [benchmark(expr, subject, runs=runs) for expr in expressions.values()]
    return sorted(results, key=lambda b: b.mean_us)


def scales_linearly(expression: str, make_subject, sizes=(200, 400, 800, 1600)) -> bool:
    """A safe regex grows roughly linearly; catastrophic backtracking explodes."""
    timings = [benchmark(expression, make_subject(n), runs=5).mean_us for n in sizes]
    return timings[-1] < timings[0] * 12
