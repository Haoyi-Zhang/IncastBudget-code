# Mathematical specification and proofs

This is a written mathematical proof, not a proof-assistant development.
Executable tests establish agreement only on their declared finite inputs.

## 1. Model and quantifiers

There are n queues, initially empty. Burst j has tenant i(j), size b_j>0,
and a closed release window [l_j,u_j], with 0<=l_j<=u_j. The release vector
ranges over the Cartesian product of these windows. Every burst arrives once,
atomically. Simultaneous arrivals are summed before occupancy is observed.

The positive theorem uses a *release-oblivious service clock*. For each tenant i,
S_i(t) is the cumulative service opportunity offered strictly before observation
time t. It is fixed before releases are chosen, nondecreasing, S_i(0)=0, and an
empty queue discards unused opportunity. Hence a continuously backlogged queue
receives S_i(t)-S_i(s) service over [s,t). If an arrival and a service opportunity
share a timestamp, the arrival and the pre-service occupancy are observed first;
the opportunity belongs to the next interval. Constant reservation r_i is the
special clock S_i(t)=r_i t. A fixed equal-cell calendar is another special clock,
with S_i(t) equal to the number of tenant-i slots before t. The proof does not
cover service decisions that depend on the realized release vector or another
queue's occupancy.

Rates and data can be rational. The executable constant-rate interface represents
time and bytes in integer units, so rational times and sizes first require an
exact common scale. It never rounds a rational into an integer grid. Calendar
inputs are integer slots and cells. The theorem itself is not restricted to those
two implementations: it requires only an exactly evaluable fixed service clock.

For the reservation-design sections, output capacity C requires sum_i r_i<=C.
A weight w_i>0 and declared scale gamma>=0 mean r_i>=gamma*w_i. These are
backlogged service guarantees, not unconditional rates for finite demand,
relative completion-time guarantees, or a claim of work conservation. Unused
reservations are not redistributed in the exact reference model.

B denotes capacity of a pool storing all tenant queues. Private cap bcap_i is
an additional, distinct admission condition. Safety means hypothetical lossless
occupancy never exceeds the cap. It prevents overflow in this model, not all
causes of operational throughput collapse.

## 2. Fixed-time extremal trace under a service clock

Let A_i(t) be tenant i's cumulative arrived mass through observation t. For a
fixed release vector and fixed clock, the lossless queue obeys the busy-interval
identity

    Q_i(t) = max(0, sup_{0<=s<=t}
                    [A_i(t)-A_i(s-)-(S_i(t)-S_i(s))]).

The s=t term includes arrivals exactly at t and no co-located service. The formula
follows by choosing the beginning of the current busy interval, or by unrolling
q <- max(0,q-[S_i(e)-S_i(previous)])+arrival at ordered events. It covers clocks
with jumps, tied arrivals and zero service, under the stated event convention.

Let Q_i^U(t) be occupancy when every burst is released at its upper endpoint.
Let P_i(t)=sum_{j:i(j)=i,l_j<=t<u_j} b_j and define F_i(t)=Q_i^U(t)+P_i(t).

**Lemma 1 (delaying equal arrived mass).** Fix a queue and observation t. If
arrivals that already occur by t are moved later but remain no later than t,
then occupancy at t cannot decrease under a release-oblivious service clock.

Proof. The move leaves A_i(t) unchanged and cannot increase A_i(s-) at any
s<=t. The service-clock term is fixed. Every candidate in the busy-interval
maximum therefore stays the same or increases. Repeating the argument handles
any finite set of moved arrivals. QED.

**Theorem 1 (simultaneous extremal vector).** At every t>=0, for every feasible
release vector tau, Q_i(t;tau)<=F_i(t), simultaneously for all tenants. One
feasible release vector attains equality for all tenants at that t.

Proof. Bursts with l_j>t cannot have arrived and are irrelevant to Q(t). Bursts
with u_j<=t must have arrived. Move each such burst from its actual release to
u_j; Lemma 1 shows that this cannot decrease the affected occupancy. Every
remaining eligible burst has l_j<=t<u_j. If it has already arrived, move it to
t; if it has not, release it at t. Moving or adding that mass at the observation
cannot reduce occupancy. The resulting trace has, before t, exactly the expired
upper-endpoint arrivals; at t it has every upper-endpoint arrival due at t and
every still-pending eligible burst. Its occupancy is Q_i^U(t)+P_i(t).

The same transformation applies to every tenant because all service clocks are
fixed independently of releases. It is jointly feasible because the release set
is a Cartesian product. Explicitly choose

    tau_j^t = min(u_j,t) if l_j<=t; otherwise tau_j^t=u_j.

