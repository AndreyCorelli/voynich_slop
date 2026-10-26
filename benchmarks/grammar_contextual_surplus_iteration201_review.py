"""Independent rational labels, augmented least squares and held-out evaluation audit."""
import re,random,math
from fractions import Fraction
from collections import Counter,defaultdict
import numpy as np
from benchmarks.grammar_contextual_surplus_iteration201 import OUT,BASE,PREVIOUS,AUTHORS,EPS,Path,load,save,digest
from benchmarks.grammar_case_applicability_iteration180_review import close
from benchmarks.grammar_consensus_core_iteration195_review import scalar_metrics
CASES={'Nom','Gen','Dat','Acc','Abl','Voc','Loc'}

def independent_labels(g,ref):
    buckets=defaultdict(Counter)
    for i,p in enumerate(g['positions']):
        if p:buckets[(g['ids'][i],ref['pos'][i])][ref['case'][i]]+=1
    labels=[]
    for e in g['descriptors']:
        oo=[];ee=[];nn=[]
        for frame in e['frames']:
            observed=0;expected=Fraction(0);n=0
            for i in frame['a_positions']:
                for j in frame['b_positions']:
                    assert g['ids'][i]!=g['ids'][j];a=buckets[(g['ids'][i],ref['pos'][i])];b=buckets[(g['ids'][j],ref['pos'][j])];den=sum(a.values())*sum(b.values());expected+=Fraction(sum(a[c]*b[c] for c in CASES),den);observed+=int(ref['case'][i] in CASES and ref['case'][i]==ref['case'][j]);n+=1
            oo.append(Fraction(observed,n));ee.append(expected/n);nn.append(n)
        obs=sum(oo)/len(oo);exp=sum(ee)/len(ee);labels.append(dict(a=e['a'],b=e['b'],observed_frame_macro_joint_matching=float(obs),expected_frame_macro_joint_matching=float(exp),surplus=float(obs-exp),frames=e['shared_frames'],frame_comparison_counts=nn))
    return labels,buckets

def metrics(ix,labels,rows,eligible):
    n=len(ix);values=[labels[i]['surplus'] for i in ix]
    return dict(selected=n,mean_surplus=sum(values)/n if n else None,positive_surplus_pairs=sum(v>EPS for v in values),negative_surplus_pairs=sum(v<-EPS for v in values),zero_surplus_pairs=sum(abs(v)<=EPS for v in values),observed_frame_macro_joint_matching=sum(labels[i]['observed_frame_macro_joint_matching'] for i in ix)/n if n else None,expected_frame_macro_joint_matching=sum(labels[i]['expected_frame_macro_joint_matching'] for i in ix)/n if n else None,case_metrics=scalar_metrics([rows[i] for i in ix],eligible))

