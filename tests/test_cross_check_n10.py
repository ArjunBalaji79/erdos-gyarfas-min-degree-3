"""Gate 3 -- soundness cross-check at n = 10 (THE KEY TEST).

For each structural config, the C4-free min-degree-3 graphs admitted by
(min3 & structural & lex_canon & c4_free) must equal -- as isomorphism
classes -- those geng enumerates and filters. missing = extra = 0.

This is the check that catches an over-constraining encoding (spurious UNSAT):
a too-strong constraint shows up as missing > 0. Run it every time the
encoding changes.
"""
import pytest

from erdos_gyarfas.ground_truth.reference import reference_set
from erdos_gyarfas.sat.cegar import build_formula
from erdos_gyarfas.sat.enumerate import canonical_set, enumerate_graphs

N = 10


@pytest.mark.parametrize("use_a", [False, True], ids=["config()", "config(a)"])
def test_cross_check_n10(use_a):
    cnf, _ = build_formula(N, use_property_a=use_a, use_lex=True, use_c4free=True)
    sat = canonical_set(enumerate_graphs(cnf, N, cap=500000), N)
    ref = reference_set(N, with_property_a=use_a)
    missing = ref - sat
    extra = sat - ref
    assert not missing, f"spurious UNSAT: {len(missing)} iso-classes missing from SAT side"
    assert not extra, f"over-permissive: {len(extra)} extra iso-classes on SAT side"
