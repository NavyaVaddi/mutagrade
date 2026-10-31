"""Render a GradeReport as text, JSON, or a self-contained HTML page."""
from __future__ import annotations

import html
import json

from .grader import GradeReport
from .mutators import HINTS


def to_text(rep: GradeReport) -> str:
    out = [f"mutagrade: {rep.target} vs {rep.tests}",
           f"Mutation score: {rep.score:.1f}% ({rep.rating})  -  {rep.killed} of {rep.total} mutants caught", "",
           "By operator:"]
    for op, (k, t) in rep.by_operator().items():
        out.append(f"  {op:<18} {k}/{t}")
    if rep.survivors:
        out += ["", "Survived (your tests did not notice these changes):"]
        for r in rep.survivors:
            m = r.mutant
            out += [f"  #{m.id} line {m.lineno} [{m.operator}] {m.description}",
                    f"      {m.before}   ->   {m.after}",
                    f"      hint: {HINTS[m.operator]}"]
        out += ["", "Note: some survivors may be equivalent mutants (the change cannot alter behavior)."]
    else:
        out += ["", "No survivors: every injected bug was caught."]
    return "\n".join(out)


def to_json(rep: GradeReport) -> str:
    return json.dumps({
        "target": rep.target, "tests": rep.tests, "score": round(rep.score, 2),
        "rating": rep.rating, "killed": rep.killed, "total": rep.total,
        "survivors": [{"id": r.mutant.id, "line": r.mutant.lineno, "operator": r.mutant.operator,
                       "change": r.mutant.description, "before": r.mutant.before, "after": r.mutant.after,
                       "hint": HINTS[r.mutant.operator]} for r in rep.survivors],
    }, indent=2)


def to_html(rep: GradeReport) -> str:
    e = html.escape
    color = {"strong": "#1a7f37", "moderate": "#9a6700", "weak": "#cf222e"}[rep.rating]
    rows = "".join(
        f"<tr><td>#{r.mutant.id}</td><td>{r.mutant.lineno}</td><td>{e(r.mutant.operator)}</td>"
        f"<td><code>{e(r.mutant.before)}</code><br>&rarr; <code>{e(r.mutant.after)}</code></td>"
        f"<td>{e(HINTS[r.mutant.operator])}</td></tr>" for r in rep.survivors
    ) or '<tr><td colspan="5">No survivors: every injected bug was caught.</td></tr>'
    ops = "".join(f"<li>{e(op)}: {k}/{t}</li>" for op, (k, t) in rep.by_operator().items())
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<title>mutagrade report</title>
<style>body{{font:16px system-ui,sans-serif;max-width:900px;margin:2rem auto;padding:0 1rem;color:#1f2328}}
.score{{font-size:3rem;font-weight:700;color:{color}}}table{{border-collapse:collapse;width:100%}}
td,th{{border:1px solid #d0d7de;padding:.5rem;text-align:left;vertical-align:top}}th{{background:#f6f8fa}}
code{{background:#f6f8fa;padding:.1rem .3rem;border-radius:4px}}</style></head><body>
<h1>mutagrade report</h1><p>{e(rep.target)} vs {e(rep.tests)}</p>
<div class="score">{rep.score:.1f}%</div><p>{e(rep.rating)} &middot; {rep.killed} of {rep.total} mutants caught</p>
<h2>By operator</h2><ul>{ops}</ul>
<h2>Survivors</h2><table><tr><th>ID</th><th>Line</th><th>Operator</th><th>Change</th><th>Hint</th></tr>{rows}</table>
</body></html>"""
