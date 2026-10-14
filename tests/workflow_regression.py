"""Evidence-preserving workflow regressions, separate from the frozen 34 methods."""
import argparse, ast, json, subprocess, sys, tempfile, time, unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT)]
import validate_cases as vc
import reproduce
from run_environment import enforce_limits, measurement


class WorkflowTests(unittest.TestCase):
    def test_explicit_scientific_falsifiers(self):
        self.assertFalse(any(isinstance(n,ast.Assert) for n in ast.walk(ast.parse((ROOT/'src/validate_cases.py').read_text()))))
        row={'bursts':[{'tenant':0,'lower':0,'upper':0,'size':1}],'rates':['1']}
        with patch.object(vc,'simulate',return_value={'pool':999,'private':[999]}):
            with self.assertRaises(AssertionError):vc.fluid_case(row,[])
        with patch.object(vc,'phase_trace',return_value={'pool':999,'time':0}):
            with self.assertRaises(AssertionError):vc.graph_cases(1)

    def test_cli_preserves_sources_and_retained_outputs(self):
        with tempfile.TemporaryDirectory() as td:
            base=Path(td);inp=base/'input.json';payload=(ROOT/'inputs/example.json').read_bytes();inp.write_bytes(payload)
            retained=base/'summary.json';retained.write_text('retained')
            oldtmp=base/'rows.jsonl.tmp';oldtmp.write_text('retained temporary name')
            python=[sys.executable,'-B']+(['-'+'O'*sys.flags.optimize] if sys.flags.optimize else [])
            command=python+[str(ROOT/'src/queue_certificate.py'),'check',str(inp)]
            for options in (['--output',str(inp)],['--rows-output',str(inp)],['--output',str(retained)],
                            ['--output',str(base/'both'),'--rows-output',str(base/'both')]):
                cp=subprocess.run(command+options,capture_output=True,text=True,timeout=40)
                self.assertEqual(cp.returncode,2,cp.stderr)
                self.assertEqual(inp.read_bytes(),payload);self.assertEqual(retained.read_text(),'retained')
            cp=subprocess.run(command+['--rows-output',str(base/'rows.jsonl')],capture_output=True,text=True,timeout=40)
            self.assertEqual(cp.returncode,0,cp.stderr)
            self.assertEqual(oldtmp.read_text(),'retained temporary name')
            self.assertEqual(len((base/'rows.jsonl').read_text().splitlines()),6)

    def test_reproduction_preserves_prior_attempts(self):
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)
            for part,name in ((None,'all-worker-01.log'),('first','pilot.json'),('second','resource-use.json')):
                path=out/name;path.write_text('retained')
                with self.assertRaises(ValueError):reproduce.reserve_outputs(out,part)
                self.assertEqual(path.read_text(),'retained');path.unlink()

    def test_portable_mode_is_explicit_not_native_guards(self):
        limits=enforce_limits(True)
        self.assertEqual(limits['mode'],'portable')
        self.assertIsNone(limits['cpu_limit_seconds']);self.assertIsNone(limits['address_space_mib'])
        self.assertFalse(limits['affinity_pinned'])
        if sys.platform=='win32':
            with self.assertRaises(ValueError):enforce_limits(False)


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    cpu=time.process_time();wall=time.perf_counter()
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(WorkflowTests))
    report={'workflow_test_methods':r.testsRun,'failures':len(r.failures),'errors':len(r.errors),
            'successful':r.wasSuccessful(),'scope':'4 separate workflow methods; no new scientific input population',
            'measurement':measurement(cpu,wall,enforce_limits(True))}
    a.output.write_text(json.dumps(report,indent=2)+'\n')
    return 0 if r.wasSuccessful() else 1
if __name__=='__main__':raise SystemExit(main())
