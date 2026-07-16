# Erdős–Gyárfás conjecture for minimum-degree-3 graphs

A SAT-based verification that every graph of minimum degree at least 3 on **at most
31 vertices** contains a cycle whose length is a power of two — establishing that
any minimum-degree-3 counterexample to the **Erdős–Gyárfás conjecture** must have at
least **32 vertices**.

This raises the published *general* minimum-degree-3 frontier from `n ≥ 17` (Royle &
Markström, ~2004) to `n ≥ 32`, and is, to our knowledge, the first application of
SAT methods to this conjecture. Since the cubic class is contained in the
minimum-degree-3 class, it also surpasses Markström's separate cubic bound of 30.
Verifying through `n = 31` settles the entire range in which `C₄, C₈, C₁₆` are the
only admissible power-of-two cycle lengths (`C₃₂` first fits at `n = 32`).

## Result

For each `n` we decide whether a minimum-degree-3 graph on `n` vertices exists that
contains **no** `C₄`, `C₈`, or `C₁₆` (the power-of-two cycle lengths ≤ 31). The
answer is "none" for every `n` from 17 to 31; together with the established `n ≤ 16`
baseline this proves the bound.

| n | 17 | 18 | 19 | 20 | 21 | 22 | 23 | 24 | 25 | 26 | 27 | 28 | 29 | 30 | 31 |
|---|----|----|----|----|----|----|----|----|----|----|----|----|----|----|----|
| result | UNSAT | UNSAT | UNSAT | UNSAT | UNSAT | UNSAT | UNSAT | UNSAT | UNSAT | UNSAT | UNSAT | UNSAT | UNSAT | UNSAT | UNSAT |
| time (s) | 2.9 | 7.8 | 24.1 | 27.8 | 19.3 | 101 | 203 | 148 | 340 | 415 | 1000 | 1892 | 2343 | 6889 | 7351 |

UNSAT = no such graph exists at that order.

Full data and timings: [`erdos_gyarfas/experiments/sms_results.md`](erdos_gyarfas/experiments/sms_results.md).

## Two independent methods

- **SAT Modulo Symmetries (SMS)** — the main result. SMS (Kirchweger–Szeider)
  performs complete, isomorph-free graph generation; the Glasgow Subgraph Solver is
  used as a complete forbidden-subgraph propagator for `C₄, C₈, C₁₆`. This reaches
  `n = 31`. Driver: [`erdos_gyarfas/experiments/modal_sms.py`](erdos_gyarfas/experiments/modal_sms.py).
- **CEGAR-SAT** — an independent, self-contained solver (PySAT/CaDiCaL, a DFS
  power-of-two cycle detector, a lexicographic symmetry break) used as a
  cross-check. It reaches `n = 19` and agrees with SMS there. Code in
  [`erdos_gyarfas/sat/`](erdos_gyarfas/sat/); results in
  [`erdos_gyarfas/experiments/results.md`](erdos_gyarfas/experiments/results.md).

## Verification

A non-existence claim cannot be brute-forced at this scale, so the result is
corroborated by several independent checks (no check produced a contradiction):
an exact ground-truth count against `nauty` at `n = 10`, reproduction of the
`n ≤ 16` baseline, agreement of the two solvers for `n ≤ 19`, robustness across two
cardinality encodings and a second symmetry-breaking method, and positive controls.
Details: [`erdos_gyarfas/experiments/verification.md`](erdos_gyarfas/experiments/verification.md).

## Repository layout

```
erdos_gyarfas/
├── sat/            # CEGAR encoding: edge vars, reified counter, structural
│                   # constraints, power-of-2 cycle detector, CEGAR loop, verifier
├── ground_truth/   # nauty (geng/labelg) wrappers + reference sets for the gates
└── experiments/
    ├── modal_sms.py       # SMS + Glasgow frontier (the main result)
    ├── modal_frontier.py  # CEGAR frontier on Modal (cross-check)
    ├── run_frontier.py    # CEGAR frontier locally
    ├── sms_results.md / results.md / verification.md
tests/              # validation gates (Gates 0,1,3,4,5)
```

## Reproducing

### Local validation gates (fast)
Requires Python ≥ 3.10, `python-sat`, `networkx`, and `nauty` (`geng`, `labelg`;
`brew install nauty` / `apt install nauty`).

```bash
pip install -e '.[dev]'
PYTHONPATH=. pytest -q          # Gate 0 (counter), 1 (vs geng), 3 (n=10 cross-check), 4 (n≤16), 5 (certificates)
```

### SMS frontier (the main result)
Requires a [Modal](https://modal.com) account (`pip install modal`). The container
image builds SMS + the Glasgow Subgraph Solver from source (pinned commits are in
`modal_sms.py`).

```bash
# soundness checks: n=10 forbidding only C4 -> 5 (matches nauty); n=6..16 -> 0
modal run erdos_gyarfas/experiments/modal_sms.py::validate_main

# the frontier: n=17..31 (each returns UNSAT = no such graph)
modal run --detach erdos_gyarfas/experiments/modal_sms.py::frontier_main --start 17 --end 31
modal run erdos_gyarfas/experiments/modal_sms.py::fetch_main   # read results
```

### CEGAR cross-check (no Modal needed for small n)
```bash
PYTHONPATH=. python -m erdos_gyarfas.experiments.run_frontier --start 17 --end 19
```

## License

[MIT](LICENSE) © 2026 Arjun Balaji.
