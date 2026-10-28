from __future__ import annotations

import argparse
import json
import re

from .bench import benchmark
from .engine import audit, compile_pattern, explain, find_all
from .patterns import CATALOGUE


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="regexlab", description="Test and audit regular expressions.")
    sub = p.add_subparsers(dest="command", required=True)

    m = sub.add_parser("match", help="find matches in a sample text")
    m.add_argument("pattern")
    m.add_argument("text")
    m.add_argument("-i", "--ignore-case", action="store_true")

    sub.add_parser("check", help="validate against the built-in catalogue")
    c = sub.add_parser("validate", help="validate a value against a named pattern")
    c.add_argument("name")
    c.add_argument("value")
    sub.add_parser("list", help="list catalogue entries")

    a = sub.add_parser("audit", help="detect catastrophic backtracking risks")
    a.add_argument("pattern")

    e = sub.add_parser("explain", help="explain a pattern token by token")
    e.add_argument("pattern")

    b = sub.add_parser("bench", help="micro-benchmark a pattern")
    b.add_argument("pattern")
    b.add_argument("-n", type=int, default=100, help="length of the generated subject")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.command == "list":
        for name, p in sorted(CATALOGUE.items()):
            print(f"{name:<12} {p.expression}\n{'':<12} {p.description}")
        return 0

    if args.command == "validate":
        from .patterns import validate

        try:
            ok = validate(args.name, args.value)
        except KeyError as exc:
            print(exc.args[0])
            return 2
        print("valid" if ok else "invalid")
        return 0 if ok else 1

    if args.command == "match":
        flags = re.IGNORECASE if args.ignore_case else 0
        try:
            pattern = compile_pattern(args.pattern, flags)
        except ValueError as exc:
            print(f"error: {exc}")
            return 2
        matches = find_all(pattern, args.text)
        print(json.dumps([{"text": m.text, "span": [m.start, m.end], "groups": m.groups} for m in matches], indent=2))
        return 0

    if args.command == "audit":
        for finding in audit(args.pattern):
            print(f"[{finding.severity}] {finding.message}")
        return 0

    if args.command == "explain":
        print("\n".join(explain(args.pattern)))
        return 0

    if args.command == "bench":
        subject = ("a1b2-c3d4 " * (args.n // 9 + 1))[: args.n]
        print(benchmark(args.pattern, subject, runs=100))
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
