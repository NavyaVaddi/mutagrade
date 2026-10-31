"""Run a test suite against every mutant and score how many it catches."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

from .mutators import Mutant, generate_mutants


class BaselineError(RuntimeError):
    """The tests do not pass on the original, unmodified code."""


@dataclass
class MutantResult:
    mutant: Mutant
    status: str  # "killed" | "survived" | "timeout"


@dataclass
class GradeReport:
    target: str
    tests: str
    results: list[MutantResult]

    @property
    def total(self) -> int:
        return len(self.results)

    @property
    def killed(self) -> int:
        # A timeout means the mutant caused an infinite loop, so the tests noticed it.
        return sum(r.status in ("killed", "timeout") for r in self.results)

    @property
    def survivors(self) -> list[MutantResult]:
        return [r for r in self.results if r.status == "survived"]

    @property
    def score(self) -> float:
        return 100.0 * self.killed / self.total if self.total else 100.0

    @property
    def rating(self) -> str:
        return "strong" if self.score >= 80 else "moderate" if self.score >= 60 else "weak"

    def by_operator(self) -> dict[str, tuple[int, int]]:
        stats: dict[str, list[int]] = defaultdict(lambda: [0, 0])
        for r in self.results:
            stats[r.mutant.operator][1] += 1
            stats[r.mutant.operator][0] += r.status != "survived"
        return {k: (v[0], v[1]) for k, v in sorted(stats.items())}


def _run_tests(source: str, target_name: str, tests_path: str, timeout: float) -> str:
    """Run the test file against `source` in a throwaway directory. Returns pass | fail | timeout."""
    with tempfile.TemporaryDirectory() as d:
        (Path(d) / target_name).write_text(source)
        shutil.copy(tests_path, Path(d) / Path(tests_path).name)
        env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
        try:
            proc = subprocess.run(
                [sys.executable, "-m", "pytest", "-x", "-q", "-p", "no:cacheprovider", Path(tests_path).name],
                cwd=d, capture_output=True, text=True, timeout=timeout, env=env,
            )
        except subprocess.TimeoutExpired:
            return "timeout"
        return "pass" if proc.returncode == 0 else "fail"


def grade(target: str, tests: str, timeout: float = 10.0, jobs: int = 4,
          max_mutants: int | None = None) -> GradeReport:
    source = Path(target).read_text()
    name = Path(target).name

    if _run_tests(source, name, tests, timeout) != "pass":
        raise BaselineError(f"{tests} does not pass on the original {target}; fix the tests first.")

    mutants = generate_mutants(source)
    if max_mutants:
        mutants = mutants[:max_mutants]

    def work(m: Mutant) -> MutantResult:
        outcome = _run_tests(m.source, name, tests, timeout)
        return MutantResult(m, {"pass": "survived", "fail": "killed", "timeout": "timeout"}[outcome])

    with ThreadPoolExecutor(max_workers=max(1, jobs)) as pool:
        results = list(pool.map(work, mutants))
    return GradeReport(target, tests, results)
