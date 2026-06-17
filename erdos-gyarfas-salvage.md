# Erdős–Gyárfás min-degree-3 extension — salvage notes

> Reconstructed 2026-06-09 from a frozen Claude Code cloud session.
> Source code in the sandbox (branch `claude/stoic-thompson-TpWtb`, commits `6e86a97`, `945c58d`, …) is presumed lost. This file preserves the result, the proof, the algorithm, and enough detail to rebuild.

---

## 1. Headline result (the prize)

**The Erdős–Gyárfás conjecture holds for every graph with minimum degree ≥ 3 on at most 23 vertices.**

This improves the prior general lower bound from **n ≥ 17** (Royle / Markström) to **n ≥ 24**.

The result is **unconditional** — it does not depend on the Carr (b)/(c) structural properties (which could not be verified from the unreachable arXiv paper). It rests only on property (a), which is self-proved below.

### Frontier table (CEGAR-SAT under property (a) only)

| n  | refinements | wall time | result            |
|----|-------------|-----------|-------------------|
| 17 | 10,702      | 6.6 s     | UNSAT             |
| 18 | 18,694      | 15 s      | UNSAT             |
| 19 | 31,601      | 37 s      | UNSAT             |
| 20 | 50,673      | 88 s      | UNSAT             |
| 21 | 81,624      | 191 s     | UNSAT             |
| 22 | 127,766     | 478 s     | UNSAT             |
| 23 | 200,785     | ~20 min   | **UNSAT** → bound ≥ 24 |
| 24 | 300,227+    | > 45 min  | wall (budget cap) |

Growth ≈ 1.6× per +1 in n, both in refinement count and wall time.

---

## 2. Property (a) — self-verified proof (the rigorous bedrock)

**Claim.** In any minimum-size counterexample (a min-degree-3 graph with no cycle of length a power of 2), the vertices of degree ≥ 4 form an independent set.

**Proof.** Suppose `u, v` are adjacent, both of degree ≥ 4. Delete the edge `uv`. The resulting graph `G'`:
- has fewer edges than `G`,
- still has min-degree ≥ 3 (both `u` and `v` had degree ≥ 4, so each is still degree ≥ 3 in `G'`),
- contains no cycle of length a power of 2 (deleting an edge cannot create a cycle).

So `G'` is a smaller counterexample — contradicting minimality of `G`.  ∎

> Note: properties (b) and (c) from Carr's paper would give further structural constraints (and were implemented in the original code) but the empirical finding was that (a) alone gives essentially all the speedup, so the rigorous frontier uses only (a).

---

## 3. Algorithmic recipe (enough to rebuild)

### 3.1 The CEGAR loop

```
loop:
    model = SAT(base ∧ min3 ∧ structural(a) ∧ lex_canon ∧ refinements_so_far)
    if model is UNSAT:
        return UNSAT for this n
    G = decode(model)
    bad_cycle = power_of_2_cycle_detector(G)
    if bad_cycle is None:
        return SAT, G   # counterexample found — would halt loudly
    refinements_so_far ∧= forbid(bad_cycle)
```

- **Detector remains the sole certifier.** Any SAT model halts the search loudly; the SAT solver never gets to "prove" non-existence by itself, only to drive refinement.
- **Ladder steps by 1** (n = 4, 5, 6, …). Skipping sizes breaks the minimality argument that justifies property (a).

### 3.2 Base CNF

- Variables `x_{ij}` for each unordered pair `i < j`, meaning "edge ij is present."
- **min-degree ≥ 3** at each vertex via a **reified Sinz sequential `≥k` counter**:
  - Standard Sinz sequential counter on the n−1 incident edge vars.
  - Reify each `(row, k)` aux into an output literal `cubic_v ↔ deg(v) ≥ 3`.
  - This gives a per-vertex Boolean `cubic_v` that can be used to define structural constraints.
- **Refinements**: for each previously-witnessed `power_of_2` cycle `C` on edges `e_1,…,e_L`, add the clause `¬e_1 ∨ ¬e_2 ∨ … ∨ ¬e_L` to forbid that exact cycle.

### 3.3 Property (a) constraint (the only structural one needed)

Property (a) says: degree-≥4 vertices form an independent set.

