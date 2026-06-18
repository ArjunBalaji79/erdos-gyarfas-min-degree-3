"""SAT-Modulo-Symmetries (SMS) frontier on Modal -- native forbidden-subgraph route.

SMS (Kirchweger-Szeider) does COMPLETE symmetry breaking and, built WITH the
Glasgow subgraph solver, can forbid subgraphs via a complete propagator during
search. So we ask SMS directly:

    enumerate minimum-degree-3 graphs on n vertices that contain NO cycle of
    length 4, 8, or 16 (the powers of two <= n).

If SMS finds none, every min-degree-3 graph on n vertices has a power-of-two
cycle -> the conjecture holds at n. One smsg call per n; no CEGAR, no detector.

Soundness rests on: SMS symmetry breaking (sound), the Glasgow forbidden-subgraph
propagator (complete subgraph isomorphism), and the min-degree CNF. We VALIDATE
this by reproducing our nauty ground truth (C4-only at n=10 -> 5 classes) and the
n<=16 baseline (0 solutions).

Build is Linux-only and compiles CaDiCaL + the Glasgow solver, so it lives in the
image.

    modal run erdos_gyarfas/experiments/modal_sms.py::diag_main
"""
from __future__ import annotations

import modal

app = modal.App("erdos-gyarfas-sms")

# Build SMS WITH the Glasgow subgraph solver (-s) for the forbidden-subgraph
# propagator. Local install (-l) into /root/.local avoids sudo.
sms_image = (
    modal.Image.debian_slim(python_version="3.12")
    .apt_install("git", "cmake", "g++", "make", "libboost-all-dev", "zlib1g-dev",
                 "libgmp-dev")  # GMP/GMPXX required by the Glasgow subgraph solver
    .run_commands(
        "git clone --recursive https://github.com/markirch/sat-modulo-symmetries /opt/sms",
        "cd /opt/sms && git submodule update --init --recursive",
        # SMS links the Glasgow static lib but not GMP (which Glasgow needs);
        # append gmp/gmpxx to the global link (after Glasgow -> correct order).
        "cd /opt/sms && sed -i '/libglasgow_subgraphs.a/a link_libraries(gmpxx gmp)' CMakeLists.txt",
        "cd /opt/sms && bash build-and-install.sh -s -l",
        "cd /opt/sms && pip install .",
    )
    .env({"LD_LIBRARY_PATH": "/root/.local/lib:/usr/local/lib",
          "PATH": "/root/.local/bin:/usr/local/bin:/usr/bin:/bin"})
    .pip_install("networkx>=3.0")
    .add_local_python_source("erdos_gyarfas")
)


def _powers_of_two_upto(n):
    out, L = [], 4
    while L <= n:
        out.append(L)
        L *= 2
    return out


def _write_cycle_file(path, lengths):
    """Forbidden-subgraph file: one cycle per line as 'k v0 v1 v1 v2 ... v(k-1) v0'."""
    with open(path, "w") as f:
        for k in lengths:
            edges = []
            for i in range(k):
                edges += [i, (i + 1) % k]
            f.write(f"{k} " + " ".join(map(str, edges)) + "\n")


results_volume = modal.Volume.from_name("erdos-gyarfas-sms-results", create_if_missing=True)
VOL = "/results"

HARD_TIMEOUT_S = int(4.5 * 60 * 60)  # 4.5h hard ceiling per container
# (pass --time-budget 14400 = 4h for the smsg subprocess; ~1800s headroom to save)


def _parse_count(stdout: str):
    for line in stdout.splitlines():
        if line.strip().startswith("Number of graphs:"):
            return int(line.split(":")[1].strip())
    return None


def _run_smsg(n, lengths, time_budget, capture_graphs=False):
    """One smsg call: min-degree-3 + forbid the given cycle lengths, with SMS
    symmetry breaking. Returns (count, status, elapsed, stdout_tail)."""
    import subprocess
    import time

    from pysms.graph_builder import GraphEncodingBuilder

    b = GraphEncodingBuilder(n, directed=False)
    b.minDegree(3)
    cnf = f"/tmp/enc_{n}.cnf"
    with open(cnf, "w") as fh:
        b.print_dimacs(fh)
    cyc = f"/tmp/cyc_{n}.txt"
    _write_cycle_file(cyc, lengths)

    cmd = ["smsg", "--vertices", str(n), "--all-graphs",
           "--forbidden-subgraph-file", cyc, "--dimacs", cnf]
    if not capture_graphs:
        cmd.insert(4, "--hide-graphs")
    t = time.monotonic()
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=time_budget)
    except subprocess.TimeoutExpired:
        return None, "WALL", round(time.monotonic() - t, 2), ""
    count = _parse_count(p.stdout)
    if count is None:
        status = "ERROR"
    elif count == 0:
        status = "UNSAT"        # no min-deg-3 graph avoids all power-of-2 cycles
    else:
        status = "SAT"          # !!! a counterexample would live here
    return count, status, round(time.monotonic() - t, 2), p.stdout[-1500:]


