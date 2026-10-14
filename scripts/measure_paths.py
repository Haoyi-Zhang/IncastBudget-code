"""Paired complete-path costs on existing inputs, never a new input matrix.

Both window paths return exact pool/private thresholds plus a replayed attaining
release. Both allocation identifiers return the exact value and smallest
optimizer plus a replayed witness. The producer's extra compact certificate is
fully charged. Supplied-candidate verification is a separate, weaker task.
"""
import argparse, hashlib, json, sys, time
from fractions import Fraction as F
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from queues import Burst,shadow_fast,shadow_reference,witness,simulate
from oracle import interval_bound,vertex_allocation_oracle
from allocation import optimize_two,verify_two
from queue_certificate import encode
from run_environment import environment


def require(ok,label):
    if not ok:raise ArithmeticError(label)


def timed(fn):
    cpu=time.process_time();wall=time.perf_counter();value=fn()
    return value,{'cpu_seconds':time.process_time()-cpu,'wall_seconds':time.perf_counter()-wall}


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if a.output.exists():raise ValueError('measurement output must be new')
    names=['pilot.json','bounded.jsonl','allocation-pilot.json','allocation-bounded.json']
    raw={n:(ROOT/'inputs'/n).read_bytes() for n in names}
    report={'scope':'One serial paired pass over existing authored inputs; not independent workload samples or deployed network measurements.',
            'environment':environment(),'read_scope':'input file bytes loaded once outside timers; each timed path includes JSON decoding, object conversion, computation, witness replay/checking and output serialization; excludes interpreter startup/disk I/O',
            'sources':{n:{'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)} for n,b in raw.items()},'groups':[]}
    for name in names:
        allocation=name.startswith('allocation-')
        # Candidate bytes are used ONLY by the separate candidate-verification
        # measurement. Neither timed identification path receives them.
        certificates=[]
        if allocation:
            for row in json.loads(raw[name]):
                certificates.append(optimize_two([Burst(**b) for b in row['bursts']],F(row['capacity']),list(map(F,row['floors'])))['certificate'])
        def path(production):
            rows=[json.loads(line) for line in raw[name].splitlines()] if name.endswith('jsonl') else json.loads(raw[name])
            outputs=[]
            for k,row in enumerate(rows):
                bs=[Burst(**b) for b in row['bursts']]
                if allocation:
                    C=F(row['capacity']);floors=list(map(F,row['floors']))
                    if production:
                        out=optimize_two(bs,C,floors) # includes internal verify_two
                        cert=json.loads(json.dumps(out['certificate']))
                        verify_two(bs,C,floors,cert) # independent consumption, also charged
                        x=out['rates'][0];value=out['pool']
                    else:
                        direct=vertex_allocation_oracle(bs,C,floors)
                        x=direct['rate0'];value=direct['pool']
                    rates=[x,C-x]
                    check=shadow_reference(bs,rates)
                    releases=witness(bs,check['time'])
                    require(simulate(bs,rates,releases)['pool']==value,'allocation witness differs')
                    payload={'pool':value,'rate0':x,'attaining_releases':releases}
                else:
                    rates=list(map(F,row['rates']))
                    if production:
                        out=shadow_fast(bs,rates);ref=shadow_reference(bs,rates)
                        require((out['pool'],out['private'])==(ref['pool'],ref['private']),'checker differs')
                    else:out=interval_bound(bs,rates)
                    releases=witness(bs,out['time'])
                    require(simulate(bs,rates,releases)['pool']==out['pool'],'window witness differs')
                    payload={k:out[k] for k in ('pool','private','time')};payload['attaining_releases']=releases
                outputs.append(json.dumps(encode(payload),sort_keys=True,separators=(',',':')))
            return outputs
        # Alternate order across the four fixed files; no best-of selection.
        order=(True,False) if len(report['groups'])%2==0 else (False,True)
        records={}
        for production in order:records[production]=timed(lambda:path(production))
        candidate_cost=None
        if allocation:
            def check_candidates():
                for row,cert in zip(json.loads(raw[name]),json.loads(json.dumps(certificates))):
                    bs=[Burst(**b) for b in row['bursts']];C=F(row['capacity']);floors=list(map(F,row['floors']))
                    verify_two(bs,C,floors,cert)
                    json.dumps(cert,sort_keys=True)
            _,candidate_cost=timed(check_candidates)
        prod,pcost=records[True];direct,dcost=records[False]
        require(prod==direct,'paired scientific output differs')
        report['groups'].append({'input':name,'instances':len(prod),'order':['production' if x else 'direct' for x in order],
            'production':pcost,'direct':dcost,'production_over_direct_wall':pcost['wall_seconds']/dcost['wall_seconds'],
            'all_outputs_equal':True,'serialized_output_bytes':sum(len(s.encode()) for s in prod),
            'output_sha256':hashlib.sha256(('\n'.join(prod)+'\n').encode()).hexdigest(),
            'supplied_candidate_verifier':candidate_cost,
            'certificate_preparation_scope':'candidate preparation excluded ONLY from separate weaker verification task; identifiers get no candidate' if allocation else None})
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
