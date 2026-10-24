"""Verify frozen predictive keys, candidate retention and paired downstream gains."""
import hashlib,json,math
from collections import Counter
from pathlib import Path
import numpy as np
from benchmarks.latin_compact_cipher import OUT,ARMS,resource,metrics,evaluate,tag,TAGS
from voynich_smt.letter_discovery import ALPHABET,SPACE,BASE,encode_text,decode_text,pattern
from voynich_smt.data.corpus import digest,write_json
from voynich_smt.letter_key_codec import pack_key,unpack_key,KEY_BYTES


def run():
    r=resource();rows,words,posmodel,logs,frequency,nodes,terminal=r;inventory=set(words);groups=Counter(pattern(w) for w in words);fixtures={f['id']:f for f in json.loads((OUT/'fixtures.json').read_text())};primary=json.loads((OUT/'report.json').read_text());budget=json.loads((OUT/'budget-report.json').read_text());checked=0
    for rr in (primary['runs'],budget['runs']):
        for result in rr:
            f=fixtures[result['fixture']];truth=json.loads((OUT/'truth'/f"{digest(f['id'])}.json").read_text());hyp=result['hypothesis'];assert len(hyp['decryption_permutation'])==SPACE and sorted(hyp['decryption_permutation'])==list(range(SPACE)) and hyp['exceptions']==[]
            packed=pack_key(hyp['decryption_permutation']);assert len(packed)==10 and unpack_key(packed)==hyp['decryption_permutation']
            path=OUT/'compact-keys'/f"{digest((f['id'],result['arm'],result.get('budget',10000)))}.bin";path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(packed)
            assert decode_text(encode_text(' '.join(w for sent in f['heldout'] for w in sent)),unpack_key(path.read_bytes()))==decode_text(encode_text(' '.join(w for sent in f['heldout'] for w in sent)),hyp['decryption_permutation'])
            recalculated=evaluate(f,result,truth)
            assert result['heldout']==recalculated['heldout'] and result['discovery']==recalculated['discovery'];checked+=1
            assert 'key_seed' not in f and 'key' not in f and 'generation_seed' not in f
    for arm in ARMS:
        for fixture in fixtures:
            if fixtures[fixture]['split']!='test':continue
            full=next(x for x in primary['runs'] if x['fixture']==fixture and x['arm']==arm)
            for early in (x for x in budget['runs'] if x['fixture']==fixture and x['arm']==arm):
                for er,fr in zip(early['runs'],full['runs']):
                    checkpoint=next(c for c in fr['checkpoints'] if c[0]==early['budget'])
                    assert np.isclose(er['objective'],checkpoint[2],atol=1e-8)
    paired={}
    for name,rr in [('full',primary['runs'])]+[(str(b),[x for x in budget['runs'] if x['budget']==b]) for b in (100,1000)]:
        lookup={(x['fixture'],x['arm']):x for x in rr};paired[name]={}
        for arm in ARMS[1:]:
            deltas=[x['heldout']['letter_accuracy']-lookup[(x['fixture'],'baseline')]['heldout']['letter_accuracy'] for x in rr if x['arm']==arm]
            paired[name][arm]={'mean_letter_gain_percentage_points':float(np.mean(deltas)*100),'wins':sum(d>1e-12 for d in deltas),'losses':sum(d<-1e-12 for d in deltas),'ties':sum(abs(d)<=1e-12 for d in deltas),'median_letter_gain_percentage_points':float(np.median(deltas)*100)}
    percase=[];n=correct=0;candidate_sizes=[];retained=total=0;types_retained=types_total=0
    for f in fixtures.values():
        if f['split']!='test':continue
        truth=json.loads((OUT/'truth'/f"{digest(f['id'])}.json").read_text());tw=[t['word'] for s in truth['discovery'] for t in s['tokens']];retained+=sum(w in inventory for w in tw);total+=len(tw);types_retained+=sum(w in inventory for w in set(tw));types_total+=len(set(tw));candidate_sizes.extend(groups[pattern(w)] for w in set(tw))
        for cipherwords,s in zip(f['discovery'],truth['discovery']):
            p=posmodel.predict(cipherwords)
            for i,t in enumerate(s['tokens']):correct+=TAGS[int(p[i].argmax())]==tag(t);n+=1
        key=json.loads((OUT/'truth'/f"{digest(f['id'])}.json").read_text())['key'];percase.append(tuple(key))
    baseline=[x for x in primary['runs'] if x['arm']=='baseline'];function=[];aux=[]
    for x in baseline:
        for key,acc in (('function_words',function),('auxiliary_words',aux)):
            if x['heldout'][key+'_accuracy'] is not None:acc.append((x['heldout'][key+'_accuracy'],x['heldout'][key+'_count']))
    # Caesar-family sanity check on calibration texts only; max language score selects shift.
    sanity=[]
    cal=[f for f in fixtures.values() if f['split']=='calibration' and f['width']==300]
    for f in cal[::2]:
        truth=json.loads((OUT/'truth'/f"{digest(f['id'])}.json").read_text());plain=encode_text(' '.join(t['word'] for s in truth['discovery'] for t in s['tokens']));encryption=(np.arange(SPACE)+5)%SPACE;cipher=np.r_[encryption,SPACE][plain];candidates=[]
        for shift in range(SPACE):
            key=(np.arange(SPACE)-shift)%SPACE;decoded=np.r_[key,SPACE][cipher];codes=np.zeros(len(decoded)-3,dtype=np.int64)
            for k in range(4):codes=codes*BASE+decoded[k:k+len(codes)]
            candidates.append(float(logs[codes].mean()))
        selected=int(np.argmax(candidates));assert selected==5;sanity.append({'fixture':f['id'],'selected_shift':selected,'true_shift':5})
    audit={'compact_key_bytes':KEY_BYTES,'binary_keys_predict_without_language_model_or_dictionary':True,'independent_frozen_metric_checks':checked,'earlier_objectives_match_full_run_archives':True,'test_independent_keys':len(set(percase)),'test_encrypted_fixtures':len(percase),'pos_token_accuracy_on_discovery':correct/n,'pos_evaluated_tokens':n,'candidate_inventory_words':len(words),'true_word_token_retention':retained/total,'true_word_type_retention':types_retained/types_total,'median_candidates_per_type':float(np.median(candidate_sizes)),'mean_candidates_per_type':float(np.mean(candidate_sizes)),'paired_gains':paired,'baseline_token_weighted_function_accuracy':sum(a*c for a,c in function)/sum(c for a,c in function),'baseline_token_weighted_auxiliary_accuracy':sum(a*c for a,c in aux)/sum(c for a,c in aux),'caesar_calibration_sanity':sanity,'scope':'Overlapping discovery widths and repeated heldout passages are paired, not independent samples. Key discovery family is fixed and word boundaries known. Early-budget weights were selected at full budget.'}
    write_json(OUT/'audit.json',audit);paths=[Path(__file__),Path('src/voynich_smt/letter_key_codec.py'),OUT/'report.json',OUT/'budget-report.json'];write_json(OUT/'audit-manifest.json',{'sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}});print(json.dumps(audit,indent=2),flush=True)
if __name__=='__main__':run()
