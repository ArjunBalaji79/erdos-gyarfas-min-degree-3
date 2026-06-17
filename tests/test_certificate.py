"""Gate 5 -- certificate verification.

Every refinement clause a CEGAR run adds must forbid a genuine simple cycle whose
length is a power of two, and an independent second solver must agree the result
is UNSAT. This gate runs a few small orders end-to-end and checks both.
"""
import pytest

from erdos_gyarfas.sat.cegar import search
from erdos_gyarfas.sat.verify import is_power_of_two, is_simple_cycle, verify_result


def test_helpers():
    assert is_power_of_two(4) and is_power_of_two(8) and is_power_of_two(16)
    assert not is_power_of_two(2) and not is_power_of_two(6) and not is_power_of_two(12)
    assert is_simple_cycle([(0, 1), (1, 2), (2, 3), (3, 0)])      # 4-cycle
    assert not is_simple_cycle([(0, 1), (1, 2), (2, 0), (0, 3)])  # not 2-regular
    assert not is_simple_cycle([(0, 1), (1, 2), (2, 3), (3, 4)])  # path, not closed


@pytest.mark.parametrize("n", [12, 14, 16])
def test_certificate_and_recheck(n):
    r = search(n, record_certificate=True, recheck_solver="glucose42")
    assert r.status == "UNSAT"
    assert r.recheck == "UNSAT", f"n={n}: independent re-check said {r.recheck}"
    ok, msg = verify_result(r, n)
    assert ok, f"n={n}: {msg}"
    assert len(r.certificate) == r.refinements
