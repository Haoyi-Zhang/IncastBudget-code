"""Independent exact event verifier for fixed constant-rate queues.

This module builds each tenant's queue segments from that tenant's own arrival
epochs and exact empty times.  It deliberately does not call the producer,
reference recurrence, or ordinary replay in :mod:`queues`.
"""
from __future__ import annotations

from collections import defaultdict
from fractions import Fraction as F

from queues import validate


def _event(events, time):
    """Return mutable [queue jump, queue-slope delta] at ``time``."""
    return events[time]


def _tenant_segments(bursts, rate, queue_events, pending_events=None):
    """Build one queue's additive event changes and its private envelope max.

    Queue slope is either zero or ``-rate``.  Empty transitions occur at the
    exact rational time ``last + q/rate``; arrivals are then applied at their
    endpoint, before any service at that endpoint.
    """
    upper = defaultdict(int)
    starts = defaultdict(int)
    ends = defaultdict(int)
    for burst in bursts:
        upper[burst.upper] += burst.size
        starts[burst.lower] += burst.size
        ends[burst.upper] += burst.size
    r = F(rate)

    q = F(0)
    last = F(0)
    active = False
    for raw_time, amount in sorted(upper.items()):
        time = F(raw_time)
        if active and r > 0:
            empty = last + q / r
            if empty <= time:
                row = _event(queue_events, empty)
                row[1] += r
                q = F(0)
                last = empty
                active = False
        q = max(F(0), q - r * (time - last))
        last = time
        row = _event(queue_events, time)
        row[0] += amount
        if amount and not active:
            row[1] -= r
            active = True
        q += amount
    if active and r > 0:
        _event(queue_events, last + q / r)[1] += r

    if pending_events is not None:
        for time, amount in starts.items():
            pending_events[F(time)] += amount
        for time, amount in ends.items():
            pending_events[F(time)] -= amount

    # Private envelope maxima are attained at lower endpoints.  Replay this
    # one queue only; no tenant-wide vector is formed at global event times.
    q = F(0)
    pending = 0
    last = F(0)
    peak = F(0)
    endpoint_times = sorted(set(starts) | set(ends))
    for raw_time in endpoint_times:
        time = F(raw_time)
        q = max(F(0), q - r * (time - last))
        q += ends.get(raw_time, 0)
        pending += starts.get(raw_time, 0) - ends.get(raw_time, 0)
        last = time
        if raw_time in starts:
            peak = max(peak, q + pending)
    return peak


def _merge_peak(events, pending_events=None):
    """Sweep additive queue jumps, pending deltas and queue slope changes."""
    q = F(0)
    pending = 0
    slope = F(0)
    last = F(0)
    peak = F(0)
    when = 0
    for time in sorted(events.keys() | (pending_events or {}).keys()):
        q += slope * (time - last)
        jump, slope_delta = events.get(time, (F(0), F(0)))
        q += jump
        if pending_events is not None:
            pending += pending_events.get(time, 0)
        slope += slope_delta
        total = q + pending
        if total > peak:
            peak = total
            when = time
        last = time
    # Increases occur only at integer arrivals/lower endpoints. Exact empty
    # events drain mass and cannot introduce a new maximum. Preserve the
    # integer observation-time contract rather than serializing a Fraction.
    if isinstance(when, F):
        if when.denominator != 1:
            raise ArithmeticError('a draining event cannot introduce a peak')
        when = when.numerator
    return peak, when


def shadow_segments(bursts, rates):
    """Return exact pooled/private envelope maxima and earliest maximizing time.

    The fixed-rate event verifier uses O((m+n) log(m+n)) rational arithmetic
    and O(m+n) event/segment storage, apart from operand bit complexity.
    """
    validate(bursts, rates)
    n = len(rates)
    by_tenant = [[] for _ in range(n)]
    for burst in bursts:
        by_tenant[burst.tenant].append(burst)

    events = defaultdict(lambda: [F(0), F(0)])
    pending_events = defaultdict(int)
    private = [F(0)] * n
    for tenant, own_bursts in enumerate(by_tenant):
        private[tenant] = _tenant_segments(
            own_bursts, rates[tenant], events, pending_events)

    pool, when = _merge_peak(events, pending_events)
    return {'pool': pool, 'private': private, 'time': when}


def simulate_segments(bursts, rates, releases):
    """Replay a concrete release vector using independent queue segments.

    The return fields match ``queues.simulate(..., record=False)``.  In
    particular, ``trace`` is empty: producing dense queue rows would itself
    require Theta(nm) output storage.
    """
    validate(bursts, rates)
    if len(releases) != len(bursts):
        raise ValueError('release length mismatch')
    by_tenant = [[] for _ in rates]
    for burst, time in zip(bursts, releases):
        if type(time) is not int or not burst.lower <= time <= burst.upper:
            raise ValueError('release outside declared window')
        by_tenant[burst.tenant].append((time, burst.size))

    events = defaultdict(lambda: [F(0), F(0)])
    private = [F(0)] * len(rates)
    for tenant, arrivals in enumerate(by_tenant):
        r = F(rates[tenant])
        grouped = defaultdict(int)
        for time, size in arrivals:
            grouped[time] += size

        q = F(0)
        last = F(0)
        active = False
        for raw_time, amount in sorted(grouped.items()):
            time = F(raw_time)
            if active and r > 0:
                empty = last + q / r
                if empty <= time:
                    events[empty][1] += r
                    q = F(0)
                    last = empty
                    active = False
            q = max(F(0), q - r * (time - last))
            last = time
            events[time][0] += amount
            if amount and not active:
                events[time][1] -= r
                active = True
            q += amount
            private[tenant] = max(private[tenant], q)
        if active and r > 0:
            events[last + q / r][1] += r

    pool, when = _merge_peak(events)
    return {'pool': pool, 'private': private, 'time': when, 'trace': []}