This lies in [l_j,u_j] and attains every F_i(t). The bound is therefore a maximum,
not merely a supremum. The attaining vector may change with t; the entire envelope
curve need not come from one physical trace. QED.

The proof does not assume equal burst sizes, positive rates, continuous service,
distinct endpoints, non-overlapping windows, or a fixed ordering among tied
arrivals. Empty inputs yield zero. It DOES require independent admissible release
choices and release-oblivious service opportunities.

**Corollary 1 (exact pooled and private capacities).** Let L be the finite set
of lower endpoints. If m=0, define B_star=0 and every private peak to be zero
directly; no maximum over the empty set is used. For nonempty inputs,

    B_star(S)=max_{t in L} sum_i F_i(t),
    bcap_i_star(S)=max_{t in L} F_i(t).

The fixed service clocks are robustly safe for pooled capacity B and private
caps bcap_i iff B>=B_star and each bcap_i>=bcap_i_star.

Proof. Between consecutive window endpoints there are no upper-trace arrivals,
pending mass is constant, and a nondecreasing service clock can only drain a
queue. At an upper endpoint u_j, P_i loses b_j while Q_i^U gains b_j before any
co-located service; the changes cancel. At a lower endpoint l_j, F_i may increase
by b_j. When l_j=u_j the pending term never exists, but the upper-trace queue
gains b_j at that same lower endpoint. Tied updates add. Thus only lower endpoints
can create a larger envelope. Theorem 1 supplies a jointly attaining trace at
each maximizer, proving necessity; its coordinatewise bound proves sufficiency.
For m=0 there are no arrivals, so every initially empty queue remains zero;
this proves the separately defined empty values. QED.

Extra service that dominates a certified clock in every backlogged interval
preserves the bound but may make it non-minimal. Necessity is NOT claimed over
all work-conserving schedulers. A fully work-conserving single output is a
different aggregate-rate queue.

## 3. Exact checking and arithmetic complexity

Let e_k be the sorted union of all lower and upper endpoints. Let a_ik be mass
whose lower endpoint is e_k and d_ik mass whose upper endpoint is e_k. With
q_i=p_i=0 at time zero, the transparent service-clock recurrence is

    q_ik = max(0,q_i,k-1-[S_i(e_k)-S_i(e_k-1)]) + d_ik,
    p_ik = p_i,k-1 + a_ik - d_ik.

All p_ik are nonnegative and q_ik+p_ik is the exact envelope row. The reference
implementation stores only nonzero endpoint masses, three n-vectors, and the
sorted endpoint keys, hence O(n+m) working entries while performing O(nm)
arithmetic. Retaining every full q/p row is a distinct Theta(nm)-scalar output
choice; the default result omits it and a diagnostic sink can stream rows one at
a time. Transient q/p row snapshots also require O(n) entries. The reported
selected-container count excludes those snapshots and is not a bound on all
live entries. A violated cap is demonstrated by the explicit clipped release vector.
That witness proves a lower bound; the recurrence plus Theorem 1 proves the
upper bound.

For the constant-rate specialization S_i(t)=r_i t, a faster producer maintains
total shadow queue, total pending mass, the total rate of currently nonempty
shadows, per-queue lazy-update times, and a heap of predicted empty events. At
an endpoint it processes valid empty events through that time, drains the active
total, then applies all tied lower/upper updates. A deadline arrival invalidates
the queue's old empty prediction using a generation tag; zero-rate queues are
never inserted. Between valid events total shadow mass is linear with slope
minus the active rate. Induction over endpoints and valid heap events shows that
the maintained totals equal the transparent recurrence; stale records never
change state.

There are at most 2m endpoint occurrences, m deadline-caused heap insertions,
and m removals including stale records. Each touched queue is updated lazily;
an untouched queue's F_i cannot have increased. Sorting and heap maintenance
therefore use O((m+n) log(m+n)) arithmetic/comparison operations and O(m+n)
storage. This is not a unit-cost bit-complexity claim. With L-bit integer
times/sizes and L-bit rational rates, denominators arise from input rates and
empty-time divisions; sums and products have polynomial encoding length, so
standard exact rational arithmetic gives polynomial bit complexity, with
runtime dependent on numerator and denominator lengths.

## 4. Admission from private caps

For a lower endpoint t and tenant i, let C_i(t)={t} union {u_j<=t:i(j)=i}.
For each cut s in C_i(t), define

    W_i(s,t) = sum_{j:i(j)=i,l_j<=t,u_j>=s} b_j.

