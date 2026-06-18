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
# Base SMS build (no local source yet, so further build steps can be layered).
_sms_base = (
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
)

sms_image = _sms_base.add_local_python_source("erdos_gyarfas")

# SMS image + an INDEPENDENT LRAT proof checker (drat-trim's lrat-check), which
# shares no code with SMS -- for verifying smsg's UNSAT proofs. drat-trim is
# built BEFORE the local source is added (Modal requires add_local_* last).
lrat_image = (
    _sms_base
    .run_commands(
        "git clone --depth 1 https://github.com/marijnheule/drat-trim /opt/drat-trim",
        "cd /opt/drat-trim && gcc -O2 lrat-check.c -o /usr/local/bin/lrat-check",
    )
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


def _run_smsg(n, lengths, time_budget, capture_graphs=False,
              counter="sequential", extra_args=None, first_only=False,
              lrat_file=None):
    """One smsg call: min-degree-3 + forbid the given cycle lengths, with SMS
    symmetry breaking. Returns (count, status, elapsed, stdout_tail).

    ``counter`` selects the cardinality CNF (sequential|totalizer).
    ``extra_args`` are appended to smsg (e.g. ['--colex-ordering']).
    ``first_only`` stops at the first solution (existence check, for positive
    controls). ``lrat_file`` writes a machine-checkable LRAT proof of UNSAT."""
    import subprocess
    import time

    from pysms.graph_builder import GraphEncodingBuilder

    b = GraphEncodingBuilder(n, directed=False)
    b.minDegree(3, countertype=counter)
    cnf = f"/tmp/enc_{n}_{counter}.cnf"
    with open(cnf, "w") as fh:
        b.print_dimacs(fh)
    cyc = f"/tmp/cyc_{n}.txt"
    _write_cycle_file(cyc, lengths)

    cmd = ["smsg", "--vertices", str(n)]
    if not first_only:
        cmd.append("--all-graphs")
        if not capture_graphs:
            cmd.append("--hide-graphs")
    cmd += ["--forbidden-subgraph-file", cyc, "--dimacs", cnf]
    if lrat_file:
        cmd += ["--lrat-output", lrat_file]
    if extra_args:
        cmd += list(extra_args)
    t = time.monotonic()
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=time_budget)
    except subprocess.TimeoutExpired:
        return None, "WALL", round(time.monotonic() - t, 2), ""
    elapsed = round(time.monotonic() - t, 2)
    if first_only:
        # returncode 10 = a solution was found; 20 = none (UNSAT)
        exists = (p.returncode == 10)
        return (1 if exists else 0), ("SAT" if exists else "UNSAT"), elapsed, p.stdout[-1500:]
    count = _parse_count(p.stdout)
    if count is None:
        status = "ERROR"
    elif count == 0:
        status = "UNSAT"        # no min-deg-3 graph avoids all power-of-2 cycles
    else:
        status = "SAT"          # !!! a counterexample would live here
    return count, status, elapsed, p.stdout[-1500:]


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


def _persist_verify(key: str, rec: dict):
    import json
    import os
    os.makedirs(f"{VOL}/verify", exist_ok=True)
    with open(f"{VOL}/verify/{key}.json", "w") as f:
        json.dump(rec, f)
    results_volume.commit()


@app.function(image=sms_image, timeout=HARD_TIMEOUT_S, cpu=1.0,
              volumes={VOL: results_volume})
def verify_config(n: int, counter: str, colex: bool, time_budget: float = 3300.0) -> dict:
    """Re-decide n with an alternative cardinality encoding and/or the colex
    symmetry-breaking variant. Must still give count=0 (robust to config)."""
    lengths = _powers_of_two_upto(n)
    extra = ["--colex-ordering"] if colex else None
    count, status, elapsed, tail = _run_smsg(
        n, lengths, time_budget, counter=counter, extra_args=extra)
    rec = {"n": n, "check": f"config(counter={counter},colex={colex})",
           "count": count, "status": status, "elapsed": elapsed, "expect": 0,
           "ok": count == 0}
    _persist_verify(f"config_n{n:02d}_{counter}_colex{int(colex)}", rec)
    print(f"[verify config n={n} {counter} colex={colex}] count={count} {elapsed}s")
    return rec


@app.function(image=sms_image, timeout=1800, cpu=1.0,
              volumes={VOL: results_volume})
def positive_control(n: int, lengths: list, time_budget: float = 1500.0) -> dict:
    """Forbid FEWER cycle lengths than the full power-of-2 set: a graph MUST
    exist (e.g. C4-free min-degree-3 graphs do). Confirms the pipeline returns
    a solution when one exists -- i.e. the frontier '0's are not a broken/empty
    pipeline always returning UNSAT."""
    count, status, elapsed, tail = _run_smsg(
        n, lengths, time_budget, first_only=True)
    rec = {"n": n, "check": f"positive(forbid={lengths})", "count": count,
           "status": status, "elapsed": elapsed, "expect": "SAT (exists)",
           "ok": status == "SAT"}
    _persist_verify(f"pos_n{n:02d}", rec)
    print(f"[verify positive n={n} forbid={lengths}] {status} {elapsed}s")
    return rec


