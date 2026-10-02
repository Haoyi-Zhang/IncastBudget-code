"""Independent finite-domain max-sum variable elimination with witness recovery."""
from __future__ import annotations
from dataclasses import dataclass
from fractions import Fraction
from itertools import product
from typing import Dict, Hashable, Iterable, Mapping, MutableMapping, Sequence, Tuple

Value = Hashable
Var = Hashable
Assignment = Dict[Var, Value]


@dataclass(frozen=True)
class Factor:
    scope: Tuple[Var, ...]
    table: Mapping[Tuple[Value, ...], Fraction]
    name: str = ""

    def evaluate(self, assignment: Mapping[Var, Value]) -> Fraction:
        key = tuple(assignment[v] for v in self.scope)
        if key not in self.table:
            raise ValueError(f"factor {self.name or self.scope} has no row {key}")
        return Fraction(self.table[key])


@dataclass(frozen=True)
class VETrace:
    order: Tuple[Var, ...]
    induced_width: int
    max_table_entries: int
    objective: Fraction
    assignment: Mapping[Var, Value]


def _check(domains, factors):
    if not domains or any(not tuple(d) for d in domains.values()):
        raise ValueError("each variable needs a nonempty finite domain")
    known = set(domains)
    for f in factors:
        if len(set(f.scope)) != len(f.scope) or any(v not in known for v in f.scope):
            raise ValueError("invalid factor scope")
        expected = set(product(*(domains[v] for v in f.scope)))
        if set(f.table) != expected:
            raise ValueError("factor table is incomplete or contains invalid rows")


def score(factors: Sequence[Factor], assignment: Mapping[Var, Value]) -> Fraction:
    return sum((f.evaluate(assignment) for f in factors), Fraction(0))


def verify_assignment(domains, factors, assignment, claimed_value):
    try:
        _check(domains, factors)
        if set(assignment) != set(domains): return False
        if any(assignment[v] not in domains[v] for v in domains): return False
        return score(factors, assignment) == Fraction(claimed_value)
    except (KeyError, ValueError, TypeError, ZeroDivisionError):
        return False


def brute_force_max(domains, factors):
    _check(domains, factors)
    vars_ = tuple(domains)
    best = None
    for values in product(*(domains[v] for v in vars_)):
        a = dict(zip(vars_, values)); val = score(factors, a)
        key = (val, tuple(repr(a[v]) for v in vars_))
        if best is None or key > best[0]: best = (key, val, a)
    return best[1], best[2]


def _factor_from_function(scope, domains, fn, name=""):
    table = {}
    for vals in product(*(domains[v] for v in scope)):
        table[vals] = Fraction(fn(dict(zip(scope, vals))))
    return Factor(tuple(scope), table, name)


def variable_elimination_max(domains, factors, order):
    """Exact max-sum elimination; deterministic tie-breaking and witness recovery."""
    _check(domains, factors)
    order = tuple(order)
    if set(order) != set(domains) or len(order) != len(domains):
        raise ValueError("order must contain every variable exactly once")
    current = list(factors)
    back = []
    width = 0; max_entries = max((len(f.table) for f in factors), default=1)
    for var in order:
        bucket = [f for f in current if var in f.scope]
        current = [f for f in current if var not in f.scope]
        union = []
        for f in bucket:
            for v in f.scope:
                if v != var and v not in union: union.append(v)
        width = max(width, len(union))
        arg_table = {}
        out_table = {}
        for vals in product(*(domains[v] for v in union)):
            partial = dict(zip(union, vals)); candidates = []
            for x in domains[var]:
                a = dict(partial); a[var] = x
                val = sum((f.evaluate(a) for f in bucket), Fraction(0))
                candidates.append((val, repr(x), x))
            val, _, arg = max(candidates)
            out_table[vals] = val; arg_table[vals] = arg
        back.append((var, tuple(union), arg_table))
        nf = Factor(tuple(union), out_table, f"elim({var!r})")
        current.append(nf); max_entries = max(max_entries, len(out_table))
    if any(f.scope for f in current):
        raise RuntimeError("elimination left nonconstant factor")
    optimum = sum((next(iter(f.table.values())) for f in current), Fraction(0))
    assignment = {}
    for var, scope, arg_table in reversed(back):
        key = tuple(assignment[v] for v in scope)
        assignment[var] = arg_table[key]
    if not verify_assignment(domains, factors, assignment, optimum):
        raise RuntimeError("reconstructed witness does not attain optimum")
    return VETrace(order, width, max_entries, optimum, assignment)
