# mutagrade

**Passing tests don't mean good tests.** `mutagrade` grades a Python test suite by injecting small
bugs into your code (flipping `<` to `<=`, `+` to `-`, `and` to `or`, dropping a return value) and
checking whether your tests notice. Every bug the tests miss is a gap in the suite, and mutagrade
tells you where it is and what kind of test would close it.

I built it from my work reviewing AI-generated solutions and writing test suites: a green test run
says very little if the tests never check boundaries or exact values. A mutation score measures
test quality directly, whether the tests were written by a person or by an AI model.

## Demo

Same code (`examples/pricing.py`), two test suites that both pass:

| Suite | Mutation score | Mutants caught |
|---|---|---|
| `test_pricing_weak.py` (happy path only) | **48.6%** (weak) | 17 / 35 |
| `test_pricing_strong.py` (boundaries, exact values) | **94.3%** (strong) | 33 / 35 |

```
$ python -m mutagrade examples/pricing.py examples/test_pricing_weak.py
Mutation score: 48.6% (weak)  -  17 of 35 mutants caught
...
Survived (your tests did not notice these changes):
  #7 line 2 [compare] < -> <=
      if x < lo:   ->   if x <= lo:
      hint: Add a test exactly on the boundary value (and one on each side of it).
```

## Install and use
```bash
pip install -e .
mutagrade path/to/module.py path/to/test_module.py
```

| Option | What it does |
|---|---|
| `--html report.html` | also write a shareable HTML report |
| `--json` | machine-readable output |
| `--min-score 80` | exit with code 1 if the score is lower (use as a CI quality gate) |
| `--jobs N` | run N mutants in parallel (default 4) |
| `--timeout S` | per-run timeout; a mutant that hangs counts as caught |
| `--max-mutants N` | try only the first N mutants (quick check) |

## How it works
1. Confirms your tests pass on the original code, otherwise there is nothing to compare against.
2. Walks the AST and creates one mutant per mutation site. Operators: comparison swaps,
   arithmetic swaps, `and`/`or` swaps, integer and boolean constants, negated conditions, and
   dropped return values.
3. Runs your test file against each mutant in an isolated temp directory (in parallel).
4. A mutant is **killed** if any test fails, or if it hangs and times out. If all tests still pass, it
   **survived**, which means the suite has a blind spot.
5. Reports the score, a per-operator breakdown, and every survivor with the changed line and a hint.

## Equivalent mutants
Some survivors cannot be killed because the change does not alter behavior. For example, in
`clamp`, `x < lo` becomes `x <= lo`: when `x == lo`, both return the same value. That is why the strong
suite scores 94.3% rather than 100%. Review survivors; don't chase 100%.

## Run the project's own tests
```bash
pip install -e . && pytest
```
CI also runs mutagrade on its own example and fails if the strong suite drops below 80%.

## Limitations (v0.1)
- Python only; one target module and one pytest file per run
- Mutation operators are a focused set, not exhaustive
- Mutants run sequentially per worker; large codebases need `--max-mutants` or more `--jobs`

## Roadmap
- Multi-file projects and `pytest` config discovery
- Skip lines marked `# pragma: no mutate`
- More operators (`in`/`not in`, `is`, slicing, string constants)
- Compare two test suites side by side (human-written vs AI-generated)

## License
MIT
