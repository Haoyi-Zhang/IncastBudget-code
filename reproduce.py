#!/usr/bin/env python3
"""Reproduce exact results in serial bounded subprocesses, optionally in two parts.

Only per-run measurement fields are ignored in comparison. No network, hashes,
external solver, hidden cache or paper directory is required.
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
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
sys.path.insert(0, str(ROOT / 'src'))
from run_environment import resource, child_cpu, rss_kib, environment


def reproduction_binding():
    # Consumed on resume: a part cannot silently continue with different code
    # or declared inputs. This is a local binding, not a publisher signature.
    paths=list((ROOT/'src').glob('*.py'))+list((ROOT/'tests').glob('*.py'))
    paths += [ROOT/'reproduce.py',ROOT/'export_results.py']
    paths += list((ROOT/'independent_oracles').glob('*.py'))
    paths += list((ROOT/'inputs').glob('*.json'))+list((ROOT/'inputs').glob('*.jsonl'))
    return {p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(paths)}


def reserve_outputs(out, part):
    selected = JOBS[:SPLIT] if part == 'first' else JOBS[SPLIT:] if part == 'second' else JOBS
    names = [result_name(kind, chunk) for kind, chunk in selected]
    label = part or 'all'
    worker_count = len(selected) + (0 if part == 'first' else 8)
    names += [f'{label}-worker-{i:02d}.log' for i in range(1, worker_count+1)]
    names += [f'{part}-part-resources.json' if part else 'resource-use.json']
    if part != 'first':
        names += ['test-summary.json', 'example-check.json', 'example-certificate.json',
                  'example-verification.json', 'workflow-summary.json', 'derived', 'resource-use.json']
    for name in names:
        if (out / name).exists():
            raise ValueError(f'Refusing to overwrite retained output: {name}; choose a fresh run directory.')


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
    parser.add_argument('--portable', action='store_true',
                        help='explicitly omit unavailable POSIX CPU/address-space guards')
    args = parser.parse_args()
    out = args.output.resolve()
    if out.is_relative_to((ROOT / 'results').resolve()):
        raise ValueError('Choose a separate output directory; shipped evidence is read-only.')
    if resource is None and not args.portable:
        raise ValueError('POSIX resource unavailable; use --portable explicitly (no CPU/address-space guards).')
    reserve_outputs(out, args.part)
    out.mkdir(parents=True, exist_ok=True)
    binding=reproduction_binding()
    if args.part == 'second':
        # Validate the retained first-part evidence before continuing.
        first_resources = json.loads((out / 'first-part-resources.json').read_text())
        if first_resources.get('part') != 'first':
            raise ValueError('The first part has not completed.')
        if first_resources.get('environment') != environment() or first_resources['limits']['mode'] != ('portable' if args.portable else 'posix'):
            raise ValueError('Resume must use the same interpreter, optimization mode and guard mode.')
        if first_resources.get('source_input_binding') != binding:
            raise ValueError('Resume source/input binding differs; start a fresh run, preserving the old attempt.')
        for kind, chunk in JOBS[:SPLIT]:
            name = result_name(kind, chunk)
            compare_json(out / name, ROOT / 'results' / name)
    else:
        first_resources = None

    start = time.perf_counter()
    before = child_cpu()
    parent_start = time.process_time()
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONHASHSEED='0')

    worker_index = 0
    def run(command, quiet=False):
        nonlocal worker_index
        worker_index += 1
        label = args.part or 'all'
        log_path = out / f'{label}-worker-{worker_index:02d}.log'
        with log_path.open('x', encoding='utf-8') as log:
            log.write(json.dumps({'command': command}) + '\n')
            log.flush()
            subprocess.run(command, check=True, timeout=CHILD_WALL_TIMEOUT_SECONDS,
                           cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT)
        if not quiet:
            print(log_path.read_text(encoding='utf-8'), end='', flush=True)

    selected = JOBS[:SPLIT] if args.part == 'first' else JOBS[SPLIT:] if args.part == 'second' else JOBS
    python = [sys.executable, '-B'] + (['-'+'O'*sys.flags.optimize] if sys.flags.optimize else [])
    guard = ['--portable'] if args.portable else []
    for kind, chunk in selected:
        name = result_name(kind, chunk)
        command = python + [str(ROOT / 'src/validate_cases.py'), kind,
                            '--output', str(out / name)] + guard
        if chunk is not None:
            command += ['--chunk', str(chunk)]
        run(command, quiet=True)
        compare_json(out / name, ROOT / 'results' / name)
        print(name, 'matches', flush=True)

    test_contract=None
    if args.part != 'first':
        run(python + [str(ROOT / 'tests/run.py'), '--output', str(out / 'test-summary.json')] + guard)
        compare_json(out / 'test-summary.json', ROOT / 'results/test-summary.json')
        test_contract=json.loads((out / 'test-summary.json').read_text())
        # Separate regression contract: never inflate the historical 19+15 suite.
        run(python + [str(ROOT / 'tests/snapshot_regression.py')])
        run(python + [str(ROOT / 'tests/replay_storage_regression.py')])
        run(python + [str(ROOT / 'tests/workflow_regression.py'),
                      '--output', str(out / 'workflow-summary.json')])
        actions = [('check', None, 'example-check'), ('optimize', None, 'example-certificate'),
                   ('verify', out / 'example-certificate.json', 'example-verification')]
        for action, certificate, name in actions:
            command = python + [str(ROOT / 'src/queue_certificate.py'), action,
                       str(ROOT / 'inputs/example.json')]
            if certificate is not None:
                command.append(str(certificate))
            command += ['--output', str(out / (name + '.json'))]
            run(command)
            compare_json(out / (name + '.json'), ROOT / 'results' / (name + '.json'))
        run(python + [str(ROOT / 'export_results.py'), '--results', str(out),
             '--output', str(out / 'derived')], quiet=True)
        for name in ('summary.json', 'corners.csv', 'allocation.csv'):
            if (out / 'derived' / name).read_bytes() != (ROOT / 'results/derived' / name).read_bytes():
                raise ValueError(f'Derived result mismatch: {name}')
        for kind, chunk in JOBS:
            name = result_name(kind, chunk)
            compare_json(out / name, ROOT / 'results' / name)

    after = child_cpu()
    usage = {
        'part': args.part or 'all',
        'parent_cpu_seconds': time.process_time() - parent_start,
        'child_cpu_seconds': None if after is None else after-before,
        'wall_seconds': time.perf_counter() - start,
        'parent_peak_rss_kib': rss_kib(),
        'largest_child_peak_rss_kib': rss_kib('children'),
        'validation_worker_cpu_seconds': sum(json.loads((out/result_name(k,c)).read_text())['measurement']['cpu_seconds'] for k,c in selected),
        'environment': environment(),
        'source_input_binding': binding,
        'workers': 1,
        'validation_jobs': len(selected),
        'core_test_methods': 0 if test_contract is None else test_contract['core_test_methods'],
        'additional_test_methods': 0 if test_contract is None else test_contract['additional_test_methods'],
        'test_methods': 0 if test_contract is None else test_contract['test_methods'],
        'separate_regression_methods': 0 if args.part == 'first' else 8,
        'certificate_actions': 0 if args.part == 'first' else 3,
        'derived_files_checked': 0 if args.part == 'first' else 3,
        'limits': {'mode': 'portable' if args.portable else 'posix',
                   'child_cpu_seconds': None if args.portable else CHILD_CPU_LIMIT_SECONDS,
                   'child_wall_seconds': CHILD_WALL_TIMEOUT_SECONDS,
                   'address_space_mib': None if args.portable else ADDRESS_SPACE_MIB,
                   'cpu_address_space_scope': 'validation workers and tests/run.py; regression/CLI/export workers have wall timeout only',
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
            'child_cpu_seconds': None if any(p['child_cpu_seconds'] is None for p in pieces) else sum(p['child_cpu_seconds'] for p in pieces),
            'wall_seconds': sum(p['wall_seconds'] for p in pieces),
            'parent_peak_rss_kib': None if any(p['parent_peak_rss_kib'] is None for p in pieces) else max(p['parent_peak_rss_kib'] for p in pieces),
            'largest_child_peak_rss_kib': None if any(p['largest_child_peak_rss_kib'] is None for p in pieces) else max(p['largest_child_peak_rss_kib'] for p in pieces),
            'validation_worker_cpu_seconds': sum(p['validation_worker_cpu_seconds'] for p in pieces),
            'environment': environment(),
            'source_input_binding': binding,
            'workers': 1,
            'validation_jobs': sum(p['validation_jobs'] for p in pieces),
            'core_test_methods': sum(p['core_test_methods'] for p in pieces),
            'additional_test_methods': sum(p['additional_test_methods'] for p in pieces),
            'test_methods': sum(p['test_methods'] for p in pieces),
            'separate_regression_methods': sum(p['separate_regression_methods'] for p in pieces),
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
