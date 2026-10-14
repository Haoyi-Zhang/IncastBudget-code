"""Measure replay storage on the six already-shipped sparse controls."""
import argparse, importlib, json, sys, time, tracemalloc
from collections import defaultdict
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]


def main():
    p=argparse.ArgumentParser();p.add_argument('--module-root',type=Path,default=ROOT)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if a.output.exists():raise ValueError('output must be new')
    sys.path.insert(0,str(a.module_root/'src'))
    q=importlib.import_module('queues')
    controls=json.loads((ROOT/'results/controls.json').read_text())['storage_scaling']['rows']
    rows=[]
    for control in controls:
        n=control['n'];bs=[q.Burst(i,2*i,2*i,1) for i in range(n)];rates=[q.F(1)]*n;times=[b.lower for b in bs]
        maps=[]
        def capture(factory):
            value=defaultdict(factory);maps.append(value);return value
        with patch.object(q,'defaultdict',capture):
            out=q.simulate(bs,rates,times)
        entries=sum(len(v) for d in maps for v in d.values())
        tracemalloc.start();cpu=time.process_time();wall=time.perf_counter()
        repeated=q.simulate(bs,rates,times)
        cost={'cpu_seconds':time.process_time()-cpu,'wall_seconds':time.perf_counter()-wall,
              'peak_traced_python_bytes':tracemalloc.get_traced_memory()[1]}
        tracemalloc.stop()
        if out!=repeated or out['pool']!=1 or out['private']!=[q.F(1)]*n:
            raise ArithmeticError('sparse replay control changed')
        rows.append({'n':n,'m':len(bs),'arrival_entries':entries,'expected_nonzero_entries':n,
                     'pool':str(out['pool']),'private_sum':str(sum(out['private'])),**cost})
    report={'source_module':str(Path(q.__file__).resolve()),'optimization':sys.flags.optimize,
            'input_origin':'existing results/controls.json storage_scaling.rows; same fixed-time authored construction',
            'measurement_scope':'one replay per existing size; inputs constructed before tracing; Python traced allocations, not process RSS or physical buffer memory',
            'rows':rows}
    a.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
