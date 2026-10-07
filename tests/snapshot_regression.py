"""Portable finite row-output conformance; independent busy-interval reference.

MIT, see ../LICENSE. No historical implementation, private path or driver.
"""
from copy import deepcopy
from fractions import Fraction as F
from itertools import product
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
import queues
import allocation


def domain():
    windows = ((0, 0), (0, 1), (0, 2), (1, 1), (1, 2), (2, 2))
    atoms = [(i, lo, hi, b) for i in (0, 1) for lo, hi in windows for b in (1, 2)]
    rates = ((0, 0), (1, 1), (F(1, 2), F(2, 3)), (F(7, 3), 0))
    for rr in rates:
        yield [], rr
        for a in atoms:
            yield [a], rr
        for a, b in product(atoms, repeat=2):
            yield [a, b], rr
    yield [(0, 0, 0, 4), (0, 3, 4, 3), (1, 1, 2, 3), (1, 4, 5, 4)], (1, 1)
    for n in (8, 32, 128):
        yield [(i, 2*i, 2*i, 1) for i in range(n)], (F(1),)*n
    yield [(j % 3, j, j+1, j % 5+1) for j in range(30)], (F(3, 7), F(5, 11), 0)


def reference_rows(atoms, rates):
    """Upper trace's busy-interval maximum at each endpoint, not recurrence."""
    out = []
    for t in sorted({v for _, lo, hi, _ in atoms for v in (lo, hi)}):
        qs = []; ps = []
        for i, r in enumerate(rates):
            arrived = [(hi, b) for owner, _, hi, b in atoms if owner == i and hi <= t]
            q = max([F(0)] + [sum(b for hi, b in arrived if hi >= s)-r*(t-s)
                             for s in {hi for hi, _ in arrived}])
            qs.append(q)
            ps.append(sum(b for owner, lo, hi, b in atoms if owner == i and lo <= t < hi))
        out.append((t, tuple(qs), tuple(ps), sum(q+p for q, p in zip(qs, ps))))
    return out


def concrete_peak(atoms, rates):
    """Literal integer release words, ordinary independently coded queues."""
    peak = F(0); private = [F(0)]*len(rates)
    for releases in product(*(range(lo, hi+1) for _, lo, hi, _ in atoms)):
        q = [F(0)]*len(rates); last = 0
        for t in sorted(set(releases)):
            for i, r in enumerate(rates):
                q[i] = max(F(0), q[i]-r*(t-last))
                q[i] += sum(b for (owner, _, _, b), at in zip(atoms, releases) if owner == i and at == t)
                private[i] = max(private[i], q[i])
            peak = max(peak, sum(q)); last = t
    return peak, private


class SnapshotRegression(unittest.TestCase):
    def test_four_modes_and_independent_rows(self):
        for atoms, rates in domain():
            bursts = [queues.Burst(*a) for a in atoms]
            rows = reference_rows(atoms, rates)
            peak = max([F(0)]+[row[3] for row in rows])
            private = [max([F(0)]+[row[1][i]+row[2][i] for row in rows]) for i in range(len(rates))]
            when = next((row[0] for row in rows if row[3] == peak), 0)
            if len(atoms) <= 2:
                self.assertEqual((peak, private), concrete_peak(atoms, rates))
            for record, stream in product((False, True), repeat=2):
                seen = []
                result = queues.shadow_reference(bursts, rates, record, seen.append if stream else None)
                self.assertEqual((result['pool'], result['private'], result['time']), (peak, private, when))
                self.assertEqual(result['trace'], rows if record else [])
                self.assertEqual(seen, rows if stream else [])
                if record and stream:
                    for a, b in zip(result['trace'], seen):
                        self.assertIs(a, b)
                count = len(rows); n = len(rates)
                masses = {(lo, 0, i) for i, lo, _, _ in atoms} | {(hi, 1, i) for i, _, hi, _ in atoms}
                self.assertEqual(result['row_count'], count)
                self.assertEqual(result['storage'], {
                    'event_times': count, 'sparse_event_entries': len(masses),
                    'state_vector_entries': 3*n, 'event_index_entries': 2*count,
                    'selected_container_entries': 3*n+len(masses)+2*count,
                    'entry_accounting': 'state vectors + sparse masses + event-map keys + sorted index',
                    'emitted_row_payload_entries': count*(2*n+2) if record or stream else 0,
                    'materialized_row_payload_entries': count*(2*n+2) if record else 0})

    def test_boundary_and_callback_semantics(self):
        b = [queues.Burst(0, 0, 2, 2), queues.Burst(0, 2, 3, 1)]
        rates = [F(1)]
        held = []
        def sink(row):
            held.append(row)
            rates[0] = F(0)  # Fresh rates read at the next row; no cross-call cache.
        result = queues.shadow_reference(b, rates, True, sink)
        self.assertEqual(result['trace'], held)
        self.assertEqual(held[0], (0, (F(0),), (2,), F(2)))
        self.assertEqual(held[-1], (3, (F(3),), (0,), F(3)))
        class Record:
            calls = 0
            def __bool__(self):
                self.calls += 1
                return self.calls % 2 == 1
        flag = Record()
        out = queues.shadow_reference(b, [1], flag)
        self.assertEqual(flag.calls, out['row_count']+1)
        self.assertEqual([row[0] for row in out['trace']], [0, 3])
        def stop(_):
            raise RuntimeError('finite diagnostic stop')
        with self.assertRaisesRegex(RuntimeError, '^finite diagnostic stop$'):
            queues.shadow_reference(b, [1], True, stop)
        for rr in ([], [-1], [True], [0.5], [None]):
            for rec, stream in product((False, True), repeat=2):
                with self.assertRaisesRegex(ValueError, '^nonempty nonnegative rate vector required$'):
                    queues.shadow_reference(b, rr, rec, held.append if stream else None)
        for bad, message in ((queues.Burst(True, 0, 1, 1), 'burst fields must be integers, not bools or floats'),
                             (queues.Burst(0, 2, 1, 1), 'invalid tenant, window, or size'),
                             (queues.Burst(2, 0, 1, 1), 'invalid tenant, window, or size')):
            with self.assertRaisesRegex(ValueError, '^'+message+'$'):
                queues.shadow_reference([bad], [1])

    def test_allocator_and_attaining_witness(self):
        for atoms, rates in list(domain())[:601] + [next(v for v in domain() if len(v[0]) == 4)]:
            bursts = [queues.Burst(*a) for a in atoms]
            out = queues.shadow_reference(bursts, rates)
            self.assertEqual(queues.simulate(bursts, rates, queues.witness(bursts, out['time']))['pool'], out['pool'])
        atoms = [(0, 0, 0, 4), (0, 3, 4, 3), (1, 1, 2, 3), (1, 4, 5, 4)]
        bursts = [queues.Burst(*a) for a in atoms]
        out = allocation.optimize_two(bursts, 2, [F(1, 4), F(1, 2)])
        self.assertEqual(out['pool'], 8)
        self.assertTrue(allocation.verify_two(bursts, 2, [F(1, 4), F(1, 2)], out['certificate']))
        bad = deepcopy(out['certificate']); bad['buffer'] = '0'
        with self.assertRaisesRegex(ValueError, '^claimed upper bound too small$'):
            allocation.verify_two(bursts, 2, [F(1, 4), F(1, 2)], bad)


if __name__ == '__main__':
    unittest.main(verbosity=2)
