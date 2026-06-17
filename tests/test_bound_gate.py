"""Gate 4 -- bound reproduction.

Run CEGAR for every n in 4..16 with property (a) ON and OFF. Both must be
UNSAT and they must agree. This reproduces the known >= 17 baseline before any
new claim, and confirms property (a) never changes a result (only the speed).
"""
import pytest

from erdos_gyarfas.sat.cegar import search


@pytest.mark.parametrize("n", list(range(4, 17)))
def test_bound_reproduction(n):
    plain = search(n, use_property_a=False, use_lex=True)
    struct = search(n, use_property_a=True, use_lex=True)
    assert plain.status == "UNSAT", f"n={n} plain: {plain.status}"
    assert struct.status == "UNSAT", f"n={n} structural: {struct.status}"
    assert plain.status == struct.status, f"n={n}: configs disagree"
