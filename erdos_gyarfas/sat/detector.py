"""The power-of-2 cycle detector -- the sole certifier.

A SAT model that survives this detector (no power-of-2 cycle found) is a real
counterexample to Erdos-Gyarfas. The detector must therefore be COMPLETE: if a
power-of-2 cycle exists it must return one. We search lengths 4, 8, 16, ...
(smallest first) with a bounded DFS that is exact for each target length.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import networkx as nx


def powers_of_two_upto(n: int) -> List[int]:
    """Cycle lengths that are powers of two and <= n (smallest cycle is 4)."""
    out, L = [], 4
    while L <= n:
        out.append(L)
        L *= 2
    return out


def _adj(edges: List[Tuple[int, int]], n: int) -> Dict[int, List[int]]:
    adj: Dict[int, List[int]] = {v: [] for v in range(n)}
    for (u, v) in edges:
        adj[u].append(v)
        adj[v].append(u)
    return adj


def _find_cycle_len(adj: Dict[int, List[int]], n: int, L: int) -> Optional[List[int]]:
    """Return a simple cycle of EXACTLY length L as a vertex list, or None.

    To avoid enumerating each cycle L times (once per rotation/direction) we
    require the start vertex to be the minimum vertex on the cycle, and fix an
    orientation by requiring the second vertex to be smaller than the last.
    """
    for start in range(n):
        path = [start]
        on_path = {start}

        def dfs(u: int) -> Optional[List[int]]:
            if len(path) == L:
                # close the cycle back to start
                if start in adj[u]:
                    # orientation tie-break: second < last (dedupe direction)
                    if path[1] < path[-1]:
                        return list(path)
                return None
            for w in adj[u]:
                if w < start:
                    continue  # start must be the minimum vertex
                if w in on_path:
                    continue
                # prune: need at least (L - len(path)) more distinct vertices
                path.append(w)
                on_path.add(w)
                res = dfs(w)
                if res is not None:
                    return res
                path.pop()
                on_path.discard(w)
            return None

        res = dfs(start)
        if res is not None:
            return res
    return None


def find_power_of_2_cycle(
    edges: List[Tuple[int, int]], n: int
) -> Optional[List[Tuple[int, int]]]:
    """Return the edge list of a power-of-2 cycle if one exists, else None.

    Returned edges are normalised (i < j) for use in a refinement clause.
    """
    adj = _adj(edges, n)
    for L in powers_of_two_upto(n):
        cyc = _find_cycle_len(adj, n, L)
        if cyc is not None:
            cyc_edges = []
            for idx in range(L):
                u, v = cyc[idx], cyc[(idx + 1) % L]
                cyc_edges.append((min(u, v), max(u, v)))
            return cyc_edges
    return None


# --- graph predicates used by the Gate-3 ground-truth filtering ---

def is_c4_free(edges: List[Tuple[int, int]], n: int) -> bool:
    adj = _adj(edges, n)
    nbr = {v: set(adj[v]) for v in range(n)}
    for u in range(n):
        for v in range(u + 1, n):
            if len(nbr[u] & nbr[v]) >= 2:
                return False
    return True


def satisfies_property_a(edges: List[Tuple[int, int]], n: int) -> bool:
    """deg>=4 vertices form an independent set."""
    deg = {v: 0 for v in range(n)}
    for (u, v) in edges:
        deg[u] += 1
        deg[v] += 1
    for (u, v) in edges:
        if deg[u] >= 4 and deg[v] >= 4:
            return False
    return True


def graph6_to_edges(line: str) -> Tuple[List[Tuple[int, int]], int]:
    g = nx.from_graph6_bytes(line.strip().encode())
    n = g.number_of_nodes()
    edges = [(min(u, v), max(u, v)) for (u, v) in g.edges()]
    return edges, n
