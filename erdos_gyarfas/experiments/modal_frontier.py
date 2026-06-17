"""Cloud frontier driver on Modal -- detached, with hard cost guards.

The frontier only needs the SAT solver + the cycle detector (no nauty), so the
image is just python-sat + networkx. Each size runs in its own 1-core container
and writes its result to a persistent Volume, so results survive even if the
laptop disconnects.

COST SAFETY -- three independent guards, because an unbounded cloud bill is the
thing we must never risk:
  1. ``search(time_budget=...)``   SOFT stop: CEGAR returns status "WALL".
  2. ``@app.function(timeout=...)`` HARD ceiling Modal enforces by killing the
     container. Set just above the soft budget; Modal bills ACTUAL runtime, so
     this only bounds the worst case.
  3. ``cpu=1.0`` + ``MAX_SIZES`` + an entrypoint assertion that
     ``soft + margin <= hard`` and that the worst-case core-hours are printed
     before anything is dispatched.

Usage:
    # cheap smoke test (one size, 90s budget) -- foreground, blocks:
    modal run erdos_gyarfas/experiments/modal_frontier.py --start 17 --end 17 --time-budget 90

    # real detached run (close your laptop afterwards):
    modal run --detach erdos_gyarfas/experiments/modal_frontier.py --start 17 --end 23

    # read results back later:
    modal run erdos_gyarfas/experiments/modal_frontier.py::fetch
"""
from __future__ import annotations

import json

import modal

# ---- COST GUARDS (edit these, not the call sites) ----
HARD_TIMEOUT_S = 3900            # 65 min: Modal kills the container at this wall time
DEFAULT_SOFT_BUDGET_S = 3300     # 55 min CEGAR budget; ~10 min headroom for the re-check
                                 # (and the result is persisted BEFORE the re-check anyway)
SAFETY_MARGIN_S = 180            # soft budget must be at least this far below hard
MAX_SIZES = 12                   # refuse to dispatch more containers than this
# Rough Modal CPU price (USD per core-hour) used only to PRINT a worst-case
# estimate before dispatch. Not authoritative billing.
EST_USD_PER_CORE_HOUR = 0.30

app = modal.App("erdos-gyarfas-frontier")

results_volume = modal.Volume.from_name(
    "erdos-gyarfas-results", create_if_missing=True
)
VOL_PATH = "/results"

image = (
    modal.Image.debian_slim(python_version="3.12")
    # python-sat only ships .devN pre-releases on PyPI, so pin the exact version
    # (matches the local env; an explicit ==dev pin installs without --pre).
    .pip_install("python-sat==1.9.dev5", "networkx>=3.0")
    .add_local_python_source("erdos_gyarfas")
)


@app.function(
    image=image,
    timeout=HARD_TIMEOUT_S,
    cpu=1.0,
    volumes={VOL_PATH: results_volume},
)
def solve_n(
    n: int,
    time_budget: float,
    use_property_a: bool = True,
    use_lex: bool = True,
    solver_name: str = "cadical195",
    recheck_max_refinements: int = 500000,
) -> dict:
    """Run CEGAR for a single order n; verify it; persist to the Volume.

    Robust ordering: the primary result + certificate are committed to the
    Volume BEFORE the independent re-check runs, so a slow re-check that hits the
    container hard timeout can never lose a completed result.
    """
    import gzip
    import os

    from erdos_gyarfas.sat.cegar import recheck_unsat, search
    from erdos_gyarfas.sat.verify import verify_certificate

    # --- primary CEGAR (no internal re-check; we do that separately below) ---
    r = search(
        n,
        use_property_a=use_property_a,
        use_lex=use_lex,
        time_budget=time_budget,
        solver_name=solver_name,
        record_certificate=True,
    )
    cert_ok, cert_msg = verify_certificate(r.certificate, n)
    rec = {
        "n": r.n,
        "status": r.status,
        "refinements": r.refinements,
        "elapsed": round(r.elapsed, 2),
        "counterexample": r.counterexample,
        "cert_ok": cert_ok,
        "cert_msg": cert_msg,
        "recheck": "pending" if r.status == "UNSAT" else None,
        "verified": bool(cert_ok and r.status == "UNSAT"),
        "config": r.config,
    }
    os.makedirs(VOL_PATH, exist_ok=True)

    def _persist():
        with open(f"{VOL_PATH}/n{n:02d}.json", "w") as f:
            json.dump(rec, f)
        results_volume.commit()

    # commit the result + certificate FIRST
    if r.certificate is not None:
        with gzip.open(f"{VOL_PATH}/n{n:02d}_cert.json.gz", "wt") as f:
            json.dump(r.certificate, f)
    _persist()
    print(f"[n={n}] {rec['status']} refinements={rec['refinements']} "
          f"{rec['elapsed']}s cert_ok={cert_ok} (persisted; re-checking...)")

    # --- independent re-check, AFTER the result is safely stored ---
    if r.status == "UNSAT" and r.certificate is not None:
        if r.refinements > recheck_max_refinements:
            rec["recheck"] = f"skipped(>{recheck_max_refinements} refs)"
        else:
            rec["recheck"] = recheck_unsat(
                n, r.certificate, use_property_a, use_lex,
                use_c4free=False, solver_name="glucose42",
            )
        # an UNSAT result is only "verified" if the re-check did not disagree
        rec["verified"] = bool(cert_ok and rec["recheck"] in
                               ("UNSAT", f"skipped(>{recheck_max_refinements} refs)"))
        _persist()
        print(f"[n={n}] recheck={rec['recheck']} verified={rec['verified']} -> volume")
    return rec


