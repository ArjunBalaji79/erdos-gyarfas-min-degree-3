"""Base SAT encoding: edge variables, a fresh-variable pool, and a fully
reified Sinz "at-least-k" sequential counter.

Conventions
-----------
* Vertices are 0-indexed: 0 .. n-1.
* Edge variables occupy ids 1 .. C(n,2); auxiliary (counter) variables are
  allocated afterwards by a VarPool.
* A *literal* is a nonzero int (positive = variable, negative = its negation).
  Internally the reified counter also threads Python booleans ``True``/``False``
  to represent constant-folded register cells; these never escape into clauses.

The single most important invariant is checked exhaustively by Gate 0
(tests/test_reified_counter.py): the literal returned by ``reified_atleast`` is
true under an assignment iff at least ``k`` of the inputs are true.
"""
from __future__ import annotations

from typing import List, Sequence, Union

Lit = int
# A register cell is either a literal (int) or a folded constant (bool).
Cell = Union[int, bool]


def edge_var(i: int, j: int, n: int) -> int:
    """Return the SAT variable id for the unordered edge {i, j}.

    Pairs are laid out in row-major upper-triangular order:
    (0,1),(0,2),...,(0,n-1),(1,2),... so ids run 1 .. C(n,2).
    """
    if i == j:
        raise ValueError(f"no self-loop edge ({i},{i})")
    if i > j:
        i, j = j, i
    if not (0 <= i < n and 0 <= j < n):
        raise ValueError(f"edge ({i},{j}) out of range for n={n}")
    # number of pairs whose first coordinate is < i
    offset = i * n - (i * (i + 1)) // 2
    return 1 + offset + (j - i - 1)


def num_edge_vars(n: int) -> int:
    return n * (n - 1) // 2


def incident_edges(n: int) -> dict:
    """Return {v: [edge_var(v,u) for all u != v]}."""
    return {v: [edge_var(v, u, n) for u in range(n) if u != v] for v in range(n)}


class VarPool:
    """Hands out fresh variable ids starting just past the edge variables."""

    def __init__(self, n: int):
        self._next = num_edge_vars(n) + 1

    def new(self) -> int:
        v = self._next
        self._next += 1
        return v

    @property
    def top(self) -> int:
        """Highest id allocated so far (0 if none beyond edges... )."""
        return self._next - 1


def _neg(c: Cell) -> Cell:
    return (not c) if isinstance(c, bool) else -c


def _emit(cnf: List[List[int]], cell_clause: Sequence[Cell]) -> None:
    """Append a clause built from cells, folding constants.

    A ``True`` cell satisfies the clause (drop it). A ``False`` cell is removed.
    If every cell folds away we emit the empty clause (forces UNSAT) -- this
    should never happen for well-formed counter encodings.
    """
    lits: List[int] = []
    for c in cell_clause:
        if isinstance(c, bool):
            if c:
                return  # clause satisfied
            # False -> drop this literal
        else:
            lits.append(c)
    cnf.append(lits)


def reified_atleast(
    input_lits: Sequence[Lit], k: int, cnf: List[List[int]], pool: VarPool
) -> Lit:
    """Return a literal that is TRUE iff at least ``k`` of ``input_lits`` hold.

    Clauses realising the full equivalence are appended to ``cnf``. Fresh
    auxiliary variables are drawn from ``pool``.

    Implements a fully reified Sinz sequential counter via register cells
    ``r[i][j]`` = "at least j of the first i inputs are true", with the
    recurrence  r[i][j] <-> r[i-1][j] OR (x_i AND r[i-1][j-1]).
    """
    m = len(input_lits)
    if k <= 0:
        # always true: a fresh var forced true
        v = pool.new()
        cnf.append([v])
        return v
    if k > m:
        # impossible: a fresh var forced false
        v = pool.new()
        cnf.append([-v])
        return v

    cap = k  # we never need register columns beyond k

    def reg_const(i: int, j: int) -> Cell:
        """Constant value of r[i][j] when it is forced, else None."""
        if j <= 0:
            return True  # at least 0 always holds
        if j > i:
            return False  # cannot have j>=1 true among fewer than j inputs
        return None

    # r[i] is a dict j -> Cell for j in 1..min(i,cap); j<=0 -> True, j>i -> False
    prev: dict = {}  # represents row i-1, only the materialised columns

    def cell(row: dict, i: int, j: int) -> Cell:
        c = reg_const(i, j)
        if c is not None:
            return c
        return row[j]

    # row 0: all r[0][j>=1] are False (handled by reg_const)
    for i in range(1, m + 1):
        x = input_lits[i - 1]
        cur: dict = {}
        for j in range(1, min(i, cap) + 1):
            A = cell(prev, i - 1, j)        # r[i-1][j]
            C = cell(prev, i - 1, j - 1)    # r[i-1][j-1]
            B = x
            # If both feeders are constants we can fold the whole cell.
            if isinstance(A, bool) and isinstance(C, bool):
                # R <-> A OR (B AND C)
                if A:
                    cur[j] = True
                    continue
                if not C:
                    cur[j] = False
                    continue
                # A False, C True  => R <-> B
                cur[j] = B
                continue
            R = pool.new()
            # R -> (A OR (B AND C)) : two clauses
            _emit(cnf, [_neg(R), A, B])
            _emit(cnf, [_neg(R), A, C])
            # (A OR (B AND C)) -> R
            _emit(cnf, [_neg(A), R])            # A -> R
            _emit(cnf, [_neg(B), _neg(C), R])   # (B AND C) -> R
            cur[j] = R
        prev = cur

    out = cell(prev, m, k)
    # out should be a literal for 1<=k<=m, but fold defensively.
    if isinstance(out, bool):
        v = pool.new()
        cnf.append([v] if out else [-v])
        return v
    return out
