"""Exact admission with private caps and a checked two-tenant pooled allocator.

Uses only rational arithmetic. The two-tenant algorithm is an upper-envelope
construction, not a general-purpose LP solver. Its verifier checks supporting
busy-interval lines without calling that optimizer.
"""
from __future__ import annotations
from fractions import Fraction as F
from dataclasses import dataclass
from exact import rational
from queues import Burst, validate, shadow_reference


def cuts(bursts, n):
    """Yield (observation, tenant, interval_start, amount) for exact affine cuts."""
    validate(bursts, [F(0)] * n)
    for t in sorted({b.lower for b in bursts}):
        for i in range(n):
            eligible = [b for b in bursts if b.tenant == i and b.lower <= t]
            for s in sorted({t} | {b.upper for b in eligible if b.upper <= t}):
                yield t, i, s, sum(b.size for b in eligible if b.upper >= s)


def private_admission(bursts, caps, floors, capacity):
    """Necessary and sufficient fixed-reservation admission for private caps.

    All arguments besides burst fields may be integers or Fractions. Rejected
    instances return a genuine violated instantaneous or aggregate rate cut.
    """
    caps = list(map(rational, caps)); floors = list(map(rational, floors)); capacity = rational(capacity)
    n = len(caps)
    if n != len(floors) or capacity < 0 or any(x < 0 for x in caps + floors):
        raise ValueError('invalid caps, floors, or capacity')
    validate(bursts, floors)
    rates = list(floors); causes = [None] * n
    for t, i, s, amount in cuts(bursts, n):
        if s == t:
            if amount > caps[i]:
                return {'feasible': False, 'reason': 'instantaneous',
                        'tenant': i, 'time': t, 'amount': F(amount), 'cap': caps[i]}
        else:
            required = (F(amount) - caps[i]) / (t - s)
            if required > rates[i]:
                rates[i] = required; causes[i] = (t, s, amount)
    if sum(rates) > capacity:
        return {'feasible': False, 'reason': 'capacity', 'rates': rates,
                'required': sum(rates), 'capacity': capacity, 'causes': causes}
    # This replay is a sanity check, not the proof of sufficiency.
    out = shadow_reference(bursts, rates)
    if any(a > b for a, b in zip(out['private'], caps)):
        raise ArithmeticError('rate construction does not meet its cap')
    return {'feasible': True, 'rates': rates, 'spare': capacity - sum(rates),
            'private': out['private'], 'pool': out['pool'], 'causes': causes}


@dataclass(frozen=True)
class Line:
    slope: F
    intercept: F
    time: int
    s0: int
    s1: int

    def value(self, x):
        return self.slope * x + self.intercept

    def record(self):
        return {'slope': str(self.slope), 'intercept': str(self.intercept),
                'time': self.time, 's0': self.s0, 's1': self.s1}


def pool_lines(bursts, capacity):
    """Exact B(x) lines for nonempty two-tenant traffic.

    Empty traffic is handled by an explicit zero-certificate branch in
    ``optimize_two`` and ``verify_two``; its serialization sentinel is not a
    genuine busy-interval cut.
    """
    capacity = rational(capacity)
    grouped = {}
    for t, i, s, amount in cuts(bursts, 2):
        grouped.setdefault(t, [[], []])[i].append((s, F(amount)))
    lines = []
    for t, arms in grouped.items():
        for s0, a0 in arms[0]:
            for s1, a1 in arms[1]:
                lines.append(Line(F(s0-s1), a0+a1-capacity*(t-s1), t, s0, s1))
    if not lines:
        raise ArithmeticError('nonempty traffic produced no cut lines')
    return lines


def upper_hull(lines):
    """Increasing slopes and the exact abscissa where each becomes active."""
    by_slope = {}
    for line in lines:
        old = by_slope.get(line.slope)
        if old is None or line.intercept > old.intercept:
            by_slope[line.slope] = line
    hull = []; starts = []
    for line in sorted(by_slope.values(), key=lambda v: v.slope):
        start = None
        while hull:
            start = (hull[-1].intercept-line.intercept)/(line.slope-hull[-1].slope)
            if starts[-1] is None or start > starts[-1]:
                break
            hull.pop(); starts.pop()
        if not hull: start = None
        hull.append(line); starts.append(start)
    return hull, starts


