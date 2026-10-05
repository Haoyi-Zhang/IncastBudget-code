"""Bounded, deterministic validation of retained mathematical claims."""
from __future__ import annotations
import argparse, csv, itertools, json, os, resource, sys, time
from pathlib import Path
from fractions import Fraction as F
from queues import (Burst, shadow_fast, shadow_reference, simulate, witness,
                    cell_shadow, cell_shadow_events, cell_simulate)
from oracle import enumerate_releases, interval_bound, vertex_allocation_oracle
from allocation import optimize_two, verify_two, private_admission
from phases import graph_instance, phase_trace
from phase_dp import robust_phase_peak

ROOT=Path(__file__).resolve().parents[1]
CALENDARS=[[0,1],[0,0,1],[-1,1,0,1]]

def pack(value):
    if isinstance(value,F): return str(value)
    if isinstance(value,dict): return {str(k):pack(v) for k,v in value.items()}
    if isinstance(value,(list,tuple)): return [pack(v) for v in value]
    return value

def same(a,b):
    if a['pool']!=b['pool'] or a['private']!=b['private']:
        raise AssertionError((a,b))

def fluid_case(row,calendars):
    bs=[Burst(**v) for v in row['bursts']]; rates=list(map(F,row['rates']))
    fast=shadow_fast(bs,rates); reference=shadow_reference(bs,rates)
    exact=enumerate_releases(bs,rates); cuts=interval_bound(bs,rates)
    for other in (reference,exact,cuts): same(fast,other)
    attained=simulate(bs,rates,witness(bs,fast['time']))
    assert attained['pool']==fast['pool']
    cells=[]
    for cal in calendars:
        ce=enumerate_releases(bs,rates,calendar=cal)
        slow=cell_shadow(bs,cal,len(rates)); event=cell_shadow_events(bs,cal,len(rates))
        same(ce,slow);same(ce,event)
        wc=cell_simulate(bs,witness(bs,event['time']),cal,len(rates))
        assert wc['pool']==event['pool']
        cells.append({'pool':event['pool'],'private':event['private']})
    return {'case':row.get('case'),'pool':fast['pool'],'private':fast['private'],
            'traces':exact['count'],'cells':cells}

def independent_private(bs,caps,floors,C):
    """Inverse cap oracle from ALL actual integer traces, not window cuts."""
    req=list(map(F,floors)); n=len(req)
    for times in itertools.product(*(range(b.lower,b.upper+1) for b in bs)):
        for t in set(times):
            for i in range(n):
                arrived=[(u,b.size) for b,u in zip(bs,times) if b.tenant==i and u<=t]
                for s in {t}|{u for u,v in arrived}:
                    amount=sum(v for u,v in arrived if u>=s)
                    if s==t:
                        if amount>caps[i]:return False,None
                    else:req[i]=max(req[i],(F(amount)-caps[i])/(t-s))
    return sum(req)<=C,req

def allocation_case(row,include_caps=False):
    bs=[Burst(**v) for v in row['bursts']]; C=F(row['capacity']);floors=list(map(F,row['floors']))
    out=optimize_two(bs,C,floors); ref=vertex_allocation_oracle(bs,C,floors)
    assert out['pool']==ref['pool'] and out['rates'][0]==ref['rate0']
    verify_two(bs,C,floors,out['certificate'])
    cap_checks=0
    if include_caps:
        for caps in itertools.product((F(1),F(2),F(3)),repeat=2):
            actual=private_admission(bs,caps,floors,C)
            expected,rr=independent_private(bs,caps,floors,C)
            assert actual['feasible']==expected
            if expected:assert actual['rates']==rr
            cap_checks+=1
    return {'case':row.get('case'),'pool':out['pool'],'rates':out['rates'],
            'traces':ref['traces'],'vertices':ref['vertices'],
            'certificate':out['certificate'],'private_cap_checks':cap_checks}

