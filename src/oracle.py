"""Bounded exhaustive releases and an independent busy-interval formula."""
from itertools import product
from fractions import Fraction as F
from queues import Burst,simulate,cell_simulate,validate


def enumerate_releases(bursts,rates,limit=200000,calendar=None):
    validate(bursts,rates)
    count=1
    for b in bursts:count*=b.upper-b.lower+1
    if count>limit:raise ValueError('oracle release-product cap exceeded')
    peak=F(0);private=[F(0)]*len(rates);best=[]
    for times in product(*(range(b.lower,b.upper+1) for b in bursts)):
        out=simulate(bursts,rates,times) if calendar is None else cell_simulate(bursts,times,calendar,len(rates))
        if out['pool']>peak:peak=out['pool'];best=list(times)
        private=[max(x,y) for x,y in zip(private,out['private'])]
    return {'pool':peak,'private':private,'count':count,'releases':best}


def interval_bound(bursts,rates):
    """O(m^3) direct interval-overlap maximization, no shadow recurrence."""
    validate(bursts,rates)
    peak=F(0);private=[F(0)]*len(rates);when=0
    for t in sorted({b.lower for b in bursts}):
        vals=[]
        for i,r in enumerate(rates):
            eligible=[b for b in bursts if b.tenant==i and b.lower<=t]
            cuts={t}|{b.upper for b in eligible if b.upper<=t}
            val=max([F(0)]+[sum(b.size for b in eligible if b.upper>=s)-r*(t-s) for s in cuts])
            vals.append(val);private[i]=max(private[i],val)
        if sum(vals)>peak:peak=sum(vals);when=t
    return {'pool':peak,'private':private,'time':when}


def vertex_allocation_oracle(bursts, capacity, floors, limit=200000):
    """Enumerate actual integer releases, then all rate-plane intersections.

    No shadow or production line generator is called. Two tenants only; this is
    an independent finite model checker, not a scalable allocation algorithm.
    """
    C = F(capacity); lo = F(floors[0]); hi = C-F(floors[1])
    validate(bursts, [F(0), F(0)])
    count = 1
    for b in bursts: count *= b.upper-b.lower+1
    if count > limit: raise ValueError('release-product cap exceeded')
    if not 0 <= lo <= hi <= C: raise ValueError('invalid feasible interval')
    coefficients = {(F(0), F(0))}
    for times in product(*(range(b.lower, b.upper+1) for b in bursts)):
        for t in sorted(set(times)):
            arms = []
            for i in range(2):
                events = [(u, b.size) for b, u in zip(bursts, times) if b.tenant == i and u <= t]
                options = [(F(0), F(0))]  # amount, duration
                for s in set(u for u, _ in events):
                    options.append((F(sum(v for u, v in events if u >= s)), F(t-s)))
                arms.append(options)
            for a0, d0 in arms[0]:
                for a1, d1 in arms[1]:
                    coefficients.add((d1-d0, a0+a1-C*d1))
    # Dominated parallel lines can never be the maximum.
    maximal = {}
    for slope, intercept in coefficients:
        maximal[slope] = max(intercept, maximal.get(slope, intercept))
    lines = list(maximal.items()); candidates = {lo, hi}
    for j, (a, b) in enumerate(lines):
        for c, d in lines[j+1:]:
            x = (d-b)/(a-c)
            if lo <= x <= hi: candidates.add(x)
    value, x = min((max(a*x+b for a, b in lines), x) for x in candidates)
    return {'pool': value, 'rate0': x, 'traces': count,
            'lines': len(coefficients), 'vertices': len(candidates)}
