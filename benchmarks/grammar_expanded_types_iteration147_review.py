"""Independent eligibility/no-expansion audit; no model predictions generated."""
from benchmarks.grammar_expanded_types_iteration147 import *

def run():
    hc=0
    for name in ['design-freeze','eligibility-freeze']:
        for p,h in load(OUT/(name+'.json'))['inputs'].items():assert digest(p)==h,p;hc+=1
    saved=load(OUT/'eligibility.json');data=load(ROOT/'iteration44/annotations-truth.json');fit=load(ROOT/'iteration49/manifest.json')['partitions']['0']['fit'];old=load(ROOT/'iteration116/type-split.json')['training'];targets=set(load(ROOT/'iteration93/types.json')['candidates']);counts={};tokens=0
    reserved={r['sent_id'] for rows in load('experiments/holdouts/grammar-construction-next.json')['authors'].values() for r in rows};assert not set(fit)&reserved
    for sid in fit:
        for t in data[sid]['tokens']:
            key=(t['word'],t['pos']);counts[key]=counts.get(key,0)+1;tokens+=1
    vocabulary={w for w,pos in counts};records={};eligible=[]
    for w in sorted(vocabulary):
        cc={pos:n for (word,pos),n in counts.items() if word==w};total=sum(cc.values());modal=sorted(cc,key=lambda p:(-cc[p],p))[0];n=cc[modal];ok=w not in targets and total>=5 and modal in ['ADP','CCONJ'] and n*5>=total*4
        if ok:eligible.append(w)
        if modal in ['ADP','CCONJ'] or w in old:records[w]=dict(count=total,modal=modal,modal_count=n,purity=n/total,eligible_new=ok and w not in old,pos_counts=cc)
    assert records==saved['records'];assert not set(eligible)-set(old);assert saved['training']==sorted(old);anchors=load(ROOT/'iteration85/anchor-budgets.json')['195'];assert saved['labels']=={w:anchors[w] for w in old};assert saved['folds']==load(ROOT/'iteration116/type-split.json')['oof_folds'];assert not set(saved['training'])&targets
    for w,i in saved['lookup'].items():assert i==hashlib.sha256(('fit116|'+w).encode()).hexdigest()
    assert (OUT/'no-expansion.json').exists() and not (OUT/'models.json').exists() and not (OUT/'predictions.json').exists()
    save(OUT/'audit.json',dict(input_hashes_verified=hc,source_fit_sentences=len(fit),source_fit_tokens=tokens,source_fit_types=len(vocabulary),candidate_records_verified=len(records),additional_eligible_types=0,training_types=13,target_types_excluded=16,reserve_overlap=0,no_model_or_target_prediction_generated=True))
if __name__=='__main__':run()
