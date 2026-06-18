# Novelty / literature verdict (deep adversarial review, 100 agents)

**Bottom line: the result is genuinely novel — YES — on two independent counts.**

1. **First extension of the GENERAL minimum-degree-3 frontier past 17.** The prior
   frontier is general ≥ 17 (Royle/Markström, commonly cited) and cubic ≥ 30
   (Markström, *Congr. Numer.* 171 (2004) **177–188**). An adversarial search across
   papers, theses, tech reports, OEIS, House of Graphs, and the two most recent
   surveys found **no post-2004 improvement of the general bound**.
2. **First SAT / SAT-Modulo-Symmetries / CP / isomorph-free method ever applied to
   this conjecture.** Verified by full-text checks of Szeider's Dec-2025 SMS survey
   and Jooken's 2025 "Computer-assisted graph theory" survey (zero mentions).

**Carr 2026 (arXiv:2605.22844)** is purely structural (≥4/7 of a minimal
counterexample's vertices are degree exactly 3), an unrefereed arXiv preprint, uses
no computation, and establishes no vertex-count frontier — it does **not** threaten
novelty.

## The one framing trap (addressed in the paper)
Our general verified order **30** numerically coincides with Markström's **cubic
bound** of 30. These are different statements:
- Markström: cubic verified to **29** → cubic bound ≥ 30.
- This work: **all min-degree-3** verified to **30** → general bound ≥ 31 (and,
  as a sub-case, cubic verified to 30 → cubic bound ≥ 31).
The paper's "General versus cubic" paragraph spells this out so a referee cannot
misread it as duplicating Markström.

## Loose ends to close before submission
1. **Markström pagination** — resolved to 177–188 (author's listing; some records
   say 179–192). Confirm against the physical Congr. Numer. 171.
2. **Exact prior GENERAL bound** — the ≥17 figure is cited via Wikipedia/MathWorld
   and attributed to Royle; the primary publication pinning the general search to a
   precise order is thin. Worth confirming with Royle/Markström directly.
3. **Non-obvious venues** — directly check House of Graphs and OEIS for any
   "min-degree-3 / no power-of-two cycle" verification record; and a citation-graph
   / thesis search on Markström 2004 for any 2004–2026 reproduction/extension.
4. **Citations marked [verify]** in the .tex — confirm author initials / exact
   titles for the $P_{10}$ (Hu–Shen?) and $P_8$ (Gao–Shan) papers, the SMS TOCL
   title, and Shauger / Daniel–Shauger.
5. **AI-assistance disclosure** and **independent third-party reproduction** —
   required before this carries an author's name to a venue (see paper acks +
   `experiments/verification.md`).

## Related work a referee will expect cited (now in the paper)
Shauger 1998 ($K_{1,m}$-free); Daniel–Shauger 2001 (planar claw-free);
Heckman–Krakovski 2013 (3-conn. cubic planar); Gao–Shan 2022 ($P_8$);
Hu–Shen 2024 ($P_{10}$); Hegde–Sandeep–Shashank 2024 ($P_{13}$, computer-aided);
Carr 2026 (structural); Kirchweger–Szeider TOCL 2024 + Szeider survey 2025 (SMS);
McCreesh–Prosser–Trimble 2020 (Glasgow); McKay–Piperno 2014 (nauty);
Jooken 2025 (computer-assisted graph theory survey).
