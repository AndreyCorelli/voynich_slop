"""Independent cost, code-coverage, ownership and continuation audit; no solves."""
from collections import Counter
import json
import math
from pathlib import Path

from benchmarks import contraction_coverage_calibration as experiment
from benchmarks.contraction_hidden_validation import independent_paths, independent_decode
from benchmarks.broader_contraction_capacity import minimum
from benchmarks.l3_conflict import verify
from voynich_smt.data.corpus import digest, write_json
from voynich_smt.experiments.hidden import HiddenRecoveryRequest


def normalize(value): return json.loads(json.dumps(value))


def audit_prediction(case,result,p,prediction,control=False):
    if result['status']!='SAT':
        assert prediction=={'status':'NOT_EVALUATED_NO_SAT'}
        return [],0
    field='control_held_cipher' if control else 'held_cipher'
    train_field='control_request' if control else 'request'
    training={tuple(w) for w in case[train_field]['ciphertext']['words']}
    spelling_train=set(case['training_spellings']);rows=[]
    for i,(cipher,saved) in enumerate(zip(case[field]['words'],prediction['words'])):
        decoded=independent_decode(cipher,result['encoder'])
        assert (decoded is not None)==saved['fully_decoded']
        spelling=None if decoded is None else ''.join(p['expansions'].get(u,u) for u in decoded)
        assert spelling==saved['expanded_word']
        assert saved['novel_ciphertext']==(tuple(cipher) not in training)
        assert saved['dictionary_hit']==(spelling in case['vocabulary'])
        legal=False
        if decoded is not None:
            legal=tuple(decoded) in independent_paths(spelling,p['rules'] if case['contracted'] else [])
        row={'index':i,'decoded':decoded,'expanded':spelling,'legal_contraction_path':legal}
        if not control:
            assert saved['exact']==(spelling==case['held_plaintext'][i])
            assert saved['novel_plaintext']==(case['held_plaintext'][i] not in spelling_train)
            if saved['exact']: assert legal
            row.update(exact=saved['exact'],novel_plaintext=saved['novel_plaintext'])
        rows.append(row)
    assert prediction['decoded']==sum(r['decoded'] is not None for r in rows)
    if not control:
        assert prediction['exact']==sum(r['exact'] for r in rows)
        assert prediction['novel_plaintext_exact']==sum(r['exact'] and r['novel_plaintext'] for r in rows)
        assert prediction['novel_plaintext_words']==sum(r['novel_plaintext'] for r in rows)
    return rows,len(rows)


def ownership(case,result):
    if result['status']!='SAT':return []
    targets=sorted({u for w in case['held_units']['words'] for u in w})
    rows=[]
    for unit in targets:
        outputs=[independent_decode(c,result['encoder']) for c in case['truth']['encoder']['codebook'][unit]]
        grouped=all(o is not None and len(o)==1 for o in outputs) and outputs[0]==outputs[1]
        rows.append({'generating_unit':unit,'recovered_outputs':outputs,'both_codes_grouped_as_one_unit':grouped,
            'correct_ownership':all(o==[unit] for o in outputs)})
    return rows


