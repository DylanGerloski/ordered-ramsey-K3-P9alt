"""gen_cases.py -- expected answers for test_core.mjs, from the two Python checkers in this repository.

    python -I tests/gen_cases.py cases.json

The page ordered-ramsey-check.html carries its own checker, written in JavaScript. This script writes the answers
that checker is expected to give, using code that shares nothing with it:
  - clique size 3: k3palt.find(), a depth-first search over path positions;
  - clique size 4: kapalt_check.find(), a separate enumeration written from the definition.
Random colourings at these sizes are nearly all invalid, so on their own they would test one answer only. Small
orders, and sub-colourings of the two real colourings with 0 to 2 edges flipped, give both answers.
"""
import importlib.util
import itertools
import json
import os
import random
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")


def load(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(ROOT, name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


k3 = load("k3palt")
ka = load("kapalt_check")


def valid4(b, n, first):
    """kapalt_check takes the path-colour edges; the page takes the clique-colour edges."""
    blue = {e for e in itertools.combinations(range(n), 2) if e not in first}
    return ka.find(n, blue, 4, b) is None


def main(out):
    rnd = random.Random(20261119)
    cases = []

    def add(a, b, n, first):
        if a == 3:
            cases.append({"a": 3, "b": b, "n": n, "first": sorted(first), "valid": k3.find(b, n, first) is None, "by": "k3palt.find"})
        else:
            cases.append({"a": 4, "b": b, "n": n, "first": sorted(first), "valid": valid4(b, n, first), "by": "kapalt_check.find"})

    def rand(n, p):
        return {e for e in itertools.combinations(range(n), 2) if rnd.random() < p}

    for _ in range(400):
        b, n = rnd.choice([(4, 7), (5, 9), (6, 10), (4, 8), (5, 10), (6, 12)])
        add(3, b, n, rand(n, rnd.choice([0.2, 0.35, 0.5])))
    for _ in range(200):
        b = rnd.choice([4, 5, 6])
        n = rnd.randint(b, b + 3)
        add(3, b, n, rand(n, rnd.choice([0.3, 0.45, 0.6])))
    for _ in range(150):
        b, n = rnd.choice([(4, 9), (5, 11), (5, 12)])
        add(4, b, n, rand(n, rnd.choice([0.4, 0.55, 0.7])))

    def sub(first_edges, big, m, flips):
        keep = sorted(rnd.sample(range(big), m))
        at = {v: i for i, v in enumerate(keep)}
        first = {(at[i], at[j]) for i, j in first_edges if i in at and j in at}
        for e in rnd.sample(list(itertools.combinations(range(m), 2)), flips):
            first ^= {e}
        return m, first

    k19 = sorted(k3.read_model(os.path.join(ROOT, "n19_colouring.txt")))
    for _ in range(200):
        n, first = sub(k19, 19, rnd.randint(12, 19), rnd.choice([0, 0, 1, 2]))
        add(3, 9, n, first)

    n22, blue22 = ka.g6_decode(open(os.path.join(ROOT, "k4_p7_n22.g6"), encoding="ascii").read())
    first22 = sorted(e for e in itertools.combinations(range(n22), 2) if e not in blue22)
    for _ in range(120):
        n, first = sub(first22, 22, rnd.randint(14, 20), rnd.choice([0, 0, 1, 2]))
        add(4, 7, n, first)

    for c in cases:  # every edge must lie inside its own colouring's vertex set
        assert all(0 <= i < j < c["n"] for i, j in c["first"])
    json.dump({"cases": cases,
               "k19_first": k19, "k19_valid": k3.find(9, 19, set(k19)) is None,
               "k22_n": n22, "k22_second": sorted(blue22), "k22_valid": ka.find(n22, blue22, 4, 7) is None},
              open(out, "w"))
    print("wrote %d cases, %d valid; K_19 by k3palt.find: %s; K_22 by kapalt_check.find: %s"
          % (len(cases), sum(c["valid"] for c in cases), k3.find(9, 19, set(k19)) is None, ka.find(n22, blue22, 4, 7) is None))


if __name__ == "__main__":
    main(sys.argv[1])
