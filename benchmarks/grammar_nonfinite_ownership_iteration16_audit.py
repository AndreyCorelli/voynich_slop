"""Readable audit of every primary ownership conflict/error and bridge change."""
from benchmarks.grammar_nonfinite_ownership_iteration16 import OUT,NINE,load,save
from benchmarks.grammar_relative_constituents_iteration15 import signature


def run():
    dev=load(NINE/'development-truth.json');truth={(t['stream'],t['position']):t for t in load(OUT/'evaluation-truth.json')}
    conflicts=[];wrong=[];relative=[]
    for row in load(OUT/'ownership.json'):
        if (row['mode'],row['boundaries'],row['arm'])!=('reference_scope','hidden','joint'):continue
        i=row['stream'];s=dev[i]
        for c in row['ownership']['components']:
            if c['satisfiable']:continue
            conflicts.append({'stream':i,'positions':c['positions'],'text':' '.join(s['tokens']),
                'records':[{'position':nf,'surface':s['tokens'][nf],
                    'candidate_parents':next(r['candidate_parents'] for r in row['ownership']['records'] if r['position']==nf),
                    'reference':truth.get((i,nf))} for nf in c['positions']]})
        for rec in row['ownership']['records']:
            ref=truth.get((i,rec['position']))
            if rec['status']=='unique' and (ref is None or rec['possible_parents']!=[ref['owner']]):
                wrong.append({'stream':i,'record':rec,'reference':ref,'text':' '.join(s['tokens'])})
    rows=load(OUT/'predictions.json');original={(r['stream'],r['marker']):r for r in rows if (r['mode'],r['boundaries'],r['arm'])==('reference_scope','hidden','original')}
    for r in rows:
        if (r['mode'],r['boundaries'],r['arm'])!=('reference_scope','hidden','joint'):continue
        old=original[r['stream'],r['marker']]
        if signature(old['result'])!=signature(r['result']) or old['result']['status']!=r['result']['status']:
            relative.append({'stream':r['stream'],'marker':r['marker'],'text':' '.join(dev[r['stream']]['tokens']),
                'old_chains':signature(old['result']),'new_chains':signature(r['result']),
                'old_status':old['result']['status'],'new_status':r['result']['status'],
                'rejected':r['result']['rejected']})
    save(OUT/'failure-audit.json',{'ownership_conflicts':conflicts,'wrong_selected_owners':wrong,'relative_changes':relative})
    print(f'{len(conflicts)} conflicting components; {len(wrong)} wrong firm owners; {len(relative)} changed relative cases')
    for c in conflicts:print(c['stream'],[(r['surface'],r['candidate_parents'],r['reference']['owner'] if r['reference'] else None) for r in c['records']])

if __name__=='__main__':run()
