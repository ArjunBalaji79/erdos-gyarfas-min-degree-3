"""Independent verification of a CEGAR run's lemma certificate.

Each refinement clause forbids one cycle. For the UNSAT verdict to be a sound
verification of the conjecture at order n, every such forbidden cycle must be a
genuine simple cycle whose length is a power of two -- otherwise the loop forbade
something it had no right to. This module re-checks each certificate entry from
scratch (independently of the solver), so the result is auditable rather than
"trust the loop".

A clean UNSAT then means: no minimum-degree-3 graph on n vertices avoids all of
these (verified) power-of-2 cycles -- and a real counterexample would avoid every
power-of-2 cycle, so it would satisfy the formula. Hence none exists.
"""
from __future__ import annotations

from typing import List, Tuple


def is_power_of_two(L: int) -> bool:
    return L >= 4 and (L & (L - 1)) == 0


def is_simple_cycle(edges: List[Tuple[int, int]]) -> bool:
    """True iff ``edges`` is exactly one simple cycle (each vertex degree 2,
    edges distinct, single connected component, |E| == |V|)."""
    norm = [(min(u, v), max(u, v)) for (u, v) in edges]
    if len(set(norm)) != len(norm):
        return False  # repeated edge
    deg = {}
    adj = {}
    for (u, v) in norm:
        if u == v:
            return False
        deg[u] = deg.get(u, 0) + 1
        deg[v] = deg.get(v, 0) + 1
        adj.setdefault(u, []).append(v)
        adj.setdefault(v, []).append(u)
    if any(d != 2 for d in deg.values()):
        return False
    if len(norm) != len(deg):
        return False  # single cycle needs |E| == |V|
    # connectivity: walk from one vertex, must reach all
    start = next(iter(deg))
    seen = {start}
    stack = [start]
    while stack:
        x = stack.pop()
        for y in adj[x]:
            if y not in seen:
                seen.add(y)
                stack.append(y)
    return len(seen) == len(deg)


def verify_certificate(certificate, n: int) -> Tuple[bool, str]:
    """Check every forbidden cycle is a genuine power-of-two simple cycle.

    Returns (ok, message). ``certificate`` is the list of (length, edges) entries
    produced by ``cegar.search(record_certificate=True)``.
    """
    if certificate is None:
        return False, "no certificate recorded"
    for idx, (length, edges) in enumerate(certificate):
        if length != len(edges):
            return False, f"entry {idx}: declared length {length} != {len(edges)} edges"
        if not is_power_of_two(length):
            return False, f"entry {idx}: length {length} is not a power of two >= 4"
        for (u, v) in edges:
            if not (0 <= u < n and 0 <= v < n):
                return False, f"entry {idx}: edge ({u},{v}) out of range for n={n}"
        if not is_simple_cycle(edges):
            return False, f"entry {idx}: edges do not form a single simple cycle"
    return True, f"all {len(certificate)} forbidden cycles are valid power-of-2 simple cycles"


def verify_result(result, n: int) -> Tuple[bool, str]:
    """Verify a SearchResult: certificate lemmas valid AND (if present) the
    independent re-check agrees on UNSAT."""
    ok, msg = verify_certificate(result.certificate, n)
    if not ok:
        return False, f"certificate INVALID: {msg}"
    if result.status == "UNSAT" and result.recheck is not None and result.recheck != "UNSAT":
        return False, f"independent re-check DISAGREES: {result.recheck}"
    rc = f"; independent re-check={result.recheck}" if result.recheck else ""
    return True, f"{msg}{rc}"
