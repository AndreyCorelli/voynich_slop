"""Contextual-profile starts and skip-association alignment on frozen Latin inputs."""
from collections import Counter
import gzip
import json
from pathlib import Path
import shutil
import time

from benchmarks.scalable_latin_caesar import ROOT as ORIGINAL, frozen_documents, write, measure
from benchmarks.scalable_english_run import run
from voynich_smt.data.corpus import digest
from voynich_smt.word_mapping.scalable.association import AssociationModel, pair_counts
from voynich_smt.word_mapping.scalable.data import CipherStream
from voynich_smt.word_mapping.scalable.inventory import Inventory
from voynich_smt.word_mapping.scalable.profiles import PROFILE_VERSION, NEIGHBORS, JITTER
from voynich_smt.word_mapping.scalable.search import SearchConfig, peak_rss
from voynich_smt.word_mapping.scalable.trigram import load_model

ROOT=ORIGINAL.parent/'profiles-association-v1'
RESOURCES=ORIGINAL/'resources'
FIXTURE=ORIGINAL/'fixture'
VARIANTS=('profile_lm','association_random','association_profile')


def build_association(output):
    """Independent resource builder: no target/cipher/truth argument or read."""
    started=time.monotonic();output.mkdir(parents=True,exist_ok=False)
    for name in ('inventory.sqlite','protocol.json','training-pos.json'):
        shutil.copyfile(RESOURCES/name,output/name)
    inventory=Inventory(output/'inventory.sqlite')
    try:
        bigram=load_model(RESOURCES/'model.sqlite',inventory)
        pairs=Counter()
        for document in frozen_documents(RESOURCES):
            pairs.update(pair_counts(tuple(inventory.id(w) for w in document),(1,2,4)))
        model=AssociationModel(bigram,pairs)
        model.save(output/'model.sqlite')
        report=json.loads((RESOURCES/'report.json').read_text())
        report.update(model_sha256=model.identity,parent_model_sha256=bigram.identity,
                      objective='skip-association-v1',distances=model.distances,clip=model.clip,shrinkage=model.shrinkage,
                      association_edges=len(pairs),association_pair_occurrences=sum(pairs.values()),
                      resource_build_seconds=time.monotonic()-started,peak_rss_bytes=peak_rss())
        report['limitations']+=['Skip-association score is an unnormalized graph discrepancy, not a log likelihood.',
                               'Existing adjacent-LM retrieval remains a heuristic proposal generator.']
        write(output/'report.json',report)
        return report
    finally: inventory.close()


def shortlist_evaluate(resources,root):
    """Truth-derived reports only; cannot influence already-completed inference."""
    anchors=json.loads((root/'anchors-evaluation.json').read_text())
    inference=json.loads((root/'inference.json').read_text())
    stream=CipherStream.load(root/'public/cipher.json')
    truth=json.loads((FIXTURE/'evaluation-only/truth.json').read_text())
    assert truth['public_sha256']==stream.identity==inference['protocol']['cipher_sha256']
    counts=Counter(c for d in stream.documents for c in d)
    inventory=Inventory(resources/'inventory.sqlite')
    try:
        assert inventory.identity==inference['protocol']['inventory_sha256']
        initial=[]
        for saved in inference['runs']:
            with gzip.open(root/f"traces/seed-{saved['seed']}.jsonl.gz",'rt') as handle:
                event=json.loads(next(handle))
            assert event['kind']=='initial';initial.append(event['assignments'])
        initial_rows=[]
        for c in counts:
            votes=Counter(key[c] for key in initial)
            word,count=min(votes.items(),key=lambda p:(-p[1],p[0]))
            original=truth['decoding'][c];predicted=inventory.word(word)
            initial_rows.append({'cipher':c,'votes':count,'count':counts[c],
                                 'original':original,'proposed':predicted,'correct':original==predicted})
        def metrics(rows):
            n=len(rows);tokens=sum(r['count'] for r in rows)
            correct=[r for r in rows if r['correct']]
            return {'types':n,'correct_types':len(correct),'type_precision':len(correct)/n if n else None,
                    'tokens':tokens,'token_precision':sum(r['count'] for r in correct)/tokens if tokens else None,
                    'votes_histogram':dict(Counter(r['votes'] for r in rows)),
                    'duplicate_predictions':n-len({r['proposed'] for r in rows})}
        def ranked(rows):return sorted(rows,key=lambda r:(-r['votes'],-r['count'],r['cipher']))
        rows=ranked(anchors['rows']);initial_rows=ranked(initial_rows)
        report={'scope':'Post-hoc literal word-type accuracy; agreement is uncalibrated',
                'ranking':'Descending votes, descending public occurrence count, ascending cipher ID',
                'shortlists':{str(k):{**metrics(rows[:k]),'rows':rows[:k]} for k in (10,20,50)},
                'majority_only':{str(k):metrics([r for r in rows if r['votes']>=2][:k]) for k in (10,20,50)},
                'initial_shortlists':{str(k):metrics(initial_rows[:k]) for k in (10,20,50)},
                'initial_unanimous_types':sum(r['votes']==3 for r in initial_rows),
                'initial_unanimous_frequent_types':sum(r['votes']==3 and r['count']>=100 for r in initial_rows),
                'primary_anchors':anchors['primary'],
                'limits':['Profiles share model/features across starts; jitter does not remove shared bias.',
                          'Vote-1 padded shortlists can contain conflicting assignments and are not high-confidence dictionaries.']}
        write(root/'shortlists-evaluation.json',report);return report
    finally:inventory.close()


