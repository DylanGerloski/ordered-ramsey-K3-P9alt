[README.md](https://github.com/user-attachments/files/35095135/README.md)
# R_ord(K_3, P_9^alt) = 20: re-run material

The claim: every red/blue colouring of the edges of the complete graph on vertices 1 < 2 < ... < 20 has a red
triangle or a blue copy of the alternating path P_9^alt in increasing vertex order; a colouring on 19 vertices
without either exists. So R_ord(K_3, P_9^alt) = 20. Definitions follow arXiv 2604.16188, Section 1 and Figure 1;
its Table 9 gives this cell as at least 20.

The lower bound is one explicit colouring. The upper bound is a SAT computation: 256 sub-problems (cubes), each found
unsatisfiable by a SAT solver and each proof checked by drat-trim. Nothing here is formally verified in a proof
assistant, and the result has not been confirmed independently.

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