@app.function(image=sms_image, timeout=HARD_TIMEOUT_S, cpu=1.0,
              volumes={VOL: results_volume})
def sms_solve(n: int, time_budget: float = 3300.0) -> dict:
    """Decide the conjecture at order n via SMS: forbid every power-of-2 cycle
    <= n and min-degree-3. count==0 -> holds at n. Persists to the Volume."""
    import json
    import os

    lengths = _powers_of_two_upto(n)
    count, status, elapsed, tail = _run_smsg(n, lengths, time_budget)
    witness = None
    if status == "SAT":
        # capture the witness graph(s) -- would be a genuine counterexample
        _, _, _, wtail = _run_smsg(n, lengths, min(time_budget, 600), capture_graphs=True)
        witness = wtail
    rec = {"n": n, "lengths": lengths, "count": count, "status": status,
           "elapsed": elapsed, "witness": witness, "stdout_tail": tail}
    os.makedirs(VOL, exist_ok=True)
    with open(f"{VOL}/n{n:02d}.json", "w") as f:
        json.dump(rec, f)
    results_volume.commit()
    print(f"[n={n}] {status} count={count} {elapsed}s lengths={lengths} -> volume")
    return rec


@app.function(image=sms_image, timeout=1800, cpu=1.0)
def validate() -> list:
    """Soundness anchors before any frontier claim:
    - n=10 forbidding ONLY C4 must give 5 (our nauty ground truth).
    - n=6..16 forbidding all power-of-2 cycles must give 0 (published baseline)."""
    out = []
    c, s, e, _ = _run_smsg(10, [4], 600)
    out.append({"n": 10, "lengths": [4], "count": c, "status": s, "elapsed": e,
                "expect": 5})
    for n in range(6, 17):
        c, s, e, _ = _run_smsg(n, _powers_of_two_upto(n), 600)
        out.append({"n": n, "lengths": _powers_of_two_upto(n), "count": c,
                    "status": s, "elapsed": e, "expect": 0})
    return out


@app.local_entrypoint()
def validate_main():
    print("== SMS soundness validation ==")
    ok = True
    for d in validate.remote():
        flag = "OK" if d["count"] == d["expect"] else "*** MISMATCH ***"
        if d["count"] != d["expect"]:
            ok = False
        print(f"n={d['n']:2d} forbid={d['lengths']}  count={d['count']} "
              f"(expect {d['expect']})  {d['elapsed']}s  {flag}")
    print("\nALL SOUNDNESS CHECKS PASSED" if ok else "\nSOUNDNESS FAILURE")


@app.local_entrypoint()
def frontier_main(start: int = 16, end: int = 26, time_budget: float = 3300.0):
    """Dispatch the SMS frontier, detached-safe (results stream to the Volume)."""
    sizes = list(range(start, end + 1))
    print(f"SMS frontier n={start}..{end} (forbid power-of-2 cycles, min-deg-3)")
    handles = [(n, sms_solve.spawn(n, time_budget)) for n in sizes]
    print(f"dispatched {len(sizes)} sizes; results -> Volume 'erdos-gyarfas-sms-results'")
    print("fetch later with ::fetch_main")
    for n, h in handles:
        try:
            d = h.get()
            print(f"[n={n}] {d['status']} count={d['count']} {d['elapsed']}s")
        except Exception as e:  # noqa: BLE001
            print(f"[n={n}] (disconnected/err: {type(e).__name__}) -- check Volume")


@app.function(image=sms_image, volumes={VOL: results_volume})
def _collect() -> list:
    import json
    import os
    results_volume.reload()
    out = []
    if os.path.isdir(VOL):
        for name in sorted(os.listdir(VOL)):
            if name.endswith(".json"):
                out.append(json.load(open(f"{VOL}/{name}")))
    return out


@app.local_entrypoint()
def fetch_main():
    rows = sorted(_collect.remote(), key=lambda d: d["n"])
    if not rows:
        print("no SMS results yet")
        return
    for d in rows:
        line = f"[n={d['n']:2d}] {d['status']:5s} count={d['count']} {d['elapsed']}s"
        if d["status"] == "SAT":
            line += f"  !!! COUNTEREXAMPLE witness: {d.get('witness')}"
        print(line)
    cont = min(d["n"] for d in rows)
    by = {d["n"]: d for d in rows}
    while by.get(cont, {}).get("status") == "UNSAT":
        cont += 1
    print(f"\nContiguous UNSAT through n={cont-1}  ->  bound >= {cont}.")
