"""Replay aggregates and sample sentence features; cluster inference by work."""
import hashlib,json,math,random
from pathlib import Path
from types import SimpleNamespace
from collections import Counter
import numpy as np
from benchmarks.latin_passage_proxy_audit import OUT,SENTENCE,chunks
from benchmarks.word_mapping_neural_model import DEFAULT_MODEL
from benchmarks import word_mapping_anchor_recovery as resource
from voynich_smt.data.corpus import digest,write_json
from voynich_smt.word_mapping.corpora import WordStream
from voynich_smt.word_mapping.ngram import NgramModel,NgramConfig
from voynich_smt.neural_scoring import WholeWordScorer
from voynich_smt.structural_language import StructuralLanguageModel
from voynich_smt.bootstrap_mapping import AgreementModel
from voynich_smt.bootstrap_marginal import MarginalAgreementModel

def run():
    docs=json.loads((OUT/'dataset.json').read_text());saved=json.loads((OUT/'report.json').read_text());rows=json.loads((OUT/'passages.json').read_text());selection=json.loads((OUT/'selection.json').read_text());e=json.loads((OUT/'morphology.json').read_text())['entries'];resources=json.loads((OUT/'resource-audit.json').read_text())
    for f,h in resources['files_sha256'].items():assert hashlib.sha256(Path(f).read_bytes()).hexdigest()==h
    assert digest(rows)==saved['passages_sha256'] and digest(selection)==saved['selection_sha256']
    files={d['document']:json.loads((OUT/'sentences'/f"{d['document']}.json").read_text()) for d in docs}
    originals=np.concatenate([np.asarray(files[d['document']]['original']) for d in docs if d['split']=='fit']);assert np.array_equal(np.quantile(originals,.1,axis=0),selection['tails'])
    earlier=json.loads((SENTENCE/'selection.json').read_text());old=earlier['candidates'][0]
    byid={r['id']:r for r in rows}
    for d in docs:
        values=files[d['document']]
        for width in (250,1000,'whole_work'):
            for ci,idx in enumerate(chunks(d['sentences'],width)):
                weights=np.asarray([len(d['sentences'][i]['words']) for i in idx])
                for family,features in values.items():
                    rid=f"{d['document']}/{width}/{ci}/{family}"
                    if rid not in byid:continue
                    rr=byid[rid];x=np.asarray(features)[idx]
                    means=np.sum(x*weights[:,None],axis=0)/sum(weights)
                    rates=-np.sum((x<selection['tails'])*weights[:,None],axis=0)/sum(weights)
                    scores=((x-earlier['mean'])/earlier['scale'])@np.asarray(old['parameters'][:-1])+old['parameters'][-1]
                    acceptance=sum(weights[scores>=old['threshold']])/sum(weights)
                    assert np.allclose(rr['features'],np.r_[means,rates,acceptance],atol=1e-12,rtol=0)
                    if family.startswith('corrupt_'):assert rr['witnessed_violations']>0
    train=list(WordStream.load(resource.PARENT/'splits/train.json').segments());neural=WholeWordScorer.load(DEFAULT_MODEL/'inference',batch_size=16,threads=4)
    bg=NgramModel.train(train,NgramConfig(bigram_weight=1.,trigram_weight=0.));tg=NgramModel.train(train,NgramConfig(bigram_weight=0.,trigram_weight=1.));structural=StructuralLanguageModel(e).fit(train);m=SimpleNamespace(entries=e,identity='audit');agreement=AgreementModel(m);marginal=MarginalAgreementModel(m)
    counts=Counter(w for s in train for w in s);total=sum(counts.values());vocab=len(counts)+1;sampled=[]
    for d in docs:
        for family,mapping in d['mappings'].items():
            eligible=[i for i,s in enumerate(d['sentences']) if any(w in mapping for w in s['words'])] or list(range(len(d['sentences'])))
            i=eligible[len(eligible)//2];words=[mapping.get(w,w) for w in d['sentences'][i]['words']];n=len(words)
            part_scores=[neural.segment(words[j:j+64]).totals() for j in range(0,n,64)]
            values=[sum(a['word_normalized_log_sum'] for a in part_scores)/n,sum(a['word_masked_log_sum'] for a in part_scores)/n,sum(math.log((counts[w]+.1)/(total+.1*vocab)) for w in words)/n,bg.score([words]).log_likelihood/n,tg.score([words]).log_likelihood/n,structural.score([words])/n,agreement.score([words])/max(1,n-1),marginal.score([words])/max(1,n-1),sum(bool(e.get(w)) for w in words)/n]
            assert np.allclose(values,files[d['document']][family][i],atol=1e-6,rtol=0)
            sampled.append({'document':d['document'],'family':family,'sentence':i})
    validation={'aggregate_features_all_replayed':True,'tails_fit_only_replayed':True,'source_resource_hashes_verified':True,'sampled_all_nine_sentence_features_replayed':sampled,'tolerance':1e-6,'report_sha256':digest(saved),'sentence_feature_files_sha256':{d['document']:hashlib.sha256((OUT/'sentences'/f"{d['document']}.json").read_bytes()).hexdigest() for d in docs}}
    write_json(OUT/'validation.json',validation)
    diagnostics=[]
    rng=np.random.default_rng(1711)
    for model in saved['results']:
        bywidth=[]
        for record in model['lengths']:
            pp={r['id']:r for r in record['predictions']};rr=[r for r in rows if r['split']=='test' and r['width']==record['width'] and r['family']!='optimizer_transfer'];documents=sorted({r['document'] for r in rr})
            # Additive counts avoid treating nested blocks/variants as independent.
            counts_by_doc=[]
            for doc in documents:
                local=[r for r in rr if r['document']==doc];positive=[r for r in local if r['valid']];negative=[r for r in local if not r['valid']]
                counts_by_doc.append([sum(pp[r['id']]['predicted_valid'] for r in positive),len(positive),sum(not pp[r['id']]['predicted_valid'] for r in negative),len(negative),sum(pp[r['base']+'/original']['score']>pp[r['id']]['score']+1e-10 for r in negative)])
            data=np.asarray(counts_by_doc);bs=[]
            for _ in range(1000):
                a=data[rng.integers(0,len(data),len(data))].sum(0);bs.append([.5*(a[0]/a[1]+a[2]/a[3]),a[4]/a[3]])
            bounds=np.quantile(bs,[.025,.975],axis=0).T.tolist();contrasts=[]
            for r in rr:
                if r['family'].startswith('corrupt_'):
                    control=r['base']+'/'+r['family'].replace('corrupt_','control_')
                    if control in pp:contrasts.append({'base':r['base'],'tier':r['family'],'control_preferred':pp[control]['score']>pp[r['id']]['score']+1e-10,'delta_control_minus_corrupt':pp[control]['score']-pp[r['id']]['score']})
            bywidth.append({'width':record['width'],'work_cluster_bootstrap_95':{'balanced_accuracy':bounds[0],'paired_accuracy':bounds[1]},'control_vs_corruption_pairs':len(contrasts),'control_vs_corruption_accuracy':float(np.mean([c['control_preferred'] for c in contrasts])),'contrasts':contrasts})
        diagnostics.append({'name':model['name'],'lengths':bywidth})
    write_json(OUT/'diagnostics.json',{'scope':'Post-hoc descriptive control contrasts; work-cluster intervals with at most four test works are unstable. Equal changed-token counts guaranteed for whole-work controls only.','results':diagnostics})
    print('VALIDATED',len(rows),'aggregates;',len(sampled),'sampled sentences',flush=True)
if __name__=='__main__':run()
