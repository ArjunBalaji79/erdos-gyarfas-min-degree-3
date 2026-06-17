"""Thin wrappers around nauty's ``geng`` (enumeration) and ``labelg``
(canonical labelling). nauty must be installed at the system level
(``brew install nauty`` / ``apt install nauty``)."""
from __future__ import annotations

import shutil
import subprocess
from typing import List, Optional

_SEARCH = ["geng", "/opt/homebrew/bin/geng", "/usr/local/bin/geng", "/usr/bin/geng"]
_SEARCH_L = ["labelg", "/opt/homebrew/bin/labelg", "/usr/local/bin/labelg", "/usr/bin/labelg"]


def _find(cands: List[str]) -> str:
    for c in cands:
        p = shutil.which(c) or (c if shutil.os.path.exists(c) else None)
        if p:
            return p
    raise FileNotFoundError(
        "nauty binary not found; install nauty (brew install nauty)"
    )


def max_degree_cap(n: int) -> int:
    """Largest degree allowed by the C4-free counting bound (salvage 3.5):
    d(d-1) <= (n-1)(n-6).  Clamped to [3, n-1]."""
    rhs = (n - 1) * (n - 6)
    d = 3
    while (d + 1) * d <= rhs and d + 1 <= n - 1:
        d += 1
    return max(3, min(d, n - 1))


def geng_min3(
    n: int,
    connected: bool = True,
    max_degree: Optional[int] = None,
    timeout: Optional[float] = 600.0,
) -> List[str]:
    """Return graph6 strings for all min-degree-3 graphs on n vertices.

    ``max_degree`` defaults to the C4-free counting cap (salvage 3.5); pass an
    explicit value (e.g. ``n-1`` for no cap) for the non-C4-free Gate-1 domain.
    With ``connected`` this is complete ground truth for n <= 19 (see salvage
    3.5 connectivity note)."""
    geng = _find(_SEARCH)
    cap = max_degree_cap(n) if max_degree is None else min(max_degree, n - 1)
    args = [geng, "-q"]
    if connected:
        args.append("-c")
    args += [f"-d3", f"-D{cap}", str(n)]
    out = subprocess.run(
        args, capture_output=True, text=True, timeout=timeout, check=True
    )
    return [ln for ln in out.stdout.splitlines() if ln.strip()]


def canonical(graph6_lines: List[str], timeout: Optional[float] = 600.0) -> List[str]:
    """Canonicalise a batch of graph6 strings via labelg. Order is preserved."""
    if not graph6_lines:
        return []
    labelg = _find(_SEARCH_L)
    inp = "\n".join(graph6_lines) + "\n"
    out = subprocess.run(
        [labelg, "-q"], input=inp, capture_output=True, text=True,
        timeout=timeout, check=True,
    )
    return [ln for ln in out.stdout.splitlines() if ln.strip()]