def objective_diagnostics(resources,root):
    """Evaluation-only feasible reference and public uninformative-key control."""
    from itertools import islice
    from benchmarks.scalable_english_objective_reference import reference
    from voynich_smt.word_mapping.scalable.state import DictionaryState
    from voynich_smt.word_mapping.scalable.incremental import full_score
    result={'reference':reference(resources,root/'public/cipher.json',FIXTURE/'evaluation-only/truth.json')}
    inventory=Inventory(resources/'inventory.sqlite')
    try:
        model=load_model(resources/'model.sqlite',inventory)
        stream=CipherStream.load(root/'public/cipher.json')
        unused=list(islice((w for w in range(model.size) if not model.counts[w]),stream.type_count))
        if len(unused)==stream.type_count:
            result['all_untrained_key_score']=full_score(model,stream,DictionaryState.create(stream,model,unused))
            result['null_scope']='Public control: injective assignments entirely to training-unobserved forms; not a recovery result.'
        inference=json.loads((root/'inference.json').read_text())
        result['best_found_score']=max(r['best_score'] for r in inference['runs'])
        result['limits']='Reference uses truth only after search; neither control is an inference input or an optimum bound.'
        write(root/'objective-diagnostics.json',result)
        return result
    finally:inventory.close()


def main():
    ROOT.mkdir(parents=True,exist_ok=False)
    design={'scope':'Same complete inventory, same source texts, same cipher; no target labels/topic hints in inference',
            'variants':VARIANTS,'seeds':[3,5,7],'proposals':4000,'budget_seconds_per_chain':600,
            'profile':{'version':PROFILE_VERSION,'neighbors':NEIGHBORS,'jitter':JITTER,
                       'features':'frequency + directional diversity, entropy, mean neighbor frequency, common-neighbor fraction',
                       'normalization':'Separate within-corpus feature midrank percentiles; frequency dimension half-weighted',
                       'matching':'64 nearest observed-form profiles, greedy injective matching high-frequency first; full-range fallback',
                       'restriction':'Initialization only; full inventory remains eligible for all subsequent search'},
            'association':{'distances':[1,2,4],'clip':3.,'shrinkage':5.,
                           'value':'clip(log((observed_pairs+1)/(independent_expected_pairs+1)), -3, 3)',
                           'objective':'-sum n/(n+5) * (target_association-source_association)^2 over observed skip pairs',
                           'boundaries':'Never cross actual document endpoints; no sentence boundaries supplied',
                           'retrieval':'Unchanged original adjacent-LM candidate retrieval'},
            'primary_metrics':'Top 10/20/50 agreement-first type precision + original unanimous/count>=100 anchors',
            'comparison':'All variants retained; no selection of a best seed/objective using truth',
            'limitations':'Exploratory development on previously inspected Caesar, not blind confirmation or calibrated confidence'}
    write(ROOT/'design.json',design)
    report=build_association(ROOT/'association-resources')
    print('RESOURCES',json.dumps({k:report[k] for k in ('association_edges','association_pair_occurrences','resource_build_seconds')}),flush=True)
    summaries={}
    # Re-score only shortlists for original controls; search keys remain untouched.
    for mode in ('random','frequency'):
        shortlist=shortlist_evaluate(RESOURCES,ORIGINAL/mode)
        summaries[f'baseline_{mode}']={'top50':shortlist['shortlists']['50']['type_precision'],
                                     'anchors':shortlist['primary_anchors']}
    write(ROOT/'summary.json',summaries)
    for name in VARIANTS:
        resources=RESOURCES if name=='profile_lm' else ROOT/'association-resources'
        initialization='random' if name=='association_random' else 'profile'
        output=ROOT/name
        run(resources,FIXTURE/'public/cipher.json',output,seeds=(3,5,7),
            config=SearchConfig(initialization=initialization,proposals=4000,budget_seconds=600,reserve_seconds=10),trace=True)
        measured=measure(resources,FIXTURE,output)
        shortlist=shortlist_evaluate(resources,output)
        inference=json.loads((output/'inference.json').read_text())
        if not all(r['step']==4000 and r['stop_reason']=='proposal_limit' for r in inference['runs']):
            raise ValueError('Incomplete fixed-proposal run')
        diagnostics=objective_diagnostics(resources,output)
        summaries[name]={'objective_diagnostics':diagnostics,'metrics':measured,'type_precision':{k:v['type_precision'] for k,v in shortlist['shortlists'].items()},
                         'initial_type_precision':{k:v['type_precision'] for k,v in shortlist['initial_shortlists'].items()},
                         'initial_unanimous_types':shortlist['initial_unanimous_types'],
                         'search_seconds':sum(r['elapsed_seconds'] for r in inference['runs']),
                         'peak_rss_bytes':max(r['peak_rss_bytes'] for r in inference['runs']),
                         'inference_sha256':digest(inference)}
        write(ROOT/'summary.json',summaries)
        print('COMPLETED',name,json.dumps(summaries[name]),flush=True)


if __name__=='__main__':main()
