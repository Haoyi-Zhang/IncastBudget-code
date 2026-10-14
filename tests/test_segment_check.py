"""Bounded exact tests for the independent constant-rate segment verifier."""
import itertools
import json
import subprocess
import sys
import tempfile
import unittest
from fractions import Fraction as F
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from queues import Burst, shadow_reference, simulate
from segment_check import shadow_segments, simulate_segments
from segment_certificate import checked_segments


def brute_trace(bursts, rates, releases):
    """Busy-interval oracle enumerating arrival starts, not queue segments."""
    arrivals = [[] for _ in rates]
    for burst, time in zip(bursts, releases):
        arrivals[burst.tenant].append((time, burst.size))
    times = sorted(set(releases))
    private = [F(0)] * len(rates)
    pool = F(0)
    when = 0
    for time in times:
        queues = []
        for tenant, own in enumerate(arrivals):
            starts = {0} | {t for t, _ in own if t <= time}
            q = max((sum(size for t, size in own if start <= t <= time)
                     - F(rates[tenant]) * (time - start)
                     for start in starts), default=F(0))
            q = max(F(0), q)
            queues.append(q)
            private[tenant] = max(private[tenant], q)
        total = sum(queues, F(0))
        if total > pool:
            pool, when = total, time
    return {'pool': pool, 'private': private, 'time': when, 'trace': []}


class SegmentVerifierTests(unittest.TestCase):
    def test_full_existing_window_domains(self):
        inputs = json.loads((ROOT / 'inputs/pilot.json').read_text())
        inputs += [json.loads(line) for line in
                   (ROOT / 'inputs/bounded.jsonl').read_text().splitlines()]
        self.assertEqual(len(inputs), 96 + 20736)
        for row in inputs:
            bursts = [Burst(**b) for b in row['bursts']]
            rates = list(map(F, row['rates']))
            actual = checked_segments(bursts, rates)
            ref = shadow_reference(bursts, rates)
            for k in ('pool', 'private', 'time'):
                self.assertEqual(actual[k], ref[k], row.get('case'))
            replay = simulate(bursts, rates, actual['attaining_releases'])
            self.assertEqual(replay['pool'], actual['pool'])
            self.assertIs(type(actual['time']), int)

    def test_independent_verifier_does_not_invoke_reference_or_producer(self):
        from unittest.mock import patch
        with patch('queues.shadow_fast', side_effect=RuntimeError('not verifier')), \
             patch('queues.shadow_reference', side_effect=RuntimeError('not verifier')), \
             patch('queues.simulate', side_effect=RuntimeError('not verifier')):
            bursts = [Burst(0, 0, 3, 1), Burst(1, 3, 3, 2)]
            self.assertEqual(shadow_segments(bursts, [F(2, 3), F(1)])['pool'], 3)
            self.assertEqual(simulate_segments(bursts, [F(2, 3), F(1)], [3, 3])['pool'], 3)

    def test_cli_matches_and_preserves_existing_files(self):
        python = [sys.executable, '-B'] + (['-O'] if sys.flags.optimize else [])
        command = python + [str(ROOT / 'src/segment_certificate.py'), 'check',
                            str(ROOT / 'inputs/example.json')]
        result = subprocess.run(command, capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)
        out = json.loads(result.stdout)
        self.assertEqual((out['pool'], out['private'], out['time']), ('8', ['4', '5'], 4))
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / 'result.json'
            target.write_text('owned pre-existing content')
            result = subprocess.run(command + ['--output', str(target)],
                                    capture_output=True, text=True, timeout=20)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(target.read_text(), 'owned pre-existing content')

    def test_matches_transparent_recurrence_and_replay(self):
        cases = [
            ([], [F(0), F(3, 5), F(2)]),
            ([Burst(0, 0, 0, 4), Burst(1, 0, 3, 2),
              Burst(1, 3, 5, 7)], [F(1, 2), F(0), F(3, 2), F(7)]),
            ([Burst(0, 0, 4, 3), Burst(0, 2, 2, 5),
              Burst(2, 2, 6, 4), Burst(1, 6, 6, 1)],
             [F(2, 3), F(1, 4), F(5, 2)]),
            ([Burst(0, 4, 4, 3), Burst(1, 0, 8, 2)], [F(1), F(1, 3)]),
        ]
        for bursts, rates in cases:
            with self.subTest(bursts=bursts, rates=rates):
                got = shadow_segments(bursts, rates)
                ref = shadow_reference(bursts, rates)
                self.assertEqual(got, {k: ref[k] for k in ('pool', 'private', 'time')})

                releases = [b.upper for b in bursts]
                got_replay = simulate_segments(bursts, rates, releases)
                expected = simulate(bursts, rates, releases)
                self.assertEqual(got_replay, expected)

    def test_small_exhaustive_release_oracle(self):
        cases = [
            ([Burst(0, 0, 1, 1), Burst(1, 0, 2, 2)], [F(1), F(1, 2), F(0)]),
            ([Burst(0, 0, 2, 2), Burst(0, 1, 2, 1),
              Burst(1, 0, 1, 2)], [F(2, 3), F(0)]),
            ([Burst(1, 0, 3, 3)], [F(7, 5), F(1, 3), F(0), F(9)]),
            ([Burst(0, 2, 2, 4), Burst(1, 0, 2, 1),
              Burst(1, 2, 4, 3)], [F(0), F(3, 2), F(2, 5)]),
        ]
        for bursts, rates in cases:
            domains = [range(b.lower, b.upper + 1) for b in bursts]
            expected_pool = F(0)
            expected_private = [F(0)] * len(rates)
            expected_time = 0
            for releases in itertools.product(*domains):
                value = brute_trace(bursts, rates, releases)
                for i, q in enumerate(value['private']):
                    expected_private[i] = max(expected_private[i], q)
                if value['pool'] > expected_pool:
                    expected_pool, expected_time = value['pool'], value['time']

            found = shadow_segments(bursts, rates)
            self.assertEqual(found, {'pool': expected_pool,
                                     'private': expected_private,
                                     'time': expected_time})

            for releases in itertools.product(*domains):
                expected = brute_trace(bursts, rates, releases)
                got = simulate_segments(bursts, rates, releases)
                self.assertEqual(got, expected)

    def test_exact_empty_times_ties_zero_rates_and_pool_time_tie(self):
        bursts = [Burst(0, 0, 0, 1), Burst(0, 2, 3, 1),
                  Burst(1, 2, 2, 2), Burst(2, 5, 5, 1)]
        rates = [F(2, 3), F(0), F(4)]
        result = shadow_segments(bursts, rates)
        reference = shadow_reference(bursts, rates)
        self.assertEqual(result, {k: reference[k] for k in ('pool', 'private', 'time')})
        self.assertEqual(result['pool'], F(3))
        self.assertEqual(result['time'], 2)
        replay = simulate_segments(bursts, rates, [0, 3, 2, 5])
        self.assertEqual(replay, simulate(bursts, rates, [0, 3, 2, 5]))

    def test_invalid_inputs_are_rejected(self):
        with self.assertRaises(ValueError):
            shadow_segments([Burst(0, 0, 1, 1)], [F(-1)])
        with self.assertRaises(ValueError):
            shadow_segments([Burst(1, 0, 1, 1)], [F(1)])
        with self.assertRaises(ValueError):
            simulate_segments([Burst(0, 0, 1, 1)], [F(1)], [2])
        with self.assertRaises(ValueError):
            simulate_segments([Burst(0, 0, 1, 1)], [F(1)], [0, 1])


if __name__ == '__main__':
    unittest.main()
