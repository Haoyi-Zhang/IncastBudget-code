"""Exact constant-rate admission with a separate segment verifier and replay.

The transparent recurrence remains available through queue_certificate.py for
full endpoint diagnostics. This route does not construct dense endpoint rows.
"""
from pathlib import Path
import argparse
import json
import sys

from queues import shadow_fast, witness
from segment_check import shadow_segments, simulate_segments
from queue_certificate import encode, instance, load


def checked_segments(bursts, rates):
    proposal = shadow_fast(bursts, rates)
    verified = shadow_segments(bursts, rates)
    if any(proposal[k] != verified[k] for k in ('pool', 'private', 'time')):
        raise ArithmeticError('producer/segment verifier mismatch')
    releases = witness(bursts, verified['time'])
    replay = simulate_segments(bursts, rates, releases)
    if replay['pool'] != verified['pool']:
        raise ArithmeticError('segment witness replay mismatch')
    return dict(verified, attaining_releases=releases,
                checker={'algorithm': 'independent-tenant-segments',
                         'exact_constant_rates': True, 'rows_materialized': False},
                model='independent-windows-fixed-reservations')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['check'])
    parser.add_argument('input', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    try:
        if args.output is not None:
            if args.output.resolve() == args.input.resolve() or args.output.exists():
                raise ValueError('output must be a new path distinct from input')
        bursts, rates, _, _ = instance(load(args.input))
        out = json.dumps(encode(checked_segments(bursts, rates)), indent=2) + '\n'
        if args.output is None:
            print(out, end='')
        else:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            with args.output.open('x', encoding='utf-8') as stream:
                stream.write(out)
    except (ValueError, KeyError, TypeError, OSError, ArithmeticError) as exc:
        print(f'error: {exc}', file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