def controls():
    rows=[]
    for m in range(2,11):
        bs=[Burst(0,j,m+j,1) for j in range(m)]
        corners=max(simulate(bs,[F(1)],ts)['pool']
                    for ts in itertools.product(*[(b.lower,b.upper) for b in bs]))
        robust=shadow_fast(bs,[F(1)])['pool']
        assert corners==1 and robust==m
        rows.append({'bursts':m,'corners':1<<m,'corner_peak':corners,'exact_peak':robust})
    m=6;correlated=[Burst(0,j,j+m-1,1) for j in range(m)]
    phase=max(simulate(correlated,[F(1)],[j+d for j in range(m)])['pool'] for d in range(m))
    rect=shadow_fast(correlated,[F(1)])['pool'];assert (phase,rect)==(1,m)
    bs=[Burst(1,0,0,1),Burst(1,2,2,1)]
    fluid=shadow_fast(bs,[F(1,2),F(1,2)])['pool']
    bursty=cell_shadow_events(bs,[0,0,1,1],2)['pool']
    interleaved=cell_shadow_events(bs,[0,1,0,1],2)['pool']
    assert (fluid,bursty,interleaved)==(1,2,1)
    bs=[Burst(i,3*i,3*i,1) for i in range(6)]
    pooled=shadow_fast(bs,[F(1)]*6);assert pooled['pool']==1 and sum(pooled['private'])==6
    # A reservation can idle even when the aggregate output has backlog.
    bs=[Burst(0,0,0,2),Burst(0,2,2,2)]
    isolated=shadow_fast(bs,[F(1,2),F(3,2)])['pool']
    aggregate=shadow_fast(bs,[F(2)])['pool'];assert (isolated,aggregate)==(3,2)
    # Sparse checker-storage audit: n=m, one fixed burst per tenant at a
    # different time.  The sparse endpoint representation stores two nonzero
    # endpoint entries per burst rather than two dense n-vectors per time.
    storage_rows=[];recorded_payload=None
    for n in (8,16,32,64,128,256):
        sparse=[Burst(i,2*i,2*i,1) for i in range(n)];rates=[F(1)]*n
        streamed=[0]
        def count_row(_row):streamed.__setitem__(0,streamed[0]+1)
        reference=shadow_reference(sparse,rates,row_sink=count_row)
        fast=shadow_fast(sparse,rates)
        assert (reference['pool'],reference['private'],reference['time'])==(fast['pool'],fast['private'],fast['time'])
        profile=reference['storage']
        assert profile['event_times']==n and profile['sparse_event_entries']==2*n
        assert profile['event_index_entries']==2*n
        assert profile['selected_container_entries']==7*n
        assert profile['materialized_row_payload_entries']==0 and streamed[0]==n
        storage_rows.append({'n':n,'m':n,'event_times':profile['event_times'],
                             'sparse_event_entries':profile['sparse_event_entries'],
                             'state_vector_entries':profile['state_vector_entries'],
                             'event_index_entries':profile['event_index_entries'],
                             'selected_container_entries':profile['selected_container_entries'],
                             'streamed_rows':streamed[0],'pool':reference['pool']})
        if n==8:
            recorded=shadow_reference(sparse,rates,record=True)
            recorded_payload=recorded['storage']['materialized_row_payload_entries']
            assert recorded_payload==n*(2*n+2)
    return {'corner_family':rows,'correlation':{'phase_peak':phase,'rectangle_peak':rect},
            'calendar':{'fluid_peak':fluid,'clustered_peak':bursty,'interleaved_peak':interleaved},
            'pooling':{'private_sum':sum(pooled['private']),'pool':pooled['pool']},
            'scheduler':{'fixed_reservation':isolated,'work_conserving_aggregate':aggregate},
            'storage_scaling':{'construction':'n=m, one distinct fixed-time burst per tenant',
                               'all_numerical_matches':True,'rows':storage_rows,
                               'materialized_row_payload_entries_at_n8':recorded_payload}}

