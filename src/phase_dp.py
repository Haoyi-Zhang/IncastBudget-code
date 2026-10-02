"""Exact max-sum elimination for binary shared-phase queue schedules.

Each phase group chooses one bit. A grouped job with integer ``base`` arrives at
``base + offset * bit``; fixed jobs have ``group=None``. Tenant queues receive
arrival-independent constant service rates and unused service is discarded.
The robust pooled peak is the maximum, over assignments and arrival epochs, of
the sum of tenant occupancies.  This module is exact, but exponential in the
induced width of the supplied phase-variable elimination order.
"""
from __future__ import annotations

from fractions import Fraction as F
from itertools import product
from typing import Dict, Iterable, List, Sequence, Tuple


def _fraction(value):
    if isinstance(value, bool) or isinstance(value, float):
        raise ValueError('exact integer, fraction, or decimal string required')
    try:
        out = value if isinstance(value, F) else F(value)
    except (TypeError, ValueError, ZeroDivisionError) as exc:
        raise ValueError('invalid exact numeric value') from exc
    return out


def validate_phase_instance(instance):
    """Validate the explicit finite binary-phase input used by the checker."""
    if not isinstance(instance, dict):
        raise ValueError('phase instance must be a mapping')
    groups = instance.get('groups')
    tenants = instance.get('tenants')
    if type(groups) is not int or groups < 0:
        raise ValueError('nonnegative integer group count required')
    if type(tenants) is not int or tenants < 1:
        raise ValueError('positive integer tenant count required')
    offset = _fraction(instance.get('offset'))
    if offset < 0:
        raise ValueError('nonnegative phase offset required')
    rates = instance.get('rates')
    if not isinstance(rates, list) or len(rates) != tenants:
        raise ValueError('one service rate per tenant required')
    parsed_rates = [_fraction(v) for v in rates]
    if any(v < 0 for v in parsed_rates):
        raise ValueError('nonnegative service rates required')
    jobs = instance.get('jobs')
    if not isinstance(jobs, list):
        raise ValueError('jobs must be an explicit list')
    parsed_jobs = []
    for job in jobs:
        if not isinstance(job, dict):
            raise ValueError('each job must be a mapping')
        tenant = job.get('tenant')
        group = job.get('group')
        if type(tenant) is not int or not 0 <= tenant < tenants:
            raise ValueError('invalid tenant index')
        if group is not None and (type(group) is not int or not 0 <= group < groups):
            raise ValueError('invalid phase group')
        base = _fraction(job.get('base'))
        size = _fraction(job.get('size'))
        if base < 0 or size <= 0:
            raise ValueError('nonnegative base and positive size required')
        parsed_jobs.append((tenant, group, base, size))
    return groups, tenants, offset, parsed_rates, parsed_jobs


def candidate_times(instance):
    """All epochs at which a robust pooled maximum can first be attained."""
    groups, tenants, offset, rates, jobs = validate_phase_instance(instance)
    del groups, tenants, rates
    times = set()
    for _tenant, group, base, _size in jobs:
        times.add(base)
        if group is not None:
            times.add(base + offset)
    return tuple(sorted(times)) if times else (F(0),)


def interaction_graph(instance):
    """Primal graph: groups are adjacent when one tenant factor contains both."""
    groups, tenants, offset, rates, jobs = validate_phase_instance(instance)
    del offset, rates
    scopes = [set() for _ in range(tenants)]
    for tenant, group, _base, _size in jobs:
        if group is not None:
            scopes[tenant].add(group)
    graph = {v: set() for v in range(groups)}
    for scope in scopes:
        for u in scope:
            graph[u].update(scope - {u})
    return graph


def induced_width(instance, order: Sequence[int]):
    """Return induced width for ``order`` on the phase interaction graph."""
    groups, _tenants, _offset, _rates, _jobs = validate_phase_instance(instance)
    if (not isinstance(order, (list, tuple)) or len(order) != groups
            or set(order) != set(range(groups))
            or any(type(v) is not int for v in order)):
        raise ValueError('elimination order must be a permutation of all groups')
    graph = {v: set(nbrs) for v, nbrs in interaction_graph(instance).items()}
    width = 0
    for v in order:
        nbrs = graph[v]
        width = max(width, len(nbrs))
        for u in nbrs:
            graph[u].update(nbrs - {u})
            graph[u].discard(v)
        del graph[v]
    return width


def min_fill_order(instance):
    """Deterministic min-fill order; exactness does not depend on this heuristic."""
    graph = {v: set(nbrs) for v, nbrs in interaction_graph(instance).items()}
    order = []
    while graph:
        def score(v):
            nbrs = sorted(graph[v])
            missing = sum(1 for i, u in enumerate(nbrs)
                          for w in nbrs[i + 1:] if w not in graph[u])
            return missing, len(nbrs), v
        v = min(graph, key=score)
        nbrs = set(graph[v])
        for u in nbrs:
            graph[u].update(nbrs - {u})
            graph[u].discard(v)
        del graph[v]
        order.append(v)
    return order


