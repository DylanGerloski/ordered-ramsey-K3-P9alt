"""k3palt.py -- R_ord(K_3, P_b^alt) as SAT (Architect card #70659). TRIAGE.

    <sat-venv python> -I k3palt.py cnf B N OUT.cnf        write the CNF, print its LF sha256 and counts
    <sat-venv python> -I k3palt.py check B N MODEL.txt    check a colouring without the encoder (exit 0 VALID)
    <sat-venv python> -I k3palt.py selftest               encoder and checker against each other, and the checker red

Vertices 0..N-1 in their natural order. Variable x(i,j), i<j, numbered in lexicographic order from 1, is TRUE when
edge ij has colour 1 (the K_3 side) and FALSE for colour 2 (the P_b^alt side), as R_ord(H1, H2) is defined in
2604.16188 Section 1: every colouring of K_n holds H_j in colour j for some j.
  - no colour-1 triangle:  for i<j<k, (-x_ij  -x_ik  -x_jk)
  - no colour-2 ordered P_b^alt: P_b^alt is the path (0, b-1, 1, b-2, 2, ..., floor(b/2)) (Section 1, Figure 1).
    For each b-subset v_0<...<v_{b-1} the path's b-1 edges {v_s[t], v_s[t+1]}, s = alt(b), may not all be colour 2:
    one clause (x_e1 or ... or x_e{b-1}).
No symmetry breaking: every colouring of K_N is a model of the CNF exactly when it has neither, so SAT at N means
R_ord > N and UNSAT at N means R_ord <= N.
MODEL.txt: one line per colour-1 edge, "i j" with i<j; every other edge is colour 2.
The checker (check) reads only MODEL.txt, B and N and searches by brute force with its own code: every triangle, and
every increasing embedding of P_b^alt, by a depth-first search over vertex positions in path order, not by
re-enumerating the encoder's clauses.
"""
import hashlib
import itertools
import os
import sys


def alt(b):
    """(0, b-1, 1, b-2, ...): the vertex order of P_b^alt's path."""
    lo, hi, out = 0, b - 1, []
    while lo <= hi:
        out.append(lo)
        if hi != lo:
            out.append(hi)
        lo, hi = lo + 1, hi - 1
    return out


def var(i, j, n):
    if i > j:
        i, j = j, i
    return i * n - i * (i + 1) // 2 + (j - i - 1) + 1


def clauses(b, n):
    s = alt(b)
    for i, j, k in itertools.combinations(range(n), 3):
        yield (-var(i, j, n), -var(i, k, n), -var(j, k, n))
    for vs in itertools.combinations(range(n), b):
        yield tuple(sorted(var(vs[s[t]], vs[s[t + 1]], n) for t in range(b - 1)))


