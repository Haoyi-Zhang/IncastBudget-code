#!/usr/bin/env python3
"""Derive every plotted number and compact scientific summary from exact results."""
from pathlib import Path
from fractions import Fraction as F
import argparse,csv,json,sys
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'src'))
from queue_certificate import load,instance
from queues import shadow_reference

def export(results,output):
    output.mkdir(parents=True,exist_ok=True)
    get=lambda name:json.loads((results/(name+'.json')).read_text())
    chunks=[get(f'bounded-{i:02d}') for i in range(12)]
    a=get('allocation-bounded');p=get('pilot');ap=get('allocation-pilot');g=get('correlation');t=get('test-summary');c=get('controls')
    storage_rows=c['storage_scaling']['rows']
    summary={'bounded_instances':sum(d['instances'] for d in chunks),
             'bounded_fluid_traces':sum(d['fluid_traces'] for d in chunks),
             'bounded_cell_traces':sum(d['cell_traces'] for d in chunks),
             'pilot_instances':p['instances'],'pilot_fluid_traces':p['fluid_traces'],
             'pilot_cell_traces':p['cell_traces'],'allocation_instances':a['instances'],
             'allocation_traces':a['traces'],'private_cap_checks':a['private_cap_checks'],
             'allocation_pilot_instances':ap['instances'],'allocation_pilot_traces':ap['traces'],
             'graphs':g['graphs'],'phase_assignments':g['phase_assignments'],
             'core_test_methods':t['core_test_methods'],
             'additional_test_methods':t['additional_test_methods'],
             'test_methods':t['test_methods'],'failures':t['failures'],'errors':t['errors'],
             'storage_scaling_instances':len(storage_rows),
             'storage_scaling_max_n':max(row['n'] for row in storage_rows)}
    (output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    with (output/'corners.csv').open('w',newline='') as f:
        w=csv.writer(f);w.writerow(['bursts','endpoint_peak','exact_peak'])
        for row in get('controls')['corner_family']:
            w.writerow([row['bursts'],row['corner_peak'],row['exact_peak']])
    bs,_,C,floors=instance(load(ROOT/'inputs/example.json'))
    lo,hi=floors[0],C-floors[1]
    with (output/'allocation.csv').open('w',newline='') as f:
        w=csv.writer(f);w.writerow(['rate0','pool','decreasing_cut','increasing_cut'])
        for k in range(51):
            x=lo+(hi-lo)*F(k,50); B=shadow_reference(bs,[x,C-x])['pool']
            # PGFPlots consumes decimal coordinates. Here all numbers terminate
            # exactly at <=3 decimal places, and the fractions are also retained.
            w.writerow([format(float(x),'.6f'),format(float(B),'.6f'),
                        format(float(10-2*x),'.6f'),format(float(6+2*x),'.6f')])
    return summary

def main():
    p=argparse.ArgumentParser();p.add_argument('--results',type=Path,default=ROOT/'results')
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    print(json.dumps(export(a.results,a.output),indent=2))
if __name__=='__main__':main()