@app.function(image=image, volumes={VOL_PATH: results_volume})
def collect() -> list:
    """Read every result file from the Volume (run server-side)."""
    import os

    results_volume.reload()
    out = []
    if os.path.isdir(VOL_PATH):
        for name in sorted(os.listdir(VOL_PATH)):
            if name.endswith(".json"):
                with open(f"{VOL_PATH}/{name}") as f:
                    out.append(json.load(f))
    return out


def _summarise(results: list, start: int) -> None:
    results = sorted(results, key=lambda d: d["n"])
    for d in results:
        line = (f"[n={d['n']}] {d['status']:5s}  refinements={d['refinements']}  "
                f"{d['elapsed']}s  recheck={d.get('recheck')}  "
                f"verified={d.get('verified')}")
        if d["status"] == "SAT":
            line += f"   !!! COUNTEREXAMPLE: {d['counterexample']}"
        print(line)
    # Only contiguous UNSAT sizes that ALSO passed verification advance the bound.
    contiguous = start
    by_n = {d["n"]: d for d in results}
    while True:
        d = by_n.get(contiguous)
        if d and d.get("status") == "UNSAT" and d.get("verified"):
            contiguous += 1
        else:
            break
    print(f"\nVerified contiguous UNSAT through n={contiguous - 1}  ->  bound >= {contiguous}.")


@app.local_entrypoint()
def main(
    start: int = 17,
    end: int = 23,
    time_budget: float = DEFAULT_SOFT_BUDGET_S,
    no_property_a: bool = False,
    no_lex: bool = False,
    solver_name: str = "cadical195",
):
    # ---- cost guards, enforced before anything is dispatched ----
    if time_budget + SAFETY_MARGIN_S > HARD_TIMEOUT_S:
        raise SystemExit(
            f"REFUSING: --time-budget {time_budget:.0f}s + {SAFETY_MARGIN_S}s margin "
            f"exceeds hard container timeout {HARD_TIMEOUT_S}s. Lower the budget or "
            f"raise HARD_TIMEOUT_S deliberately."
        )
    sizes = list(range(start, end + 1))
    if not sizes:
        raise SystemExit("empty size range")
    if len(sizes) > MAX_SIZES:
        raise SystemExit(
            f"REFUSING: {len(sizes)} sizes > MAX_SIZES={MAX_SIZES}. Narrow the range."
        )

    worst_core_hours = len(sizes) * HARD_TIMEOUT_S / 3600.0
    print(f"Dispatching n={start}..{end} ({len(sizes)} containers, 1 core each)")
    print(f"  soft budget {time_budget:.0f}s/size, hard ceiling {HARD_TIMEOUT_S}s/size")
    print(f"  WORST-CASE cost ceiling: {worst_core_hours:.1f} core-hours "
          f"(~${worst_core_hours * EST_USD_PER_CORE_HOUR:.2f}); "
          f"actual billing is real runtime, typically far less.")

    handles = []
    for n in sizes:
        fc = solve_n.spawn(n, time_budget, not no_property_a, not no_lex, solver_name)
        handles.append((n, fc))
        print(f"  spawned n={n}  call_id={fc.object_id}")

    print("\nAll sizes dispatched. Results stream to Volume 'erdos-gyarfas-results'.")
    print("If you ran with --detach you can close your laptop now; fetch later with:")
    print("  modal run erdos_gyarfas/experiments/modal_frontier.py::fetch")

    # If we stay connected, block and print as they finish. If the laptop
    # disconnects (detached run), this dies but the containers keep going and
    # still write to the Volume.
    collected = []
    for n, fc in handles:
        try:
            collected.append(fc.get())
        except Exception as e:  # noqa: BLE001 - best-effort live printing only
            print(f"  [n={n}] live result unavailable ({type(e).__name__}); "
                  f"check the Volume via ::fetch")
    if collected:
        print()
        _summarise(collected, start)


@app.local_entrypoint()
def fetch():
    """Print the frontier results saved in the Volume."""
    results = collect.remote()
    if not results:
        print("No results in the Volume yet.")
        return
    # infer start as the smallest n present
    start = min(d["n"] for d in results)
    _summarise(results, start)
