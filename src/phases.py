"""Binary shared-phase inputs and the explicit graph reduction.

This is a benign synthetic queue model. No network connection is opened.
"""
from itertools import product
from fractions import Fraction as F
from phase_dp import validate_phase_instance

def graph_instance(vertices, edges):
    """Unit bursts, unit reservations, and four possible arrival epochs."""
    if type(vertices) is not int or vertices < 1:
        raise ValueError('positive integer vertex count required')
    clean=[]
    for edge in edges:
        if len(edge)!=2 or any(type(v) is not int for v in edge):
            raise ValueError('integer endpoint pair required')
        u,v=edge
        if not 0<=u<v<vertices or (u,v) in clean:
            raise ValueError('simple sorted-endpoint graph required')
        clean.append((u,v))
    E=len(clean); M=4*E+1; D=M+2; n=2*E+1
    jobs=[]
    for e,(u,v) in enumerate(clean):
        jobs += [{'tenant':2*e,'group':u,'base':0,'size':1},
                 {'tenant':2*e,'group':v,'base':D,'size':1},
                 {'tenant':2*e+1,'group':u,'base':D,'size':1},
                 {'tenant':2*e+1,'group':v,'base':0,'size':1}]
    jobs += [{'tenant':n-1,'group':None,'base':D+1,'size':1} for _ in range(M)]
    return {'groups':vertices,'offset':D,'tenants':n,'rates':['1']*n,
            'jobs':jobs,'anchor_mass':M,'observation':D+1}

def phase_trace(instance, bits):
    """Ordinary event replay on the same exact-rational domain as phase DP.

    Only input validation is shared with the solver; replay does not construct
    occupancy factors or call elimination. Tied arrivals are coalesced before
    observing the queues, and unused constant service is discarded.
    """
    g,n,D,rates,jobs=validate_phase_instance(instance)
    if len(bits)!=g or any(type(b) is not int or b not in (0,1) for b in bits):
        raise ValueError('one binary choice per phase group required')
    events={}
    for tenant,group,base,size in jobs:
        at=base if group is None else base+D*bits[group]
        arrivals=events.setdefault(at,[F(0)]*n)
        arrivals[tenant]+=size
    q=[F(0)]*n;private=[F(0)]*n;peak=F(0);when=F(0);last=F(0)
    for at,arrivals in sorted(events.items()):
        q=[max(F(0),v-r*(at-last))+a for v,r,a in zip(q,rates,arrivals)]
        private=[max(v,p) for v,p in zip(q,private)]
        if sum(q)>peak:peak=sum(q);when=at
        last=at
    return {'pool':peak,'private':private,'time':when,'trace':[]}

def exhaustive_phase_peak(instance, group_limit=20):
    """Exact exponential checker, deliberately bounded; not a polynomial solver."""
    g=instance['groups']
    if not 0<=g<=group_limit:
        raise ValueError('phase enumeration limit exceeded')
    best=F(-1);witness=[]
    for bits in product((0,1),repeat=g):
        out=phase_trace(instance,bits)
        if out['pool']>best:best=out['pool'];witness=list(bits)
    return {'pool':best,'phases':witness,'assignments':1<<g}
