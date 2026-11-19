// test_core.mjs -- runs the page's own checker (cut from ordered-ramsey-check.html between the CORE markers)
// against the expected answers written by gen_cases.py.
//
//     python -I tests/gen_cases.py cases.json
//     node tests/test_core.mjs cases.json
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.join(path.dirname(fileURLToPath(import.meta.url)), "..");
const html = fs.readFileSync(path.join(root, "ordered-ramsey-check.html"), "utf8");
const core = html.split("/*CORE-START*/")[1].split("/*CORE-END*/")[0];
const api = new Function(core + "; return { altOrder, subsets, createCheck, decodeGraph6, binom };")();
const data = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));

function matrix(n, firstEdges) {
  const f = Array.from({ length: n }, () => new Array(n).fill(false));
  for (const [i, j] of firstEdges) f[i][j] = f[j][i] = true;
  return f;
}
function valid(first, a, b) {
  const job = api.createCheck(first, a, b);
  while (!job.done) job.step(100000);
  return { ok: job.hit === null, job };
}
let fail = 0;
const say = (ok, msg) => { console.log((ok ? "PASS " : "FAIL ") + msg); if (!ok) fail++; };

say(JSON.stringify(api.altOrder(5)) === "[0,4,1,3,2]" && JSON.stringify(api.altOrder(6)) === "[0,5,1,4,2,3]"
  && JSON.stringify(api.altOrder(9)) === "[0,8,1,7,2,6,3,5,4]", "altOrder(5), (6), (9) equal k3palt.alt");
say(api.binom(22, 4) === 7315 && api.binom(22, 7) === 170544 && api.binom(19, 9) === 92378, "binom counts");
let count = 0; for (const _ of api.subsets(10, 4)) count++;
say(count === 210, "subsets(10,4) yields 210 sets");

const agree = {}, both = {};
let hitsOk = true;
for (const c of data.cases) {
  const first = matrix(c.n, c.first), r = valid(first, c.a, c.b);
  agree[c.by] ??= [0, 0]; both[c.by] ??= [0, 0];
  agree[c.by][1]++; if (r.ok === c.valid) agree[c.by][0]++;
  both[c.by][c.valid ? 0 : 1]++;
  if (r.job.hit) {  // a reported hit must really be one, read straight off the matrix
    const h = r.job.hit;
    if (h.kind === "clique") { for (const x of h.vertices) for (const y of h.vertices) if (x !== y && !first[x][y]) hitsOk = false; }
    else {
      for (let t = 0; t + 1 < h.walk.length; t++) if (first[h.walk[t]][h.walk[t + 1]]) hitsOk = false;
      for (let t = 0; t + 1 < h.vertices.length; t++) if (!(h.vertices[t] < h.vertices[t + 1])) hitsOk = false;
    }
  }
}
for (const k of Object.keys(agree)) say(agree[k][0] === agree[k][1], `agrees with ${k} on ${agree[k][0]} of ${agree[k][1]} colourings`);
for (const k of Object.keys(both)) say(both[k][0] >= 40 && both[k][1] >= 40, `the ${k} cases hold both answers (${both[k][0]} valid, ${both[k][1]} not)`);
say(hitsOk, "every reported clique or path is really there in the matrix");

// K_19: the list typed into the page equals n19_colouring.txt, and is valid by both checkers
const m = html.match(/const K19_FIRST = "([^"]+)"/)[1];
const typed = []; for (const part of m.split(";")) { const [i, rest] = part.split(":"); for (const t of rest.split(" ")) typed.push([+i, +t]); }
const key = e => e.map(x => x.join("-")).sort().join(",");
say(key(typed) === key(data.k19_first) && typed.length === 67, "the page's K_19 list equals n19_colouring.txt, 67 edges");
const r19 = valid(matrix(19, typed), 3, 9);
say(r19.ok && data.k19_valid && r19.job.cliqueSets === 969 && r19.job.pathSets === 92378, "K_19 valid for (3,9): page checker and k3palt.find, all 969 + 92,378 sets seen");

// K_22: the page's graph6 string equals k4_p7_n22.g6, decodes to the same edges, and is valid for (4,7)
const g = html.match(/const G6_K22 = "([^"]+)"/)[1];
say(g === fs.readFileSync(path.join(root, "k4_p7_n22.g6"), "utf8").trim(), "the page's graph6 string equals k4_p7_n22.g6");
const adj = api.decodeGraph6(g), second = [];
for (let i = 0; i < 22; i++) for (let j = i + 1; j < 22; j++) if (adj[i][j]) second.push([i, j]);
say(adj.length === data.k22_n && key(second) === key(data.k22_second), `graph6 decodes to the same ${second.length} edges as kapalt_check.g6_decode`);
const first22 = Array.from({ length: 22 }, (_, i) => Array.from({ length: 22 }, (_, j) => i !== j && !adj[i][j]));
const r22 = valid(first22, 4, 7);
say(r22.ok && data.k22_valid && r22.job.cliqueSets === 7315 && r22.job.pathSets === 170544, "K_22 valid for (4,7): page checker and kapalt_check.find, all 7,315 + 170,544 sets seen");

// The checker must be able to say no. Flip each edge of K_22 in turn and count how many flips break it.
let broken = 0, total = 0;
for (let i = 0; i < 22; i++) for (let j = i + 1; j < 22; j++) {
  first22[i][j] = first22[j][i] = !first22[i][j];
  if (!valid(first22, 4, 7).ok) broken++;
  total++;
  first22[i][j] = first22[j][i] = !first22[i][j];
}
say(broken > 0, `one-edge flips of K_22 that break it: ${broken} of ${total}`);
say(!valid(matrix(8, []), 3, 4).ok && !valid(Array.from({ length: 8 }, (_, i) => Array.from({ length: 8 }, (_, j) => i !== j)), 3, 4).ok, "both one-colour colourings of K_8 fail for (3,4)");

console.log(fail ? `FAIL (${fail})` : "ALL PASS");
process.exit(fail ? 1 : 0);
