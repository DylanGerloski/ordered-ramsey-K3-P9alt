# R_ord(K_3, P_9^alt) = 20: re-run material

The claim: every red/blue colouring of the edges of the complete graph on vertices 1 < 2 < ... < 20 has a red
triangle or a blue copy of the alternating path P_9^alt in increasing vertex order; a colouring on 19 vertices
without either exists. So R_ord(K_3, P_9^alt) = 20. Definitions follow arXiv 2604.16188, Section 1 and Figure 1;
its Table 9 gives this cell as at least 20.

The lower bound is one explicit colouring. The upper bound is a SAT computation: 256 sub-problems (cubes), each found
unsatisfiable by a SAT solver and each proof checked by drat-trim. Nothing here is formally verified in a proof
assistant, and the result has not been confirmed independently.

## Check the colourings in a browser

https://dylangerloski.github.io/ordered-ramsey-K3-P9alt/

That page checks two colourings on the visitor's own machine, set by set, and loads nothing from anywhere else:

- the colouring of K_19 below, the lower half of R_ord(K_3, P_9^alt) = 20;
- a colouring of K_22 with no K_4 in one colour and no ordered P_7^alt in the other, `k4_p7_n22.g6`, which gives
  R_ord(K_4, P_7^alt) >= 23. Table 15 of arXiv 2604.16188 prints this cell as at least 22. This is a lower bound
  only; the upper bound is not shown here.

Clicking a square of the matrix flips that edge, and the check then reports the clique or path that appears. A
browser cannot re-run the upper half of the value 20; the rest of this file is how to do that.

The page's checker is JavaScript. Its tests compare it with the two Python checkers here, `k3palt.py` and
`kapalt_check.py`, on 1,070 colourings that hold both answers (Python 3.9 or later and Node 18 or later):

```
python -I tests/gen_cases.py cases.json
node tests/test_core.mjs cases.json
python -I kapalt_check.py check 4 7 k4_p7_n22.g6
```

The loose files in this repository are the same bytes as the members of `R_ord_K3_P9alt_20.zip`, except this
README, which adds this section. `kapalt_check.py`, `k4_p7_n22.g6`, `ordered-ramsey-check.html`, `index.html`,
`tests/` and `note/` are not in the zip.

## A note on Conjecture 4.13, with hand proofs

`note/ordered_ramsey_proofs.pdf`, with its LaTeX source `note/ordered_ramsey_proofs.tex`, is a note on
Conjecture 4.13 of arXiv 2604.16188: for a >= 3 and b >= 2,
R_ord(C_a^mon, P_b^alt) = N(a, b) := (a-1)(b-1) + floor(b/2).

What the note proves by hand:

- the lower bound R_ord(C_a^mon, P_b^alt) >= N(a, b) for all a >= 3 and b >= 2;
- the conjecture for b = 2, 3 and 4, at every a;
- a general upper bound (b-1)(a + sqrt(a-2)), which gives the leading term only.

The upper bound for b >= 5 is not proved. The note also lists the exact values found by computer, each with its
own status, a second route to (3, 9) = 20, and the lower bound R_ord(K_4, P_7^alt) >= 23.

Status, stated plainly: I worked on this with Kiln, my own system of AI agents built on Claude, and the proofs
were found by that system. The proof of the lower bound was checked by two independent reviews inside that
system; the other hand proofs were reviewed inside my own lab only. Nothing in the note has been confirmed
outside it. The note was sent to the first author of arXiv 2604.16188 on 25 November 2026; this repository holds
the re-run material for (3, 9) = 20 and the K_22 colouring only. The files behind the note's other computed
values, which it says were sent by mail, are not here; they can be provided on request. Corrections are welcome
as issues.

The PDF was compiled with XeTeX. sha256: PDF `00d3c6f36825eff95e92e08c260272fcfc77ca309b12b033addca2cf7eb9f19c`,
source `55fd46342a59502affecbeedab88c27e7558cf91a823bf3b6acdeacf15b27bb4`.

## Files

| File | What it is |
|---|---|
| `k3palt.py` | The encoder and an independent checker (standard library only; `selftest` needs PySAT). |
| `rerun_leaf.py` | Rebuilds the full CNF or any cube's CNF and checks its sha256 against the record; checks that the 256 cubes form a complete cover. |
| `cubes.txt` | The 256 cubes: every sign pattern of the 8 edge variables 19, 36, 37, 52, 53, 54, 69, 70. |
| `leaves.csv` | Per cube: unit clauses, CNF sha256, solver result and time, DRAT proof size and sha256, compressed proof sha256, drat-trim result and time. |
| `n19_colouring.txt` | The colouring on 19 vertices: one line `i j` per red edge (vertices 0..18), every other edge blue. |

## The encoding

Vertices 0..N-1 in their natural order. Variable x(i,j) for i < j, numbered lexicographically from 1, is true when
edge ij is red (the K_3 colour). For every triangle, the clause (-x_ij -x_ik -x_jk). For every 9-subset
v_0 < ... < v_8, the path P_9^alt on it visits v_0, v_8, v_1, v_7, v_2, v_6, v_3, v_5, v_4, and one clause says at
least one of its 8 edges is red. No symmetry breaking. At N = 20: 190 variables, 1,140 triangle clauses, 167,960
path clauses; the CNF's sha256 is `484f9ddb4891e2a2890e7c352de318e8855367c81ef2ebd850cb1da04355ac95`.

## Re-running

Python 3.9 or later. For `solve` and `selftest`, `pip install python-sat`.

```
python k3palt.py check 9 19 n19_colouring.txt      # lower bound: prints VALID, by brute force, not by the clauses
python rerun_leaf.py base full_n20.cnf              # the full CNF; checks its sha256
python rerun_leaf.py cover                          # the 256 cubes cover every colouring
python rerun_leaf.py cnf cnppppppp leaf.cnf         # one cube's CNF (full CNF plus 8 unit clauses); checks its sha256
```

Each cube's CNF can then be given to any DRAT-producing solver and its proof checked by drat-trim, for example:

```
cadical leaf.cnf proof.drat
drat-trim leaf.cnf proof.drat                       # s VERIFIED
```

`python rerun_leaf.py solve LEAF` solves one cube with PySAT's CaDiCaL, without a proof.

## How it was run

- Solver: CaDiCaL 1.9.5 through PySAT 1.9.dev21, binary DRAT output, one process per cube.
- Checker: drat-trim, source commit c21257dd, default mode, each proof against its own cube's CNF. Each binary
  proof was first converted to text DRAT by a short script of the run's own, then given to drat-trim.
- Every cube is UNSAT and every proof is `s VERIFIED`. None needed a further split under a 30-minute cap.
- Cost: 12,552 s of solving and 9,584 s of proof checking, about 6 core-hours in all on one desktop machine.
- The 256 proofs are 8.75 GB uncompressed and 3.28 GB as xz. They are not included; each one's sha256 is in
  `leaves.csv`, and they can be provided on request.
