"""Search a saved fixed-model sample for a minimal UNSAT prefix and contiguous conflict."""
import argparse
from dataclasses import asdict, replace
import json
from pathlib import Path
from time import perf_counter

from voynich_smt.data.corpus import digest, write_json
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.models.text import Text


def run(source, output, artifacts, budgets=(30000,120000), resume=False, comparisons_only=False):
    scaling=json.loads(source.read_text())
    original=HiddenRecoveryRequest.from_dict(json.loads(Path(scaling['experiments'][-1]['public_input']).read_text()))
    words=original.ciphertext.words
    report={'schema_version':1,'source_report':str(source),'source_sha256':digest(scaling),
            'fixed_model':scaling['fixed_model'],'budgets_ms':list(budgets),'experiments':[],
            'prefix':{},'conflict':{},'relaxations':[],'complete':False}
    if resume and output.exists():
        prior=json.loads(output.read_text())
        if prior['source_sha256']!=report['source_sha256']:
            raise ValueError('Resume requires identical source')
        if prior['complete'] and prior['budgets_ms']==list(budgets):
            return prior
        report=prior;report['complete']=False
        report['budgets_ms']=list(budgets)
    cache={}
    for e in report['experiments']:
        if e['result']['status']!='UNKNOWN':
            cache[(e['start'],e['end'],e['model'])]=e
    # Reuse independently recorded full-observation prefix outcomes.
    for e in scaling['experiments']:
        if e['result']['status']!='UNKNOWN':
            cache.setdefault((0,e['word_count'],'baseline'),{'start':0,'end':e['word_count'],
                'model':'baseline','result':e['result'],'public_input':e['public_input'],'reused':True})

    def checkpoint():
        write_json(output,report)

    def solve(start,end,model='baseline',modified=None):
        key=(start,end,model)
        if key in cache:
            return cache[key]
        template=modified or original
        for budget in budgets:
            previous=[e for e in report['experiments'] if
                      (e['start'],e['end'],e['model'])==key and e['timeout_ms']>=budget]
            if previous:
                row=previous[-1]
                continue
            request=replace(template,ciphertext=Text(words[start:end]),timeout_ms=budget)
            path=artifacts/'inputs'/f'{model}-start{start}-end{end}-ms{budget}.json'
            write_json(path,asdict(request))
            print(f'{model} words[{start}:{end}] timeout={budget}ms: constructing/checking',flush=True)
            begun=perf_counter();result=request.solve();wall=perf_counter()-begun
            row={'start':start,'end':end,'model':model,'timeout_ms':budget,'public_input':str(path),
                 'source_record_indices':scaling['maximum_sample']['record_indices'][start:end],
                 'request_sha256':digest(asdict(request)),'wall_seconds':wall,'result':asdict(result)}
            report['experiments'].append(row);checkpoint()
            print(f'  {result.status} check={result.runtime_seconds:.3f}s wall={wall:.3f}s',flush=True)
            if result.status!='UNKNOWN':
                cache[key]=row
                return row
        return row

    if comparisons_only:
        if not resume or not report['conflict']:
            raise ValueError('Comparisons-only requires a resumed boundary/suffix checkpoint')
        saved_prefix,saved_conflict=report['prefix'],report['conflict']
    lo=max(e['end'] for e in cache.values() if e['start']==0 and e['model']=='baseline'
           and e['result']['status']=='SAT')
    hi=min(e['end'] for e in cache.values() if e['start']==0 and e['model']=='baseline'
           and e['result']['status']=='UNSAT')
    unresolved=[]
    report['prefix']={'largest_verified_sat':lo,'smallest_proved_unsat':hi,
                      'minimality_proven':hi==lo+1,'unresolved_sizes':[]}
    while not comparisons_only and hi-lo>1:
        choices=[n for n in range(lo+1,hi) if n not in unresolved]
        if not choices:
            break
        # After a hard midpoint, try the boundary with more candidate pruning.
        middle=max(choices) if unresolved else min(choices,key=lambda n:abs(n-(lo+hi)/2))
        e=solve(0,middle)
        if e['result']['status']=='SAT':lo=middle
        elif e['result']['status']=='UNSAT':hi=middle
        else:unresolved.append(middle)
        report['prefix']={'largest_verified_sat':lo,'smallest_proved_unsat':hi,
                          'minimality_proven':hi==lo+1,'unresolved_sizes':[n for n in unresolved if lo<n<hi]}
        checkpoint()
    # Contiguous deletion preserves cycle semantics: initial phases can rotate
    # each inferred code order. Arbitrary word deletion would change counters.
    left,right=0,hi
    empty=solve(hi,hi)
    if empty['result']['status']!='SAT':
        raise RuntimeError('Empty block should inherit the existing SAT codebook')
    report['conflict']={'start':left,'end':hi,'words':[''.join(w) for w in words[left:hi]],
                        'source_record_indices':scaling['maximum_sample']['record_indices'][left:hi],
                        'shortest_unsat_suffix_proven':right==left+1,'unresolved_starts':[],
                        'semantics':'contiguous observed block with inferred initial cycle phase; not an arbitrary deletion core'}
    unresolved_starts=[]
    while not comparisons_only and right-left>1:
        choices=[n for n in range(left+1,right) if n not in unresolved_starts]
        if not choices:break
        middle=min(choices,key=lambda n:abs(n-(left+right)/2))
        e=solve(middle,hi)
        if e['result']['status']=='UNSAT':left=middle
        elif e['result']['status']=='SAT':right=middle
        else:unresolved_starts.append(middle)
        report['conflict']={'start':left,'end':hi,'words':[''.join(w) for w in words[left:hi]],
                            'source_record_indices':scaling['maximum_sample']['record_indices'][left:hi],
                            'shortest_unsat_suffix_proven':right==left+1,
                            'unresolved_starts':[n for n in unresolved_starts if left<n<right],
                            'semantics':'contiguous observed block with inferred initial cycle phase; not an arbitrary deletion core'}
        checkpoint()
    if comparisons_only:
        report['prefix'],report['conflict']=saved_prefix,saved_conflict
    from voynich_smt.models.settings import HomophoneSelection
    variants=[('free',replace(original,selection=HomophoneSelection())),
              ('word-reset',replace(original,selection=HomophoneSelection('cycle','word'))),
              ('h3',replace(original,bounds=replace(original.bounds,max_homophones=3))),
              ('l3',replace(original,bounds=replace(original.bounds,max_code_length=3)))]
    report['relaxations']=[]
    for name,request in variants:
        e=solve(0,hi,name,request)
        report['relaxations'].append({'name':name,'baseline_prefix_words':hi,'result':e['result'],
                                       'public_input':e['public_input']})
        checkpoint()
    report['complete']=True;checkpoint()
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,default=Path('experiments/results/sample-scaling.json'))
    p.add_argument('--output',type=Path,default=Path('experiments/results/unsat-boundary.json'))
    p.add_argument('--artifact-dir',type=Path,default=Path('data/generated/unsat-boundary'))
    p.add_argument('--budgets-ms',type=int,nargs='+',default=[30000,120000])
    p.add_argument('--resume',action='store_true')
    p.add_argument('--comparisons-only',action='store_true')
    args=p.parse_args()
    if not args.budgets_ms or any(n<=0 for n in args.budgets_ms):p.error('Timeout budgets must be positive')
    run(args.source,args.output,args.artifact_dir,tuple(args.budgets_ms),args.resume,args.comparisons_only)


if __name__=='__main__':main()
