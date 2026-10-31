"""Command line: mutagrade <target.py> <tests.py>"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .grader import BaselineError, grade
from .report import to_html, to_json, to_text


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="mutagrade", description="Grade a test suite by mutating the code under test.")
    p.add_argument("target", help="Python module under test")
    p.add_argument("tests", help="pytest file that tests the module")
    p.add_argument("--jobs", type=int, default=4, help="parallel mutant runs (default 4)")
    p.add_argument("--timeout", type=float, default=10.0, help="seconds per test run (default 10)")
    p.add_argument("--max-mutants", type=int, default=None, help="only try the first N mutants")
    p.add_argument("--json", action="store_true", help="print JSON instead of text")
    p.add_argument("--html", metavar="PATH", help="also write an HTML report")
    p.add_argument("--min-score", type=float, default=0.0, help="exit with code 1 if score is below this (for CI)")
    args = p.parse_args(argv)

    try:
        rep = grade(args.target, args.tests, args.timeout, args.jobs, args.max_mutants)
    except BaselineError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print(to_json(rep) if args.json else to_text(rep))
    if args.html:
        Path(args.html).write_text(to_html(rep))
    return 1 if rep.score < args.min_score else 0


if __name__ == "__main__":
    raise SystemExit(main())
