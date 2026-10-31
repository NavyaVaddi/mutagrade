import ast

from mutagrade.mutators import generate_mutants


def ops(src):
    return {m.operator for m in generate_mutants(src)}


def test_finds_expected_operator_families():
    src = "def f(a, b):\n    if a < b and a != 0:\n        return a + 1\n    return b\n"
    assert {"compare", "boolean", "arithmetic", "constant", "negate_condition", "return_value"} <= ops(src)


def test_every_mutant_is_valid_python_and_differs():
    src = "def f(x):\n    return x * 2 if x > 3 else x - 1\n"
    mutants = generate_mutants(src)
    assert mutants
    for m in mutants:
        ast.parse(m.source)
        assert m.source != ast.unparse(ast.parse(src))


def test_boundary_mutant_reports_changed_line():
    (m,) = [m for m in generate_mutants("def f(x):\n    return x < 3\n") if m.operator == "compare"]
    assert "<" in m.before and "<=" in m.after and m.lineno == 2


def test_no_sites_means_no_mutants():
    assert generate_mutants("x = 'hello'\n") == []


def test_bool_constants_flip_instead_of_incrementing():
    descs = [m.description for m in generate_mutants("def f():\n    flag = True\n    return flag\n")]
    assert "True -> False" in descs
