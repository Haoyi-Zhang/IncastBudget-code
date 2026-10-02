# Binary shared phases: exact elimination and a hardness boundary

This document contains written mathematical arguments, not proof-assistant
output.  Executable checks establish agreement only on their declared finite
inputs.  The release set below is different from the Cartesian product of
continuous windows used in `core.md`; the change of quantifiers is essential.

## 1. Model

There are `n` initially empty tenant queues.  Queue `i` receives a fixed,
arrival-independent constant service rate `r_i>=0`; unused service is discarded.
A binary phase group `v` chooses one bit `x_v in {0,1}` for the entire schedule.
A grouped burst `j`, assigned to group `g(j)`, has base time `a_j`, common phase
offset `D>=0`, tenant `i(j)`, and size `b_j>0`, and arrives at

    a_j + D*x_{g(j)}.

A fixed burst has no group and arrives at its base time.  Simultaneous arrivals
are summed before occupancy is observed.  All numbers are supplied explicitly
and are exactly representable.  The robust pooled peak is

    B_phase = max_{x in {0,1}^g} max_{t>=0} sum_i Q_i(t;x).

This model permits a phase group to affect bursts in several tenants.  It does
not permit an arbitrary value in `[0,D]`, precedence constraints, feedback-
dependent service, or a work-conserving redistribution of unused reservations.

## 2. Finite candidate observations

Let `T` contain every possible arrival epoch: `a_j` for every burst, and also
`a_j+D` for every grouped burst.  Thus `|T|<=2m`, after duplicate removal.
Between two consecutive epochs in `T`, no queue receives an arrival and every
queue is nonincreasing.  Consequently

    B_phase = max_{t in T} max_x sum_i Q_i(t;x),

with the empty-input value defined as zero at time zero.  This reduction is
independent of any treewidth assumption.

## 3. Factorization at a fixed observation

For tenant `i`, let `G_i` be the phase groups that control at least one of its
bursts.  At a fixed `t in T`, replaying only tenant `i` defines an exact factor

    f_{i,t} : {0,1}^{G_i} -> nonnegative rationals,
    f_{i,t}(x_{G_i}) = Q_i(t;x).

Therefore the pooled occupancy at `t` is the max-sum objective

    P_t = max_x sum_i f_{i,t}(x_{G_i}).

The *phase interaction graph* has one vertex per group and an edge between two
groups whenever they occur together in some `G_i`.  Every tenant scope is a
clique in this graph.  Fixed bursts affect factor values but introduce no phase
vertex.

## 4. Exact variable elimination

Choose any elimination order `pi=(v_1,...,v_g)`.  When eliminating `v_k`, collect
all current factors whose scope contains `v_k`, sum them, and maximize over the
two values of `v_k`.  The resulting factor is indexed by the other variables in
the union of those scopes.  Store, for every resulting table entry, one maximizing
bit.  After all variables are eliminated, the remaining scalars sum to `P_t`;
reading stored choices in reverse order reconstructs a maximizing assignment.

The induced width `w(pi)` is the largest number of still-live neighbors of a
variable when it is eliminated in the filled interaction graph.  Equivalently,
every intermediate factor has at most `w(pi)` remaining variables, while the
bucket being maximized contains at most `w(pi)+1` variables.

**Theorem 1 (exact bounded-width phase certificate).**  For an explicitly
listed binary-phase instance and any supplied elimination order `pi`, max-sum
elimination computes `B_phase`, a maximizing observation, and a maximizing phase
assignment exactly.  With exact arithmetic its time is

    O(|T| * poly(m+n+g) * 2^{w(pi)+1})

and its working storage is `poly(m+n+g)*2^{w(pi)+1}`.  The reported order and its
filled-neighborhood sizes are directly checkable; optimal treewidth need not be
computed.

Proof.  The candidate-time argument reduces the outer maximum to finite `T`.
For one `t`, the tenant replay tables are precisely the factors above.  The
standard distributive identity

    max_{x_v} [h(x_v,y)+k(x_v,z)]

produces a factor on `(y,z)` with the same optimum as the eliminated objective.
Induction over the order preserves the exact maximum.  The recorded argmax bit
for each table row reconstructs a jointly consistent assignment in reverse.
Every original tenant scope is a clique, so it contains at most `w(pi)+1`
variables; every intermediate bucket has the same bound by the definition of
induced width.  Enumerating binary table rows and replaying explicit bursts gives
the stated exponential factor times polynomial bookkeeping and exact-arithmetic
cost.  Taking the largest exact `P_t` over `T` proves the result.  QED.

A deterministic min-fill order is only a heuristic for obtaining a small
reported width.  Exactness does not depend on the heuristic.  In particular,
forests admit width one orders, so this algorithm is polynomial on phase
interaction forests.  A supplied poor order may be exponentially slower while
still returning the exact answer.

## 5. Decision problem

