# Verification of the SMS frontier result (bound ≥ 31)

The headline claim — every minimum-degree-3 graph on n ≤ 30 vertices has a
power-of-two cycle (⟹ any general counterexample needs ≥ 31 vertices) — is a
*non-existence* result, which cannot be brute-forced at n=30 (geng is infeasible
past ~n=13). So we corroborate it with several independent checks. **No check
produced a contradiction.**

## 1. Ground-truth anchor (nauty)
n = 10, forbidding only C4 → SMS returns **5**, matching the independent count of
the 5 C4-free minimum-degree-3 graphs on 10 vertices from `nauty` (geng + labelg).
Confirms SMS's isomorph-free generation, the min-degree encoding, and the Glasgow
forbidden-subgraph propagator all agree with ground truth.

## 2. Baseline reproduction
n = 6..16, forbidding all power-of-two cycles → **0**, reproducing the known
published result (no counterexample there).

## 3. Cross-method agreement (two independent codebases)
Our pure-Python CEGAR-SAT solver (PySAT/cadical, our own DFS cycle detector, our
own lex symmetry break — see `results.md`) and SMS (C++ CaDiCaL + Glasgow + the
SMS canonicity propagator) **both return UNSAT at n = 17, 18, 19**. Different
solvers, different symmetry breaking, different cycle handling — same answer.

## 4. Config robustness — cardinality encoding
Re-deciding with the **totalizer** counter (a structurally different CNF for
min-degree-3) instead of the default sequential counter:
- n = 17, 20, 22, 25 → all **count = 0**. Robust to the encoding.

## 5. Config robustness — symmetry-breaking method
Re-deciding with the **colex** minimality ordering (a different canonicity check):
- n = 17, 20 → **count = 0**.
- n = 22, 25 → **timed out at 55 min** (colex is SMS's slower, "experimental"
  variant). INCONCLUSIVE, not a contradiction — and §4 (totalizer) already
  confirms 0 at those n.

## 6. Positive controls (pipeline is not trivially returning 0)
Forbidding only C4 (a strictly weaker constraint, where graphs are known to exist)
→ SMS finds a graph (**SAT**) at n = 17, 20, 25, 30. So the frontier's "0"s come
from the constraints actually being unsatisfiable, not from a broken/empty
pipeline that always reports UNSAT.

## 7. LRAT proof certificate — status: future work
`smsg --lrat-output` emits an LRAT proof for UNSAT (e.g. 649 KB at n=16), but a
generic checker (drat-trim `lrat-check`) cannot validate it against the
min-degree-3 CNF: the forbidden-cycle clauses are added by the Glasgow propagator
during search and are **not RUP/RAT-derivable from the min-degree-3 CNF alone**
(they remove valid min-degree-3 graphs). A referee-grade, end-to-end machine-
checkable certificate therefore requires the **certified-SMS** clause-logging
machinery (Kirchweger et al.), where the propagator justifies its own clauses.
This is the identified next hardening step.

## Verdict
Across an independent ground-truth count, baseline reproduction, a second
independent solver, two cardinality encodings, a second symmetry-breaking method,
and positive controls — **no check contradicted the result**. The bound ≥ 31 is
well corroborated, with a formal proof certificate (§7) as the remaining step
toward a fully machine-checked claim. This remains a fresh computational result
pending independent (third-party) reproduction.