Encoding: define `high_v ↔ deg(v) ≥ 4` (another reified Sinz counter at threshold 4). Then for every edge `uv`, add `¬(high_u ∧ high_v)`, i.e. `¬high_u ∨ ¬high_v ∨ ¬x_{uv}`.

### 3.4 Lex canonization

Order vertex labellings lexicographically and add clauses that keep only the lex-min representative of each isomorphism class. This is the standard symmetry break — it is what makes the n=10 ground-truth cross-check return exact agreement (missing = extra = 0).

### 3.5 Provable max-degree cap (for ground-truth generation)

If G is C4-free, every pair of vertices has at most one common neighbour, so
`Σ_v C(d_v, 2) ≤ C(n, 2)`.
Combined with `d_w ≥ 3` for all other `w`, the maximum degree `d` satisfies

```
d(d − 1) ≤ (n − 1)(n − 6)
```

Used as `geng -D⌊…⌋` to keep ground-truth enumeration **complete** while making it fast enough to run.

Connectivity note: the smallest C4-free min-degree-3 graph is the Petersen graph (n = 10). A disconnected such graph needs two components of ≥ 10 vertices, so ≥ 20 total. Therefore every C4-free min-degree-3 graph on n ≤ 19 is connected — meaning `geng -c -d3 -D…` is complete ground truth in our range, and far cheaper than `geng -d3` alone.

---

## 4. Validation gates (in order)

These are what made the result trustworthy. Re-implement them all.

### Gate 0 — reified counter unit test
Brute-force enumerate every assignment of n−1 input bits up to ~n=12, check the reified `≥k` literal matches the true count. **Must pass exhaustively.**

### Gate 1 — base validation
For small n where `geng -d3` is tractable, confirm `SAT(base ∧ min3)` produces only graphs that geng also enumerates. (Catches encoding bugs.)

### Gate 3 — soundness cross-check at n = 10
The single most important gate. For each property config — `()`, `(a)`, `(a,b,c)`:
- Enumerate isomorphism classes via `geng -c -d3 -D⌊…⌋ 10` filtered for C4-free.
- Enumerate SAT models under `min3 ∧ structural ∧ lex_canon`.
- Reduce both to canonical labellings, compare sets.

**Must report missing = 0, extra = 0.** This is the check that catches over-constraining (spurious-UNSAT) bugs, which the Step 4 gate cannot.

### Gate 4 — bound reproduction gate
Run `min3` and `min3 + structural(a,b,c)` for every n in 4..16. Both must be UNSAT, and they must agree. This reproduces the known ≥ 17 baseline before we start claiming anything new.

### Gate 5 — frontier feasibility probe
Spot-check n = 14, 16, 17 with structural ON before launching the full frontier run, to confirm growth is sane.

### Gate 6 — frontier
Run n = 17, 18, 19, … with a per-size wall-time budget (used: 45 min). Each UNSAT result advances the published bound by 1.

---

## 5. Suggested file layout for the rebuild

```
erdos-gyarfas/
├── README.md                # this doc, polished
├── sat/
│   ├── encoding.py          # var index, base_cnf, min3, reified_atleast, lex_canon
│   ├── structural.py        # property (a), (b), (c) constraints
│   ├── cegar.py             # the CEGAR loop, refinement clauses
│   └── detector.py          # power-of-2 cycle detector — the certifier
├── ground_truth/
│   ├── stream_graph6.py     # geng -c -d3 -D<cap> n with the proven cap
│   └── canonicalize.py      # iso-class reduction via nauty
├── experiments/
│   ├── run_frontier.py      # the per-n driver with time budget
│   └── results.csv          # frontier table
├── tests/
│   ├── test_reified_counter.py    # Gate 0
│   ├── test_base_validation.py    # Gate 1
│   ├── test_cross_check_n10.py    # Gate 3 — KEY TEST
│   └── test_bound_gate.py         # Gate 4
└── pyproject.toml
```

Suggested dependencies: `python-sat` (PySAT) for the solver, `networkx` for graph utilities, `pynauty` for canonical labelling, `nauty` (geng) at the system level for ground truth.

---

## 6. Quick start sketch (pseudocode for the rebuild's first hour)