OVERLOAD asks whether some phase assignment yields pooled occupancy greater than
an integer capacity `B` at some time.  SAFE is its complement: every phase
assignment stays within `B`.  The input contains the groups, explicitly listed
bursts, rates, and integer time parameters.  A proposed overload assignment can
be replayed in polynomial time, so OVERLOAD is in NP.

## 6. Four-epoch MAX-CUT reduction

Start with an unweighted simple graph `G=(V,E)`, with `e` edges.  The decision
version of simple MAX-CUT is NP-complete (Garey, Johnson and Stockmeyer, 1976,
Theoretical Computer Science 1(3), 237--267,
DOI 10.1016/0304-3975(76)90059-1).  Define `M=4e+1` and `D=M+2`.  There are two
queues per edge and one anchor queue, so `n=2e+1`; every queue has rate one.

For each vertex `v`, create phase bit `x_v`.  For each edge `{u,v}`, with `u<v`,
put two unit bursts in queue `q_uv^+`:

- a burst controlled by `u` with base zero, arriving at `D*x_u`;
- a burst controlled by `v` with base `D`, arriving at `D+D*x_v`.

Put two unit bursts in queue `q_uv^-`:

- a burst controlled by `u` with base `D`, arriving at `D+D*x_u`;
- a burst controlled by `v` with base zero, arriving at `D*x_v`.

Finally put `M` fixed unit bursts in the anchor queue at `D+1`.  The construction
has `8e+1` explicitly listed bursts, `2e+1` queues, and `|V|` phase groups.  Every
arrival is at one of `0`, `D`, `D+1`, and `2D`; all numerical parameters are
polynomially bounded.

Fix an assignment.  Any edge-queue mass arriving at zero has drained before
`D`.  Immediately after `D`,

    q_uv^+ contains x_u + (1-x_v),
    q_uv^- contains (1-x_u) + x_v.

After one unit of service, immediately before the anchor arrives at `D+1`, their
residuals are respectively

    1{x_u=1 and x_v=0},   1{x_u=0 and x_v=1}.

They sum to one exactly when the edge crosses the cut defined by `x`.  The anchor
queue was empty, hence

    pooled_Q(D+1;x) = M + cut_G(x).

At epochs zero and `D`, pooled occupancy is at most `4e<M`; between arrivals it
only decreases.  Edge residuals after `D+1` drain by `D+2`, while the anchor
drains by `D+1+M=2D-1`.  Thus the system is empty immediately before `2D`; at
`2D` at most `4e<M` edge bursts arrive.  No later arrivals exist.  Therefore,
for every assignment,

    max_t pooled_Q(t;x) = M + cut_G(x),

and consequently `B_phase=M+MAXCUT(G)`.

For a MAX-CUT threshold `k`, set `B=M+k-1`.  Since peaks are integral, an
overload exists iff `MAXCUT(G)>=k`.  This is a polynomial many-one reduction.
Together with membership in NP it proves the following.

**Theorem 2 (unbounded-width boundary).**  OVERLOAD is NP-complete and SAFE is
coNP-complete, even with unit bursts, equal fixed reservations, and four arrival
epochs.  The statement also holds after normalizing aggregate service capacity
to one: multiply all epochs and `D` by `n` and replace every rate one by `1/n`.

The phase interaction graph of this construction is exactly `G`: each edge queue
creates scope `{u,v}`, and the anchor has empty scope.  Hence Theorem 1 solves
the same reduction family in time exponential in an elimination width of `G`,
while Theorem 2 rules out a polynomial algorithm for arbitrary width unless
P=NP.  This is a tractability boundary, not a contradiction.

## 7. Consequence for universal safety certificates

If every SAFE instance in this binary shared-phase class had a polynomial-length
certificate accepted by a sound, complete polynomial-time verifier, then SAFE
would lie in NP.  Since SAFE is coNP-complete, this would imply NP=coNP.  This is
conditional: it is not an unconditional lower bound on every proof system, and
it does not say that particular safe instances lack short certificates.  The
rectangular-window checker avoids the obstruction by assuming independent
release coordinates; it does not solve general phase-coupled admission.

## 8. Scope attacks and retained finite checks

The anchor is necessary to make the cut-dependent observation the global peak;
the choice `D=M+2` supplies enough final drain time.  Replacing fixed reservations
with a work-conserving aggregate server, allowing continuous phases, or adding
precedence changes the model and is not covered by the reduction or algorithm.
Marginal windows are only an outer relaxation of the grouped release set.

The retained validation exhaustively checks all 75 labeled simple graphs on one
through four vertices and all 1,098 phase assignments.  For each assignment,
ordinary queue replay checks the full peak, its observation time, and the
identity `M+cut_G(x)`.  Exact elimination matches exhaustive optimization for
all 75 graphs; the observed induced-width histogram under deterministic
min-fill is `{0:4, 1:44, 2:26, 3:1}`.  A separate 64-vertex path check has width
one, 63 edges, exact peak 316, four candidate epochs, and 2,020 constructed
factor entries.  These finite checks test the implementation and construction;
they neither prove the general theorems nor establish workload realism or
scholarly novelty.
