"""Compile, match and explain patterns - with a static safety audit."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# Two shapes account for nearly every ReDoS bug in the wild.
NESTED_QUANTIFIER = re.compile(r"\((?:[^()]*[+*][^()]*)\)\s*[+*]")
OVERLAPPING_ALTERNATION = re.compile(r"\([^()]*\|[^()]*\)\s*[+*]")


@dataclass(slots=True, frozen=True)
class Match:
    text: str
    start: int
    end: int
    groups: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True, frozen=True)
class AuditFinding:
    severity: str
    message: str


def compile_pattern(expression: str, flags: int = 0) -> re.Pattern[str]:
    try:
        return re.compile(expression, flags)
    except re.error as exc:
        raise ValueError(f"invalid regular expression: {exc}") from exc


def find_all(pattern: re.Pattern[str], text: str) -> list[Match]:
    results = []
    for m in pattern.finditer(text):
        groups = {k: v for k, v in m.groupdict().items() if v is not None}
        results.append(Match(m.group(0), m.start(), m.end(), groups))
    return results


def replace_all(pattern: re.Pattern[str], text: str, replacement: str) -> tuple[str, int]:
    """Unlike re.subn this reports how many replacements happened, not how many groups changed."""
    count = len(pattern.findall(text))
    return pattern.sub(replacement, text), count


def audit(expression: str) -> list[AuditFinding]:
    """Cheap static checks for the two classic causes of catastrophic backtracking."""
    findings: list[AuditFinding] = []
    if NESTED_QUANTIFIER.search(expression):
        findings.append(AuditFinding("high", "nested quantifier such as (a+)+ can backtrack exponentially"))
    if OVERLAPPING_ALTERNATION.search(expression):
        findings.append(AuditFinding("high", "overlapping alternation under a quantifier is ambiguous"))
    if expression.count(".*") > 1:
        findings.append(AuditFinding("medium", "multiple .* makes matching O(n^2) on long input"))
    if re.search(r"\\[1-9]", expression):
        findings.append(AuditFinding("low", "backreference disables linear-time matching"))
    if not findings:
        findings.append(AuditFinding("ok", "no obvious backtracking hazards"))
    return findings


def explain(expression: str) -> list[str]:
    """Very small token-level explainer - enough to read someone else's regex."""
    tokens = re.findall(
        r"\\[dwsSbB]|\\\w|\[\^?[^\]]+\]|\(\?:|\(\?P<\w+>|[()|]|[+*?]\??|\{\d+(?:,\d*)?\}|.", expression
    )
    meanings = {
        r"\d": "a digit 0-9",
        r"\w": "a word character (letter, digit or _)",
        r"\s": "whitespace",
        r"\S": "a non-whitespace character",
        r"\b": "a word boundary",
        "*": "zero or more of the previous token",
        "+": "one or more of the previous token",
        "?": "zero or one, or makes the previous quantifier lazy",
        ".": "any character except newline",
        "^": "start of line/string",
        "$": "end of line/string",
        "|": "alternation - either side",
        "(?:": "start of a non-capturing group",
        "(": "start of a capturing group",
        ")": "end of a group",
    }
    out: list[str] = []
    for token in tokens:
        if token in meanings:
            out.append(f"{token!r:>10} -> {meanings[token]}")
        elif token.startswith("["):
            out.append(f"{token!r:>10} -> a character class (any single char listed)")
        elif token.startswith("{"):
            out.append(f"{token!r:>10} -> a repetition count")
        else:
            out.append(f"{token!r:>10} -> the literal character")
    return out