Then F_i(t) = max_s [W_i(s,t)-r_i*(t-s)]. The cut s=t makes the maximum
nonnegative. This follows from the upper-trace busy-interval expansion:
arrivals with deadline in [s,t] are queued in the interval, and P_i(t) adds all
pending eligible arrivals, exactly giving W. There is no need to use a cut at
a deadline of a not-yet-eligible burst since u_j>=l_j>t.

**Theorem 2 (minimum required rates).** If m=0 and h_i>=0, define R_i(h_i)=0.
For nonempty traffic and proposed private cap h_i, require W_i(t,t)<=h_i for
every lower endpoint t. If any such instantaneous condition fails, no finite
rate can satisfy the cap. Otherwise set

    R_i(h_i)=max({0} union {(W_i(s,t)-h_i)/(t-s): t in L,
                           s in C_i(t), s<t}),
    r_i_min=max(gamma*w_i,R_i(h_i)).

The explicit zero member handles an empty positive-duration cut set, including
nonempty traffic consisting of one fixed burst at time zero. No maximum over
an empty set is required.

Feasible reservations exist iff sum_i r_i_min<=C; assigning these rates is a
constructive solution (unused capacity may remain unassigned).

Proof. For m=0 there are no queue constraints, so only the floors and aggregate
capacity remain. For nonempty traffic, each cut with s<t is equivalent to
r_i >= its displayed quotient.
Each cut with s=t is independent of the rate and is precisely an instantaneous
condition. By Corollary 1 these cuts are jointly necessary and sufficient for
the private cap. Floors add independent lower bounds. Nonnegativity of rates
and the single sum constraint imply feasibility iff the sum of individual
minima fits. QED. These are routine consequences of the exact reduction;
quotient-based allocation alone is not asserted as a new scheduling principle.

## 5. Joint pooled rate design and certificates

Assume m>0 in the max-affine and active-cut statements below. For constant
reservations, the cut representation from Section 4 gives, for any lower
endpoint t,

    F_i(t;r_i)=max_{s in C_i(t)} [W_i(s,t)-r_i*(t-s)],

where C_i(t) contains t and every upper endpoint of a tenant-i burst no later
than t. Therefore the exact pooled requirement is the finite max-affine function

    B_star(r)=max_{t in L, s_i in C_i(t)} L_{t,s}(r),
    L_{t,s}(r)=sum_i W_i(s_i,t)-sum_i r_i*(t-s_i).

It follows directly that B_star is convex, coordinatewise nonincreasing and
piecewise affine. This observation is useful for both an LP formulation and a
small independently checkable optimum certificate.

For any n, robust pooled rate design has the linear feasibility formulation

    B>=0, r_i>=g_i, sum_i r_i<=C,
    z_ik>=d_ik,
    z_ik>=z_i,k-1-r_i*delta_k+d_ik,
    sum_i(z_ik+p_ik)<=B, for every endpoint k,

with z_i,-1=0. Minimizing B gives the minimum robust pool for fixed reservations
respecting the floors. It is enough to check pool inequalities at lower
endpoints, though all endpoints simplify the statement.

**Theorem 3 (epigraph equivalence).** This LP is feasible exactly when some
admissible rate vector is robustly safe for B.

Proof. Actual shadow values satisfy the first two z inequalities with equality
in their maximum, so any robustly safe r supplies a feasible z. Conversely,
induction on k and monotonicity of x -> max(0,x-r_i*delta)+d imply that any z
satisfying the two inequalities dominates the actual shadow q. Therefore its
pool inequalities imply the exact pool inequalities and Corollary 1 proves
safety. Extra epigraph slack cannot falsely admit a smaller pool. QED.

**Theorem 4 (general active-cut optimum certificate).** Consider

    minimize B_star(r)
    subject to r_i>=g_i and sum_i r_i<=C,

and assume m>0 and the feasible set is nonempty. A feasible r_star
with value B_star is globally optimal if there are K<=n+1 active valid cut-tuple lines L_k, weights
lambda_k>=0 summing to one, lower-bound multipliers mu_i>=0 and a capacity
multiplier nu>=0 such that

    L_k(r_star)=B_star for every k,
    sum_k lambda_k*grad L_k - mu + nu*1 = 0,
    mu_i*(r_star_i-g_i)=0 for every i,
    nu*(C-sum_i r_star_i)=0.

Such a certificate exists at every optimum.

Proof of sufficiency. Every valid line lower-bounds B_star everywhere. For any
feasible r, activity and affinity give

    B_star(r) >= sum_k lambda_k L_k(r)
              = B_star + (mu-nu*1) dot (r-r_star).

