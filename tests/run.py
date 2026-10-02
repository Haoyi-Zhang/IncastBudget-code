#!/usr/bin/env python3
"""Run the frozen 18-test core suite and all 15 independent exactness/adversarial tests."""
from pathlib import Path
import argparse
import json
import os
import resource
import sys
import time
import unittest

ROOT=Path(__file__).resolve().parents[1]
TEST_DIR=Path(__file__).resolve().parent
# A script launched by pathname otherwise places tests/, not the repository root,
# first on sys.path on current Python versions.
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/'src'))

CORE_PATTERN='test_models.py'
ADDITIONAL_PATTERNS=('test_independent_oracles.py',
                     'test_independent_oracles_adversarial.py')
EXPECTED_CORE=18
EXPECTED_ADDITIONAL=15


def discover(pattern):
    return unittest.defaultTestLoader.discover(
        str(TEST_DIR),pattern=pattern,top_level_dir=str(TEST_DIR))


def run_suite(label,suite):
    print(f'=== {label}: {suite.countTestCases()} discovered methods ===',file=sys.stderr)
    return unittest.TextTestRunner(verbosity=2).run(suite)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if hasattr(os,'sched_setaffinity'):
        os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
    resource.setrlimit(resource.RLIMIT_AS,(3584*1024**2,3584*1024**2))
    resource.setrlimit(resource.RLIMIT_CPU,(40,40))

    core=discover(CORE_PATTERN)
    additional=unittest.TestSuite(discover(p) for p in ADDITIONAL_PATTERNS)
    discovered_core=core.countTestCases()
    discovered_additional=additional.countTestCases()

    cpu_start=time.process_time();wall_start=time.perf_counter()
    core_result=run_suite('core model suite',core)
    additional_result=run_suite('additional exactness/adversarial suite',additional)
    contract_ok=(discovered_core==EXPECTED_CORE and
                 discovered_additional==EXPECTED_ADDITIONAL and
                 core_result.testsRun==EXPECTED_CORE and
                 additional_result.testsRun==EXPECTED_ADDITIONAL)
    if not contract_ok:
        print('test discovery contract mismatch',file=sys.stderr)

    failures=len(core_result.failures)+len(additional_result.failures)
    errors=len(core_result.errors)+len(additional_result.errors)
    report={
        'core_test_methods':core_result.testsRun,
        'additional_test_methods':additional_result.testsRun,
        'test_methods':core_result.testsRun+additional_result.testsRun,
        'failures':failures,
        'errors':errors,
        'successful':contract_ok and core_result.wasSuccessful() and additional_result.wasSuccessful(),
        'suite_contract':{
            'core':{'pattern':CORE_PATTERN,'expected':EXPECTED_CORE,
                    'discovered':discovered_core,'executed':core_result.testsRun},
            'additional':{'patterns':list(ADDITIONAL_PATTERNS),
                          'expected':EXPECTED_ADDITIONAL,
                          'discovered':discovered_additional,
                          'executed':additional_result.testsRun},
            'strict_counts_match':contract_ok,
        },
        'measurement':{
            'cpu_seconds':time.process_time()-cpu_start,
            'wall_seconds':time.perf_counter()-wall_start,
            'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            'workers':1,
        },
    }
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    return 0 if report['successful'] else 1


if __name__=='__main__':
    raise SystemExit(main())