def optimize_two(bursts, capacity, floors):
    """Minimize robust pooled buffer, preserving both declared rate floors."""
    capacity = rational(capacity); floors = list(map(rational, floors))
    if len(floors) != 2 or any(x < 0 for x in floors) or sum(floors) > capacity:
        raise ValueError('two feasible nonnegative floors required')
    validate(bursts, floors)
    lo, hi = floors[0], capacity-floors[1]
    if not bursts:
        x=lo
        cert={'rate0':str(x),'buffer':'0','mode':'empty',
              'support':[{'line':{'kind':'empty-zero-sentinel','slope':'0',
                                  'intercept':'0','time':0,'s0':0,'s1':0},
                          'weight':'1'}]}
        verify_two(bursts,capacity,floors,cert)
        return {'rates':[x,capacity-x],'pool':F(0),'certificate':cert,
                'candidate_lines':0,'hull_lines':0}
    lines = pool_lines(bursts, capacity)
    hull, starts = upper_hull(lines)
    candidates = {lo, hi} | {x for x in starts if x is not None and lo <= x <= hi}
    value, x = min((max(v.value(x) for v in hull), x) for x in candidates)
    active = [v for v in hull if v.value(x) == value]
    flat = next((v for v in active if v.slope == 0), None)
    if flat:
        support = [(flat, F(1))]; mode = 'flat'
    elif x == lo and any(v.slope >= 0 for v in active):
        support = [(next(v for v in active if v.slope >= 0), F(1))]; mode = 'left'
    elif x == hi and any(v.slope <= 0 for v in active):
        support = [(next(v for v in active if v.slope <= 0), F(1))]; mode = 'right'
    elif lo == hi:
        support = [(active[0], F(1))]; mode = 'fixed'
    else:
        a = next(v for v in active if v.slope < 0)
        b = next(v for v in active if v.slope > 0)
        support = [(a, b.slope/(b.slope-a.slope)),
                   (b, -a.slope/(b.slope-a.slope))]; mode = 'interior'
    cert = {'rate0': str(x), 'buffer': str(value), 'mode': mode,
            'support': [dict(line=v.record(), weight=str(w)) for v, w in support]}
    verify_two(bursts, capacity, floors, cert)
    return {'rates': [x, capacity-x], 'pool': value, 'certificate': cert,
            'candidate_lines': len(lines), 'hull_lines': len(hull)}


def verify_two(bursts, capacity, floors, cert):
    """Check feasibility and a one/two-line global lower-bound certificate.

    This does NOT invoke optimize_two, upper_hull, or pool_lines. Each supplied
    line is reconstructed directly from its two workload intervals.
    """
    C = rational(capacity); floors = list(map(rational, floors))
    if len(floors) != 2 or any(v < 0 for v in floors) or sum(floors) > C:
        raise ValueError('invalid capacity or floors')
    validate(bursts, floors)
    x, B = rational(cert['rate0']), rational(cert['buffer'])
    lo, hi = floors[0], C-floors[1]
    if not lo <= x <= hi or B < 0:
        raise ValueError('infeasible rates or budget')
    if shadow_reference(bursts, [x, C-x])['pool'] > B:
        raise ValueError('claimed upper bound too small')
    support = cert['support']
    if not bursts:
        if B != 0 or cert.get('mode') != 'empty' or len(support) != 1:
            raise ValueError('empty traffic requires the explicit zero certificate')
        entry=support[0];record=entry.get('line',{})
        expected={'kind':'empty-zero-sentinel','slope':'0','intercept':'0',
                  'time':0,'s0':0,'s1':0}
        if record != expected or rational(entry.get('weight')) != 1:
            raise ValueError('invalid empty zero sentinel')
        return True
    if not 1 <= len(support) <= 2:
        raise ValueError('one or two support lines required')
    sw = F(0); slope = F(0); intercept = F(0)
    observations = {b.lower for b in bursts} or {0}
    for entry in support:
        record = entry['line']; weight = rational(entry['weight'])
        t, s0, s1 = (record[k] for k in ('time', 's0', 's1'))
        if any(type(v) is not int for v in (t, s0, s1)) or t not in observations:
            raise ValueError('invalid support observation')
        amounts = []
        for i, s in enumerate((s0, s1)):
            eligible = [b for b in bursts if b.tenant == i and b.lower <= t]
            allowed = {t} | {b.upper for b in eligible if b.upper <= t}
            if s not in allowed:
                raise ValueError('invalid interval start')
            amounts.append(sum(b.size for b in eligible if b.upper >= s))
        a = F(s0-s1); b = F(sum(amounts))-C*(t-s1)
        if rational(record['slope']) != a or rational(record['intercept']) != b:
            raise ValueError('support line inconsistent with workload')
        if weight < 0 or a*x+b != B:
            raise ValueError('non-supporting line or negative weight')
        sw += weight; slope += weight*a; intercept += weight*b
    if sw != 1:
        raise ValueError('support weights do not sum to one')
    # A convex combination of support cuts is a global lower bound.
    if lo == hi:
        pass
    elif x == lo:
        if slope < 0: raise ValueError('left-bound lower bound has wrong slope')
    elif x == hi:
        if slope > 0: raise ValueError('right-bound lower bound has wrong slope')
    elif slope != 0:
        raise ValueError('interior lower bound is not stationary')
    mode = cert.get('mode')
    valid_mode = ((mode == 'flat' and slope == 0) or
                  (mode == 'left' and x == lo and slope >= 0) or
                  (mode == 'right' and x == hi and slope <= 0) or
                  (mode == 'fixed' and lo == hi) or
                  (mode == 'interior' and lo < x < hi and slope == 0))
    if not valid_mode:
        raise ValueError('inconsistent certificate mode')
    if slope*x+intercept != B:
        raise ValueError('lower bound does not match claimed optimum')
    return True
