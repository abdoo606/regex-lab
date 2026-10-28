"""A small, reviewed catalogue of the patterns people get wrong."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class Pattern:
    name: str
    expression: str
    description: str

    def compile(self, flags: int = 0) -> re.Pattern[str]:
        return re.compile(self.expression, flags)


CATALOGUE: dict[str, Pattern] = {
    "email": Pattern(
        "email",
        r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}$",
        "Pragmatic email check - deliberately not RFC 5322 complete.",
    ),
    "ipv4": Pattern(
        "ipv4",
        r"^(?:(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)\.){3}(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)$",
        "Validates each octet is 0-255 instead of the naive \\d{1,3}.",
    ),
    "date_iso": Pattern(
        "date_iso",
        r"^(\d{4})-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])$",
        "ISO date with captured year/month/day.",
    ),
    "time_hhmm": Pattern("time_hhmm", r"^([01]\d|2[0-3]):[0-5]\d$", "24-hour clock."),
    "uuid4": Pattern(
        "uuid4",
        r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
        "Only version 4 UUIDs (the version nibble is pinned).",
    ),
    "semver": Pattern(
        "semver",
        r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-[\da-zA-Z.-]+)?(?:\+[\da-zA-Z.-]+)?$",
        "Semantic versioning 2.0.0.",
    ),
    "arabic_word": Pattern("arabic_word", r"^[\u0600-\u06FF\s]+$", "Arabic letters and spaces only."),
}


def validate(name: str, value: str) -> bool:
    pattern = CATALOGUE.get(name)
    if pattern is None:
        raise KeyError(f"unknown pattern {name!r}; available: {', '.join(sorted(CATALOGUE))}")
    return pattern.compile().match(value) is not None
