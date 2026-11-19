"""kapalt_check.py -- T2 of Architect #71063: an R_ord(K_a, P_b^alt) witness checker written from the definition,
importing nothing from desk/ramsey/. Stdlib only. TRIAGE.

    python -I kapalt_check.py check A B FILE.g6      exit 0 VALID, 1 NOT VALID (prints the copy found)
    python -I kapalt_check.py selftest

Definitions (arXiv 2604.16188, Sec. 1, as in my k3palt.py and g81/ordcheck.py):
  - A red/blue colouring of the pairs of 0 < 1 < ... < n-1 is a witness for R_ord(K_a, P_b^alt) > n when it has no
    red K_a (any a vertices, all pairs red) and no blue P_b^alt embedded by an INCREASING map.
  - P_b^alt on 0..b-1 is the path visiting 0, b-1, 1, b-2, 2, ...; its edges are consecutive pairs of that sequence.
  - The file's graph6 EDGES are the blue (path) colour and NON-EDGES the red (clique) colour, the convention of the
    encoder's model output ("true means the pair has the path colour"). Read once here and fixed; selftest shows the
    checker refuses when the colours are swapped on a known witness.
Both searches are plain exhaustive enumeration of every a-subset and every b-subset: no pruning, no reachability,
nothing shared with the chain encoding.
"""
import itertools
import sys


def g6_decode(s):
    b = s.strip().encode("ascii")
    if b.startswith(b">>graph6<<"):
        b = b[10:]
    if not b or b[0] == 126:
        raise ValueError("empty, or order above 62")
    n = b[0] - 63
    bits = []
    for c in b[1:]:
        v = c - 63
        if not 0 <= v < 64:
            raise ValueError("byte out of graph6 range")
        bits += [(v >> k) & 1 for k in range(5, -1, -1)]
    need = n * (n - 1) // 2
    if len(b) - 1 != -(-need // 6) or any(bits[need:]):
        raise ValueError("length or padding does not match order %d" % n)
    edges, k = set(), 0
    for j in range(1, n):          # graph6 upper triangle order: (0,1),(0,2),(1,2),(0,3),...
        for i in range(j):
            if bits[k]:
                edges.add((i, j))
            k += 1
    return n, edges


def g6_encode(n, edges):
    bits = [1 if (i, j) in edges else 0 for j in range(1, n) for i in range(j)]
    bits += [0] * (-len(bits) % 6)
    return chr(n + 63) + "".join(chr(63 + int("".join(map(str, bits[k:k + 6])), 2)) for k in range(0, len(bits), 6))


def palt_pairs(b):
    order, lo, hi, left = [], 0, b - 1, True
    while lo <= hi:
        if left:
            order.append(lo)
            lo += 1
        else:
            order.append(hi)
            hi -= 1
        left = not left
    return [tuple(sorted(p)) for p in zip(order, order[1:])]


def find(n, blue, a, b):
    """First red K_a or blue increasing P_b^alt, or None. blue: set of (i, j), i < j."""
    for q in itertools.combinations(range(n), a):
        if not any((q[i], q[j]) in blue for i in range(a) for j in range(i + 1, a)):
            return ("red K_%d" % a, q)
    pp = palt_pairs(b)
    for v in itertools.combinations(range(n), b):
        if all((v[i], v[j]) in blue for i, j in pp):
            return ("blue P_%d^alt" % b, v)
    return None


def check(a, b, g6):
    n, blue = g6_decode(g6)
    return n, find(n, blue, a, b)


def selftest():
    ok = True
    t = palt_pairs(5) == [(0, 4), (1, 4), (1, 3), (2, 3)] and palt_pairs(6) == [(0, 5), (1, 5), (1, 4), (2, 4), (2, 3)]
    print("%s P_b^alt edges: b=5 path 0,4,1,3,2; b=6 path 0,5,1,4,2,3 (Figure 1)" % ("PASS" if t else "FAIL"))
    ok &= t
    rt = all(g6_decode(g6_encode(n, e)) == (n, e) for n, e in [(1, set()), (5, {(0, 1), (2, 4)}), (13, {(i, i + 1) for i in range(12)})])
    print("%s graph6 round trip" % ("PASS" if rt else "FAIL"))
    ok &= rt

    def exists(n, a, b):  # exhaustive over all colourings: some witness on n vertices?
        pairs = [(i, j) for j in range(n) for i in range(j)]
        for mask in range(1 << len(pairs)):
            if find(n, {p for k, p in enumerate(pairs) if mask >> k & 1}, a, b) is None:
                return True
        return False

    # small exact values by exhaustion, against the paper's Table 9 a=3 (2.5(b-1) rounded up) and trivial values:
    # R_ord(K_3, P_3^alt) = 5, R_ord(K_3, P_4^alt) = 8 (Table 9), R_ord(K_a, P_2) = a.
    vals = {}
    for a, b, n in [(3, 3, 4), (3, 3, 5), (2, 4, 3), (2, 4, 4), (4, 2, 3), (4, 2, 4)]:
        vals[(a, b, n)] = exists(n, a, b)
    small = vals[(3, 3, 4)] and not vals[(3, 3, 5)] and vals[(2, 4, 3)] and not vals[(2, 4, 4)] \
        and vals[(4, 2, 3)] and not vals[(4, 2, 4)]
    print("%s exhaustive: R_ord(K_3,P_3^alt)=5, R_ord(K_2,P_4^alt)=4, R_ord(K_4,P_2^alt)=4" % ("PASS" if small else "FAIL"))
    ok &= small
    # R_ord(K_3, P_4^alt) = 8: a witness on 7 exists; found by a random search here, then every one-pair flip is
    # checked so the checker is shown able to say NOT VALID on a near-witness.
    import random
    rnd = random.Random(71064)
    pairs7 = [(i, j) for j in range(7) for i in range(j)]
    w = None
    for _ in range(200000):
        e = {p for p in pairs7 if rnd.random() < 0.5}
        if find(7, e, 3, 4) is None:
            w = e
            break
    flips = 0
    if w is not None:
        flips = sum(find(7, w ^ {p}, 3, 4) is not None for p in pairs7)
    print("%s a K_3/P_4^alt witness on 7 found (%s); %d of %d one-pair flips are NOT VALID"
          % ("PASS" if w is not None else "FAIL", g6_encode(7, w) if w else "-", flips, len(pairs7)))
    ok &= w is not None
    swapped = find(7, set(pairs7) - w, 3, 4) is not None if w else False
    print("%s the same witness with colours swapped is NOT VALID (the edge convention matters and is fixed)"
          % ("PASS" if swapped else "FAIL"))
    ok &= swapped
    print("ALL PASS" if ok else "FAIL")
    return ok


def main(a):
    if a[:1] == ["selftest"]:
        return 0 if selftest() else 1
    if a[:1] == ["check"] and len(a) == 4:
        A, B = int(a[1]), int(a[2])
        n, hit = check(A, B, open(a[3], encoding="ascii").read())
        if hit is None:
            print("VALID: no red K_%d and no blue increasing P_%d^alt on %d vertices, so R_ord(K_%d, P_%d^alt) > %d"
                  % (A, B, n, A, B, n))
            return 0
        print("NOT VALID on %d vertices: %s at %s" % (n, hit[0], hit[1]))
        return 1
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
