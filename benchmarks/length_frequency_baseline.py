"""Frozen length/frequency prediction versus saved cipher recovery, no new solves."""
import argparse
from collections import Counter
import json
from pathlib import Path
from benchmarks import natural_training_vocabulary as natural
from benchmarks import one_oov_calibration as tolerant
from benchmarks import oov_type_calibration as synthetic
from voynich_smt.data.corpus import digest,write_json

OUT=Path('experiments/results/length-frequency-baseline')
SOURCES=(('natural-strict',natural),('natural-one-occurrence',tolerant),('synthetic-one-type',synthetic))


def predict(training_plain,training_cipher,dictionary,held_cipher):
    plain=[tuple(w) for w in training_plain];cipher=[tuple(w) for w in training_cipher]
    if not plain or len(plain)!=len(cipher) or any(not w for w in plain):raise ValueError('Invalid paired training')
    numerator=sum(map(len,cipher));denominator=sum(map(len,plain));frequency=Counter(plain)
    pool=sorted(set(map(tuple,dictionary))|set(plain))
    # Integer distance avoids floating-point ties. No key/profile/glyph identities used.
    predictions=[min(pool,key=lambda w:(abs(len(w)*numerator-len(c)*denominator),-frequency[w],w)) for c in held_cipher]
    return {'expansion_ratio_numerator':numerator,'expansion_ratio_denominator':denominator,'predicted_words':predictions}


def prepare():
    cases=[];identity={}
    for group,module in SOURCES:
        source=module.prepare();report=json.loads((module.OUT/'report.json').read_text())
        if not report['complete'] or report['prepared_sha256']!=digest(source):raise ValueError('Unmatched completed source')
        identity[group]={'prepared_sha256':digest(source),'report_sha256':digest(report)}
        rows=report['arms'] if group=='synthetic-one-type' else report['cases']
        for case in source['cases']:
            saved=next(r for r in rows if (r.get('case',r.get('id'))==case['id']) and (group!='synthetic-one-type' or r['arm']=='type'))
            positive=None
            if case['kind']=='shuffle':
                # Pair by frozen IDs, never by accuracy or solver status.
                if group=='synthetic-one-type':positive=next(c for c in source['cases'] if c['id']==case['id'].replace('-shuffle','-positive'))
                else:positive=next(c for c in source['cases'] if c['id']==case['id'].replace('-shuffle',''))
            elif case['kind']=='positive':positive=case
            request=case['request'];training=positive['truth']['plaintext']['words']
            baseline=predict(training,request['ciphertext']['words'],request['dictionary']['words'],case['holdout']['words'])
            cases.append({'id':group+':'+case['id'],'group':group,'kind':case['kind'],'request':request,
                'training_plaintext':training,'holdout':case['holdout'],'holdout_plaintext':case.get('holdout_plaintext'),
                'baseline':baseline,'saved_solver':saved})
    identity['code_sha256']={str(p):digest(p.read_text()) for p in (Path(__file__),Path('benchmarks/frozen_key_holdout.py'))}
    path=OUT/'prepared.json'
    if path.exists():
        frozen=json.loads(path.read_text())
        if frozen['identity']!=identity:raise ValueError('Frozen identity changed')
        assert digest(frozen['cases'])==digest(cases)
        return frozen
    protocol={'identity':identity,'solver_runs':0,'groups':[g for g,_ in SOURCES],
        'rule':'Learn ratio total training ciphertext glyphs / total true training plaintext letters. For each holdout word choose vocabulary entry minimizing absolute scaled length error, then maximizing true training frequency, then lexical tuple order. Candidate pool supplied dictionary union true training words. No key, glyph identity, generating profile or heldout plaintext enters predictor.',
        'scope':'Oracle-supervised training baseline, stronger assistance than hidden recovery. Natural strict, natural one-OOV-occurrence and synthetic repeated one-OOV-type sources, all completed saved results included. Same-source/profile/text correlations, not independent trials. Frozen rule/predictions before scoring; no tuning. SAT comparisons conditional on recovery; UNKNOWN/UNSAT positive outcomes retained separately, not counted as wrong decoded keys. Controls have no generating-plaintext accuracy: report vocabulary membership only, never compare that with exact accuracy.'}
    frozen={'identity':identity,'protocol':protocol,'cases':cases};write_json(OUT/'protocol.json',protocol);write_json(path,frozen);return frozen


