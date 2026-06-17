"""Local frontier driver (Gates 5-6).

Ladder n upward by 1, running CEGAR with a per-size wall-time budget. Each
UNSAT advances the published lower bound. A SAT result is a genuine
counterexample and halts loudly. A WALL result (budget hit) is the stopping
rule -- larger n would only be harder, so we stop.

    python -m erdos_gyarfas.experiments.run_frontier --start 17 --end 24 \
        --time-budget 2700 --out erdos_gyarfas/experiments/results.csv
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
from typing import List

from ..sat.cegar import SearchResult, search


def _write_csv(path: str, rows: List[SearchResult]) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["n", "status", "refinements", "elapsed_s", "config"])
        for r in rows:
            w.writerow([r.n, r.status, r.refinements, f"{r.elapsed:.2f}",
                        json.dumps(r.config)])


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Erdos-Gyarfas CEGAR frontier")
    ap.add_argument("--start", type=int, default=17)
    ap.add_argument("--end", type=int, default=24)
    ap.add_argument("--time-budget", type=float, default=2700.0,
                    help="per-size wall-time budget in seconds (default 45 min)")
    ap.add_argument("--no-property-a", action="store_true")
    ap.add_argument("--no-lex", action="store_true")
    ap.add_argument("--out", type=str, default="erdos_gyarfas/experiments/results.csv")
    args = ap.parse_args(argv)

    rows: List[SearchResult] = []
    bound = args.start  # last n proven UNSAT + 1 is the bound
    for n in range(args.start, args.end + 1):
        print(f"[n={n}] solving (budget {args.time_budget:.0f}s)...", flush=True)
        t = time.monotonic()
        r = search(n, use_property_a=not args.no_property_a,
                   use_lex=not args.no_lex, time_budget=args.time_budget)
        rows.append(r)
        print(f"[n={n}] {r.status}  refinements={r.refinements}  "
              f"{r.elapsed:.1f}s  (wall {time.monotonic()-t:.1f}s)", flush=True)

        if r.status == "SAT":
            print("\n" + "!" * 60)
            print(f"!!! COUNTEREXAMPLE FOUND at n={n} -- survived the detector !!!")
            print(f"!!! edges: {r.counterexample}")
            print("!" * 60)
            _write_csv(args.out, rows)
            return 2
        if r.status == "WALL":
            print(f"[n={n}] hit wall-time budget -- stopping ladder.", flush=True)
            break
        bound = n + 1  # UNSAT at n -> conjecture holds for all <= n -> bound n+1

    _write_csv(args.out, rows)
    print(f"\nResults -> {args.out}")
    print(f"Established: Erdos-Gyarfas holds for min-degree-3 graphs on "
          f"<= {bound - 1} vertices  (bound >= {bound}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
