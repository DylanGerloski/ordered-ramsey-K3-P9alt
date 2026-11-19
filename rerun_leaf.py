"""rerun_leaf.py -- rebuild and re-check the R_ord(K_3, P_9^alt) <= 20 cube cover. Needs only k3palt.py beside it.

    python rerun_leaf.py base OUT.cnf            write the full N = 20 CNF (no cube) and check its sha256
    python rerun_leaf.py cnf LEAF OUT.cnf        write one leaf's CNF (base + its 8 unit clauses), check its sha256
    python rerun_leaf.py cover                   check that the 256 cubes in cubes.txt are all 2^8 sign patterns
                                                 of the same 8 edge variables, so their union is every colouring
    python rerun_leaf.py solve LEAF              solve one leaf with PySAT's CaDiCaL 1.9.5 (pip install python-sat);
                                                 prints SAT or UNSAT. For a checkable proof use a DRAT-writing
                                                 solver on the CNF from `cnf`, then drat-trim (see README.md).

Every sha256 is of the CNF file as written here: DIMACS, LF line ends, ASCII, header "p cnf 190 <clauses>".
leaves.csv holds each leaf's expected sha256, solver result and drat-trim result as measured.
"""
import csv
import hashlib
import itertools
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import k3palt  # noqa: E402

B, N = 9, 20
BASE_SHA = "484f9ddb4891e2a2890e7c352de318e8855367c81ef2ebd850cb1da04355ac95"


def leaves():
    with open(os.path.join(HERE, "leaves.csv"), newline="", encoding="ascii") as f:
        return {r["leaf"]: r for r in csv.DictReader(f)}


def write(units, path):
    cls = [list(c) for c in k3palt.clauses(B, N)] + [[u] for u in units]
    nv = N * (N - 1) // 2
    data = ("p cnf %d %d\n" % (nv, len(cls)) + "".join(" ".join(map(str, c)) + " 0\n" for c in cls)).encode("ascii")
    with open(path, "wb") as f:
        f.write(data)
    return hashlib.sha256(data).hexdigest(), cls


def main(a):
    if a[:1] == ["base"]:
        h, _ = write([], a[1])
        print("sha256 %s %s" % (h, "EQUAL to the recorded base" if h == BASE_SHA else "DIFFERS from " + BASE_SHA))
        return 0 if h == BASE_SHA else 1
    if a[:1] == ["cnf"]:
        r = leaves()[a[1]]
        h, _ = write([int(x) for x in r["units"].split()], a[2])
        ok = h == r["cnf_sha256"]
        print("sha256 %s %s" % (h, "EQUAL to leaves.csv" if ok else "DIFFERS from " + r["cnf_sha256"]))
        return 0 if ok else 1
    if a[:1] == ["cover"]:
        cubes = []
        for ln in open(os.path.join(HERE, "cubes.txt"), encoding="ascii"):
            p = ln.split()
            if p and p[0] == "a":
                cubes.append(tuple(int(x) for x in p[1:-1]))
        vs = {tuple(sorted(abs(u) for u in c)) for c in cubes}
        signs = {tuple(u > 0 for u in sorted(c, key=abs)) for c in cubes}
        ok = len(cubes) == 256 and len(vs) == 1 and len(next(iter(vs))) == 8 and len(signs) == 256
        print("%d cubes on variables %s, %d distinct sign patterns of 256: %s"
              % (len(cubes), sorted(next(iter(vs))) if len(vs) == 1 else "MIXED", len(signs),
                 "COVER COMPLETE" if ok else "NOT A COVER"))
        lv = leaves()
        same = len(lv) == 256 and {tuple(sorted(int(x) for x in r["units"].split())) for r in lv.values()} == \
            {tuple(sorted(c)) for c in cubes}
        print("leaves.csv holds the same 256 cubes: %s" % ("YES" if same else "NO"))
        return 0 if ok and same else 1
    if a[:1] == ["solve"]:
        from pysat.solvers import Cadical195
        r = leaves()[a[1]]
        _, cls = write([int(x) for x in r["units"].split()], os.devnull)
        with Cadical195(bootstrap_with=cls) as s:
            print("SAT" if s.solve() else "UNSAT")
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
