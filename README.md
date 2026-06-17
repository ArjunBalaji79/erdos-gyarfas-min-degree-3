# Erdős–Gyárfás for minimum-degree-3 graphs — CEGAR-SAT verification

A counterexample-guided (CEGAR) SAT search that verifies the **Erdős–Gyárfás
conjecture** — every graph with minimum degree ≥ 3 contains a cycle whose length
is a power of two — for all such graphs up to a frontier order `n`.

This is a clean rebuild from [`erdos-gyarfas-salvage.md`](erdos-gyarfas-salvage.md),
re-deriving the method from first principles with a full validation-gate suite.

**What this rebuild establishes (verified):** the method is fully reconstructed
and validated (Gate 3 proves the encoding sound at n=10; Gate 4 reproduces the
published n≤16 baseline). A cost-guarded Modal run then verified **UNSAT for
n = 17, 18, 19** — each independently re-proven by a second solver and certified
cycle-by-cycle — giving **bound ≥ 20** (any general min-degree-3 counterexample
needs ≥ 20 vertices). This **extends the 20-year-old published general frontier of
n ≥ 17 by three vertices, via the first SAT method applied to the conjecture.**
n = 20 walled at the 55-min budget. Full table: [`experiments/results.md`](erdos_gyarfas/experiments/results.md).
Reaching the salvage's n = 23 needs *complete* symmetry breaking (SMS) — see
**Performance & frontier reach**.

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
| 5 | every forbidden cycle is a valid power-of-2 simple cycle, and a 2nd solver agrees UNSAT | `tests/test_certificate.py` |

**Gate 3 is non-negotiable** — it catches an over-constrained encoding that would
return UNSAT for the wrong reason. Re-run it whenever the encoding changes:

```bash
PYTHONPATH=. pytest tests/test_cross_check_n10.py -q
```

## How a frontier UNSAT is verified

For large `n` there is no tractable independent ground truth, so each UNSAT is
made auditable three ways (`erdos_gyarfas/sat/verify.py`):

1. **Lemma certificate** — every refinement clause records the exact cycle it
   forbids; the verifier re-checks each is a genuine simple cycle of power-of-two
   length. A real counterexample avoids *all* power-of-two cycles, so it would
   satisfy the formula — hence UNSAT (over these verified lemmas) means none exists.
2. **Independent re-check** — the accumulated formula is re-solved from scratch
   with a different backend (glucose42 vs the primary cadical195); both must
   report UNSAT, guarding against a single-solver bug.
3. **Soundness anchor** — Gate 3 proves the *encoding* drops no isomorphism class
   at n=10, and Gate 4 reproduces the published n≤16 results.

The Modal driver runs all three per size and stores the certificate (gzipped) and
verdict in a persistent Volume.

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

## Performance & frontier reach

The bottleneck to reaching larger `n` is **symmetry breaking**, not solver speed.
With the current sound-but-partial break (adjacent-transposition lex-leader),
n=17 takes ~30s and ~85k refinements with cadical195; the salvage notes report
~10.7k refinements there. That ~8× gap compounds (solve time grows ~4×/step as
refinement clauses accumulate), so this implementation reaches ~n=20 in practice.

Approaches measured and **ruled out** for closing the gap (so they aren't retried):

| Approach | Outcome |
|----------|---------|
| Full-transposition lex-leader | n=17: 57k refs but **net slower** (29→36s) — CNF 3.75× bigger |
| Dynamic canonicity blocking (pynauty, model-blocking) | **Non-convergent** — exponentially many non-canonical labellings flood the loop |
| BreakID static preprocessing | Builds & works on pigeonhole, but **detects no symmetry** here — saucy doesn't recognise the Sₙ action on edge-*pairs*, even on a symmetric shadow formula |

**The real fix** is *complete* symmetry breaking via a propagator —
[SAT-Modulo-Symmetries](https://github.com/markirch/sat-modulo-symmetries) — which
prunes non-canonical graphs *during* search rather than blocking them after the
fact. That is the documented next step to reach the salvage's n=23 (bound ≥ 24).
(Note: the PyPI package `pysms` is an unrelated SMS-texting library, not this tool.)

## Context & where this sits (literature)

- The conjecture (Erdős–Gyárfás, 1995) is **open**: no counterexample is known;
  Erdős offered $100 for a proof / $50 for a counterexample.
- The published **general minimum-degree-3** verification frontier is **n ≥ 17**
  (all such graphs ≤16 verified), from computer searches by **Gordon Royle and
  Klas Markström** — and it has not been extended in ~20 years. The **cubic**
  (3-regular) case is much stronger: **n ≥ 30** (Markström, *Congr. Numer.* 171
  (2004) 179–192). So the only *new* ground for a general-graph search lies in the
  **non-cubic** min-degree-3 graphs at 17 ≤ n ≤ 29.
- **No SAT or SAT-Modulo-Symmetries method has ever been applied to this
  conjecture** (checked against Szeider's 2025 SMS survey) — so a SAT/CEGAR attack
  is methodologically new for it.
- Structural state of the art: A. Carr, *Every Minimal Counterexample to the
  Erdős–Gyárfás Conjecture is Predominantly Cubic*, arXiv:2605.22844 (2026, preprint)
  — minimal counterexamples are ≥4/7 degree-3. This subsumes property (a) here.

**Honest novelty:** a verified extension of the **general** frontier past 16,
using the first SAT method, is a genuine but **narrow** contribution; a compelling
writeup needs to reach meaningfully beyond n=17 (via complete symmetry breaking)
and to cite/build on Carr (2026).

## Notes & honest caveats

- The lower bound is only as sound as the encoding; the gates (especially Gate 3)
  are the guarantee. The symmetry break is *sound* (never drops an iso-class), so
  it can only affect speed, not correctness — Gate 3 confirms this.
- Ladder by 1: the minimality argument behind property (a) needs every smaller
  order verified first.
- "Verified" here means the three checks above (certificate + independent
  re-check + Gate 3/4 anchors), not a single formally-checked DRAT proof.

See [`erdos-gyarfas-salvage.md`](erdos-gyarfas-salvage.md) for the original
salvage notes this rebuild is based on.