def graph_cases(max_vertices=4):
    rows=[]; assignments=0; widths={}
    for nv in range(1,max_vertices+1):
        pairs=list(itertools.combinations(range(nv),2))
        for mask in range(1<<len(pairs)):
            edges=[e for j,e in enumerate(pairs) if (mask>>j)&1]
            ins=graph_instance(nv,edges);best=0
            for bits in itertools.product((0,1),repeat=nv):
                out=phase_trace(ins,bits);cut=sum(bits[u]!=bits[v] for u,v in edges)
                assert out['pool']==ins['anchor_mass']+cut
                assert out['time']==ins['observation']
                best=max(best,cut);assignments+=1
            dp=robust_phase_peak(ins)
            assert dp['pool']==ins['anchor_mass']+best
            assert phase_trace(ins,dp['phases'])['pool']==dp['pool']
            widths[dp['induced_width']]=widths.get(dp['induced_width'],0)+1
            rows.append({'vertices':nv,'edges':edges,'M':ins['anchor_mass'],
                         'D':ins['offset'],'max_cut':best,'pool':str(dp['pool']),
                         'dp_width':dp['induced_width'],'dp_order':dp['order'],
                         'dp_candidate_times':dp['candidate_times'],
                         'dp_factor_entries':dp['factor_entries']})
    # A larger bounded-treewidth instance checks the polynomial-in-size side of
    # the parameterized algorithm without replacing the exhaustive small oracle.
    chain_vertices=64
    chain=graph_instance(chain_vertices,[(i,i+1) for i in range(chain_vertices-1)])
    chain_dp=robust_phase_peak(chain)
    expected=chain['anchor_mass']+chain_vertices-1
    assert chain_dp['induced_width']==1 and chain_dp['pool']==expected
    assert phase_trace(chain,chain_dp['phases'])['pool']==expected
    return {'graphs':len(rows),'phase_assignments':assignments,
            'all_assignment_identities_hold':True,
            'all_dp_optima_match_exhaustive':True,
            'dp_width_histogram':widths,
            'chain_check':{'vertices':chain_vertices,'edges':chain_vertices-1,
                           'induced_width':chain_dp['induced_width'],
                           'pool':str(chain_dp['pool']),
                           'candidate_times':chain_dp['candidate_times'],
                           'factor_entries':chain_dp['factor_entries']},
            'rows':rows}

def run(kind,chunk):
    if kind=='bounded':
        assert 0<=chunk<12
        rows=[]
        with (ROOT/'inputs/bounded.jsonl').open() as f:
            for line in f:
                row=json.loads(line)
                if row['case']%12==chunk:rows.append(fluid_case(row,CALENDARS))
        assert len(rows)==1728
        return {'instances':len(rows),'fluid_traces':sum(v['traces'] for v in rows),
                'cell_traces':3*sum(v['traces'] for v in rows),'calendars':CALENDARS,'rows':rows}
    if kind=='pilot':
        inputs=json.loads((ROOT/'inputs/pilot.json').read_text())
        rows=[fluid_case(dict(row,case=k),[[0,1,1]]) for k,row in enumerate(inputs)]
        return {'instances':len(rows),'fluid_traces':sum(v['traces'] for v in rows),
                'cell_traces':sum(v['traces'] for v in rows),'rows':rows}
    if kind in ('allocation-pilot','allocation-bounded'):
        inputs=json.loads((ROOT/'inputs'/f'{kind}.json').read_text())
        rows=[allocation_case(dict(row,case=k),kind=='allocation-bounded') for k,row in enumerate(inputs)]
        return {'instances':len(rows),'traces':sum(v['traces'] for v in rows),
                'private_cap_checks':sum(v['private_cap_checks'] for v in rows),'rows':rows}
    if kind=='controls':return controls()
    if kind=='correlation':return graph_cases()
    raise ValueError('unknown validation group')

def main():
    p=argparse.ArgumentParser();p.add_argument('kind',choices=['bounded','pilot','allocation-pilot','allocation-bounded','controls','correlation'])
    p.add_argument('--chunk',type=int,default=0);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    if hasattr(os,'sched_setaffinity'):os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
    resource.setrlimit(resource.RLIMIT_AS,(3584*1024**2,3584*1024**2))
    resource.setrlimit(resource.RLIMIT_CPU,(40,40))
    start=time.process_time();wall=time.perf_counter();result=pack(run(args.kind,args.chunk))
    result['measurement']={'cpu_seconds':time.process_time()-start,'wall_seconds':time.perf_counter()-wall,
                           'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'workers':1}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    temp=args.output.with_suffix('.tmp');temp.write_text(json.dumps(result,indent=2)+'\n');temp.replace(args.output)
    print(json.dumps({k:v for k,v in result.items() if k!='rows'}))
if __name__=='__main__':main()
