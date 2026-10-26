"""Independent frozen-output, Case-only Cartesian scoring and word-profile null audit."""
import re,random,math
from collections import defaultdict,Counter
import numpy as np
from scipy.special import expit
from benchmarks.grammar_dante_case_transfer_iteration199 import OUT,COVER,MODELS,PREVIOUS,NAMES,SEEDS,Path,load,save,digest
from benchmarks.grammar_case_applicability_iteration180_review import independent_features,independent_evaluate,close
from benchmarks.grammar_consensus_core_iteration195_review import scalar_metrics
CASES={'Nom','Gen','Dat','Acc','Abl','Voc','Loc'}

def independent_scores(edges,cases):
    rows=[]
    for e in edges:
        total=valid=matched=cf=0;fractions=[]
        for f in e['frames']:
            fv=fm=0
            for i in f['a_positions']:
                for j in f['b_positions']:
                    total+=1
                    if cases[i] in CASES and cases[j] in CASES:fv+=1;fm+=int(cases[i]==cases[j])
            valid+=fv;matched+=fm
            if fv:cf+=1;fractions.append(fm/fv)
        rows.append(dict(a=e['a'],b=e['b'],shared_frames=e['shared_frames'],case_frames=cf,all_occurrence_pairs=total,case_occurrence_pairs=valid,matching_case_pairs=matched,frame_macro_case_agreement=sum(fractions)/len(fractions) if fractions else None,no_case_conflicts=matched==valid if valid else None))
    return rows

