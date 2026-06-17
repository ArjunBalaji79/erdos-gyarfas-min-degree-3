# SMS frontier results — Erdős–Gyárfás, general minimum-degree-3 case

**Headline:** every graph of minimum degree ≥ 3 on **n ≤ 28** vertices contains a cycle
of length a power of two ⟹ **any general min-degree-3 counterexample has ≥ 29 vertices**
(bound ≥ 29), up from the published bound ≥ 17.

> THIS IS THE GENERAL CASE (degrees ≥ 3, non-regular allowed), **not** the cubic subcase.

## Method

Tool: **SAT-Modulo-Symmetries (SMS)**, Kirchweger & Szeider — complete, isomorph-free
graph generation under constraints (CaDiCaL + in-search canonicity propagator), built with
the **Glasgow Subgraph Solver** for a complete forbidden-subgraph propagator.

Per n, one SMS call asks: *does a graph on n vertices exist with (i) minimum degree ≥ 3 and
(ii) no C4, C8, or C16 as a (non-induced) subgraph?* For 17 ≤ n ≤ 28 the power-of-two cycle
lengths are exactly {4, 8, 16} (32 > 28), so (ii) ⟺ "no cycle of length a power of two".
SMS reporting **0 graphs** proves the conjecture holds for all min-degree-3 graphs on n vertices.

```
smsg --vertices n --all-graphs --hide-graphs \
     --forbidden-subgraph-file {C4,C8,C16} --dimacs {GraphEncodingBuilder(n).minDegree(3)}
```

## Soundness anchors (independent)

- **n=10, forbidding only C4 → exactly 5 graphs**, matching the independent `nauty`
  (geng+labelg) count of the 5 C4-free min-degree-3 graphs on 10 vertices.
- **n=6..16, forbidding all power-of-two cycles → 0**, reproducing the known baseline.

## Results (Modal, 1 core/size)

| n  | result | wall      |
|----|--------|-----------|
| 17 | UNSAT  | 2.9 s     |
| 18 | UNSAT  | 7.8 s     |
| 19 | UNSAT  | 24.1 s    |
| 20 | UNSAT  | 27.8 s    |
| 21 | UNSAT  | 19.3 s    |
| 22 | UNSAT  | 101.1 s   |
| 23 | UNSAT  | 202.9 s   |
| 24 | UNSAT  | 148.3 s   |
| 25 | UNSAT  | 339.8 s   |
| 26 | UNSAT  | 414.8 s   |
| 27 | UNSAT  | 1000.3 s  |
| 28 | UNSAT  | 1892.0 s  |

**Verified contiguous UNSAT through n = 28 ⟹ bound ≥ 29.** (UNSAT = "count = 0" = no
min-degree-3 graph on n vertices avoids all power-of-two cycles.)

## Comparison to the literature

| Result | Class | Verified ≤ | counterexample needs ≥ | Method |
|---|---|---|---|---|
| Royle & Markström (~2004) | **general** min-deg-3 | 16 | 17 | exhaustive enumeration |
| Markström 2004 (*Congr. Numer.* 171, 179–192) | **cubic** (3-regular) | 29 | 30 | exhaustive (cubic generator) |
| **This work** | **general** min-deg-3 | **28** | **29** | SAT-Modulo-Symmetries |

## Honest scope

- We extend the **general** min-degree-3 frontier from 16 to 28 (bound ≥17 → ≥29) — first
  SAT/SMS attack on this conjecture. The genuinely new content is the **non-cubic**
  min-degree-3 graphs on 17 ≤ n ≤ 28 (cubic graphs ≤29 were already done by Markström).
- We do **not** surpass Markström's **cubic** bound (30). Our verified count (28) is one below
  the cubic count (29), but for the strictly larger/harder general problem.
- Fresh computational result, **not yet independently reproduced or refereed**. Soundness rests
  on SMS's exhaustive isomorph-free generation + the Glasgow (complete) subgraph propagator +
  the min-degree CNF; the two anchors above validate the composition at n=10 and n≤16. A fully
  rigorous claim would want an independent re-verification or a proof certificate.

(The earlier pure-Python CEGAR-SAT run — see `results.md` — independently reached bound ≥ 20.)
