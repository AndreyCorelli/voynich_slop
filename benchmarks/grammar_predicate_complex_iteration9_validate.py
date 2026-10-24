"""Independent quotient-tree reference checks, refits and forest verification."""
from collections import Counter
from copy import deepcopy
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
from unittest.mock import patch
import numpy as np
from benchmarks.grammar_predicate_complex_iteration9 import OUT,PREVIOUS,source_references,audit_summary,scored_candidates
from benchmarks.grammar_markers_iteration5 import marker_sentences,marker_grouped,marker_metrics,aggregate_markers,TREEBANKS
from benchmarks.grammar_training_alignment_iteration7 import vocabulary_for,marker_groups,parent_groups,FixedMarkers
from benchmarks.grammar_training_alignment_iteration7_validate import same_model,paired_interval
from benchmarks.grammar_marker_oracle_iteration6 import OracleMarkerProvider,score_audit
from benchmarks.grammar_structure_iteration3_validate import FrozenAdapter
from benchmarks.grammar_boundary_role_iteration8 import CONDITIONS,masked_options,solve_options,summarize_rows,diagnostic_counts
from benchmarks.grammar_linker_iteration4 import detailed_metrics,summarize
from voynich_smt.parent_ranking import ConditionalRanker,choices
from voynich_smt.marker_structure import MarkerModel,infer_attached_links,validate_markers
from voynich_smt.predicate_structure import validate_structure
from voynich_smt.data.corpus import digest,write_json


def quotient_reference(s,deprels):
    """Independent edge contraction, then traversal of the quotient UD tree."""
    n=len(s['tokens']);finite=set(s['finite']);aux=Counter()
    for i in finite:
        if s['upos'][i]=='AUX' and deprels[i].split(':')[0] in ['aux','cop'] and s['heads'][i] is not None:
            aux[s['heads'][i]]+=1
    component=list(range(n))
    for i in finite:
        h=s['heads'][i]
        if s['upos'][i]=='AUX' and deprels[i].split(':')[0] in ['aux','cop'] and h is not None and aux[h]==1 and h not in finite and (s['upos'][h] in ['VERB','AUX'] or deprels[i].split(':')[0]=='cop'):
            component[i]=h
    representative={component[i]:i for i in finite}
    parent={};label={}
    for i,h in enumerate(s['heads']):
        if h is None or component[i]!=(component[h]):
            parent[component[i]]=None if h is None else component[h];label[component[i]]=deprels[i].split(':')[0]
    def ancestor(node,include=True):
        cursor=node if include else parent[node];seen=set()
        while cursor is not None:
            assert cursor not in seen;seen.add(cursor)
            if cursor in representative:return representative[cursor]
            cursor=parent[cursor]
        return None
    parents={};relations={}
    for i in sorted(finite):
        c=component[i];p=ancestor(c,False);parents[i]=p
        labels=[];cursor=c
        while cursor is not None and (cursor==c or cursor not in representative):
            labels.append(label[cursor]);cursor=parent[cursor]
        relations[i]='root' if p is None else 'coordination' if 'conj' in labels else 'subordination'
    markers={}
    for i in range(n):
        dep=deprels[i].split(':')[0];h=s['heads'][i]
        if dep in ['mark','cc'] and h is not None and component[h] in representative:
            markers[i]={'target':representative[component[h]],'kind':'coordination' if dep=='cc' else 'subordination'}
        elif s['upos'][i] in ['PRON','DET'] and s['features'][i].get('PronType')=='Rel':
            target=ancestor(component[i])
            if target is not None:markers[i]={'target':target,'kind':'relative'}
    return {'parents':parents,'relations':relations,'markers':markers,'anchors':[ancestor(component[i]) for i in range(n)]}


