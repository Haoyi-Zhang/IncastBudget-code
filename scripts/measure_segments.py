"""Three fixed-order complete-path passes on existing window and sparse inputs.

No new workload population, fitted rates, sample filtering or repeat-until-gain.
"""
import argparse
import ctypes
import hashlib
import json
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from fractions import Fraction as F
from queues import Burst, shadow_fast, shadow_reference, simulate, witness
from segment_certificate import checked_segments
from queue_certificate import encode
from run_environment import environment


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError('Preserve prior output; choose a new path')
    affinity = None
    if sys.platform == 'win32':
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel.GetCurrentProcess.restype = ctypes.c_void_p
        kernel.SetProcessAffinityMask.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
        if not kernel.SetProcessAffinityMask(kernel.GetCurrentProcess(), 1):
            raise OSError(ctypes.get_last_error(), 'SetProcessAffinityMask')
        affinity = 1
        import winreg
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                            r'HARDWARE\DESCRIPTION\System\CentralProcessor\0') as key:
            cpu = winreg.QueryValueEx(key, 'ProcessorNameString')[0].strip()
    else:
        cpu = None
        if hasattr(os, 'sched_getaffinity'):
            first = min(os.sched_getaffinity(0))
            os.sched_setaffinity(0, {first})
            affinity = [first]
    names = ['src/queues.py', 'src/queue_certificate.py', 'src/segment_certificate.py',
             'src/segment_check.py', 'scripts/measure_segments.py', 'src/run_environment.py']
    before = {name: sha(ROOT / name) for name in names}
    groups = []
    for name in ('pilot.json', 'bounded.jsonl'):
        data = (ROOT / 'inputs' / name).read_bytes()
        groups.append((name, data, name.endswith('.jsonl')))
    # The six sparse sizes are exactly the retained controls in validate_cases.
    for n in (8, 16, 32, 64, 128, 256):
        row = {'bursts': [dict(tenant=i, lower=2*i, upper=2*i, size=1) for i in range(n)],
               'rates': ['1'] * n}
        groups.append(('sparse-' + str(n), json.dumps([row]).encode(), False))
    records = []
    for name, data, jsonl in groups:
        for round_ in range(3):
            outputs = {}
            for position in range(2):
                route = ('transparent', 'segments')[(round_ + position) % 2]
                wall, cpu_start = time.perf_counter(), time.process_time()
                rows = [json.loads(line) for line in data.splitlines()] if jsonl else json.loads(data)
                results = []
                for row in rows:
                    bursts = [Burst(**b) for b in row['bursts']]
                    rates = list(map(F, row['rates']))
                    if route == 'segments':
                        result = checked_segments(bursts, rates)
                        releases = result['attaining_releases']
                    else:
                        result = shadow_fast(bursts, rates)
                        ref = shadow_reference(bursts, rates)
                        if any(result[k] != ref[k] for k in ('pool', 'private', 'time')):
                            raise ArithmeticError('transparent checker mismatch')
                        releases = witness(bursts, result['time'])
                        if simulate(bursts, rates, releases)['pool'] != result['pool']:
                            raise ArithmeticError('transparent replay mismatch')
                    payload = {k: result[k] for k in ('pool', 'private', 'time')}
                    payload['attaining_releases'] = releases
                    results.append(json.dumps(encode(payload), sort_keys=True, separators=(',', ':')))
                elapsed = {'wall_seconds': time.perf_counter() - wall,
                           'process_cpu_seconds': time.process_time() - cpu_start}
                body = ('\n'.join(results) + '\n').encode()
                outputs[route] = body
                records.append(dict(group=name, round=round_, position=position, route=route,
                                    instances=len(rows), input_bytes=len(data),
                                    input_sha256=hashlib.sha256(data).hexdigest(),
                                    output_bytes=len(body), output_sha256=hashlib.sha256(body).hexdigest(),
                                    **elapsed))
            if outputs['transparent'] != outputs['segments']:
                raise ArithmeticError('Same-guarantee serialized outputs differ')
    after = {name: sha(ROOT / name) for name in names}
    if before != after:
        raise ArithmeticError('Sources changed during measurement')
    report = dict(scope='Current complete fixed-rate paths on existing authored inputs, not network deployment',
                  environment=environment(), processor=cpu, affinity=affinity,
                  rounds=3, samples_retained=len(records), all_outputs_equal=True,
                  source_sha256=before, source_unchanged=True, samples=records,
                  timer_scope='JSON decoding, instance construction, producer, independent verifier, clipped witness replay and per-instance output serialization; excludes file acquisition/interpreter startup; group validation follows timers',
                  limits='One process and one logical CPU; no hardware-exclusive claim; three unfiltered passes with fixed alternating order, not a statistical deployment estimate')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x', encoding='utf-8') as stream:
        json.dump(report, stream, indent=2)
    print(json.dumps({'samples': len(records), 'all_outputs_equal': True, 'output': str(args.output)}))


if __name__ == '__main__':
    main()