def _tenant_occupancy(jobs, rate, time, assignment):
    arrivals = {}
    for group, base, size in jobs:
        at = base if group is None else base + assignment[group]
        if at <= time:
            arrivals[at] = arrivals.get(at, F(0)) + size
    q = F(0)
    last = F(0)
    for at, amount in sorted(arrivals.items()):
        q = max(F(0), q - rate * (at - last)) + amount
        last = at
    return max(F(0), q - rate * (time - last))


def factor_tables(instance, time):
    """One exact occupancy factor per tenant at a fixed observation time."""
    groups, tenants, offset, rates, jobs = validate_phase_instance(instance)
    time = _fraction(time)
    if time < 0:
        raise ValueError('nonnegative observation time required')
    by_tenant = [[] for _ in range(tenants)]
    for tenant, group, base, size in jobs:
        by_tenant[tenant].append((group, base, size))
    factors = []
    entries = 0
    for tenant in range(tenants):
        scope = tuple(sorted({group for group, _base, _size in by_tenant[tenant]
                              if group is not None}))
        table = {}
        for bits in product((0, 1), repeat=len(scope)):
            phase = {v: offset * bit for v, bit in zip(scope, bits)}
            table[bits] = _tenant_occupancy(by_tenant[tenant], rates[tenant], time, phase)
        entries += len(table)
        factors.append((scope, table))
    return factors, entries


def _lookup(factor, assignment):
    scope, table = factor
    return table[tuple(assignment[v] for v in scope)]


def max_sum(factors, order: Sequence[int]):
    """Eliminate binary variables exactly and reconstruct one maximizing witness."""
    order = tuple(order)
    if len(set(order)) != len(order) or any(type(v) is not int for v in order):
        raise ValueError('distinct integer variables required')
    work = [(tuple(scope), dict(table)) for scope, table in factors]
    policies = []
    largest_scope = max((len(scope) for scope, _table in work), default=0)
    for variable in order:
        bucket = [f for f in work if variable in f[0]]
        work = [f for f in work if variable not in f[0]]
        if not bucket:
            policies.append((variable, tuple(), {tuple(): 0}))
            continue
        union = set().union(*(scope for scope, _table in bucket))
        remaining = tuple(sorted(union - {variable}))
        largest_scope = max(largest_scope, len(union))
        out = {}
        policy = {}
        for bits in product((0, 1), repeat=len(remaining)):
            partial = dict(zip(remaining, bits))
            values = []
            for choice in (0, 1):
                assignment = dict(partial)
                assignment[variable] = choice
                values.append(sum((_lookup(f, assignment) for f in bucket), F(0)))
            choice = 0 if values[0] >= values[1] else 1
            out[bits] = values[choice]
            policy[bits] = choice
        work.append((remaining, out))
        policies.append((variable, remaining, policy))
    if any(scope for scope, _table in work):
        missing = sorted(set().union(*(set(scope) for scope, _table in work)))
        raise ValueError(f'elimination order omits variables: {missing}')
    optimum = sum((table[tuple()] for _scope, table in work), F(0))
    assignment = {}
    for variable, remaining, policy in reversed(policies):
        key = tuple(assignment[v] for v in remaining)
        assignment[variable] = policy[key]
    return optimum, [assignment[v] for v in order], largest_scope


def robust_phase_peak(instance, order: Sequence[int] | None = None):
    """Exact robust pooled peak under a supplied or deterministic min-fill order.

    Returns the optimum, one phase assignment in natural group order, a maximizing
    candidate epoch, the order's induced width, and transparent table-size counts.
    """
    groups, _tenants, _offset, _rates, _jobs = validate_phase_instance(instance)
    if order is None:
        order = min_fill_order(instance)
    else:
        order = list(order)
    width = induced_width(instance, order)
    best = F(-1)
    best_bits = [0] * groups
    best_time = F(0)
    factor_entries = 0
    largest_scope = 0
    for time in candidate_times(instance):
        factors, entries = factor_tables(instance, time)
        value, ordered_bits, scope_size = max_sum(factors, order)
        factor_entries += entries
        natural = [0] * groups
        for variable, bit in zip(order, ordered_bits):
            natural[variable] = bit
        if value > best:
            best, best_bits, best_time = value, natural, time
        largest_scope = max(largest_scope, scope_size)
    return {
        'pool': best,
        'phases': best_bits,
        'time': best_time,
        'candidate_times': len(candidate_times(instance)),
        'factor_entries': factor_entries,
        'order': order,
        'induced_width': width,
        'largest_elimination_scope': largest_scope,
    }
