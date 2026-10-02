"""Exact finite affine-envelope minimization and independent KKT checking.

Problem
-------
    minimize z
    subject to a_k + b_k^T x <= z       for every affine piece k
               lower_i <= x_i <= upper_i
               sum_i x_i = capacity.

All input and output values are exact ``Fraction`` objects.  The solver is an
exhaustive vertex oracle intended for small differential-validation instances;
it is not the production implementation.  The checker never trusts a solver
status: it recomputes primal feasibility, complementary slackness, stationarity,
multiplier signs, and primal/dual objective equality from the serialized data.
"""
from __future__ import annotations
from dataclasses import dataclass
from fractions import Fraction
from itertools import combinations
from typing import Iterable, Optional, Sequence, Tuple

from .linear_exact import dot, q, solve_square


@dataclass(frozen=True)
class AffinePiece:
    intercept: Fraction
    slope: Tuple[Fraction, ...]
    name: str = ""

    @staticmethod
    def make(intercept, slope: Iterable, name: str = "") -> "AffinePiece":
        return AffinePiece(q(intercept), tuple(q(x) for x in slope), name)


@dataclass(frozen=True)
class MinimaxCertificate:
    rates: Tuple[Fraction, ...]
    value: Fraction
    piece_multipliers: Tuple[Fraction, ...]
    lower_multipliers: Tuple[Fraction, ...]
    upper_multipliers: Tuple[Fraction, ...]
    equality_multiplier: Fraction


@dataclass(frozen=True)
class _Constraint:
    # row dot (x,z) == rhs when active; inequality row dot (x,z) <= rhs.
    row: Tuple[Fraction, ...]
    rhs: Fraction
    kind: str
    index: int


def _constraints(pieces, lower, upper):
    n = len(lower)
    out = []
    for k, p in enumerate(pieces):
        out.append(_Constraint(tuple(p.slope) + (Fraction(-1),), -p.intercept, "piece", k))
    for i in range(n):
        row = [Fraction(0)] * (n + 1); row[i] = -1
        out.append(_Constraint(tuple(row), -lower[i], "lower", i))
        row = [Fraction(0)] * (n + 1); row[i] = 1
        out.append(_Constraint(tuple(row), upper[i], "upper", i))
    return out


def _validate_inputs(pieces, lower, upper, capacity):
    if not pieces:
        raise ValueError("at least one affine piece is required")
    n = len(lower)
    if n == 0 or len(upper) != n:
        raise ValueError("invalid bounds")
    if any(len(p.slope) != n for p in pieces):
        raise ValueError("piece dimension mismatch")
    if any(lo > hi for lo, hi in zip(lower, upper)):
        raise ValueError("lower bound exceeds upper bound")
    if sum(lower, Fraction(0)) > capacity or sum(upper, Fraction(0)) < capacity:
        raise ValueError("capacity equality is infeasible")


def _enumerate_primal_vertices(pieces, lower, upper, capacity):
    """Yield feasible exact vertices (x,z)."""
    n = len(lower)
    cons = _constraints(pieces, lower, upper)
    equality = tuple([Fraction(1)] * n + [Fraction(0)])
    # n active inequalities plus the one equality determine n+1 variables.
    for ids in combinations(range(len(cons)), n):
        rows = [equality] + [cons[i].row for i in ids]
        rhs = [capacity] + [cons[i].rhs for i in ids]
        sol = solve_square(rows, rhs)
        if sol is None:
            continue
        if all(dot(c.row, sol) <= c.rhs for c in cons):
            yield sol


def _active_sets(pieces, lower, upper, rates, value):
    pa = [k for k,p in enumerate(pieces) if p.intercept + dot(p.slope, rates) == value]
    la = [i for i,(x,lo) in enumerate(zip(rates, lower)) if x == lo]
    ua = [i for i,(x,hi) in enumerate(zip(rates, upper)) if x == hi]
    return pa, la, ua