def run():
    assert not (OUT/'audit.json').exists();hashes=0
    for p,h in load(OUT/'design-freeze.json')['inputs'].items():assert digest(Path(p))==h;hashes+=1
    for p,h in load(OUT/'prediction-freeze.json').items():assert digest(OUT/p)==h;hashes+=1
    for folder in [COVER,MODELS,PREVIOUS]:
        for p,h in load(folder/'verification-manifest.json').items():assert digest(Path(p))==h;hashes+=1
    assert (OUT/'prediction-freeze.json').stat().st_mtime_ns <= (OUT/'case-references.json').stat().st_mtime_ns
    g=load(COVER/'graphs.json')['primary'];dd=g['descriptors'];ff=load(OUT/'features.json');close(independent_features(g['ids'],dd),ff)
    saved=load(OUT/'models.json');frozen=load(MODELS/'models.json');assert set(saved['models'])==set(NAMES);assert saved['source_authors']==['Aquinas','Caesar','Cicero','Jerome']
    refs=load(OUT.parent/'iteration193/development-references.json');prior=sum(sum(r['case_occurrence_pairs']>0 for r in refs[a])/len(refs[a]) for a in saved['source_authors'])/4;assert math.isclose(prior,saved['prior_probability'],abs_tol=1e-12)
    outputs=load(OUT/'outputs.json');selections=load(OUT/'selections.json');expectedlists={'all_candidates':list(range(len(dd)))}
    for name in NAMES:
        m=saved['models'][name];assert m==frozen['Tacitus'][name]==frozen['Palladius'][name];model=m['model'];raw=np.array([r['values'] for r in ff])[:,model['columns']];z=(raw-model['mean'])/model['scale']
        values=z@np.array(model['beta']) if m['kind']=='ranking_score' else expit(np.column_stack([np.ones(len(z)),z])@np.array(model['beta']));assert np.max(abs(values-outputs[name]))<1e-12
        for k in [10,20]:expectedlists[name+'/top'+str(k)]=[i for i,v in enumerate(outputs[name]) if sum(x>v for x in outputs[name])<k]
        if m['kind']=='probability':expectedlists[name+'/threshold']=[i for i,v in enumerate(outputs[name]) if v>=.5]
    assert outputs['prior']==[saved['prior_probability']]*len(dd);assert selections==expectedlists
    admitted=load(COVER/'admitted-sentences.json');wanted={(r['path'],r['sent_id']) for r in admitted};cases={};rawvalues=Counter()
    for path in sorted({r['path'] for r in admitted}):
        for block in Path(path).read_text().strip().split('\n\n'):
            lines=block.splitlines();sid=next((line.split('=',1)[1].strip() for line in lines if line.startswith('# sent_id =')),None)
            if (path,sid) not in wanted:continue
            for line in lines:
                # Capture ID and FEATS, skip other columns without using their values.
                match=re.match(r'^(\d+)\t(?:[^\t]*\t){4}([^\t]*)\t',line)
                if not match:continue
                fields=[p[5:] for p in match[2].split('|') if p.startswith('Case=')];raw=fields[0] if fields else '';rawvalues[raw]+=1;cases[(path,sid,int(match[1]))]=raw if raw in CASES else ''
    cc=[cases[tuple(p)] if p else '' for p in g['positions']];casefile=load(OUT/'case-references.json');assert casefile==dict(case_by_stream_position=cc,admitted_integer_rows=len(cases),raw_case_values=dict(rawvalues),pos_fields_decoded=False)
    rows=independent_scores(dd,cc);close(rows,load(OUT/'case-details.json'));y=[int(r['case_occurrence_pairs']>0) for r in rows];eligible=len({e[k] for e in dd for k in ['a','b']});metrics={name:scalar_metrics([rows[i] for i in ix],eligible) for name,ix in selections.items()};summary=load(OUT/'summary.json');close(metrics,summary['lists'])
    classification={name:independent_evaluate(y,values) for name,values in outputs.items() if name=='prior' or saved['models'][name]['kind']=='probability'};close(classification,load(OUT/'classification.json'));close(classification,summary['classification'])
    au={}
    for name,values in outputs.items():
        positive=[v for t,v in zip(y,values) if t];negative=[v for t,v in zip(y,values) if not t];au[name]=sum((p>n)+.5*(p==n) for p in positive for n in negative)/(len(positive)*len(negative)) if positive and negative else None
    close(au,summary['auc']);assert summary['candidate_pairs']==len(dd);assert summary['case_applicable_pairs']==sum(y);assert summary['eligible_candidate_endpoint_types']==eligible
    assert load(OUT/'selected-details.json')=={name:[dict(edge=i,**rows[i]) for i in ix] for name,ix in selections.items()}
    byword=defaultdict(list)
    for i,p in enumerate(g['positions']):
        if p:byword[g['ids'][i]].append(i)
    nulls=load(OUT/'word-profile-nulls.json');assert set(nulls)==set(map(str,SEEDS));nullmetrics={};groups=0
    for seed in SEEDS:
        rng=random.Random(seed);permuted=cc.copy()
        for word,positions in sorted(byword.items()):
            values=list(map(cc.__getitem__,positions));rng.shuffle(values);assert Counter(values)==Counter(cc[i] for i in positions)
            for position,value in zip(positions,values):permuted[position]=value
        nr=independent_scores(dd,permuted);nm={name:scalar_metrics([nr[i] for i in ix],eligible) for name,ix in selections.items()};close(nm,nulls[str(seed)]);nullmetrics[str(seed)]=nm;groups+=len(nm)
    comparisons={}
    for name,actual in metrics.items():
        comparisons[name]={}
        for key in ['edge_applicability','edge_macro_frame_case_agreement','edge_joint_yield']:
            vals=[n[name][key] for n in nullmetrics.values() if n[name][key] is not None];a=actual[key];comparisons[name][key]=dict(actual=a,nonempty_nulls=len(vals),min=min(vals) if vals else None,max=max(vals) if vals else None,mean=sum(vals)/len(vals) if vals else None,at_least_actual=sum(v>=a for v in vals) if a is not None else None)
    close(comparisons,load(OUT/'null-comparisons.json'))
    save(OUT/'audit.json',dict(passed=True,hashes_verified=hashes,independent_features=76,existing_model_output_replays=4,raw_case_integer_rows_replayed=len(cases),real_edge_scores_replayed=len(rows),real_list_groups=len(metrics),null_seed_replays=len(SEEDS),null_list_groups=groups,null_edge_scores_replayed=len(SEEDS)*len(rows),all_word_profiles_preserved=True,prediction_freeze_precedes_gold_reference_artifact=True,pos_fields_not_used=True,no_model_fit_or_retuning=True))
    print(load(OUT/'audit.json'))
if __name__=='__main__':run()
