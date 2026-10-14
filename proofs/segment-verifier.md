# Fixed-rate segment verification

The constant-rate interface has integer burst sizes and endpoints and exact
nonnegative rational reservations. Occupancy is observed after all tied
arrivals. This verifier is separate from the lazy heap producer and from the
transparent endpoint-vector recurrence.

For one tenant, group its upper-endpoint arrivals in increasing time. Between
arrivals the queue has slope minus its reservation while nonempty and zero
while empty. If the queue is q immediately after an arrival at v and the
reservation r is positive, its empty time without another arrival is v+q/r.
Emit that slope transition only when it occurs no later than the next arrival;
otherwise continue the same busy segment through that arrival. The next
arrival adds its mass before observing occupancy. A zero-rate queue never
drains and needs no empty event. Induction over the tenant's own arrivals
establishes its entire upper-trace queue curve. Each arrival creates one jump
and at most one terminating empty event, hence linear event storage.

Merge all tenants' additive jump and slope events. Between merged times,
advance the aggregate by its current summed slope. At a merged time, apply
all queue jumps and pending-mass deltas together, then update the summed
slope. The pending contribution adds a burst at its lower endpoint and removes
it at its upper endpoint. At the latter time the queue gains exactly the
removed mass, preserving the envelope's tied-endpoint convention. By induction,
the aggregate equals the sum of the tenants' queues plus pending masses.
Positive jumps in that envelope occur at lower endpoints; empty transitions
and intervals between events cannot increase it. Taking its maximum therefore
returns the exact pooled capacity and earliest maximizing observation. The
zero sentinel is retained for empty traffic. Independent one-tenant endpoint
passes compute all private maxima without scanning other tenants' states.

For a concrete release vector, repeat the queue-segment construction using
actual arrivals and omit pending deltas. This gives an exact ordinary queue
replay. A clipped vector is first checked to belong to the original windows,
then replayed; its pooled maximum must equal the independently reconstructed
envelope maximum. This lower-witness test complements the upper-envelope test.

Grouping and creating events take O(m+n) work and storage. Sorting each
tenant's local events and the combined events takes at most
O((m+n) log(m+n)) arithmetic/comparison operations. No n-vector is updated at
each global event. The heap producer, segment verifier, witness construction,
and segment replay together retain that bound and O(m+n) working entries.
Exact rational operand lengths remain part of bit complexity. Arbitrary
service clocks and dense diagnostic-row output retain their transparent
recurrences; this argument does not optimize those different interfaces.

The executable comparisons cover all 96 existing pilot inputs and 20,736
bounded window inputs, including exact pool, private values, observation and
witness replay. Small release-vector oracles and tied/zero/fractional-rate
controls supplement that fixed-domain comparison; finite tests support the
implementation, while the segment invariants establish the general argument.