def run():
    assert not (OUT/'audit.json').exists();save(OUT/'review-design.json',dict(code_sha256=digest(Path(__file__)),policy='Independent rational analytic expectation; POS/Case replay; source scaling; augmented leastsquares; score/metric/oracle/copy checks. Additional label-formula validation:199wordPOS permutations seeds20100..20298 per development author, graphmean observedmatching expectation within8MonteCarlo standard errors +1e-12, no model/selection change or inference-significance claim.'))
    hashes=0
    for p,h in load(OUT/'design-freeze.json')['inputs'].items():assert digest(Path(p))==h;hashes+=1
    for n in ['label-trial-freeze.json','prediction-freeze.json']:
        for p,h in load(OUT/n).items():assert digest(OUT/p)==h;hashes+=1
    for folder in [BASE,PREVIOUS]:
        for p,h in load(folder/'verification-manifest.json').items():assert digest(Path(p))==h;hashes+=1
    ad=load(BASE/'admission.json');graphs=load(BASE/'graphs.json');refs=load(OUT/'development-references.json');labels=load(OUT/'labels.json');case=load(BASE/'development-references.json');sizes=load(BASE/'finalized-sizes.json');ff=load(BASE/'features.json');models=load(OUT/'models.json');outputs=load(OUT/'outputs.json');selected=load(OUT/'selections.json');evaluation=load(OUT/'evaluation-selections.json');summary=load(OUT/'summary.json');details=load(OUT/'selected-details.json');contrasts=load(OUT/'contrasts.json');oldmodels=load(PREVIOUS/'models.json');oldoutputs=load(PREVIOUS/'scores.json');wanted={(r['path'],r['sent_id']) for a in AUTHORS for r in ad[a]};rawref={}
    assert not any('udante' in p or 'circse' in p for p,s in wanted)
    for path in sorted({p for p,s in wanted}):
        for block in Path(path).read_text().strip().split('\n\n'):
            lines=block.splitlines();sid=next((x.split('=',1)[1].strip() for x in lines if x.startswith('# sent_id =')),None)
            if (path,sid) not in wanted:continue
            for line in lines:
                m=re.match(r'^(\d+)\t(?:[^\t]*\t){2}([^\t]*)\t[^\t]*\t([^\t]*)\t',line)
                if not m:continue
                cases=[x[5:] for x in m[3].split('|') if x.startswith('Case=')];c=cases[0] if cases and cases[0] in CASES else '';rawref[(path,sid,int(m[1]))]=(m[2],c)
    diagnostic={};label_count=0
    for a in AUTHORS:
        ref=dict(pos=[rawref[tuple(p)][0] if p else 'X' for p in graphs[a]['positions']],case=[rawref[tuple(p)][1] if p else '' for p in graphs[a]['positions']]);assert ref==refs[a];expected,buckets=independent_labels(graphs[a],ref);close(expected,labels[a]);label_count+=len(expected)
        positions=defaultdict(list)
        for i,p in enumerate(graphs[a]['positions']):
            if p:positions[(graphs[a]['ids'][i],ref['pos'][i])].append(i)
        values=[]
        for seed in range(20100,20299):
            rng=random.Random(seed);cc=ref['case'].copy()
            for key,pp in sorted(positions.items()):
                vv=[ref['case'][i] for i in pp];rng.shuffle(vv)
                for i,c in zip(pp,vv):cc[i]=c
                assert Counter(cc[i] for i in pp)==buckets[key]
            edge=[]
            for e in graphs[a]['descriptors']:
                frame=[]
                for f in e['frames']:
                    frame.append(sum(cc[i] in CASES and cc[i]==cc[j] for i in f['a_positions'] for j in f['b_positions'])/(len(f['a_positions'])*len(f['b_positions'])))
                edge.append(sum(frame)/len(frame))
            values.append(sum(edge)/len(edge))
        analytic=sum(r['expected_frame_macro_joint_matching'] for r in expected)/len(expected);mean=float(np.mean(values));se=float(np.std(values,ddof=1)/math.sqrt(len(values)));assert abs(mean-analytic)<=8*se+1e-12;diagnostic[a]=dict(analytic_expected=analytic,permutation_mean=mean,standard_error=se,within_8_standard_errors=True)
    assert load(OUT/'trials.json')=={a:[b for b in AUTHORS if b!=a] for a in AUTHORS};fits=groups=0
    for target in AUTHORS:
        train=[a for a in AUTHORS if a!=target];raw=np.array([r['values'] for a in train for r in ff[a]]);y=np.array([r['surplus'] for a in train for r in labels[a]]);w=np.concatenate([np.full(len(ff[a]),1/(len(train)*len(ff[a]))) for a in train])
        for label,cols in [('rich',list(range(19))),('control',[0,9,18])]:
            m=models[target]['surplus_'+label];xx=raw[:,cols];mean=np.average(xx,axis=0,weights=w);scale=np.sqrt(np.average((xx-mean)**2,axis=0,weights=w));scale[scale<1e-12]=1;assert m['columns']==cols;assert m['strength']==.1;assert np.allclose(mean,m['mean'],rtol=1e-12,atol=1e-12);assert np.allclose(scale,m['scale'],rtol=1e-12,atol=1e-12);assert m['mean']==oldmodels[target]['point_'+label]['model']['mean'];assert m['scale']==oldmodels[target]['point_'+label]['model']['scale']
            x=np.column_stack([np.ones(len(xx)),(xx-mean)/scale]);regularizer=np.column_stack([np.zeros(len(cols)),np.sqrt(.1)*np.eye(len(cols))]);xa=np.vstack([np.sqrt(w)[:,None]*x,regularizer]);ya=np.concatenate([np.sqrt(w)*y,np.zeros(len(cols))]);b=np.linalg.lstsq(xa,ya,rcond=None)[0];assert np.allclose(b,m['beta'],atol=1e-10,rtol=1e-10);pen=np.array(m['beta']);pen[0]=0;grad=x.T@(w*(x@np.array(m['beta'])-y))+.1*pen;assert max(abs(grad))<1e-10;objective=.5*np.sum(w*(x@np.array(m['beta'])-y)**2)+.05*(pen@pen);assert abs(objective-m['objective'])<1e-12
            xt=np.column_stack([np.ones(len(ff[target])),(np.array([r['values'] for r in ff[target]])[:,cols]-mean)/scale]);assert np.max(abs(xt@b-outputs[target]['surplus_'+label]))<1e-10;fits+=1
        for n in ['point_rich','point_control','rank_rich','rank_control']:assert outputs[target][n]==oldoutputs[target][n]
        computed={}
        for name,vv in outputs[target].items():
            for k in [10,20]:computed[name+'/top'+str(k)]=[i for i,v in enumerate(vv) if sum(t>v for t in vv)<k]
        assert computed==selected[target];computed['all_candidates']=list(range(len(labels[target])))
        for k in [10,20]:computed['oracle/top'+str(k)]=[i for i,r in enumerate(labels[target]) if sum(t['surplus']>r['surplus'] for t in labels[target])<k]
        assert computed==evaluation[target]
        for name,ix in computed.items():close(metrics(ix,labels[target],case[target],sizes[target]['types']),summary[target][name]);assert details[target][name]==[dict(edge=i,**labels[target][i]) for i in ix];groups+=1
        for kind in ['rich','control']:
            for baseline in ['point_'+kind,'rank_'+kind]:
                new=summary[target]['surplus_'+kind+'/top10'];old=summary[target][baseline+'/top10'];close(dict(mean_surplus_change=new['mean_surplus']-old['mean_surplus'],positive_pair_change=new['positive_surplus_pairs']-old['positive_surplus_pairs'],applicable_pair_change=new['case_metrics']['case_edges']-old['case_metrics']['case_edges']),contrasts[target][kind+'_vs_'+baseline])
    save(OUT/'analytic-expectation-check.json',diagnostic);save(OUT/'audit.json',dict(passed=True,hashes_verified=hashes,rational_edge_labels_replayed=label_count,development_reference_integer_rows=len(rawref),independent_augmented_least_squares_fits=fits,metric_groups=groups,baseline_score_copies=16,analytic_permutation_checks=4,permutation_profiles_preserved=True,source_and_target_exclusion_verified=True,no_dante_or_other_reserve_inputs=True,oracle_used_for_evaluation_only=True))
    print(load(OUT/'audit.json'))
if __name__=='__main__':run()
