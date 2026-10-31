from pathlib import Path

import pytest

from mutagrade.cli import main
from mutagrade.grader import BaselineError, grade

EX = Path(__file__).parent.parent / "examples"
TARGET = str(EX / "pricing.py")


def test_strong_tests_outscore_weak_tests():
    weak = grade(TARGET, str(EX / "test_pricing_weak.py"))
    strong = grade(TARGET, str(EX / "test_pricing_strong.py"))
    assert weak.score < 60 < 80 <= strong.score
    assert weak.rating == "weak" and strong.rating == "strong"
    assert len(weak.survivors) > len(strong.survivors)


def test_failing_baseline_is_rejected(tmp_path):
    bad = tmp_path / "test_bad.py"
    bad.write_text("from pricing import clamp\n\ndef test_wrong():\n    assert clamp(5, 0, 10) == 99\n")
    with pytest.raises(BaselineError):
        grade(TARGET, str(bad))


def test_cli_min_score_gate_and_html(tmp_path):
    out = tmp_path / "r.html"
    weak = main([TARGET, str(EX / "test_pricing_weak.py"), "--min-score", "80", "--html", str(out)])
    strong = main([TARGET, str(EX / "test_pricing_strong.py"), "--min-score", "80"])
    assert weak == 1 and strong == 0
    assert "mutagrade report" in out.read_text()