def _find_kkt_multipliers(pieces, lower, upper, rates, value):
    """Find a sparse exact KKT representation by Caratheodory-style enumeration."""
    n = len(rates)
    pa, la, ua = _active_sets(pieces, lower, upper, rates, value)
    labels = ([('p',k) for k in pa] + [('l',i) for i in la] + [('u',i) for i in ua])
    # Unknowns are selected nonzero multipliers followed by free nu.
    # Equations: n x-stationarity equations and sum(lambda)=1.
    for size in range(1, min(n + 1, len(labels)) + 1):
        for chosen in combinations(labels, size):
            cols = []
            for typ, idx in chosen:
                if typ == 'p':
                    # coefficient in x stationarity; 1 in z stationarity sum
                    cols.append(tuple(pieces[idx].slope) + (Fraction(1),))
                elif typ == 'l':
                    v = [Fraction(0)] * n; v[idx] = -1
                    cols.append(tuple(v) + (Fraction(0),))
                else:
                    v = [Fraction(0)] * n; v[idx] = 1
                    cols.append(tuple(v) + (Fraction(0),))
            # equality multiplier nu has coefficient +1 in every x equation, 0 last.
            cols.append(tuple([Fraction(1)] * n + [Fraction(0)]))
            # Solve possibly over/under-determined by selecting a square full system,
            # then verify all equations.  Set has size <= n+1, unknown count size+1.
            m = size + 1
            equation_rows = list(range(n + 1))
            for eqids in combinations(equation_rows, m):
                A = [[cols[c][r] for c in range(m)] for r in eqids]
                b = [Fraction(0) if r < n else Fraction(1) for r in eqids]
                sol = solve_square(A, b)
                if sol is None:
                    continue
                if any(sum(cols[c][r] * sol[c] for c in range(m)) != (0 if r < n else 1)
                       for r in equation_rows):
                    continue
                if any(sol[j] < 0 for j in range(size)):
                    continue
                lm = [Fraction(0)] * len(pieces)
                lowm = [Fraction(0)] * n
                upm = [Fraction(0)] * n
                for (typ, idx), val in zip(chosen, sol[:-1]):
                    if typ == 'p': lm[idx] = val
                    elif typ == 'l': lowm[idx] = val
                    else: upm[idx] = val
                return tuple(lm), tuple(lowm), tuple(upm), sol[-1]
    return None


def solve_exact_minimax(
    pieces: Sequence[AffinePiece],
    lower: Sequence[Fraction],
    upper: Sequence[Fraction],
    capacity: Fraction,
) -> MinimaxCertificate:
    pieces = tuple(pieces)
    lower = tuple(q(x) for x in lower); upper = tuple(q(x) for x in upper); capacity = q(capacity)
    _validate_inputs(pieces, lower, upper, capacity)
    vertices = list(_enumerate_primal_vertices(pieces, lower, upper, capacity))
    if not vertices:
        raise RuntimeError("feasible polytope unexpectedly has no enumerated vertex")
    best = min(vertices, key=lambda v: (v[-1], v[:-1]))
    rates, value = tuple(best[:-1]), best[-1]
    mult = _find_kkt_multipliers(pieces, lower, upper, rates, value)
    if mult is None:
        raise RuntimeError("failed to reconstruct an exact KKT certificate")
    cert = MinimaxCertificate(rates, value, *mult)
    ok, errors = verify_minimax_certificate(pieces, lower, upper, capacity, cert)
    if not ok:
        raise RuntimeError("internal certificate rejection: " + "; ".join(errors))
    return cert


def verify_minimax_certificate(pieces, lower, upper, capacity, cert: MinimaxCertificate):
    pieces = tuple(pieces)
    lower = tuple(q(x) for x in lower); upper = tuple(q(x) for x in upper); capacity = q(capacity)
    errors = []
    n = len(lower)
    if len(cert.rates) != n: errors.append("rate dimension mismatch")
    if len(cert.piece_multipliers) != len(pieces): errors.append("piece multiplier dimension mismatch")
    if len(cert.lower_multipliers) != n or len(cert.upper_multipliers) != n:
        errors.append("bound multiplier dimension mismatch")
    if errors: return False, tuple(errors)
    x = tuple(map(q, cert.rates)); z = q(cert.value)
    lm = tuple(map(q, cert.piece_multipliers)); lo = tuple(map(q, cert.lower_multipliers)); up = tuple(map(q, cert.upper_multipliers)); nu = q(cert.equality_multiplier)
    if sum(x, Fraction(0)) != capacity: errors.append("capacity equality violated")
    for i,(xi,a,b) in enumerate(zip(x, lower, upper)):
        if xi < a or xi > b: errors.append(f"bound {i} violated")
    vals = [p.intercept + dot(p.slope, x) for p in pieces]
    for k,v in enumerate(vals):
        if v > z: errors.append(f"piece {k} exceeds value")
    if any(v < 0 for v in lm+lo+up): errors.append("negative inequality multiplier")
    if sum(lm, Fraction(0)) != 1: errors.append("z stationarity violated")
    for i in range(n):
        stat = sum(lm[k] * pieces[k].slope[i] for k in range(len(pieces))) - lo[i] + up[i] + nu
        if stat != 0: errors.append(f"x stationarity {i} violated")
    for k in range(len(pieces)):
        if lm[k] * (z - vals[k]) != 0: errors.append(f"piece complementarity {k} violated")
    for i in range(n):
        if lo[i] * (x[i] - lower[i]) != 0: errors.append(f"lower complementarity {i} violated")
        if up[i] * (upper[i] - x[i]) != 0: errors.append(f"upper complementarity {i} violated")
    # Exact primal-dual equality follows from KKT, but an explicit recomputation
    # catches sign-convention mistakes in serialized certificates.
    dual_value = sum(lm[k] * pieces[k].intercept for k in range(len(pieces))) + sum(lo[i] * lower[i] for i in range(n)) - sum(up[i] * upper[i] for i in range(n)) - nu * capacity
    if dual_value != z: errors.append("primal/dual objective mismatch")
    return not errors, tuple(errors)
