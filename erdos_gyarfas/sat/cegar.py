"""The CEGAR loop.

    loop:
        model = SAT(base & min3 & structural(a) & lex_canon & refinements)
        if UNSAT: return UNSAT
        G = decode(model)
        bad = power_of_2_cycle_detector(G)   # the sole certifier
        if bad is None: return SAT, G        # a real counterexample
        refinements &= forbid(bad)

The detector is never weakened: a model that survives it is a genuine
counterexample and the search halts loudly.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from pysat.solvers import Solver

from .base import add_min3, base_cnf, decode
from .detector import find_power_of_2_cycle
from .encoding import edge_var
from .structural import add_c4_free, add_lex_canon, add_property_a


@dataclass
class SearchResult:
    n: int
    status: str                       # "UNSAT" | "SAT" | "WALL"
    refinements: int = 0
    elapsed: float = 0.0
    counterexample: Optional[List[Tuple[int, int]]] = None
    config: Dict = field(default_factory=dict)


def build_formula(
    n: int,
    use_property_a: bool = True,
    use_lex: bool = True,
    use_c4free: bool = False,
) -> Tuple[List[List[int]], Dict[int, List[int]]]:
    """Assemble the static part of the formula (everything except refinements)."""
    cnf, incident, pool = base_cnf(n)
    add_min3(cnf, incident, n, pool)
    if use_property_a:
        add_property_a(cnf, incident, n, pool)
    if use_c4free:
        add_c4_free(cnf, n)
    if use_lex:
        add_lex_canon(cnf, n, pool)
    return cnf, incident


def search(
    n: int,
    use_property_a: bool = True,
    use_lex: bool = True,
    use_c4free: bool = False,
    time_budget: Optional[float] = None,
    max_refinements: Optional[int] = None,
    solver_name: str = "cadical195",
) -> SearchResult:
    """Run CEGAR for a single order n.

    ``time_budget`` (seconds) and ``max_refinements`` are stopping rules; if
    either is hit before resolution the status is "WALL". ``solver_name`` selects
    the PySAT backend (e.g. "glucose4", "glucose42", "cadical195", "minisat22").
    """
    config = dict(
        property_a=use_property_a, lex=use_lex, c4free=use_c4free,
        time_budget=time_budget, max_refinements=max_refinements,
        solver=solver_name,
    )
    cnf, _ = build_formula(n, use_property_a, use_lex, use_c4free)
    solver = Solver(name=solver_name, bootstrap_with=cnf)
    start = time.monotonic()
    refinements = 0
    try:
        while True:
            if time_budget is not None and time.monotonic() - start > time_budget:
                return SearchResult(n, "WALL", refinements,
                                    time.monotonic() - start, None, config)
            if max_refinements is not None and refinements >= max_refinements:
                return SearchResult(n, "WALL", refinements,
                                    time.monotonic() - start, None, config)
            if not solver.solve():
                return SearchResult(n, "UNSAT", refinements,
                                    time.monotonic() - start, None, config)
            edges = decode(solver.get_model(), n)
            bad = find_power_of_2_cycle(edges, n)
            if bad is None:
                # Survived the certifier -> genuine counterexample.
                return SearchResult(n, "SAT", refinements,
                                    time.monotonic() - start, edges, config)
            solver.add_clause([-edge_var(u, v, n) for (u, v) in bad])
            refinements += 1
    finally:
        solver.delete()
