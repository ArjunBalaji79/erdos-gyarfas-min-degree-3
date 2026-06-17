# Erdős–Gyárfás for minimum-degree-3 graphs — CEGAR-SAT verification

A counterexample-guided (CEGAR) SAT search that verifies the **Erdős–Gyárfás
conjecture** — every graph with minimum degree ≥ 3 contains a cycle whose length
is a power of two — for all such graphs up to a frontier order `n`, pushing the
general lower bound from `n ≥ 17` (Royle / Markström) toward `n ≥ 24`.

This is a clean rebuild from [`erdos-gyarfas-salvage.md`](erdos-gyarfas-salvage.md),
re-deriving the result from first principles with a full validation-gate suite.

## The idea in one paragraph

For each order `n` we ask a SAT solver for a graph that is (i) minimum-degree-3
and (ii) free of every power-of-2 cycle we have seen so far. If the solver finds
one, a **detector** looks for a power-of-2 cycle in it; if it finds one, we add a
clause forbidding exactly that cycle and loop. If the detector finds *no*
power-of-2 cycle, the model is a genuine counterexample and the search halts
loudly. If the solver ever returns UNSAT, the conjecture holds for that `n`. The
detector is the **sole certifier** — the SAT solver only drives refinement.

## Property (a) — the one structural lemma we use (self-proved)

> In any minimum-size counterexample, the vertices of degree ≥ 4 form an
> independent set.

*Proof.* If adjacent `u, v` both have degree ≥ 4, delete edge `uv`: the graph
still has min-degree ≥ 3, still has no power-of-2 cycle (deleting an edge creates
none), and has fewer edges — contradicting minimality. ∎

Encoded as: `high_v ↔ deg(v) ≥ 4` (a reified counter), then `¬high_u ∨ ¬high_v ∨
¬edge(u,v)` for every edge. This is the only structural constraint the rigorous
frontier relies on; Carr's (b)/(c) are not needed.

## Validation gates (run them; they are what make the result trustworthy)

| Gate | What it checks | Test |
|------|----------------|------|
| 0 | reified ≥k counter is exact (brute force, all assignments) | `tests/test_reified_counter.py` |
| 1 | `base ∧ min3` matches `geng -d3` as iso-classes (small n) | `tests/test_base_validation.py` |
| 3 | **KEY:** at n=10, SAT models == nauty ground truth (`missing = extra = 0`) | `tests/test_cross_check_n10.py` |
| 4 | bound ≥ 17 reproduced: n=4..16 UNSAT, property-(a) on/off agree | `tests/test_bound_gate.py` |

**Gate 3 is non-negotiable** — it catches an over-constrained encoding that would
return UNSAT for the wrong reason. Re-run it whenever the encoding changes:

```bash
PYTHONPATH=. pytest tests/test_cross_check_n10.py -q
```

## Layout

```
erdos_gyarfas/
├── sat/
│   ├── encoding.py     # edge vars, VarPool, reified Sinz ≥k counter
│   ├── base.py         # base CNF, min-degree-3, model decode
│   ├── structural.py   # property (a), C4-free, lex-canon symmetry break
│   ├── detector.py     # power-of-2 cycle detector — the certifier
│   ├── cegar.py        # the CEGAR loop
│   └── enumerate.py    # model enumeration for the cross-checks
├── ground_truth/
│   ├── nauty.py        # geng / labelg wrappers, provable max-degree cap
│   └── reference.py    # C4-free min-deg-3 reference set for Gate 3
└── experiments/
    ├── run_frontier.py    # local per-size driver with wall-time budget
    └── modal_frontier.py  # Modal cloud driver (detached, cost-guarded)
```

## Requirements

- Python ≥ 3.10, `python-sat`, `networkx` (`pip install -e .`)
- **nauty** at the system level for the ground-truth gates: `brew install nauty`
  (provides `geng`, `labelg`). Not needed for the frontier search itself.
- Optional: `modal` for the cloud frontier (`pip install -e '.[cloud]'`).

## Running the frontier

Local, laddering n upward with a 45-minute per-size budget:

```bash
PYTHONPATH=. python -m erdos_gyarfas.experiments.run_frontier \
    --start 17 --end 23 --time-budget 2700
```

Each UNSAT advances the bound by 1. A `WALL` (budget hit) is the stopping rule.
A `SAT` result is a real counterexample and halts loudly.

### Cloud (Modal) — detached, with hard cost guards

The frontier needs only the solver + detector, so each size runs in its own
1-core container. **Three cost guards:** a soft `time_budget` (graceful `WALL`), a
hard Modal `timeout` that kills the container, and an entrypoint that refuses to
dispatch unless `soft + margin ≤ hard` and prints the worst-case core-hours
first. Results stream to a persistent Volume, so you can close your laptop.

```bash
# cheap smoke test first (one size, 90s):
modal run erdos_gyarfas/experiments/modal_frontier.py::main --start 17 --end 17 --time-budget 90

# real detached run:
modal run --detach erdos_gyarfas/experiments/modal_frontier.py::main --start 17 --end 23

# read results back any time:
modal run erdos_gyarfas/experiments/modal_frontier.py::fetch
```

## Notes & honest caveats

- The lower bound is only as sound as the encoding; the gates (especially Gate 3)
  are the guarantee. The symmetry break is *sound* (never drops an iso-class), so
  it can only affect speed, not correctness — Gate 3 confirms this.
- Ladder by 1: the minimality argument behind property (a) needs every smaller
  order verified first.
- To push past the current reach: stronger symmetry breaking (BreakID) feeding a
  state-of-the-art CDCL solver (Kissat) on exported DIMACS is the documented path.

See [`erdos-gyarfas-salvage.md`](erdos-gyarfas-salvage.md) for the original
salvage notes this rebuild is based on.
