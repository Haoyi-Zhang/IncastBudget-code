"""Exact fluid and slotted-cell queues. All experiment inputs are synthetic.

Admission is measured immediately after simultaneous arrivals, before any
positive-time fluid service or the next cell-service opportunity.
"""
from __future__ import annotations
from dataclasses import dataclass
from fractions import Fraction as F
from collections import defaultdict
import heapq
from typing import Callable, Iterable, Sequence

@dataclass(frozen=True)
class Burst:
    tenant: int
    lower: int
    upper: int
    size: int


def validate(bursts: Sequence[Burst], rates: Sequence[F]) -> None:
    if (not rates or any(type(r) is not int and not isinstance(r, F) for r in rates)
            or any(r < 0 for r in rates)):
        raise ValueError('nonempty nonnegative rate vector required')
    for b in bursts:
        if any(type(x) is not int for x in (b.tenant,b.lower,b.upper,b.size)):
            raise ValueError('burst fields must be integers, not bools or floats')
        if not 0 <= b.tenant < len(rates) or not 0 <= b.lower <= b.upper or b.size <= 0:
            raise ValueError('invalid tenant, window, or size')


def simulate(bursts: Sequence[Burst], rates: Sequence[F], releases: Sequence[int],
             record: bool = False):
    """Simple exact event-driven oracle for a single admitted arrival trace."""
    validate(bursts, rates)
    if len(releases) != len(bursts):
        raise ValueError('release length mismatch')
    events = defaultdict(lambda: [0] * len(rates))
    for b,t in zip(bursts,releases):
        if type(t) is not int or not b.lower <= t <= b.upper:
            raise ValueError('release outside declared window')
        events[t][b.tenant] += b.size
    q = [F(0) for _ in rates]
    peaks = [F(0) for _ in rates]
    peak=F(0); when=0; last=0; trace=[]
    for t,arrivals in sorted(events.items()):
        q = [max(F(0),v-r*(t-last))+a for v,r,a in zip(q,rates,arrivals)]
        peaks=[max(a,b) for a,b in zip(peaks,q)]
        if sum(q)>peak: peak=sum(q);when=t
        if record: trace.append((t,tuple(q)))
        last=t
    return {'pool':peak,'private':peaks,'time':when,'trace':trace}


def _endpoint_events(bursts: Sequence[Burst]):
    """Coalesce nonzero endpoint masses without allocating n slots per time."""
    events=defaultdict(lambda:[defaultdict(int),defaultdict(int)])
    for b in bursts:
        events[b.lower][0][b.tenant]+=b.size
        events[b.upper][1][b.tenant]+=b.size
    return events


def shadow_reference(bursts: Sequence[Burst], rates: Sequence[F], record: bool = False,
                     row_sink: Callable[[tuple], None] | None = None):
    """Transparent O(nm) recurrence with sparse events and O(n+m) work space.

    ``record=True`` retains every full q/p row and therefore intentionally uses
    Theta(nm) output space.  ``row_sink`` emits the same rows one at a time while
    keeping them out of memory.  The two output modes may be combined, although
    the command-line interface uses streaming alone for large diagnostics.
    """
    validate(bursts,rates)
    n=len(rates);events=_endpoint_events(bursts)
    q=[F(0)]*n;p=[0]*n;peaks=[F(0)]*n;peak=F(0);when=0;last=0;trace=[]
    row_count=0
    for t,(starts,ends) in sorted(events.items()):
        total=F(0)
        for i in range(n):
            d=ends.get(i,0)
            q[i]=max(F(0),q[i]-rates[i]*(t-last))+d
            p[i]+=starts.get(i,0)-d
            value=q[i]+p[i]
            if value>peaks[i]:peaks[i]=value
            total+=value
        row=(t,tuple(q),tuple(p),total)
        if record:trace.append(row)
        if row_sink is not None:row_sink(row)
        row_count+=1
        if total>peak:peak=total;when=t
        last=t
    sparse_entries=sum(len(starts)+len(ends) for starts,ends in events.values())
    payload_per_row=2*n+2
    event_times=len(events)
    # Abstract entry accounting: three n-vectors, sparse mass entries, event-map
    # keys, and the sorted event index. Python object/header overhead is not
    # claimed to be represented by this language-independent count.
    working_entries=3*n+sparse_entries+2*event_times
    return {'pool':peak,'private':peaks,'time':when,'trace':trace,
            'row_count':row_count,
            'storage':{'event_times':event_times,
                       'sparse_event_entries':sparse_entries,
                       'state_vector_entries':3*n,
                       'event_index_entries':2*event_times,
                       'working_entry_upper_bound':working_entries,
                       'entry_accounting':'state vectors + sparse masses + event-map keys + sorted index',
                       'emitted_row_payload_entries':row_count*payload_per_row if (record or row_sink is not None) else 0,
                       'materialized_row_payload_entries':len(trace)*payload_per_row}}


