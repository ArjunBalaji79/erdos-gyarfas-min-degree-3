"""Build the canonical reference set of C4-free min-degree-3 graphs for the
Gate-3 cross-check, optionally filtered by structural property (a)."""
from __future__ import annotations

from typing import Set

from ..sat.detector import graph6_to_edges, is_c4_free, satisfies_property_a
from .nauty import canonical, geng_min3


def reference_set(n: int, with_property_a: bool, connected: bool = True) -> Set[str]:
    """Canonical graph6 set of all C4-free min-degree-3 graphs on n vertices
    (filtered by property (a) when requested)."""
    lines = geng_min3(n, connected=connected)
    kept = []
    for ln in lines:
        edges, gn = graph6_to_edges(ln)
        if gn != n:
            continue
        if not is_c4_free(edges, n):
            continue
        if with_property_a and not satisfies_property_a(edges, n):
            continue
        kept.append(ln)
    return set(canonical(kept))
