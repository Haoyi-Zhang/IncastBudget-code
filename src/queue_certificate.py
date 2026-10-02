#!/usr/bin/env python3
"""Local exact queue admission and two-tenant optimality certificate interface."""
from pathlib import Path
from fractions import Fraction
import argparse
import json
import sys
from exact import rational
from queues import Burst,validate,shadow_fast,shadow_reference,witness
from allocation import optimize_two,verify_two


def encode(value):
    if isinstance(value,Fraction):return str(value)
    if isinstance(value,(tuple,list)):return [encode(v) for v in value]
    if isinstance(value,dict):return {k:encode(v) for k,v in value.items()}
    return value


def pairs(items):
    out={}
    for k,v in items:
        if k in out:raise ValueError('duplicate JSON key')
        out[k]=v
    return out


def load(path):
    if path.stat().st_size>2*1024**2:raise ValueError('input exceeds 2 MiB local-interface limit')
    def bad(value):raise ValueError('non-finite JSON number')
    return json.loads(path.read_text(encoding='utf-8'),object_pairs_hook=pairs,parse_constant=bad)


def instance(data):
    bs=[Burst(**v) for v in data['bursts']]
    if len(bs)>10000:raise ValueError('local-interface burst limit exceeded')
    rates=[rational(v) for v in data['rates']];validate(bs,rates)
    C=rational(data['capacity']);floors=[rational(v) for v in data['floors']]
    if len(floors)!=len(rates) or C<0 or any(v<0 for v in floors):raise ValueError('invalid capacity/floors')
    if sum(rates)>C or any(r<g for r,g in zip(rates,floors)):raise ValueError('rates violate service contract')
    return bs,rates,C,floors


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=['check','optimize','verify'])
    p.add_argument('input',type=Path)
    p.add_argument('certificate',type=Path,nargs='?')
    p.add_argument('--output',type=Path)
    p.add_argument('--rows-output',type=Path,
                   help='for check only: stream full q/p rows as JSON Lines')
    args=p.parse_args()
    row_temp=None;row_handle=None
    try:
        if args.rows_output is not None and args.action!='check':
            raise ValueError('--rows-output is valid only with check')
        bs,rates,C,floors=instance(load(args.input))
        if args.action=='check':
            sink=None
            if args.rows_output is not None:
                if args.output is not None and args.output.resolve()==args.rows_output.resolve():
                    raise ValueError('--output and --rows-output must differ')
                args.rows_output.parent.mkdir(parents=True,exist_ok=True)
                row_temp=args.rows_output.with_name(args.rows_output.name+'.tmp')
                row_handle=row_temp.open('w',encoding='utf-8')
                def sink(row):
                    t,q,pending,total=row
                    payload={'time':t,'q':encode(q),'pending':encode(pending),'pool':encode(total)}
                    row_handle.write(json.dumps(payload,separators=(',',':'))+'\n')
            out=shadow_fast(bs,rates)
            ref=shadow_reference(bs,rates,row_sink=sink)
            if out['pool']!=ref['pool'] or out['private']!=ref['private']:
                raise ArithmeticError('producer/checker mismatch')
            if row_handle is not None:
                row_handle.close();row_handle=None
                row_temp.replace(args.rows_output);row_temp=None
            out['attaining_releases']=witness(bs,out['time'])
            out['checker']={'row_count':ref['row_count'],
                            'event_times':ref['storage']['event_times'],
                            'sparse_event_entries':ref['storage']['sparse_event_entries'],
                            'state_vector_entries':ref['storage']['state_vector_entries'],
                            'event_index_entries':ref['storage']['event_index_entries'],
                            'working_entry_upper_bound':ref['storage']['working_entry_upper_bound'],
                            'rows_materialized':False}
            if args.rows_output is not None:
                out['row_stream']={'format':'jsonl','rows':ref['row_count'],
                                   'path':str(args.rows_output)}
            out['model']='independent-windows-fixed-reservations'
        elif args.action=='optimize':
            if len(bs)>32:raise ValueError('bounded optimizer accepts at most 32 bursts')
            out=optimize_two(bs,C,floors)['certificate']
        else:
            if args.certificate is None:raise ValueError('verify requires a certificate file')
            verify_two(bs,C,floors,load(args.certificate))
            out={'valid':True,'model':'independent-windows-fixed-reservations',
                 'scope':'two-tenant exact optimum'}
        text=json.dumps(encode(out),indent=2)+'\n'
        if args.output:
            args.output.parent.mkdir(parents=True,exist_ok=True)
            args.output.write_text(text,encoding='utf-8')
        else:print(text,end='')
    except (ValueError,KeyError,TypeError,OSError,ArithmeticError) as exc:
        if row_handle is not None:row_handle.close()
        if row_temp is not None:row_temp.unlink(missing_ok=True)
        print(f'error: {exc}',file=sys.stderr);return 2
    return 0


if __name__=='__main__':
    raise SystemExit(main())
