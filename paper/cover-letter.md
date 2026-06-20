# Cover letter — Experimental Mathematics

Dear Editors,

Please consider the enclosed manuscript, **"A SAT-Modulo-Symmetries verification of
the Erdős–Gyárfás power-of-two cycle conjecture for minimum-degree-3 graphs up to
30 vertices,"** for publication in *Experimental Mathematics*.

The Erdős–Gyárfás conjecture (1995) states that every graph of minimum degree at
least 3 contains a cycle whose length is a power of two. It is open. The strongest
previously published computer search establishes that any **general**
minimum-degree-3 counterexample has at least 17 vertices (Royle and Markström), and
that any **cubic** counterexample has at least 30 vertices (Markström, 2004) — a
frontier untouched for two decades.

This manuscript reports a new computational result: using SAT Modulo Symmetries
together with the Glasgow subgraph solver as a complete forbidden-subgraph
propagator, we verify the conjecture for **all** minimum-degree-3 graphs on at most
30 vertices, raising the general lower bound on a counterexample from 17 to 31. To
our knowledge — confirmed by an adversarial literature search — this is the first
application of SAT-based methods to this conjecture.

We believe the work fits *Experimental Mathematics* well: it is a computer-assisted
result that advances a concrete frontier, with an explicit, reproducible
methodology and a multi-layer verification protocol (an exact ground-truth check
against `nauty`, reproduction of the established baseline, cross-validation by an
independent solver, and robustness across encodings and symmetry-breaking methods).
All code and data are openly available, and we discuss the path to a fully
machine-checked proof certificate.

The manuscript is original, is not under consideration elsewhere, and has not been
previously published. In accordance with the journal's policy, the manuscript
includes a disclosure of generative-AI assistance used in its preparation; the
author takes full responsibility for all content and claims.

Thank you for your consideration.

Sincerely,
[Author name], [Affiliation], [email]