```python
# encoding.py
def edge_var(i, j, n): ...  # 1-indexed unordered pair → SAT var id

def reified_atleast(input_lits, k, cnf, next_var) -> int:
    """Sinz sequential counter, returns the var that is true iff
    at least k of input_lits are true. Adds clauses to cnf."""
    ...

def base_cnf(n) -> (CNF, dict):
    """Returns base CNF (no degree/structural constraints yet) and a
    dict mapping vertex v -> [edge_var(v, u) for u != v]."""
    ...

def add_min3(cnf, incident_edges, n) -> dict:
    """Adds clauses enforcing deg(v) >= 3 for each v. Returns
    {v: cubic_v_lit} where cubic_v is true iff deg(v) >= 3."""
    ...

def add_property_a(cnf, incident_edges, n):
    """Adds clauses for: degree-4+ vertices form an independent set."""
    high = {v: reified_atleast(incident_edges[v], 4, cnf, ...) for v in range(n)}
    for i in range(n):
        for j in range(i+1, n):
            cnf.append([-high[i], -high[j], -edge_var(i, j, n)])

def add_lex_canon(cnf, n):
    """Add lex-min symmetry break."""
    ...

# cegar.py
def search(n) -> ("UNSAT" or graph):
    cnf, incident = base_cnf(n)
    cubic = add_min3(cnf, incident, n)
    add_property_a(cnf, incident, n)
    add_lex_canon(cnf, n)
    solver = Glucose4(bootstrap_with=cnf)
    while True:
        if not solver.solve():
            return "UNSAT"
        model = solver.get_model()
        G = decode(model, n)
        bad = find_power_of_2_cycle(G)   # detector
        if bad is None:
            return G                      # WOULD BE A REAL COUNTEREXAMPLE
        solver.add_clause([-edge_var(u, v, n) for (u, v) in bad])

# detector.py
def find_power_of_2_cycle(G):
    """Return a cycle of length 2^k (k >= 1) if one exists, else None.
    Standard DFS-based simple-cycle enumeration is fine here; the
    refinement loop forbids found cycles one at a time."""
    ...
```

---

## 7. Things to be careful about during the rebuild

1. **Gate 3 is non-negotiable.** Without it, an over-constrained encoding can return UNSAT for the wrong reason and the bound will be a lie. Run it at n = 10 every time you change the encoding.
2. **Ladder by 1.** The minimality proof of (a) requires that all smaller orders have been verified. Don't skip from n=10 straight to n=17.
3. **Lex canon must be the standard one** (lex-min over the n! labellings). Cheaper symmetry breaks (degree-sorted, etc.) are not strict enough to make Gate 3 return missing = 0.
4. **The detector is the certifier.** Never weaken it. A SAT model that survives the detector is a real counterexample — that's the whole protocol.
5. **Per-size wall-time budget.** The frontier hit ~20 min at n=23 and didn't finish at 45 min for n=24. Set a budget per size and accept it as the stopping rule.

---

## 8. To push further than n = 23

Documented paths (from the original work):

- **Add Carr (b)/(c) constraints** once the paper is accessible — implemented in the lost code but flagged as paper-dependent. Modest speedup over (a) alone.
- **Parallelism.** Run multiple sizes / multiple CEGAR streams concurrently.
- **DIMACS → BreakID → Kissat.** Export the CNF, run BreakID for stronger symmetry breaking, then Kissat (state-of-the-art CDCL) — typically big wins on hard combinatorial UNSAT.

---

## 9. What was lost vs. what is preserved

| Asset                                | Status |
|--------------------------------------|--------|
| The mathematical result (bound ≥ 24) | ✅ preserved in this doc |
| Proof of property (a)                | ✅ preserved |
| Algorithm recipe (encoding + CEGAR)  | ✅ preserved |
| Validation methodology (Gates 0–6)   | ✅ preserved |
| Frontier numbers                     | ✅ preserved |
| Source files (`sat.py`, tests, README) | ❌ lost (sandbox-only) |
| Exact CNF wire format / clause counts | ❌ lost |
| DIMACS dumps                         | ❌ lost |

Rebuilding the code from this doc is a focused weekend, not a from-scratch project. The hard part — figuring out *which* structural property is verifiable and which CEGAR gates are sufficient — is done and recorded.
