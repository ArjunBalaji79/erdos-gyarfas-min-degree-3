"""Enumerate the graphs a static formula admits, as canonical iso-classes.

Used by the Gate-1 and Gate-3 cross-checks. Blocking clauses are projected
onto the EDGE variables only -- otherwise distinct auxiliary-variable
assignments would yield spurious duplicate models of the same graph.
"""
from __future__ import annotations

from typing import List, Optional, Set, Tuple

from pysat.solvers import Glucose4

from ..ground_truth.nauty import canonical
from .base import decode, edges_to_graph6
from .encoding import edge_var, num_edge_vars


def enumerate_graphs(
    cnf: List[List[int]],
    n: int,
    cap: Optional[int] = None,
) -> List[List[Tuple[int, int]]]:
    """Return every distinct graph (edge list) satisfying ``cnf``.

    ``cap`` optionally bounds the number of models; exceeding it raises so a
    test never silently truncates.
    """
    solver = Glucose4(bootstrap_with=cnf)
    n_edge = num_edge_vars(n)
    edge_ids = list(range(1, n_edge + 1))
    graphs: List[List[Tuple[int, int]]] = []
    try:
        while solver.solve():
            model = solver.get_model()
            mset = set(model)
            edges = decode(model, n)
            graphs.append(edges)
            # block this exact edge-projection (positive + negative edge lits)
            block = [(-eid if eid in mset else eid) for eid in edge_ids]
            solver.add_clause(block)
            if cap is not None and len(graphs) > cap:
                raise RuntimeError(f"enumerate_graphs exceeded cap={cap} for n={n}")
    finally:
        solver.delete()
    return graphs


def canonical_set(graphs: List[List[Tuple[int, int]]], n: int) -> Set[str]:
    """Reduce a list of graphs to the set of canonical graph6 strings."""
    g6 = [edges_to_graph6(edges, n) for edges in graphs]
    return set(canonical(g6))
