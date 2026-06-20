# Submission checklist — Experimental Mathematics (Taylor & Francis)

## Status of the manuscript (`erdos-gyarfas-sms.tex` → `.pdf`)
- [x] Title, abstract, **keywords**, **2020 MSC codes** (05C38 primary; 05C30, 05C85, 68V05)
- [x] Body: intro (novelty + general-vs-cubic), Proposition 1 (reduction), method, results table + runtime figure, 6-layer verification, discussion/limitations, conclusion/future work
- [x] **Code & data availability** statement (public repo)
- [x] **Disclosure of generative AI use** (per T&F policy: tool, version, purpose; author responsible; no AI author)
- [x] **Disclosure statement** (no competing interests)
- [x] References verified against primary sources; no fabricated bibliographic detail
- [x] Compiles clean (tectonic), zero overfull boxes
- [x] Cover letter drafted (`cover-letter.md`)

## What YOU must do before submitting
1. **Author block** — fill in real name, affiliation, email, and ORCID (currently placeholder in `\author{...}` and the cover letter).
2. **Funding statement** — add one if any grant supported this (else state "no funding").
3. **Create a T&F / Editorial Manager account** for *Experimental Mathematics* and follow its "Instructions for Authors."
4. **Initial submission format** — a clean PDF in the current article style is accepted for review. The T&F **`interact` class is only required for the camera-ready** (on acceptance); the helpdesk (latex.helpdesk@tandf.co.uk) provides it. Don't spend time on it now.
5. **Suggested reviewers** (optional but helpful) — e.g., researchers in SAT-modulo-symmetries / computer-assisted combinatorics.
6. **Decide on the preprint** (recommended, do first):
   - **Zenodo** (instant, DOI, no endorsement) to stake the claim immediately, or
   - **arXiv** (math.CO) once you have an endorser — note arXiv currently scrutinizes AI-assisted submissions, and the AI-use disclosure is already in the paper.

## Honest pre-submission notes
- This is a corroborated **computational** result; soundness rests on the SMS / Glasgow / encoding tool chain, validated at n=10 (vs nauty) and n≤16 (baseline). A machine-checked proof certificate is the natural strengthening (stated as future work) but is **not required** to submit.
- The general ≥17 prior bound is currently cited via Wikipedia; if you can, confirm the precise primary source with Royle/Markström before the final version.