Complementarity and feasibility make each term nonnegative: mu_i can be positive
only where r_star_i=g_i and then r_i-r_star_i>=0; nu can be positive only where
sum r_star=C and then -nu*sum(r-r_star)>=0. Hence B_star(r)>=B_star.

Proof of existence. B_star is a finite convex upper envelope and the feasible
set is a nonempty compact polytope. At an optimum, the polyhedral first-order
condition says that zero belongs to the convex hull of active line gradients
plus the normal cone generated by active lower and capacity constraints. This
gives nonnegative multipliers and the displayed stationarity and complementarity
conditions. Caratheodory's theorem in R^n reduces the active-line convex
combination to at most n+1 members. QED.

A verifier can reconstruct each claimed line from t and the per-tenant cuts,
check its activity, rational weights, multipliers, stationarity and
complementarity, and independently replay the exact envelope at r_star to prove
the upper bound. The artifact records this general theorem but does not implement
a general LP solver or a producer for the multipliers.

For two tenants with m>0, all capacity can be used: increasing a fixed rate cannot
increase any queue, so an optimum exists with r_0=x and r_1=C-x. The feasible
interval is [g_0,C-g_1]. For every t and pair of cuts s_0,s_1,

    L(x)=(s_0-s_1)*x + W_0(s_0,t)+W_1(s_1,t)-C*(t-s_1).

B_star(x,C-x) is exactly the maximum of these affine functions. Indeed a sum
of two independent maxima equals the maximum over pairs. Constructing the upper
hull of the lines and evaluating its
breakpoints in the feasible interval plus the two boundaries gives an exact
optimum. Every piece is affine, hence an interior minimum occurs at a
breakpoint or on a flat piece; a flat piece has a boundary candidate. There
are O(m^3) candidate lines in the uncompressed construction, so this is a
bounded small-instance allocator, not the near-linear admission sweep.

**Theorem 5 (one/two-line two-tenant certificate).** A feasible allocation x
and envelope upper bound B are optimal if a convex combination of at most two
valid interval-pair lines is active at (x,B) and has (i) zero slope in the
interior, (ii) nonnegative slope at the left boundary, or (iii) nonpositive
slope at the right boundary. A singleton feasible interval needs only one
active line.

Proof. Each interval-pair line lower-bounds B_star(y,C-y) for all y. So does
any nonnegative combination with weights summing to one. Under the stated
slope and boundary conditions that line has value at least B throughout the
feasible interval. The feasible upper bound at x is at most B. Both inequalities
force equality and global optimality. Existence follows from convexity of the
finite upper envelope: at an interior minimum, active slopes bracket zero
(or an active slope is zero); two such slopes suffice to form zero. At a
boundary minimum an active slope of the appropriate sign exists. QED.

For m=0, every feasible allocation has B_star=0. The implementation chooses
x=g_0 and serializes one unit-weight, time-zero zero sentinel; it is not a
genuine cut line and Theorems 4--5 do not obtain a convex combination from an
empty line set. The implemented nonempty two-tenant verifier reconstructs each
support line from its two workload intervals, checks the rational weights and
slope sign, and replays the transparent upper-bound recurrence. It does not invoke
the optimizer, its hull builder, or its candidate-line generator. This is an executable check of an
instance certificate, not formal verification of the checker itself.

## 6. Fixed service calendars as a service-clock corollary

Let a periodic calendar c[0..F-1] repeat, with each entry a tenant or idle. Each
assigned slot offers one equal-size cell to that tenant and wastes the opportunity
when its queue is empty. Arrivals occur at integer slot boundaries; occupancy is
measured before that slot's service. Let S_i(t) count tenant-i opportunities in
slots [0,t). This is exactly a release-oblivious service clock, so Lemma 1,
Theorem 1 and Corollary 1 apply without a separate extremal argument. The endpoint
checker becomes

    q_ik=max(0,q_i,k-1-[S_i(e_k)-S_i(e_k-1)])+d_ik.

Prefix counts evaluate S_i(t) in constant time after O(nF) preparation, giving
O(n(m+F)) arithmetic work independent of the numeric horizon. A separate slot
loop is retained as the finite oracle. The implementation validates equal cells;
the written clock theorem also permits fixed nonnegative service quanta when
S_i is supplied exactly.

