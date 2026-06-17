"""Structural constraints.

* ``add_property_a`` -- the only structural property the rigorous frontier
  needs: degree->=4 vertices form an independent set (self-proved in the
  salvage notes).
* ``add_c4_free`` -- forbid every 4-cycle. Used by the Gate-3 cross-check so
  the SAT side matches the C4-free ground truth, and available as a sound
  static speedup (4 = 2^2 is always a forbidden power-of-2 cycle).
* ``add_lex_canon`` -- a sound symmetry break (adjacent-transposition
  lex-leader). It never removes a whole isomorphism class, so it preserves
  UNSAT; Gate 3 is the safety net that catches an accidentally unsound break
  (it would show missing > 0).
"""
from __future__ import annotations

from typing import Dict, List

from .encoding import VarPool, edge_var, reified_atleast


def add_property_a(
    cnf: List[List[int]], incident: Dict[int, List[int]], n: int, pool: VarPool
) -> Dict[int, int]:
    """deg>=4 vertices form an independent set.

    Returns {v: high_v} with high_v the reified literal "deg(v) >= 4".
    """
    high = {v: reified_atleast(incident[v], 4, cnf, pool) for v in range(n)}
    for i in range(n):
        for j in range(i + 1, n):
            # not (high_i and high_j and edge_ij)
            cnf.append([-high[i], -high[j], -edge_var(i, j, n)])
    return high


def add_c4_free(cnf: List[List[int]], n: int) -> None:
    """Forbid every 4-cycle a-c-b-d-a (edges ac, cb, bd, da)."""
    for a in range(n):
        for b in range(a + 1, n):
            # c, d are the two "middle" vertices; the cycle is a-c-b-d-a.
            others = [v for v in range(n) if v != a and v != b]
            for ci in range(len(others)):
                for di in range(ci + 1, len(others)):
                    c, d = others[ci], others[di]
                    cnf.append([
                        -edge_var(a, c, n),
                        -edge_var(c, b, n),
                        -edge_var(b, d, n),
                        -edge_var(d, a, n),
                    ])


def _lex_leq(cnf: List[List[int]], a, b, pool: VarPool) -> None:
    """Append clauses enforcing the bit-vector a <=_lex b.

    ``a`` and ``b`` are equal-length lists of literals. Uses an equal-prefix
    chain: c_t = "positions 1..t-1 are all equal". Fully reified so the
    constraint fires exactly on the truly-equal prefix.
    """
    assert len(a) == len(b)
    c = True  # c_1: empty prefix is equal (Python-bool constant fold)
    for t in range(len(a)):
        at, bt = a[t], b[t]
        # constraint: c -> (a_t <= b_t)  i.e.  ~c v ~a_t v b_t
        if c is True:
            cnf.append([-at, bt])
        else:
            cnf.append([-c, -at, bt])
        if t == len(a) - 1:
            break
        # q_t <-> (a_t == b_t)
        q = pool.new()
        cnf.append([-q, -at, bt])
        cnf.append([-q, at, -bt])
        cnf.append([q, -at, -bt])
        cnf.append([q, at, bt])
        # c_{t+1} <-> (c_t and q_t)
        cnext = pool.new()
        if c is True:
            # c_{t+1} <-> q_t
            cnf.append([-cnext, q])
            cnf.append([cnext, -q])
        else:
            cnf.append([-cnext, c])
            cnf.append([-cnext, q])
            cnf.append([cnext, -c, -q])
        c = cnext


def add_lex_canon(cnf: List[List[int]], n: int, pool: VarPool, full: bool = False) -> None:
    """Transposition lex-leader symmetry break (sound, polynomial-size).

    For each checked vertex transposition (p, q) require the adjacency matrix
    (read row-major over the upper triangle) to be lexicographically <= the
    matrix obtained by swapping vertices p and q. This never removes a whole
    isomorphism class, so it preserves UNSAT; Gate 3 verifies it stays sound
    (missing = 0).

    ``full=False`` (default) checks only adjacent transpositions (n-1
    constraints): cheap to build and empirically the best build/solve trade-off
    on the frontier. ``full=True`` checks all C(n,2) transpositions -- stronger
    pruning but a much larger CNF that solved slower in practice.
    """
    pairs = [(i, j) for i in range(n) for j in range(i + 1, n)]

    if full:
        swaps = [(p, q) for p in range(n) for q in range(p + 1, n)]
    else:
        swaps = [(p, p + 1) for p in range(n - 1)]

    def swap(v, p, q):
        if v == p:
            return q
        if v == q:
            return p
        return v

    for (p, q) in swaps:
        a_vec, b_vec = [], []
        for (i, j) in pairs:
            pi, pj = swap(i, p, q), swap(j, p, q)
            if (min(pi, pj), max(pi, pj)) == (i, j):
                continue  # position fixed by the swap -> a_t == b_t, skip
            a_vec.append(edge_var(i, j, n))
            b_vec.append(edge_var(pi, pj, n))
        if a_vec:
            _lex_leq(cnf, a_vec, b_vec, pool)
