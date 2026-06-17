"""Gate 0 -- reified counter unit test.

Brute-force every assignment of m input bits (m up to 12) and every threshold
k, and check that the literal returned by ``reified_atleast`` is true under the
SAT model iff at least k inputs are true.  Must pass exhaustively.
"""
import itertools

import pytest
from pysat.solvers import Glucose4

from erdos_gyarfas.sat.encoding import VarPool, reified_atleast


def _check(m: int, k: int) -> None:
    # Inputs are variables 1..m; allocate the pool above them.
    inputs = list(range(1, m + 1))
    pool = VarPool(0)
    # VarPool(0) starts at 1; bump it past the input vars manually.
    pool._next = m + 1
    cnf: list = []
    out = reified_atleast(inputs, k, cnf, pool)

    for bits in itertools.product([False, True], repeat=m):
        assumptions = [(v if b else -v) for v, b in zip(inputs, bits)]
        true_count = sum(bits)
        expected = true_count >= k

        solver = Glucose4(bootstrap_with=cnf)
        sat = solver.solve(assumptions=assumptions)
        assert sat, f"counter CNF UNSAT under fixed inputs m={m} k={k} bits={bits}"
        model = solver.get_model()
        solver.delete()

        val = out > 0
        mval = model[abs(out) - 1] > 0 if abs(out) <= len(model) else None
        # out may be a positive literal of an aux var; read its truth from model
        got = mval if mval is not None else val
        assert got == expected, (
            f"m={m} k={k} bits={bits}: counter said {got}, expected {expected} "
            f"(true_count={true_count})"
        )


@pytest.mark.parametrize("m", [1, 2, 3, 4, 5, 6, 7, 8])
@pytest.mark.parametrize("k", [1, 2, 3, 4])
def test_atleast_small(m, k):
    _check(m, k)


def test_atleast_edge_thresholds():
    # k larger than m -> always false; k=0 -> always true.
    for m in range(1, 6):
        _check(m, m)      # exactly-all threshold
        _check(m, m + 1)  # impossible threshold