def run():
    load=lambda p:json.loads(p.read_text());manifest=load(OUT/'manifest.json');report=load(OUT/'report.json')
    assert digest(manifest)==report['manifest_sha256']
    for p,h in {**manifest['input_sha256'],**manifest['code_sha256']}.items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h
    path=TREEBANKS/'proiel-r2.17/la_proiel-ud-train.conllu';assert hashlib.sha256(path.read_bytes()).hexdigest()==manifest['source_sha256']
    previous_validation=load(PREVIOUS/'validation.json');assert previous_validation['validated']
    for n,h in previous_validation['artifact_sha256'].items():assert hashlib.sha256((PREVIOUS/n).read_bytes()).hexdigest()==h
    sentences,streams,audits=source_references()
    assert json.loads(json.dumps(audits))==load(OUT/'projection-audit.json') and audit_summary(audits)==report['audit']
    for split in streams:assert json.loads(json.dumps(streams[split]))==load(OUT/(split+'-truth.json'))
    # Build independent annotation references directly from quotient trees.
    original,_=marker_sentences(path,'proiel');old_byid={s['sent_id']:s for s in original};deps={}
    for block in path.read_text().split('\n\n'):
        sid=next((l.split(' = ',1)[1] for l in block.splitlines() if l.startswith('# sent_id = ')),None)
        if sid:deps[sid]=[l.split('\t')[7] for l in block.splitlines() if l and not l.startswith('#') and l.split('\t')[0].isdigit() and l.split('\t')[3]!='PUNCT']
    reference_checks=0
    for split,ss in sentences.items():
        assert [s['sent_id'] for s in ss]==manifest['source_split_ids'][split]
        for s in ss:
            independent=quotient_reference(old_byid[s['sent_id']],deps[s['sent_id']])
            for k,v in independent.items():assert s[k]==v,(s['sent_id'],k)
            reference_checks+=1
    regression=next(s for s in sentences['development'] if s['sent_id']=='13305')
    assert regression['parents'][13]==9 and regression['markers'][11]['target']==13 and regression['markers'][5]['target']==9
    for a,b in [('train','development'),('train','confirmation'),('development','confirmation')]:
        assert not set(manifest['source_split_ids'][a])&set(manifest['source_split_ids'][b])
    admitted={split:{s['sent_id'] for stream in ss for s in stream['sentences']} for split,ss in streams.items()}
    admitted_audit=audit_summary({split:[c for c in cc if c['sent_id'] in admitted[split]] for split,cc in audits.items()})
    adapter=FrozenAdapter(load(PREVIOUS/'morphology-lattice.json'));raw=load(OUT/'models.json');vocab=vocabulary_for(streams['train'])
    assert vocab==raw['marker_vocabulary']
    marker_ranker=ConditionalRanker.fit_groups(marker_groups(streams['train'],vocab,adapter));same_model(marker_ranker,raw['marker'])
    marker=MarkerModel(vocab,marker_ranker);folds=manifest['fold_by_training_stream'];oof=load(OUT/'oof-markers.json');fits=1
    assert folds==load(PREVIOUS/'manifest.json')['fold_by_training_stream']
    for fold in load(OUT/'crossfit-models.json'):
        fit=[i for i,f in enumerate(folds) if f!=fold['fold']];held=[i for i,f in enumerate(folds) if f==fold['fold']]
        assert fit==fold['fitting_streams'] and held==fold['held_streams'] and not set(fit)&set(held)
        local=vocabulary_for([streams['train'][i] for i in fit]);assert local==fold['vocabulary']
        ranker=ConditionalRanker.fit_groups(marker_groups([streams['train'][i] for i in fit],local,adapter));same_model(ranker,fold['model'])
        provider=MarkerModel(local,ranker)
        for i in held:assert provider.predict(streams['train'][i]['tokens'],streams['train'][i]['finite'],adapter)==oof[i]
        fits+=1
    gold_attached=[OracleMarkerProvider(marker,s['markers'],'oracle_full').predict(s['tokens'],s['finite'],adapter) for s in streams['train']]
    models={};legacy=load(PREVIOUS/'models.json')
    for name,attached in [('gold',gold_attached),('oof',oof)]:
        groups=parent_groups(streams['train'],attached,adapter);assert len(groups)==raw['group_counts'][name]==1385
        ranker=ConditionalRanker.fit_groups(groups);same_model(ranker,raw['parents']['revised_'+name]);fits+=1
        models['revised_'+name]=ConditionalRanker(**raw['parents']['revised_'+name])
        assert raw['parents']['legacy_'+name]==legacy['parents'][name]
        models['legacy_'+name]=ConditionalRanker(**raw['parents']['legacy_'+name])
    assert fits==report['models_refit']==7
    print('Independent quotient projection and seven model refits verified',flush=True)
    rows=load(OUT/'predictions.json');oldrows=load(PREVIOUS/'predictions.json')
    templates={(r['split'],r['stream']):r['prediction'] for r in oldrows if r['training_markers']=='gold' and r['evaluation_markers']=='gold'}
    scored={};index={};gaps={};checked=0
    for row in rows:
        identity=(row['split'],row['stream'],row['model'],row['markers']);key=identity+(row['condition'],)
        assert key not in index;index[key]=row
        gold=streams[row['split']][row['stream']]
        if identity not in scored:
            provider=marker if row['markers']=='predicted' else OracleMarkerProvider(marker,gold['markers'],'oracle_full')
            scored[identity]=scored_candidates(templates[row['split'],row['stream']],gold,adapter,models[row['model']],provider)
        base=scored[identity];bounds,roles=CONDITIONS[row['condition']]
        expected=solve_options(base,masked_options(base,gold,bounds,roles));saved=row['prediction']
        # Comparing integer optima permits different witnesses at a tied optimum.
        assert expected['forest_score_integer']==saved['forest_score_integer']
        validate_structure(saved);validate_markers(saved,None)
        assert saved['marker_attachments']==expected['marker_attachments'] and saved['predicates']==gold['finite']
        for c,opts in saved['arc_candidates'].items():
            assert opts==expected['arc_candidates'][int(c)]
        selected_score=sum(round(next(r['logit'] for r in saved['arc_candidates'][c] if r['parent']==p and r['relation']==saved['relations'][c])*1e6) for c,p in saved['parents'].items())
        assert selected_score==saved['forest_score_integer']
        assert score_audit(saved,gold)==row['audit'] and row['audit']['reference_forest_available']
        assert detailed_metrics(saved,gold)==row['metrics']
        assert diagnostic_counts(saved,gold)==row['diagnostic']
        assert marker_metrics(saved,gold,vocab)==row['marker_metrics']
        gaps[key]=row['audit']['optimum_minus_reference_integer'];checked+=1
    assert checked==report['conditions']==4224
    for identity in scored:
        g=lambda mode:gaps[identity+(mode,)]
        assert 0<=g('both')<=g('boundaries')<=g('unrestricted') and g('both')<=g('roles')<=g('unrestricted')
    for s in report['summary']:
        rr=[r for r in rows if all(r[k]==s[k] for k in ['split','model','markers','condition'])]
        assert summarize_rows(rr)=={k:s[k] for k in ['metrics','diagnostic','reference_strictly_outscored','reference_tied']}
        assert aggregate_markers([r['marker_metrics'] for r in rr])==s['marker_metrics']
    for s in report['unchanged_prediction_rescoring']:
        rr=[r for r in oldrows if (r['split'],'legacy_'+r['training_markers'],r['evaluation_markers'])==(s['split'],s['model'],'gold')]
        truth=load(PREVIOUS/(s['split']+'-truth.json')) if s['evaluation_reference']=='legacy' else streams[s['split']]
        assert summarize([detailed_metrics(r['prediction'],truth[r['stream']]) for r in rr])==s['metrics']
    # Cross-check exact Edmonds solutions with Z3 on previously reviewed streams.
    reviewed=load(Path('experiments/results/grammar-restoration/iteration8/review-cases.json'))
    selected=sorted({(c['split'],c['stream']) for c in reviewed});z3_checks=0
    for split,stream in selected:
        gold=streams[split][stream]
        for evidence in ['gold','predicted']:
            for mode in CONDITIONS:
                pred=index[split,stream,'revised_gold',evidence,mode]['prediction']
                allowed={int(c):{(r['parent'],r['relation']) for r in opts} for c,opts in pred['arc_candidates'].items()}
                def restricted(tokens,child,predicates,morph,**kwargs):
                    return [r for r in choices(tokens,child,predicates,morph,**kwargs) if (r['parent'],r['relation']) in allowed[child]]
                with patch('voynich_smt.parent_ranking.choices',restricted):
                    actual=infer_attached_links(gold['tokens'],gold['finite'],adapter,models['revised_gold'],FixedMarkers(pred['marker_attachments']),timeout_ms=10000)
                assert actual['status']=='optimal' and actual['forest_score_integer']==pred['forest_score_integer'],(split,stream,evidence,mode)
                z3_checks+=1
    review=load(OUT/'review.json')
    assert hashlib.sha256(Path('benchmarks/grammar_predicate_complex_iteration9_review.py').read_bytes()).hexdigest()==review['code_sha256']
    assert len(review['previous_cases'])==17 and review['previous_cases_relabeled_to_old_prediction']==1
    assert review['previous_cases_correct_under_revised_model']==1 and review['residuals']==21
    actual_residuals={(r['stream'],c['child']) for r in rows if (r['split'],r['model'],r['markers'],r['condition'])==('development','revised_gold','gold','both') for c in r['audit']['per_child'] if c['error']!='correct_parent'}
    assert actual_residuals=={(c['stream'],c['child']) for c in review['remaining_residuals']}
    intervals=[]
    for name in ['gold','oof']:
        for evidence in ['gold','predicted']:
            for mode in ['unrestricted','both']:
                select=lambda version:[r for r in rows if (r['split'],r['model'],r['markers'],r['condition'])==('confirmation',version+'_'+name,evidence,mode)]
                a,b=select('legacy'),select('revised');assert [r['stream'] for r in a]==[r['stream'] for r in b]
                intervals.append({'training_markers':name,'evaluation_markers':evidence,'condition':mode,
                    'edge_f1':paired_interval(a,b,'edges'),'root_f1':paired_interval(a,b,'roots')})
    # With fixed relation labels, the marker-only block is constant across
    # possible parents, so its contribution cancels in parent ranking.
    invariant=0
    for split in ['development','confirmation']:
        for i in range(len(streams[split])):
            for name in models:
                for mode in ['roles','both']:
                    a=index[split,i,name,'gold',mode]['prediction'];b=index[split,i,name,'predicted',mode]['prediction']
                    assert a['parents']==b['parents'] and a['relations']==b['relations'];invariant+=1
    validation={'validated':True,'reference_version':manifest['reference_version'],'independent_quotient_reference_sentences':reference_checks,
        'source_models_refit':fits,'conditions':checked,'independent_Z3_conditions':z3_checks,'admitted_projection_audit':admitted_audit,
        'marker_evidence_invariant_fixed_role_forests':invariant,'paired_confirmation_intervals':intervals,
        'report_sha256':digest(report),'validator_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'artifact_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.glob('*.json') if p.name!='validation.json'},
        'checks':['frozen inputs','independent quotient-tree projection','same tokens/predicates/splits/folds',
            'fold-local marker fitting without held examples','seven independent source refits','common revised-reference evaluation',
            'candidate scores/masks, acyclicity, exact optimum/reference scores','all metric/label-only rescoring summaries',
            'nested reference-gap monotonicity','independent Z3 scores','fixed-role marker invariance']}
    write_json(OUT/'validation.json',validation)
    print('Validated',reference_checks,'sentence projections;',fits,'refits;',checked,'forests;',z3_checks,'Z3 checks.',flush=True)


if __name__=='__main__':run()
