"""Small exact-linear-algebra helpers based only on fractions.Fraction."""
from __future__ import annotations
from fractions import Fraction
from typing import Iterable, List, Optional, Sequence, Tuple

Q = Fraction


def q(x: int | str | Fraction) -> Fraction:
    return x if isinstance(x, Fraction) else Fraction(x)


def dot(a: Sequence[Fraction], b: Sequence[Fraction]) -> Fraction:
    if len(a) != len(b):
        raise ValueError("dimension mismatch")
    return sum((x * y for x, y in zip(a, b)), Fraction(0))


def solve_square(a: Sequence[Sequence[Fraction]], b: Sequence[Fraction]) -> Optional[Tuple[Fraction, ...]]:
    """Solve A x=b by exact Gauss-Jordan elimination; return None if singular."""
    n = len(a)
    if len(b) != n or any(len(row) != n for row in a):
        raise ValueError("solve_square requires a square system")
    aug: List[List[Fraction]] = [list(map(q, row)) + [q(rhs)] for row, rhs in zip(a, b)]
    for col in range(n):
        pivot = next((r for r in range(col, n) if aug[r][col] != 0), None)
        if pivot is None:
            return None
        aug[col], aug[pivot] = aug[pivot], aug[col]
        piv = aug[col][col]
        aug[col] = [v / piv for v in aug[col]]
        for r in range(n):
            if r == col:
                continue
            mul = aug[r][col]
            if mul:
                aug[r] = [x - mul * y for x, y in zip(aug[r], aug[col])]
    return tuple(aug[i][-1] for i in range(n))


def rank(a: Sequence[Sequence[Fraction]]) -> int:
    m = [list(map(q, row)) for row in a]
    if not m:
        return 0
    nr, nc = len(m), len(m[0])
    r = 0
    for c in range(nc):
        pivot = next((i for i in range(r, nr) if m[i][c] != 0), None)
        if pivot is None:
            continue
        m[r], m[pivot] = m[pivot], m[r]
        piv = m[r][c]
        m[r] = [v / piv for v in m[r]]
        for i in range(nr):
            if i != r and m[i][c]:
                mul = m[i][c]
                m[i] = [x - mul * y for x, y in zip(m[i], m[r])]
        r += 1
        if r == nr:
            break
    return r
