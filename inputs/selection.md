# Synthetic input selection

The consumed JSON files, not a future pseudo-random generator run, are the exact
input records for reproduction. No private trace or external workload is used.

The four-burst window pilot has 96 cases. Its generator used Python's local
`random.Random(941)`. For each case and each of four bursts, in order: draw lower
from `range(4)`, upper from `range(lower,5)`, tenant from `range(2)`, size from
`range(1,4)`. Fixed rates are `(1/2,3/2)`. The cell pilot uses calendar `(0,1,1)`.
All generated cases were retained, not filtered on their outcomes.

The four-burst allocation pilot has 80 cases, using `random.Random(712)`. For
each burst in order, draw lower from `range(4)`, upper from `range(lower,5)`, and
size from `range(1,4)`; tenant is the burst index modulo two. Capacity is two
and floors are `(1/4,1/2)`. All generated cases were retained. No post-pilot
parameter tuning or stochastic confidence interval is claimed.

The extended bounded domains are completely enumerated, not sampled. Their
endpoints, sizes, tenant assignments, rates, calendar ordering, capacity and
floors are in `validation-plan.json`; exact instances are in `bounded.jsonl`
and `allocation-bounded.json`. The former fixes three bursts and has 20,736
inputs. The latter fixes two bursts, one per tenant, and has 432 inputs. Every
integer point in each closed release window is considered by the finite oracle.
The oracle limit is 200,000 combinations per input; no retained case exceeds it.

The binary-phase graph family contains every labeled simple graph on 1, 2, 3
and 4 vertices and every bit assignment. Vertex pairs are ordered
lexicographically; every edge-subset bit mask is considered in increasing order.
Graph inputs are retained with their outputs in `results/correlation.json`.
For each graph the bit assignments are regenerated lexicographically from its
vertex count. No selection depends on MAX-CUT value.

The negative controls are explicit constructions in `src/validate_cases.py`
and `proofs/core.md`. They include every endpoint combination for every
m=2,...,10 in the corner family, a six-burst shared shift with shifts 0,...,5,
fixed periodic calendar comparisons, and pooling/scheduler boundary cases.
The running example in `example.json` is explanatory, not a held-out workload.