def shadow_fast(bursts: Sequence[Burst], rates: Sequence[F]):
    """O((m+n) log(m+n)) exact sweep; lazy per-tenant empty-time heap.

    The implementation never interprets the envelope as one realizable trace.
    An attaining trace must be separately constructed for its selected time.
    """
    validate(bursts,rates)
    n=len(rates);events=_endpoint_events(bursts)
    q=[F(0)]*n;last_i=[F(0)]*n;generation=[0]*n;p=[0]*n;active=[False]*n
    total_q=F(0);total_p=0;drain=F(0);clock=F(0);heap=[]
    peak=F(0);when=0;peaks=[F(0)]*n
    for t,(starts,ends) in sorted(events.items()):
        while heap and heap[0][0] <= t:
            at,ver,i=heapq.heappop(heap)
            if ver != generation[i] or not active[i]: continue
            total_q-=drain*(at-clock);clock=at
            active[i]=False;drain-=rates[i];q[i]=F(0);last_i[i]=at
        total_q-=drain*(t-clock);clock=F(t)
        for i in starts.keys()|ends.keys():
            q[i]=max(F(0),q[i]-rates[i]*(t-last_i[i]));last_i[i]=F(t)
            a=starts.get(i,0);d=ends.get(i,0)
            p[i]+=a-d;total_p+=a-d
            if d:
                q[i]+=d;total_q+=d;generation[i]+=1
                if not active[i] and rates[i]>0:
                    active[i]=True;drain+=rates[i]
                if rates[i]>0:
                    heapq.heappush(heap,(F(t)+q[i]/rates[i],generation[i],i))
            peaks[i]=max(peaks[i],q[i]+p[i])
        if total_q+total_p > peak:peak=total_q+total_p;when=t
    return {'pool':peak,'private':peaks,'time':when}


def witness(bursts: Sequence[Burst], time: int) -> list[int]:
    """Clip every already eligible burst to time; leave future bursts at upper."""
    return [min(b.upper,time) if b.lower<=time else b.upper for b in bursts]


def cell_simulate(bursts: Sequence[Burst], releases: Sequence[int], calendar: Sequence[int], n: int):
    """One cell per slot, assigned to the indicated tenant; -1 is idle.

    calendar repeats. Each burst contains an integer number of equal-size cells.
    A slot t is served after the peak is measured at integer t.
    """
    validate(bursts,[F(0)]*n)
    if not calendar or any(type(i) is not int or not -1<=i<n for i in calendar):
        raise ValueError('invalid calendar')
    if len(releases)!=len(bursts):raise ValueError('release length mismatch')
    events=defaultdict(lambda:[0]*n)
    for b,t in zip(bursts,releases):
        if type(t) is not int or not b.lower<=t<=b.upper:raise ValueError('invalid release')
        events[t][b.tenant]+=b.size
    q=[0]*n;peak=0;peaks=[0]*n;when=0
    for t in range(max(releases,default=0)+1):
        q=[x+a for x,a in zip(q,events[t])]
        peaks=[max(x,y) for x,y in zip(peaks,q)]
        if sum(q)>peak:peak=sum(q);when=t
        i=calendar[t%len(calendar)]
        if i>=0:q[i]=max(0,q[i]-1)
    return {'pool':peak,'private':peaks,'time':when}


def cell_shadow(bursts: Sequence[Burst], calendar: Sequence[int], n: int):
    validate(bursts,[F(0)]*n)
    if not calendar or any(type(i) is not int or not -1<=i<n for i in calendar):raise ValueError('invalid calendar')
    starts=defaultdict(lambda:[0]*n);ends=defaultdict(lambda:[0]*n)
    for b in bursts:starts[b.lower][b.tenant]+=b.size;ends[b.upper][b.tenant]+=b.size
    q=[0]*n;p=[0]*n;peaks=[0]*n;peak=0;when=0
    for t in range(max((b.upper for b in bursts),default=0)+1):
        q=[x+d for x,d in zip(q,ends[t])]
        p=[x+a-d for x,a,d in zip(p,starts[t],ends[t])]
        f=[x+y for x,y in zip(q,p)]
        peaks=[max(x,y) for x,y in zip(peaks,f)]
        if sum(f)>peak:peak=sum(f);when=t
        i=calendar[t%len(calendar)]
        if i>=0:q[i]=max(0,q[i]-1)
    return {'pool':peak,'private':peaks,'time':when}


def cell_shadow_events(bursts: Sequence[Burst], calendar: Sequence[int], n: int):
    """Exact endpoint sweep with prefix-counted cell opportunities; no tick loop."""
    validate(bursts, [F(0)] * n)
    if not calendar or any(type(i) is not int or not -1 <= i < n for i in calendar):
        raise ValueError('invalid calendar')
    frame = len(calendar)
    prefixes = [[0] for _ in range(n)]
    for owner in calendar:
        for i in range(n): prefixes[i].append(prefixes[i][-1] + (owner == i))
    def service(i, t):
        k, rem = divmod(t, frame)
        return k * prefixes[i][-1] + prefixes[i][rem]
    starts = defaultdict(lambda: [0] * n); ends = defaultdict(lambda: [0] * n)
    for b in bursts:
        starts[b.lower][b.tenant] += b.size; ends[b.upper][b.tenant] += b.size
    q = [0] * n; p = [0] * n; peaks = [0] * n; peak = 0; when = 0; last = 0
    for t in sorted(starts.keys() | ends.keys()):
        q = [max(0, q[i] - (service(i, t)-service(i, last))) + ends[t][i] for i in range(n)]
        p = [v+a-d for v, a, d in zip(p, starts[t], ends[t])]
        f = [v+a for v, a in zip(q, p)]
        peaks = [max(a, b) for a, b in zip(peaks, f)]
        if sum(f) > peak: peak = sum(f); when = t
        last = t
    return {'pool': peak, 'private': peaks, 'time': when}
