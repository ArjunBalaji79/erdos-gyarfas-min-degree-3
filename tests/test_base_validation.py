"""Gate 1 -- base validation.

For small n, the graphs admitted by (base & min3) must be exactly the
min-degree-3 graphs that geng enumerates (compared as isomorphism classes).
Catches base-encoding / min-degree bugs. Runs on the full (non-C4-free)
domain, so it is restricted to tiny n.
"""
import pytest

from erdos_gyarfas.ground_truth.nauty import canonical, geng_min3
from erdos_gyarfas.sat.base import add_min3, base_cnf
from erdos_gyarfas.sat.enumerate import canonical_set, enumerate_graphs
from erdos_gyarfas.sat.structural import add_lex_canon


def _sat_iso(n):
    # lex_canon is sound -> same iso classes, far fewer labeled models.
    cnf, incident, pool = base_cnf(n)
    add_min3(cnf, incident, n, pool)
    add_lex_canon(cnf, n, pool)
    graphs = enumerate_graphs(cnf, n, cap=200000)
    return canonical_set(graphs, n)


def _ref_iso(n):
    # n <= 7: every min-degree-3 graph is connected, so -c is complete.
    lines = geng_min3(n, connected=True, max_degree=n - 1)
    return set(canonical(lines))


@pytest.mark.parametrize("n", [4, 5, 6])
def test_base_matches_geng(n):
    sat = _sat_iso(n)
    ref = _ref_iso(n)
    assert sat == ref, (
        f"n={n}: missing={len(ref - sat)} extra={len(sat - ref)}"
    )