If tenant i owns k_i slots per F-slot frame, a continuously backlogged queue gets
k_i cells in every complete frame and at least k_i*floor(h/F) cells in any h
consecutive slots. Thus its long-run rate is k_i/F and a conservative latency-rate
lower service curve is (k_i/F)*(h-F)^+ for integer h. A declared long-run floor
g_i requires k_i/F>=g_i, but the fluid guarantee on every backlogged interval
does not transfer without this latency term. An average rate alone is not an
exact packet-buffer certificate because it discards phase and clustering of the
opportunities. Variable-size nonpreemptive packets, feedback-dependent calendars,
and packet-scheduling overhead remain outside the model.

This substitution does not turn the constant-rate design LP or quotient allocator
into a calendar-design algorithm. Those mechanisms use the affine dependence on
r_i and remain restricted to constant reservations.

## 7. Sharp negative controls

**Proposition 1 (all endpoint corners can miss by an arbitrary factor).** For
one tenant with r=1 and m unit bursts, use windows [j,m+j], j=0,...,m-1.
Any vector selecting only endpoints releases at distinct integer times because
the lower and upper endpoint sets are disjoint. Successive unit bursts are
separated by at least one unit of time, so the maximum queue is exactly one.
All windows contain t=m-1. Releasing all m bursts there is feasible and creates
queue m. Total mass bounds the queue by m, so the ratio is exactly m. This
includes all 2^m corner schedules, not merely all-earliest and all-latest.

**Proposition 2 (private maxima lose a factor n under pooling).** Give each
of n tenants one unit burst in a distinct zero-width window, and unit service.
Space successive windows by more than one unit. Each private maximum is one,
but pooled maximum is one, whereas their sum is n. The ratio cannot exceed n
since each private maximum is at most the pooled maximum. A synchronized
instance with one burst per tenant at a common time has the same per-tenant
translation-invariant arrival envelopes and private maxima but pooled maximum
n. Thus timestamp-free per-tenant summaries cannot recover both exact pools.

**Proposition 3 (correlation can destroy attainability).** Impose a common
phase delta in [0,m-1] and releases tau_j=delta+j. Actual unit bursts of one
tenant, r=1, are always separated by one time unit, so exact pool is one.
Their marginal windows [j,j+m-1] all intersect at m-1; the rectangular
relaxation allows a simultaneous queue m. Hence ignoring phase coupling gives
a safe but arbitrarily loose upper bound. No independence means no assertion
of necessity from Theorem 1. This is not a counterexample to its stated model.

**Proposition 4 (calendar order matters beyond average rate).** Two unit
bursts of tenant 1 arrive at 0 and 2. With average fluid rate 1/2 their peak is
one. Calendar (0,0,1,1) has no tenant-1 service in slots 0 or 1, so its peak at
2 is two. Calendar (0,1,0,1) gives peak one. Both calendars reserve exactly
one half of the slots. The pre-service observation convention is essential.

## 8. Refinement, approximation and composition

For an admissible release set U, define

    B(U)=sup_{tau in U} sup_{t>=0} sum_i Q_i(t;tau).

**Proposition 5 (uncertainty-set monotonicity).** If U1 is a subset of U2, then
B(U1)<=B(U2). Therefore safety proved for the outer set U2 is valid for U1, and
an overload witness in the inner set U1 is valid for U2.

Proof. The trajectories maximized over U1 are a subset of those maximized over
U2. The two logical consequences follow by comparing the same cap with either
an upper bound or a concrete member of the set. QED.

Tightening windows, adding release equalities, or merging independent phase bits
into one shared bit restricts the set and cannot increase the exact capacity.
Widening windows, forgetting relations, or splitting one shared phase into
independent bits enlarges the set and cannot decrease it. Thus a marginal-window
rectangle is a safe outer approximation of a correlated declaration, whereas
endpoint corners and sampled scenarios are inner lower-bound searches and cannot
certify safety. Summing exact private maxima is also a safe outer bound on a
shared pool, but Proposition 2 shows an n-fold gap.

Per-pool certificates compose only when every pool is analyzed against the same
valid global declaration and an exogenous service clock; then certifying each
pool proves that none overflows. Separate maximizers need not coincide, so their
sum is not generally an exact network-wide requirement. If downstream arrival
times depend on upstream service, they are endogenous and cannot be replaced by
fresh independent windows without a separate correlation-preserving propagation
theorem. No such multi-hop theorem is claimed here.

## 9. What remains outside these proofs

No proof here establishes a workload's release windows from real executions,
inter-switch independence, transport throughput/collapse, fairness of collective
completion times, or optimal buffer use by arbitrary work-conserving schedulers.
No property of a real switch, transport, GPU, or model workload is inferred from
these synthetic instances. These theorems do not establish scholarly novelty;
that requires a separate, adequately complete closest-work comparison.