@app.function(image=lrat_image, timeout=HARD_TIMEOUT_S, cpu=1.0)
def lrat_certify(n: int, time_budget: float = 3300.0) -> dict:
    """Emit an LRAT proof of the n-th UNSAT from smsg, then verify it with an
    INDEPENDENT checker (drat-trim lrat-check). Returns sizes + checker verdict.
    This empirically establishes what SMS's LRAT proof certifies for our setup."""
    import os
    import subprocess

    lengths = _powers_of_two_upto(n)
    proof = f"/tmp/proof_{n}.lrat"
    count, status, elapsed, tail = _run_smsg(
        n, lengths, time_budget, lrat_file=proof)
    cnf = f"/tmp/enc_{n}_sequential.cnf"
    out = {"n": n, "status": status, "count": count, "elapsed": elapsed,
           "smsg_tail": tail}
    if status == "UNSAT" and os.path.exists(proof):
        out["proof_bytes"] = os.path.getsize(proof)
        out["cnf_bytes"] = os.path.getsize(cnf) if os.path.exists(cnf) else None
        try:
            chk = subprocess.run(["lrat-check", cnf, proof],
                                 capture_output=True, text=True, timeout=3600)
            out["lrat_check_rc"] = chk.returncode
            out["lrat_check_tail"] = (chk.stdout + chk.stderr)[-1500:]
        except subprocess.TimeoutExpired:
            out["lrat_check_rc"] = "timeout"
    else:
        out["note"] = f"no proof emitted (status={status})"
    return out


@app.local_entrypoint()
def lrat_main(n: int = 16):
    d = lrat_certify.remote(n)
    print(f"n={d['n']} status={d['status']} count={d['count']} {d['elapsed']}s")
    print(f"  proof_bytes={d.get('proof_bytes')} cnf_bytes={d.get('cnf_bytes')}")
    print(f"  lrat-check rc={d.get('lrat_check_rc')}")
    print(f"  lrat-check output:\n{d.get('lrat_check_tail', d.get('note'))}")


@app.local_entrypoint()
def verify_main():
    """Independent hardening of the frontier UNSATs (config robustness +
    positive controls). The LRAT proof certificates are a separate entrypoint."""
    jobs = []
    # (1) config robustness: alternative encodings/symmetry must also give 0
    for n in [17, 20, 22, 25]:
        for counter in ["sequential", "totalizer"]:
            for colex in [False, True]:
                if counter == "sequential" and not colex:
                    continue  # that's the original frontier config -- skip
                jobs.append(("config", verify_config.spawn(n, counter, colex)))
    # (2) positive controls: forbidding only C4 MUST yield a graph at these n
    for n in [17, 20, 25, 30]:
        jobs.append(("pos", positive_control.spawn(n, [4])))

    print(f"== independent verification: {len(jobs)} jobs dispatched ==")
    print("results persist to Volume; fetch with ::fetch_verify_main")
    for kind, h in jobs:
        try:
            d = h.get()
            print(f"  [{kind}] n={d['n']} {d['check']}: count={d['count']} "
                  f"status={d['status']} {d['elapsed']}s ok={d['ok']}")
        except Exception as e:  # noqa: BLE001
            print(f"  [{kind}] live result unavailable ({type(e).__name__}); check Volume")


@app.function(image=sms_image, volumes={VOL: results_volume})
def _collect_verify() -> list:
    import json
    import os
    results_volume.reload()
    d = f"{VOL}/verify"
    out = []
    if os.path.isdir(d):
        for name in sorted(os.listdir(d)):
            if name.endswith(".json"):
                out.append(json.load(open(f"{d}/{name}")))
    return out


@app.local_entrypoint()
def fetch_verify_main():
    rows = _collect_verify.remote()
    if not rows:
        print("no verification results yet")
        return
    cfg = [r for r in rows if r["check"].startswith("config")]
    pos = [r for r in rows if r["check"].startswith("positive")]
    print("== config robustness (alternative encoding/symmetry; want count=0) ==")
    for r in sorted(cfg, key=lambda r: (r["n"], r["check"])):
        print(f"  n={r['n']:2d} {r['check']}: count={r['count']} {r['elapsed']}s "
              f"{'OK' if r['ok'] else '*** MISMATCH ***'}")
    print("== positive controls (forbid fewer cycles; want a graph to exist) ==")
    for r in sorted(pos, key=lambda r: r["n"]):
        print(f"  n={r['n']:2d} {r['check']}: {r['status']} {r['elapsed']}s "
              f"{'OK' if r['ok'] else '*** FAIL ***'}")
    allok = all(r["ok"] for r in rows)
    print(f"\n{'ALL VERIFICATION CHECKS PASSED' if allok else 'VERIFICATION ISSUE'} "
          f"({len(cfg)} config + {len(pos)} positive)")


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
