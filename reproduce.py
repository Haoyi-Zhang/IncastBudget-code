#!/usr/bin/env python3
"""Reproduce exact results in serial bounded subprocesses, optionally in two parts.

Only per-run measurement fields are ignored in comparison. No network, hashes,
external solver, hidden cache or paper directory is required.
"""
from pathlib import Path
import argparse
import json
import os
import resource
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent
JOBS = [('pilot', None), ('allocation-pilot', None), ('allocation-bounded', None),
        ('controls', None), ('correlation', None)] + [('bounded', k) for k in range(12)]
SPLIT = 11
CHILD_CPU_LIMIT_SECONDS = 40
CHILD_WALL_TIMEOUT_SECONDS = 40
ADDRESS_SPACE_MIB = 3584


def result_name(kind, chunk):
    return f'{kind}.json' if chunk is None else f'{kind}-{chunk:02d}.json'


def compare_json(path, expected):
    actual = json.loads(path.read_text())
    reference = json.loads(expected.read_text())
    actual.pop('measurement', None)
    reference.pop('measurement', None)
    if actual != reference:
        raise ValueError(f'Scientific result mismatch: {path.name}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--part', choices=('first', 'second'),
                        help='Two bounded resumable parts; use the same output directory.')
    args = parser.parse_args()
    out = args.output.resolve()
    if out == (ROOT / 'results').resolve():
        raise ValueError('Choose a separate output directory; shipped evidence is read-only.')
    out.mkdir(parents=True, exist_ok=True)
    if args.part == 'second':
        # Validate the retained first-part evidence before continuing.
        first_resources = json.loads((out / 'first-part-resources.json').read_text())
        if first_resources.get('part') != 'first':
            raise ValueError('The first part has not completed.')
        for kind, chunk in JOBS[:SPLIT]:
            name = result_name(kind, chunk)
            compare_json(out / name, ROOT / 'results' / name)
    else:
        first_resources = None

    start = time.perf_counter()
    before = resource.getrusage(resource.RUSAGE_CHILDREN)
    parent_start = time.process_time()
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONHASHSEED='0')

    def run(command, quiet=False):
        subprocess.run(command, check=True, timeout=CHILD_WALL_TIMEOUT_SECONDS, cwd=ROOT, env=env,
                       stdout=subprocess.DEVNULL if quiet else None)

    selected = JOBS[:SPLIT] if args.part == 'first' else JOBS[SPLIT:] if args.part == 'second' else JOBS
    for kind, chunk in selected:
        name = result_name(kind, chunk)
        command = [sys.executable, str(ROOT / 'src/validate_cases.py'), kind,
                   '--output', str(out / name)]
        if chunk is not None:
            command += ['--chunk', str(chunk)]
        run(command, quiet=True)
        compare_json(out / name, ROOT / 'results' / name)
        print(name, 'matches', flush=True)

    test_contract=None
    if args.part != 'first':
        run([sys.executable, str(ROOT / 'tests/run.py'), '--output', str(out / 'test-summary.json')])
        compare_json(out / 'test-summary.json', ROOT / 'results/test-summary.json')
        test_contract=json.loads((out / 'test-summary.json').read_text())
        actions = [('check', None, 'example-check'), ('optimize', None, 'example-certificate'),
                   ('verify', out / 'example-certificate.json', 'example-verification')]
        for action, certificate, name in actions:
            command = [sys.executable, str(ROOT / 'src/queue_certificate.py'), action,
                       str(ROOT / 'inputs/example.json')]
            if certificate is not None:
                command.append(str(certificate))
            command += ['--output', str(out / (name + '.json'))]
            run(command)
            compare_json(out / (name + '.json'), ROOT / 'results' / (name + '.json'))
        run([sys.executable, str(ROOT / 'export_results.py'), '--results', str(out),
             '--output', str(out / 'derived')], quiet=True)
        for name in ('summary.json', 'corners.csv', 'allocation.csv'):
            if (out / 'derived' / name).read_bytes() != (ROOT / 'results/derived' / name).read_bytes():
                raise ValueError(f'Derived result mismatch: {name}')
        for kind, chunk in JOBS:
            name = result_name(kind, chunk)
            compare_json(out / name, ROOT / 'results' / name)

    after = resource.getrusage(resource.RUSAGE_CHILDREN)
    usage = {
        'part': args.part or 'all',
        'parent_cpu_seconds': time.process_time() - parent_start,
        'child_cpu_seconds': after.ru_utime + after.ru_stime - before.ru_utime - before.ru_stime,
        'wall_seconds': time.perf_counter() - start,
        'parent_peak_rss_kib': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        'largest_child_peak_rss_kib': after.ru_maxrss,
        'workers': 1,
        'validation_jobs': len(selected),
        'core_test_methods': 0 if test_contract is None else test_contract['core_test_methods'],
        'additional_test_methods': 0 if test_contract is None else test_contract['additional_test_methods'],
        'test_methods': 0 if test_contract is None else test_contract['test_methods'],
        'certificate_actions': 0 if args.part == 'first' else 3,
        'derived_files_checked': 0 if args.part == 'first' else 3,
        'limits': {'child_cpu_seconds': CHILD_CPU_LIMIT_SECONDS,
                   'child_wall_seconds': CHILD_WALL_TIMEOUT_SECONDS,
                   'address_space_mib': ADDRESS_SPACE_MIB,
                   'cpu_address_space_scope': 'validation and test workers',
                   'wall_timeout_scope': 'every direct child'},
        'scientific_results_match': True,
    }
    name = f'{args.part}-part-resources.json' if args.part else 'resource-use.json'
    (out / name).write_text(json.dumps(usage, indent=2) + '\n')
    if args.part == 'first':
        print('First part complete; run --part second with the same output directory.')
        return
    if args.part == 'second':
        pieces = [first_resources, usage]
        combined = {
            'execution': 'two serial resumable parts',
            'parent_cpu_seconds': sum(p['parent_cpu_seconds'] for p in pieces),
            'child_cpu_seconds': sum(p['child_cpu_seconds'] for p in pieces),
            'wall_seconds': sum(p['wall_seconds'] for p in pieces),
            'parent_peak_rss_kib': max(p['parent_peak_rss_kib'] for p in pieces),
            'largest_child_peak_rss_kib': max(p['largest_child_peak_rss_kib'] for p in pieces),
            'workers': 1,
            'validation_jobs': sum(p['validation_jobs'] for p in pieces),
            'core_test_methods': sum(p['core_test_methods'] for p in pieces),
            'additional_test_methods': sum(p['additional_test_methods'] for p in pieces),
            'test_methods': sum(p['test_methods'] for p in pieces),
            'certificate_actions': sum(p['certificate_actions'] for p in pieces),
            'derived_files_checked': sum(p['derived_files_checked'] for p in pieces),
            'limits': usage['limits'],
            'scientific_results_match': True,
            'wall_scope': 'sum of active parts; excludes time between invocations',
            'parts': pieces,
        }
        (out / 'resource-use.json').write_text(json.dumps(combined, indent=2) + '\n')
    print('All finite checks completed. This is not a general proof or novelty review.')


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        print(f'Reproduction failed: {exc}', file=sys.stderr)
        raise SystemExit(2)
