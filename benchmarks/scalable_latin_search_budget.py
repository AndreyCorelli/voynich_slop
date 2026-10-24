"""Target-independent search-budget experiment; truth is used only for post-hoc audits.

Resources, inventory and cipher are unchanged. No topic selection, target-word
filtering, inferred anchors or grammatical labels are supplied to search.
"""
from collections import Counter
import json
from pathlib import Path

from benchmarks.scalable_latin_caesar import ROOT as ORIGINAL, search, measure, write
from benchmarks.scalable_english_diagnostics import analyze
from benchmarks.scalable_english_diagnostics_validate import validate
from voynich_smt.data.corpus import digest

ROOT=ORIGINAL.parent/'search-budget-v1'
RESOURCES=ORIGINAL/'resources'
FIXTURE=ORIGINAL/'fixture'


def support_summary(report):
    result={}
    for seed,data in report['attribution'].items():
        rows=data['rows']
        def summarize(selected):
            total=sum(r['count'] for r in selected)
            return {'types':len(selected),'tokens':total,
                    'flags':{flag:{'types':sum(r[flag] for r in selected),
                                   'tokens':sum(r['count'] for r in selected if r[flag])}
                             for flag in ('visited','offered','active','proposed','accepted','ever_correct')},
                    'categories':dict(Counter(r['category'] for r in selected))}
        result[seed]={'all':summarize(rows),'frequent_100_plus':summarize([r for r in rows if r['count']>=100]),
                      'visited_types':data['visited_types'],'pool_evaluations':data['offered_evaluations'],
                      'correct_assignment_displacements':sum(r['correct_assignment_displacements'] for r in rows)}
    return result


def audit(root, output):
    truth=FIXTURE/'evaluation-only/truth.json'
    report=analyze(RESOURCES,root,truth,root/'traces',output)
    checked=validate(RESOURCES,root,truth,root/'traces',output)
    assert checked['status']=='validated'
    return support_summary(report)


def compare(control, candidate):
    old=json.loads((control/'evaluation.json').read_text())
    new=json.loads((candidate/'evaluation.json').read_text())
    before=json.loads((control/'protocol.json').read_text())
    after=json.loads((candidate/'protocol.json').read_text())
    before['retrieval'].setdefault('attested_mix',0.0)
    after['retrieval'].setdefault('attested_mix',0.0)
    assert before['search']['proposals']==4000 and after['search']['proposals']==20000
    before['search'].pop('proposals'); after['search'].pop('proposals')
    assert before==after, 'Changed something beyond proposal horizon'
    assert all(r['steps']==20000 and r['stop_reason']=='proposal_limit' for r in new['runs'])
    return {'old_mean':old['mean_score_selected_token_accuracy'],
            'new_mean':new['mean_score_selected_token_accuracy'],
            'old_selected':old['selected_token_accuracy'],'new_selected':new['selected_token_accuracy'],
            'paired_changes':[{'seed':a['seed'],
                              'before':a['score_selected_best']['token_accuracy'],
                              'after':b['score_selected_best']['token_accuracy'],
                              'change':b['score_selected_best']['token_accuracy']-a['score_selected_best']['token_accuracy']}
                              for a,b in zip(old['runs'],new['runs'])],
            'old_anchors':json.loads((control/'anchors-evaluation.json').read_text())['primary'],
            'new_anchors':json.loads((candidate/'anchors-evaluation.json').read_text())['primary']}


def main():
    ROOT.mkdir(parents=True,exist_ok=False)
    design={'scope':'No target-specific knowledge added; fixed original resources and full inventory.',
            'proposals_before':4000,'proposals_after':20000,'seeds':[3,5,7],
            'initializers':['random','frequency'],'budget_seconds_per_chain':600,
            'comparison':'Fresh runs with identical settings except a longer proposal/annealing horizon; not checkpoint continuation.',
            'primary_anchor_rule':'Unanimous three-run agreement and public frequency >=100, unchanged.',
            'input_hashes':{mode:digest(json.loads((ORIGINAL/mode/'inference.json').read_text())) for mode in ('random','frequency')},
            'forbidden_inputs':['Target vocabulary filtering','Topic-matched model selection','Handpicked function words','Truth or annotations as search input','Frozen inferred anchors'],
            'diagnostics':'Truth used only for evaluation of existing candidate traces and newly completed runs.'}
    write(ROOT/'design.json',design)
    baseline={}
    for mode in ('random','frequency'):
        baseline[mode]=audit(ORIGINAL/mode,ROOT/f'baseline-support-{mode}')
    write(ROOT/'baseline-support.json',baseline)
    print('BASELINE SUPPORT',json.dumps(baseline),flush=True)
    summaries={}
    for mode in ('random','frequency'):
        output=ROOT/mode
        search(RESOURCES,FIXTURE,output,initialization=mode,proposals=20000,budget=600)
        measured=measure(RESOURCES,FIXTURE,output)
        support=audit(output,output/'support')
        summaries[mode]={'metrics':measured,'comparison':compare(ORIGINAL/mode,output),'support':support}
        write(ROOT/'summary.json',summaries)
        print('COMPLETED',mode,json.dumps(summaries[mode]['comparison']),flush=True)


if __name__=='__main__': main()