def write_cnf(b, n, path):
    cl = list(clauses(b, n))
    nv = n * (n - 1) // 2
    body = "p cnf %d %d\n" % (nv, len(cl)) + "".join(" ".join(map(str, c)) + " 0\n" for c in cl)
    data = body.encode("ascii")
    with open(path, "wb") as f:
        f.write(data)
    return {"B": b, "N": n, "vars": nv, "clauses": len(cl), "triangle_clauses": n * (n - 1) * (n - 2) // 6,
            "path_clauses": len(cl) - n * (n - 1) * (n - 2) // 6, "cnf_sha256": hashlib.sha256(data).hexdigest()}


def read_model(path):
    red = set()
    for line in open(path, encoding="ascii"):
        if line.strip():
            i, j = map(int, line.split())
            red.add((min(i, j), max(i, j)))
    return red


def find(b, n, red):
    """Brute force, independent of clauses(): a colour-1 triangle or a colour-2 increasing P_b^alt, or None."""
    R = lambda i, j: (min(i, j), max(i, j)) in red
    for i, j, k in itertools.combinations(range(n), 3):
        if R(i, j) and R(i, k) and R(j, k):
            return ("triangle", (i, j, k))
    s = alt(b)
    # place path vertices in path order; vertex s[t] of P_b^alt must sit at a position consistent with the ordering
    # of every vertex already placed (positions increase with the graph vertex label), and the edge to the previous
    # path vertex must be colour 2.
    pos = [None] * b

    def ok(label, p):
        for q in range(b):
            if pos[q] is not None and ((q < label and pos[q] >= p) or (q > label and pos[q] <= p)):
                return False
        return True

    def dfs(t):
        if t == b:
            return True
        label = s[t]
        for p in range(n):
            if pos.count(p) or not ok(label, p):
                continue
            if t > 0 and R(pos[s[t - 1]], p):
                continue
            pos[label] = p
            if dfs(t + 1):
                return True
            pos[label] = None
        return False

    if dfs(0):
        return ("path", tuple(pos))
    return None


def solve_small(b, n):
    from pysat.solvers import Cadical195
    with Cadical195(bootstrap_with=list(clauses(b, n))) as s:
        if not s.solve():
            return None
        m = set(l for l in s.get_model() if l > 0)
    return {(i, j) for i, j in itertools.combinations(range(n), 2) if var(i, j, n) in m}


def selftest():
    ok = True
    assert alt(5) == [0, 4, 1, 3, 2] and alt(6) == [0, 5, 1, 4, 2, 3] and alt(9) == [0, 8, 1, 7, 2, 6, 3, 5, 4]
    print("PASS alt(5), alt(6) match Figure 1; alt(9) = %s" % alt(9))
    nv = 20 * 19 // 2
    assert sorted(var(i, j, 20) for i, j in itertools.combinations(range(20), 2)) == list(range(1, nv + 1))
    print("PASS var() is a bijection onto 1..190 at N=20")
    # printed cells, Table 9 of 2604.16188 at a=3: R_ord(K_3, P_b^alt) = ceil(2.5(b-1)) for b = 3..8
    want = {3: 5, 4: 8, 5: 10, 6: 13}
    for b, r in want.items():
        m = solve_small(b, r - 1)
        sat_ok = m is not None and find(b, r - 1, m) is None
        uns_ok = solve_small(b, r) is None
        print("%s b=%d SAT at N=%d with checker VALID, UNSAT at N=%d (R_ord = %d printed)"
              % ("PASS" if sat_ok and uns_ok else "FAIL", b, r - 1, r, r))
        ok &= sat_ok and uns_ok
        if m:  # the checker must be able to fail: flip one colour-2 edge of a path, or add a triangle edge
            for e in itertools.combinations(range(r - 1), 2):
                bad = m ^ {e}
                if find(b, r - 1, bad) is not None:
                    break
            red_ok = find(b, r - 1, bad) is not None
            all_blue = find(b, r - 1, set()) is not None and find(b, r - 1, set(itertools.combinations(range(r - 1), 2))) is not None
            print("%s checker red on a one-edge mutant and on both one-colour colourings" % ("PASS" if red_ok and all_blue else "FAIL"))
            ok &= red_ok and all_blue
    # encoder vs checker on random colourings: the CNF is satisfied iff the checker finds nothing
    import random
    rnd = random.Random(70659)
    agree = 0
    for _ in range(300):
        b, n = rnd.choice([(4, 7), (5, 9), (6, 10)])
        red = {e for e in itertools.combinations(range(n), 2) if rnd.random() < 0.35}
        val = lambda v: any(var(i, j, n) == v for i, j in red)
        redv = {var(i, j, n) for i, j in red}
        sat = all(any((l > 0) == (abs(l) in redv) for l in c) for c in clauses(b, n))
        agree += sat == (find(b, n, red) is None)
    print("%s encoder and checker agree on %d of 300 random colourings" % ("PASS" if agree == 300 else "FAIL", agree))
    ok &= agree == 300
    print("ALL PASS" if ok else "FAIL")
    return ok


def main(a):
    if a[:1] == ["selftest"]:
        return 0 if selftest() else 1
    if a[:1] == ["cnf"]:
        import json
        print(json.dumps(write_cnf(int(a[1]), int(a[2]), a[3])))
        return 0
    if a[:1] == ["check"]:
        b, n = int(a[1]), int(a[2])
        red = read_model(a[3])
        if any(not (0 <= i < j < n) for i, j in red):
            print("REFUSED: an edge outside 0..N-1")
            return 2
        hit = find(b, n, red)
        print("VALID: no colour-1 triangle and no colour-2 ordered P_%d^alt on %d vertices" % (b, n) if hit is None
              else "INVALID: %s at %s" % hit)
        return 0 if hit is None else 1
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
