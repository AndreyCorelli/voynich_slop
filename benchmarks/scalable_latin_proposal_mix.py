"""Target-independent proposal mixture; full vocabulary and objective unchanged."""
import json
import argparse
from benchmarks.scalable_latin_caesar import ROOT as ORIGINAL, write, measure
from benchmarks.scalable_latin_search_budget import audit
from benchmarks.scalable_english_run import run
from voynich_smt.word_mapping.scalable.retrieval import RetrievalConfig
from voynich_smt.word_mapping.scalable.search import SearchConfig

ROOT=ORIGINAL.parent/'proposal-mix-v1'
RESOURCES=ORIGINAL/'resources'
FIXTURE=ORIGINAL/'fixture'


def main():
    parser=argparse.ArgumentParser(__doc__)
    parser.add_argument('variant',choices=('mixture','joint'),nargs='?',default='mixture')
    variant=parser.parse_args().variant
    root=ROOT if variant=='mixture' else ORIGINAL.parent/'joint-moves-v1'
    root.mkdir(parents=True,exist_ok=False)
    write(root/'design.json',{'scope':'No additional resource or target-specific information',
         'change':('Random candidate draws and exploration draws use 50% uniform observed forms, 50% uniform entire inventory'
                   if variant=='mixture' else 'Existing bounded three-word cycles on 10% of selected proposal steps'),
         'trace_scope':('All selected moves and pools; unselected internal joint-cycle trials are not logged' if variant=='joint' else 'All pools and selected moves'),
         'retained_support':'Every inventory form remains eligible; no hard filtering or guessed function-word list',
         'selection':'Fixed .5 mixture or .1 joint probability before their results; no truth supplied to search',
         'proposals':4000,'seeds':[3,5,7],'initializations':['random','frequency'],
         'objective':'unchanged','training':'unchanged','primary_anchor_rule':'unchanged unanimous public-frequency>=100',
         'timing':'Runs may overlap the independent budget experiment; wall-clock cost is not a matched performance comparison'})
    summaries={}
    for mode in ('random','frequency'):
        output=root/mode
        run(RESOURCES,FIXTURE/'public/cipher.json',output,seeds=(3,5,7),
            config=SearchConfig(initialization=mode,proposals=4000,budget_seconds=600,reserve_seconds=10,
                                joint_probability=.1 if variant=='joint' else 0.),
            retrieval=RetrievalConfig(total_entries=10000,attested_mix=.5 if variant=='mixture' else 0.),trace=True)
        measured=measure(RESOURCES,FIXTURE,output)
        support=audit(output,output/'support')
        old=json.loads((ORIGINAL/mode/'evaluation.json').read_text())
        new=json.loads((output/'evaluation.json').read_text())
        before=json.loads((ORIGINAL/mode/'protocol.json').read_text())
        after=json.loads((output/'protocol.json').read_text())
        before['retrieval'].setdefault('attested_mix',0.)
        if variant=='mixture':
            assert before['retrieval'].pop('attested_mix')==0.
            assert after['retrieval'].pop('attested_mix')==.5
        else:
            assert before['search'].pop('joint_probability')==0.
            assert after['search'].pop('joint_probability')==.1
        assert before==after
        assert all(r['steps']==4000 and r['stop_reason']=='proposal_limit' for r in new['runs'])
        comparison={'old_mean':old['mean_score_selected_token_accuracy'],'new_mean':new['mean_score_selected_token_accuracy'],
                    'old_selected':old['selected_token_accuracy'],'new_selected':new['selected_token_accuracy'],
                    'paired_changes':[{'seed':a['seed'],'before':a['score_selected_best']['token_accuracy'],
                                       'after':b['score_selected_best']['token_accuracy']}
                                      for a,b in zip(old['runs'],new['runs'])],
                    'old_anchors':json.loads((ORIGINAL/mode/'anchors-evaluation.json').read_text())['primary'],
                    'new_anchors':json.loads((output/'anchors-evaluation.json').read_text())['primary']}
        summaries[mode]={'metrics':measured,'support':support,'comparison':comparison}
        write(root/'summary.json',summaries)
        print('COMPLETED',mode,json.dumps(comparison),flush=True)


if __name__=='__main__':main()
