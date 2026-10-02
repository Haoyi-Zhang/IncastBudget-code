import copy,itertools,json,subprocess,sys,tempfile,unittest
from pathlib import Path
from fractions import Fraction as F
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from queues import *
from allocation import *
from oracle import *
from exact import rational
from queue_certificate import load,instance
from phases import graph_instance,phase_trace,exhaustive_phase_peak
from phase_dp import (robust_phase_peak, induced_width, min_fill_order,
                      candidate_times, validate_phase_instance)

class QueueTests(unittest.TestCase):
    def test_empty(self):
        for rates in ([F(0)],[F(1),F(2)]):
            fast=shadow_fast([],rates); reference=shadow_reference([],rates)
            self.assertEqual(fast['pool'],0);self.assertEqual(reference['pool'],0)
            self.assertEqual(fast['private'],[F(0)]*len(rates))
            self.assertEqual(reference['private'],[F(0)]*len(rates))
        self.assertEqual(cell_shadow_events([],[0],1)['pool'],0)
        floors=[F(1,4),F(1,2)]
        admission=private_admission([], [0,0], floors, 2)
        self.assertTrue(admission['feasible'])
        self.assertEqual(admission['rates'],floors)
        self.assertEqual(admission['private'],[F(0),F(0)])
        a=optimize_two([],2,floors);self.assertEqual(a['pool'],0)
        self.assertEqual(a['rates'],[floors[0],F(2)-floors[0]])
        self.assertEqual(a['certificate']['mode'],'empty')
        self.assertEqual(a['certificate']['rate0'],str(floors[0]))
        self.assertEqual(a['certificate']['support'][0]['line']['kind'],'empty-zero-sentinel')
        self.assertTrue(verify_two([],2,floors,a['certificate']))
        bad=copy.deepcopy(a['certificate']);bad['certificate_kind']='fabricated'
        bad['support'][0]['line']['intercept']='1'
        with self.assertRaises(ValueError):verify_two([],2,floors,bad)
    def test_zero_service_ties(self):
        bs=[Burst(0,0,0,3),Burst(0,0,2,5),Burst(1,2,2,7)]
        a=shadow_fast(bs,[F(0),F(0)])
        self.assertEqual(a['pool'],15);self.assertEqual(a['private'],[8,7])
    def test_heap_staleness(self):
        bs=[Burst(j%3,j,j+1,(j%5)+1) for j in range(30)]
        rates=[F(3,7),F(5,11),F(0)]
        for subset in (bs,bs[::2],bs[::-1]):
            a=shadow_fast(subset,rates);b=shadow_reference(subset,rates)
            self.assertEqual(a['pool'],b['pool']);self.assertEqual(a['private'],b['private'])
        # Sparse-storage regression: n=m, one tenant-specific fixed burst at each
        # distinct time.  Event storage must grow linearly and streamed rows must
        # agree numerically without being materialized in memory.
        for n in (8,32,128):
            sparse=[Burst(i,2*i,2*i,1) for i in range(n)]
            seen=[]
            ref=shadow_reference(sparse,[F(1)]*n,row_sink=lambda row:seen.append(row[0]))
            fast=shadow_fast(sparse,[F(1)]*n)
            self.assertEqual((ref['pool'],ref['private'],ref['time']),
                             (fast['pool'],fast['private'],fast['time']))
            self.assertEqual(ref['storage']['event_times'],n)
            self.assertEqual(ref['storage']['sparse_event_entries'],2*n)
            self.assertEqual(ref['storage']['event_index_entries'],2*n)
            self.assertEqual(ref['storage']['working_entry_upper_bound'],7*n)
            self.assertEqual(ref['storage']['materialized_row_payload_entries'],0)
            self.assertEqual(len(seen),n)
    def test_large_calendar_horizon(self):
        bs=[Burst(0,10**12,10**12+3,2),Burst(1,10**12+1,10**12+5,3)]
        cal=[0,1,1,-1];shift=10**12
        small=[Burst(b.tenant,b.lower-shift,b.upper-shift,b.size) for b in bs]
        a=cell_shadow_events(bs,cal,2);b=cell_shadow(small,cal,2)
        self.assertEqual(a['pool'],b['pool']);self.assertEqual(a['private'],b['private'])
    def test_exact_numerics(self):
        self.assertEqual(rational('0.125'),F(1,8))
        for v in (True,False,0.1,None,float('nan'),float('inf')):
            with self.subTest(v=v):
                with self.assertRaises(ValueError):rational(v)
    def test_invalid_bursts(self):
        bad=[Burst(0,2,1,1),Burst(2,0,1,1),Burst(0,0,1,0),Burst(True,0,1,1),Burst(0,0.0,1,1)]
        for b in bad:
            with self.assertRaises(ValueError):shadow_fast([b],[F(1)])
        for rate in ([-1],[0.5],[True],[]):
            with self.assertRaises(ValueError):shadow_fast([],rate)
    def test_invalid_calendar_and_release(self):
        b=[Burst(0,0,2,1)]
        for cal in ([],[2],[True]):
            with self.assertRaises(ValueError):cell_shadow_events(b,cal,1)
        for ts in ([],[3],[0.5],[True]):
            with self.assertRaises(ValueError):simulate(b,[F(1)],ts)
    def test_witness_vector(self):
        bs=[Burst(0,0,3,2),Burst(1,1,4,3),Burst(0,3,5,2)]
        rates=[F(1,2),F(2,3)]
        for t,q,p,total in shadow_reference(bs,rates,record=True)['trace']:
            ts=witness(bs,t)
            # Add a zero-sized observation is forbidden, so drain from last actual
            # event through t manually when no real arrival is scheduled at t.
            trace=simulate(bs,rates,ts,record=True)['trace']
            past=[(at,vals) for at,vals in trace if at<=t]
            at,vals=past[-1] if past else (0,(F(0),F(0)))
            vals=[max(0,v-r*(t-at)) for v,r in zip(vals,rates)]
            self.assertEqual(vals,[x+y for x,y in zip(q,p)])
    def test_enumeration_guard(self):
        with self.assertRaises(ValueError):enumerate_releases([Burst(0,0,100,1)],[F(1)],limit=10)
    def test_private_caps(self):
        bs=[Burst(0,0,0,2),Burst(0,4,4,2)]
        out=private_admission(bs,[2],[0],1);self.assertTrue(out['feasible']);self.assertEqual(out['rates'],[F(1,2)])
        self.assertFalse(private_admission(bs,[1],[0],100)['feasible'])
        self.assertFalse(private_admission(bs,[2],[0],F(1,4))['feasible'])
    def test_boundary_rates(self):
        bs=[Burst(0,0,0,1),Burst(1,3,3,2)]
        for floors in ([0,0],[1,1],[F(1,4),F(1,2)]):
            a=optimize_two(bs,2,floors);b=vertex_allocation_oracle(bs,2,floors)
            self.assertEqual(a['pool'],b['pool']);self.assertTrue(verify_two(bs,2,floors,a['certificate']))
    def test_certificate_mutations(self):
        data=json.loads((ROOT/'inputs/example.json').read_text());bs,rates,C,floors=instance(data)
        cert=optimize_two(bs,C,floors)['certificate']
        mutations=[]
        for key,val in [('buffer','0'),('buffer',str(F(cert['buffer'])+1)),('rate0','-1'),('rate0',0.5),('mode','fabricated')]:
            z=copy.deepcopy(cert);z[key]=val;mutations.append(z)
        z=copy.deepcopy(cert);z['support']=[];mutations.append(z)
        for field,val in [('time',-1),('time',True),('s0',-1),('s1',-1)]:
            z=copy.deepcopy(cert);z['support'][0]['line'][field]=val;mutations.append(z)
        for field in ('slope','intercept'):
            z=copy.deepcopy(cert);z['support'][0]['line'][field]=str(F(z['support'][0]['line'][field])+1);mutations.append(z)
        # An equivalent exact spelling (0.5 for 1/2) is not a corruption.
        identity=copy.deepcopy(cert)
        self.assertEqual(F(identity['support'][0]['weight']),F(1,2))
        identity['support'][0]['weight']='0.5'
        self.assertTrue(verify_two(bs,C,floors,identity))
        for w in ('-1','2',True):
            z=copy.deepcopy(cert);z['support'][0]['weight']=w;mutations.append(z)
        for k,z in enumerate(mutations):
            with self.subTest(mutation=k):
                with self.assertRaises((ValueError,KeyError,TypeError)):verify_two(bs,C,floors,z)
    def test_json_input_rejection(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'x.json'
            for text in ('{"x":1,"x":2}','{"x":NaN}','{"x":Infinity}'):
                p.write_text(text)
                with self.assertRaises(ValueError):load(p)
            # The public CLI omits dense q/p histories by default and can stream
            # the same diagnostic rows without retaining them in the summary.
            summary=Path(tmp)/'summary.json'; rows=Path(tmp)/'rows.jsonl'
            proc=subprocess.run([sys.executable,str(ROOT/'src/queue_certificate.py'),
                                 'check',str(ROOT/'inputs/example.json'),
                                 '--output',str(summary),'--rows-output',str(rows)],
                                cwd=ROOT,text=True,capture_output=True)
            self.assertEqual(proc.returncode,0,proc.stderr)
            payload=json.loads(summary.read_text())
            self.assertFalse(payload['checker']['rows_materialized'])
            self.assertEqual(payload['row_stream']['rows'],
                             len(rows.read_text().splitlines()))
    def test_graph_construction(self):
        ins=graph_instance(3,[(0,1),(1,2)])
        self.assertEqual(len(ins['jobs']),17)
        a=exhaustive_phase_peak(ins);self.assertEqual(a['pool'],11)
        for bits in itertools.product((0,1),repeat=3):
            cut=(bits[0]!=bits[1])+(bits[1]!=bits[2])
            self.assertEqual(phase_trace(ins,bits)['pool'],9+cut)
    def test_phase_input_rejection(self):
        with self.assertRaises(ValueError):graph_instance(2,[(1,0)])
        with self.assertRaises(ValueError):graph_instance(2,[(0,1),(0,1)])
        ins=graph_instance(2,[(0,1)])
        with self.assertRaises(ValueError):phase_trace(ins,[0,2])
        with self.assertRaises(ValueError):exhaustive_phase_peak(ins,group_limit=1)

    def test_phase_treewidth_elimination(self):
        # In the reduction family, the phase interaction graph is exactly G.
        path=graph_instance(7,[(i,i+1) for i in range(6)])
        order=min_fill_order(path)
        self.assertEqual(induced_width(path,order),1)
        dp=robust_phase_peak(path,order)
        brute=exhaustive_phase_peak(path)
        self.assertEqual(dp['pool'],brute['pool'])
        self.assertEqual(phase_trace(path,dp['phases'])['pool'],dp['pool'])
        clique=graph_instance(5,list(itertools.combinations(range(5),2)))
        order=min_fill_order(clique)
        self.assertEqual(induced_width(clique,order),4)
        self.assertEqual(robust_phase_peak(clique,order)['pool'],
                         exhaustive_phase_peak(clique)['pool'])

    def test_phase_dp_generic_and_rejection(self):
        ins={'groups':3,'offset':4,'tenants':3,'rates':['1/2','1','0'],
             'jobs':[{'tenant':0,'group':0,'base':0,'size':2},
                     {'tenant':0,'group':2,'base':1,'size':1},
                     {'tenant':1,'group':1,'base':0,'size':3},
                     {'tenant':2,'group':None,'base':2,'size':1}]}
        dp=robust_phase_peak(ins,[0,1,2])
        brute=exhaustive_phase_peak(ins)
        self.assertEqual(dp['pool'],brute['pool'])
        self.assertEqual(phase_trace(ins,dp['phases'])['pool'],dp['pool'])
        self.assertEqual(candidate_times({'groups':0,'offset':1,'tenants':1,
                                          'rates':['1'],'jobs':[]}),(F(0),))
        with self.assertRaises(ValueError):induced_width(ins,[0,1,1])
        with self.assertRaises(ValueError):robust_phase_peak(dict(ins,offset=-1))
        with self.assertRaises(ValueError):validate_phase_instance(dict(ins,rates=[0.5,1,0]))
    def test_permutation_invariance(self):
        bs=[Burst(0,0,2,1),Burst(1,1,3,2),Burst(0,3,4,1)]
        rates=[F(2,3),F(4,5)];a=shadow_fast(bs,rates)
        for perm in itertools.permutations(bs):
            b=shadow_fast(perm,rates);self.assertEqual((a['pool'],a['private']),(b['pool'],b['private']))
if __name__=='__main__':unittest.main()