def evaluate(case):
    saved=case['saved_solver'];status=saved['result']['status'];pred=case['baseline']['predicted_words']
    dictionary=set(map(tuple,case['request']['dictionary']['words']))
    row={'id':case['id'],'group':case['group'],'kind':case['kind'],'solver_status':status,'word_count':len(pred),
         'baseline_dictionary_words':sum(tuple(w) in dictionary for w in pred)}
    if case['kind']=='positive':
        truth=list(map(tuple,case['holdout_plaintext']['words']));training=set(map(tuple,case['training_plaintext']))
        novel=[w not in training for w in truth]
        base_hits=[tuple(w)==t for w,t in zip(pred,truth)]
        row.update(novel_words=sum(novel),baseline_exact=sum(base_hits),baseline_novel_exact=sum(h and n for h,n in zip(base_hits,novel)))
        if status=='SAT':
            decoded=saved['prediction']['word_results'];hits=[w['fully_decoded'] and tuple(w['decoded_prefix'])==t for w,t in zip(decoded,truth)]
            row.update(key_exact=sum(hits),key_novel_exact=sum(h and n for h,n in zip(hits,novel)))
    elif status=='SAT':row['key_dictionary_words']=saved['prediction']['dictionary_words']
    return row


def run():
    p=prepare();rows=[evaluate(c) for c in p['cases']];summaries=[]
    for group,_ in SOURCES:
        positives=[r for r in rows if r['group']==group and r['kind']=='positive'];sat=[r for r in positives if r['solver_status']=='SAT']
        controls=[r for r in rows if r['group']==group and r['kind']=='shuffle']
        summaries.append({'group':group,'positive_status_counts':dict(Counter(r['solver_status'] for r in positives)),
            'control_status_counts':dict(Counter(r['solver_status'] for r in controls)),
            'all_positive_baseline':{'exact':sum(r['baseline_exact'] for r in positives),'words':sum(r['word_count'] for r in positives),'novel_exact':sum(r['baseline_novel_exact'] for r in positives),'novel_words':sum(r['novel_words'] for r in positives)},
            'matched_sat':{'cases':len(sat),'words':sum(r['word_count'] for r in sat),'baseline_exact':sum(r['baseline_exact'] for r in sat),'key_exact':sum(r['key_exact'] for r in sat),'novel_words':sum(r['novel_words'] for r in sat),'baseline_novel_exact':sum(r['baseline_novel_exact'] for r in sat),'key_novel_exact':sum(r['key_novel_exact'] for r in sat)}})
    r={'prepared_sha256':digest(p),'complete':True,'cases':rows,'summaries':summaries};write_json(OUT/'report.json',r);return r


def validate():
    p=prepare();before=json.loads((OUT/'report.json').read_text());assert before['prepared_sha256']==digest(p)
    for c in p['cases']:
        assert digest(c['baseline'])==digest(predict(c['training_plaintext'],c['request']['ciphertext']['words'],c['request']['dictionary']['words'],c['holdout']['words']))
    # Deterministic scoring re-evaluation; no solver calls or source changes.
    assert digest(before)==digest(run())
    write_json(OUT/'validation.json',{'verified':True,'cases':len(p['cases']),'checks':['source/report/code hashes','fixed prediction reconstruction','exact/novel scoring','matched SAT denominators','unresolved/control separation'],'limitation':'Assisted training and correlated examples; no p-values or language inference.'})
    print('Validated length/frequency baseline')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run',action='store_true');parser.add_argument('--validate',action='store_true');a=parser.parse_args()
    if a.validate:validate()
    elif a.run:
        for summary in run()['summaries']:print(summary)
    else:prepare();print('Frozen baseline predictions without scoring')
