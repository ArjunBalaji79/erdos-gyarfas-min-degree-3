"""Base CNF, minimum-degree-3 constraint, and model decoding."""
from __future__ import annotations

from typing import Dict, List, Tuple

from .encoding import (
    VarPool,
    edge_var,
    incident_edges,
    num_edge_vars,
    reified_atleast,
)


def base_cnf(n: int) -> Tuple[List[List[int]], Dict[int, List[int]], VarPool]:
    """Return (cnf, incident, pool).

    The base CNF has no clauses yet -- only the variable layout is fixed: edge
    variables 1..C(n,2). ``incident[v]`` lists the edge vars touching vertex v.
    ``pool`` hands out fresh auxiliary ids past the edge variables.
    """
    cnf: List[List[int]] = []
    incident = incident_edges(n)
    pool = VarPool(n)
    return cnf, incident, pool


def add_min3(
    cnf: List[List[int]], incident: Dict[int, List[int]], n: int, pool: VarPool
) -> Dict[int, int]:
    """Enforce deg(v) >= 3 for every vertex.

    Returns {v: cubic_v} where ``cubic_v`` is the reified literal
    "deg(v) >= 3"; the literal is asserted true as a unit clause.
    """
    cubic: Dict[int, int] = {}
    for v in range(n):
        lit = reified_atleast(incident[v], 3, cnf, pool)
        cnf.append([lit])  # assert deg(v) >= 3
        cubic[v] = lit
    return cubic


def decode(model: List[int], n: int) -> List[Tuple[int, int]]:
    """Decode a SAT model into the list of present edges (i, j), i < j."""
    truth = set(lit for lit in model if lit > 0)
    edges = []
    for i in range(n):
        for j in range(i + 1, n):
            if edge_var(i, j, n) in truth:
                edges.append((i, j))
    return edges


def edges_to_graph6(edges: List[Tuple[int, int]], n: int) -> str:
    """Encode an edge list as a graph6 string (nauty's format)."""
    import networkx as nx

    g = nx.Graph()
    g.add_nodes_from(range(n))
    g.add_edges_from(edges)
    # networkx returns bytes like b">>graph6<<...\n" optionally; normalise.
    s = nx.to_graph6_bytes(g, header=False).decode().strip()
    return s
