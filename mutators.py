"""AST mutation operators and mutant generation.

Each operator describes one small, plausible bug (an off-by-one, a flipped
operator, a dropped return value). A mutant is the original source with exactly
one such bug injected.
"""
from __future__ import annotations

import ast
import copy
import difflib
from dataclasses import dataclass
from typing import Callable, Iterator

COMPARE_SWAPS = {
    ast.Lt: ast.LtE, ast.LtE: ast.Lt, ast.Gt: ast.GtE,
    ast.GtE: ast.Gt, ast.Eq: ast.NotEq, ast.NotEq: ast.Eq,
}
BINOP_SWAPS = {
    ast.Add: ast.Sub, ast.Sub: ast.Add, ast.Mult: ast.Add,
    ast.Div: ast.Mult, ast.FloorDiv: ast.Mult, ast.Mod: ast.Mult,
}
SYM = {
    ast.Lt: "<", ast.LtE: "<=", ast.Gt: ">", ast.GtE: ">=", ast.Eq: "==", ast.NotEq: "!=",
    ast.Add: "+", ast.Sub: "-", ast.Mult: "*", ast.Div: "/", ast.FloorDiv: "//", ast.Mod: "%",
    ast.And: "and", ast.Or: "or",
}

# Advice shown for a surviving mutant, by operator.
HINTS = {
    "compare": "Add a test exactly on the boundary value (and one on each side of it).",
    "arithmetic": "Assert an exact result using operands where + / - / * / // / % give different answers.",
    "boolean": "Add a case where exactly one of the combined conditions is true.",
    "constant": "Pin down the exact constant: check the off-by-one value around it.",
    "negate_condition": "Cover both branches of this condition with distinct expected results.",
    "return_value": "Assert on the returned value itself, not just that the call does not fail.",
}


@dataclass
class Mutation:
    operator: str
    description: str
    apply: Callable[[ast.AST], None]  # mutates a node in place


@dataclass
class Mutant:
    id: int
    operator: str
    description: str
    lineno: int
    before: str
    after: str
    source: str


def _mutations_for(node: ast.AST) -> Iterator[Mutation]:
    if isinstance(node, ast.Compare):
        for i, op in enumerate(node.ops):
            new = COMPARE_SWAPS.get(type(op))
            if new:
                yield Mutation("compare", f"{SYM[type(op)]} -> {SYM[new]}",
                               lambda n, i=i, new=new: n.ops.__setitem__(i, new()))
    elif isinstance(node, ast.BinOp):
        new = BINOP_SWAPS.get(type(node.op))
        if new:
            yield Mutation("arithmetic", f"{SYM[type(node.op)]} -> {SYM[new]}",
                           lambda n, new=new: setattr(n, "op", new()))
    elif isinstance(node, ast.BoolOp):
        new = ast.Or if isinstance(node.op, ast.And) else ast.And
        yield Mutation("boolean", f"{SYM[type(node.op)]} -> {SYM[new]}",
                       lambda n, new=new: setattr(n, "op", new()))
    elif isinstance(node, ast.Constant):
        v = node.value
        if isinstance(v, bool):
            yield Mutation("constant", f"{v} -> {not v}", lambda n: setattr(n, "value", not n.value))
        elif isinstance(v, int):
            yield Mutation("constant", f"{v} -> {v + 1}", lambda n: setattr(n, "value", n.value + 1))
    elif isinstance(node, (ast.If, ast.While, ast.IfExp)):
        yield Mutation("negate_condition", "condition -> not condition",
                       lambda n: setattr(n, "test", ast.UnaryOp(op=ast.Not(), operand=n.test)))
    elif isinstance(node, ast.Return):
        v = node.value
        if v is not None and not (isinstance(v, ast.Constant) and v.value is None):
            yield Mutation("return_value", "return <value> -> return None",
                           lambda n: setattr(n, "value", ast.Constant(value=None)))


def _changed_lines(original: str, mutated: str) -> tuple[str, str]:
    before = after = ""
    for line in difflib.unified_diff(original.splitlines(), mutated.splitlines(), lineterm="", n=0):
        if line.startswith(("---", "+++", "@@")):
            continue
        if line.startswith("-") and not before:
            before = line[1:].strip()
        elif line.startswith("+") and not after:
            after = line[1:].strip()
    return before, after


def generate_mutants(source: str) -> list[Mutant]:
    """Return one Mutant per applicable mutation site in `source`."""
    tree = ast.parse(source)
    baseline = ast.unparse(tree)

    sites = []  # (node index in walk order, mutation index, mutation, lineno)
    for idx, node in enumerate(ast.walk(tree)):
        for k, m in enumerate(_mutations_for(node)):
            sites.append((idx, k, m, getattr(node, "lineno", 0)))

    mutants: list[Mutant] = []
    for idx, k, m, lineno in sites:
        clone = copy.deepcopy(tree)  # deepcopy preserves ast.walk order
        node = list(ast.walk(clone))[idx]
        list(_mutations_for(node))[k].apply(node)
        ast.fix_missing_locations(clone)
        mutated = ast.unparse(clone)
        if mutated == baseline:
            continue
        before, after = _changed_lines(baseline, mutated)
        mutants.append(Mutant(len(mutants) + 1, m.operator, m.description, lineno, before, after, mutated))
    return mutants
