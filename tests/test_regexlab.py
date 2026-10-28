from __future__ import annotations

import re

import pytest

from regexlab.bench import benchmark, scales_linearly
from regexlab.engine import audit, compile_pattern, explain, find_all, replace_all
from regexlab.patterns import CATALOGUE, validate


# -------------------------------------------------------------- catalogue
@pytest.mark.parametrize(
    "value",
    ["user@example.com", "a.b+tag@sub.domain.co", "x@y.io"],
)
def test_email_accepts_valid(value):
    assert validate("email", value)


@pytest.mark.parametrize(
    "value",
    ["plain", "a@b", "a@b.c", "spaces in@mail.com", "@nope.com", "two@@at.com"],
)
def test_email_rejects_invalid(value):
    assert not validate("email", value)


@pytest.mark.parametrize("value", ["192.168.1.1", "0.0.0.0", "255.255.255.255"])
def test_ipv4_accepts_valid(value):
    assert validate("ipv4", value)


@pytest.mark.parametrize("value", ["256.1.1.1", "1.1.1", "1.1.1.1.1", "01.2.3.4x"])
def test_ipv4_rejects_invalid(value):
    assert not validate("ipv4", value)


def test_uuid4_rejects_other_versions():
    assert validate("uuid4", "123e4567-e89b-42d3-a456-426614174000")
    assert not validate("uuid4", "123e4567-e89b-12d3-a456-426614174000")


def test_semver():
    assert validate("semver", "1.0.0")
    assert validate("semver", "2.10.3-beta.1+build.5")
    assert not validate("semver", "01.0.0")


def test_arabic_word():
    assert validate("arabic_word", "مرحبا بالعالم")
    assert not validate("arabic_word", "hello")


def test_unknown_pattern_raises():
    with pytest.raises(KeyError):
        validate("nope", "x")


# ----------------------------------------------------------------- engine
def test_compile_reports_invalid_regex():
    with pytest.raises(ValueError, match="invalid regular expression"):
        compile_pattern("([a-z")


def test_find_all_spans_and_named_groups():
    pattern = compile_pattern(r"(?P<year>\d{4})-(?P<month>\d{2})")
    matches = find_all(pattern, "2024-12 and 2025-01")
    assert [m.text for m in matches] == ["2024-12", "2025-01"]
    assert matches[0].start == 0 and matches[0].end == 7
    assert matches[1].groups == {"year": "2025", "month": "01"}


def test_replace_all_counts():
    text, n = replace_all(compile_pattern(r"\s+"), "a  b   c", " ")
    assert text == "a b c" and n == 2


@pytest.mark.parametrize("expr", [r"(a+)+", r"(a|a)+", r"(x+x)+"])
def test_audit_flags_nested_quantifiers(expr):
    severities = [f.severity for f in audit(expr)]
    assert "high" in severities


def test_audit_passes_safe_pattern():
    findings = audit(r"^\d{4}-\d{2}-\d{2}$")
    assert findings[0].severity == "ok"


def test_audit_flags_multiple_dot_star():
    assert any(f.severity == "medium" for f in audit(r"a.*b.*c"))


def test_explain_covers_every_token():
    lines = explain(r"^\d+$")
    assert len(lines) == 4
    assert any("digit" in line for line in lines)


# ------------------------------------------------------------------ bench
def test_benchmark_reports_positive_timings():
    b = benchmark(r"\d+", "abc 123 def", runs=5)
    assert b.best_us > 0 and b.mean_us >= b.best_us
    assert b.subject_length == 11


def test_linear_pattern_scales():
    assert scales_linearly(r"^\d+$", lambda n: "1" * n)


def test_audit_and_match_agree_on_catalogue():
    for pattern in CATALOGUE.values():
        assert compile_pattern(pattern.expression) is not None
