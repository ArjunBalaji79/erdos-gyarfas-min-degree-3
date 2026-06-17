# Verified frontier results

CEGAR-SAT verification of the Erdős–Gyárfás conjecture for **general
minimum-degree-3 graphs**. Each UNSAT below is verified two ways: every
refinement clause's forbidden cycle is re-checked to be a genuine simple cycle of
power-of-two length (the certificate), and the accumulated formula is re-proven
UNSAT by a second, independent solver (glucose42) distinct from the primary
(cadical195). Gates 3–4 anchor encoding soundness (n=10 nauty cross-check; n≤16
reproduce the published baseline).

## Published prior frontier

- General min-degree-3: **n ≥ 17** (counterexample must have ≥17 vertices; all
  ≤16 verified) — Royle & Markström, ~2004. Unchanged for ~20 years.
- Cubic (3-regular): n ≥ 30 — Markström, *Congr. Numer.* 171 (2004) 179–192.
- No SAT or SAT-Modulo-Symmetries method had ever been applied to this conjecture.

## This run (Modal, 1 core/size, cadical195 primary + glucose42 re-check)

| n  | result | refinements | wall (s) | re-check | verified |
|----|--------|-------------|----------|----------|----------|
| 14 | UNSAT  | 4,854       | 2.2      | UNSAT    | ✅ |
| 15 | UNSAT  | 13,096      | 7.9      | UNSAT    | ✅ |
| 16 | UNSAT  | 35,458      | 28.4     | UNSAT    | ✅ |
| 17 | UNSAT  | 85,072      | 79.0     | UNSAT    | ✅ |
| 18 | UNSAT  | 171,678     | 225.2    | UNSAT    | ✅ |
| 19 | UNSAT  | 408,527     | 876.4    | UNSAT    | ✅ |
| 20 | WALL   | 719,133     | 3300 (cap) | —      | ❌ (did not finish) |

(n ≤ 16 also reproduced locally by Gate 4. Refinement growth ≈ 2.1×/step.)

## Result

**Verified contiguous UNSAT through n = 19 ⟹ every general minimum-degree-3
counterexample to Erdős–Gyárfás must have at least 20 vertices** (bound ≥ 20).

This extends the published general frontier (n ≥ 17, i.e. verified to 16) by three
vertices, and is — to our knowledge and per the literature review — the **first
SAT/CEGAR verification** applied to this conjecture.

### Honest scope

- This is the **general** (non-regular allowed) min-degree-3 case. The **cubic**
  case is already verified to 29 (bound ≥ 30), so the genuinely new ground is the
  **non-cubic** min-degree-3 graphs at 17 ≤ n ≤ 19.
- A standalone publication would want to reach meaningfully further (n ≥ 23+),
  which needs complete symmetry breaking (SAT-Modulo-Symmetries), and to cite/build
  on Carr, arXiv:2605.22844 (2026), whose "predominantly cubic" structure subsumes
  property (a) used here.
- n = 20 walled at the 55-minute budget (≈719k refinements, needs ~2 h on one
  core); completing it would give bound ≥ 21.