def validate():
    p=experiment.prepare();report=json.loads((experiment.OUT/'report.json').read_text())
    assert report['complete'] and report['prepared_sha256']==digest(p)
    paths_checked=0;coverage_checks=0;witnesses=0;words_checked=0;rank_scores=0
    stages={};summary=[];ownership_rows=[];scope_rows=[]
    for name,fixture in p['fixtures'].items():
        d=p['designs'][name]
        assert d['train']==fixture['train']+d['carriers'] and len(d['carriers'])<=16
        assert all(w in fixture['reference_counts'] for w in d['carriers'])
        all_forms=set(fixture['vocabulary']+d['carriers']+fixture['held'])
        canonical={}
        for word in all_forms:
            paths=independent_paths(word,p['rules'])
            assert paths==set(experiment.prior.variants(word,p['rules']))
            assert min(map(len,paths))==minimum(word,p['rules'])[0]
            canonical[word]=min(paths,key=lambda path:(len(path),path));paths_checked+=len(paths)
        counts=Counter(u for w in d['train'] for u in canonical[w])
        targets={u for w in fixture['held'] for u in canonical[w]}
        assert sorted(targets)==d['target_units']
        assert {u:counts[u] for u in targets}==d['target_occurrences']
        assert all(counts[u]>=2 for u in targets)
        for label,case in p['cases'][name].items():
            assert normalize(experiment.make_case(fixture,d,p['rules'],p['expansions'],case['seed'],case['mixed'],case['contracted']))==case
            q=HiddenRecoveryRequest.from_dict(case['request']);verify(q,case['truth']);witnesses+=1
            observed=set();cursor=0;book=case['truth']['encoder']['codebook']
            for word in case['truth']['plaintext']['words']:
                for u in word:
                    observed.add(tuple(book[u][case['truth']['choices'][cursor]]));cursor+=1
            for word in case['held_units']['words']:
                for u in word:
                    for code in book[u]:assert tuple(code) in observed;coverage_checks+=1
            assert case['coverage_mask']==[True]*8
            assert case['novel_plaintext_mask']==[w not in set(d['train']) for w in fixture['held']]
    for i in range(1,8):
        stage=json.loads((experiment.OUT/f'iteration-{i}.json').read_text());stages[i]=stage
        assert stage['plan']['prepared_sha256']==digest(p)
        if i>1:assert stage['plan']['previous_sha256']==digest(stages[i-1])
        for row in stage['rows']:
            source=stage['plan']['source'];label='contracted' if row['name'].startswith('contracted') else 'letters'
            case=p['cases'][source][label];assert row['case_sha256']==digest(case)
            public=json.loads((experiment.OUT/f'iteration-{i}'/f"{row['name']}-input.json").read_text())
            assert set(public)==({'request','oracle_segmentation'} if row['oracle'] else {'request'})
            assert digest(public)==row['public_sha256']
            assert public['request']==case['control_request' if row['control'] else 'request']
            q=HiddenRecoveryRequest.from_dict(public['request']);verify(q,row['result'])
            if row['result']['status']=='SAT':witnesses+=1
            if row['oracle'] and row['result']['status']=='SAT':assert public['oracle_segmentation']==row['result']['segmentation']
            audited,number=audit_prediction(case,row['result'],p,row['prediction'],row['control']);words_checked+=number
            scope_rows.append({'iteration':i,'name':row['name'],'words':audited})
            if not row['control']:
                owners=ownership(case,row['result']);ownership_rows.append({'source':source,'label':label,'rows':owners})
                summary.append({'source':source,'label':label,'mixed':case['mixed'],'oracle':row['oracle'],
                    'status':row['result']['status'],'prediction':row['prediction'],
                    'ungrouped_target_units':[r['generating_unit'] for r in owners if not r['both_codes_grouped_as_one_unit']],
                    'wrong_target_ownership':[r['generating_unit'] for r in owners if not r['correct_ownership']],
                    'both_code_ownership_guaranteed_words':sum(all(next(a['correct_ownership'] for a in owners if a['generating_unit']==u) for u in w) for w in case['held_units']['words']) if owners else None,
                    'training_words':len(case['training_spellings']),'training_letters':case['training_letters'],
                    'training_units':case['training_units'],'training_glyph_mean':case['training_glyphs']/len(case['training_spellings']),
                    'solver_seconds':row['result'].get('runtime_seconds'),'fit_wall_seconds':row['fit_wall_seconds']})
        for proof in stage['proofs']:
            case=p['cases'][proof['source']]['contracted'];q=HiddenRecoveryRequest.from_dict(case['request'])
            assert proof['generating']==case['truth']
            assert normalize(experiment.swaps(proof['generating'],p,q))==proof['alternatives']
            for alt,ev in zip(proof['alternatives'],proof['evaluations']):
                verify(q,alt['result']);witnesses+=1
                assert alt['result']['plaintext']!=proof['generating']['plaintext']
                audited,number=audit_prediction(case,alt['result'],p,ev);words_checked+=number
        for rank in stage['ranked']:
            if rank['status']!='EVALUATED':continue
            source=rank['source'];case=p['cases'][source]['contracted'];q=HiddenRecoveryRequest.from_dict(case['request'])
            result=rank['candidates'][0]['result']
            first_stage={'caesar':2,'aquinas':3,'einhard':4,'caroli':7}[source]
            actual=next(row['result'] for row in stages[first_stage]['rows'] if row['name']=='contracted-positive')
            assert result==actual, 'No injected truth candidate'
            expected=[{'swap':None,'result':result}]+experiment.swaps(result,p,q)
            assert normalize(expected)==rank['candidates']
            values=[];model=case['reference_model'];counts=model['counts'];denom=sum(counts.values())+len(counts)+1
            for candidate,value,ev in zip(rank['candidates'],rank['scores'],rank['evaluations']):
                verify(q,candidate['result']);witnesses+=1
                words=[''.join(p['expansions'].get(u,u) for u in w) for w in candidate['result']['plaintext']['words'][:32]]
                hist=Counter(words)
                independently=sum(n*math.log((counts.get(w,0)+1)/denom) for w,n in hist.items())/32
                assert math.isclose(value,independently,abs_tol=1e-12);values.append(independently);rank_scores+=1
                audited,number=audit_prediction(case,candidate['result'],p,ev);words_checked+=number
            order=sorted(range(len(values)),key=lambda j:(-values[j],j))
            assert rank['order']==order and rank['selected_index']==order[0]
    assert report['solver_calls']==sum(len(s['rows']) for s in stages.values())==12
    validation={'verified':True,'path_checks':paths_checked,'both_code_observation_checks':coverage_checks,
        'sat_witness_checks':witnesses,'independent_continuation_words':words_checked,'independent_frequency_scores':rank_scores,
        'code_sha256':digest(Path(__file__).read_text()),
        'scope':'Complete paths and retained costs; regenerated fixtures; both code alternatives actually observed; input separation; all recovery/proof/ranking SAT witnesses; independent decoding, context-valid paths, ownership grouping, novel plaintext types and carrier-excluded unigram scores. UNSAT solver-reported without independent proof certificates.'}
    write_json(experiment.OUT/'validation.json',validation)
    write_json(experiment.OUT/'ownership-audit.json',{'rows':ownership_rows})
    write_json(experiment.OUT/'continuation-path-audit.json',{'rows':scope_rows})
    write_json(experiment.OUT/'summary.json',{'rows':summary,'ranking_stage6':stages[6]['assessment'],'mixed_stage7':stages[7]['assessment']})
    print(json.dumps(validation));return validation


if __name__=='__main__':validate()
