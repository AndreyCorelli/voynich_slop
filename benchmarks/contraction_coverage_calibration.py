"""Coverage-controlled contraction recovery, ambiguity witnesses and frozen ranking."""
import argparse
from collections import Counter
from copy import deepcopy
from dataclasses import asdict, replace
from itertools import combinations
import json
import math
from pathlib import Path
import subprocess
import sys
from time import perf_counter

from benchmarks import contraction_hidden_calibration as prior
from benchmarks.german_shuffle_controls import typewise_shuffle
from benchmarks.l3_conflict import verify
from voynich_smt.cipher.base import Bounds, generate_ciphertext
from voynich_smt.data.corpus import digest, write_json
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.language.dictionary import WordDictionary
from voynich_smt.models.alphabet import Alphabet
from voynich_smt.models.text import Text

OUT = Path('experiments/results/contraction-coverage-calibration')


def canonical(word, rules):
    return min(prior.variants(word, rules), key=lambda p: (len(p), p))


def cover_training(fixture, rules, cap=16):
    """Truth-assisted design: reference carriers, without reserving novel held forms."""
    train = list(fixture['train'])
    counts = Counter(u for w in train for u in canonical(w, rules))
    targets = {u for w in fixture['held'] for u in canonical(w, rules)}
    held_forms = set(fixture['held'])
    reference = fixture['reference_counts']
    candidates = {w: canonical(w, rules) for w in reference}
    additions = []
    while any(counts[u] < 2 for u in targets):
        missing = {u for u in targets if counts[u] < 2}
        eligible = [w for w, path in candidates.items() if missing.intersection(path)]
        if not eligible:
            raise ValueError('Reference cannot supply held-unit coverage; no replacement')
        word = min(eligible, key=lambda w: (w in held_forms, len(candidates[w]), -reference[w], w))
        if len(additions) == cap:
            raise ValueError('Fixed sixteen-carrier ceiling reached')
        additions.append(word)
        train.append(word)
        counts.update(candidates[word])
    return {'train': train, 'carriers': additions, 'target_units': sorted(targets),
            'target_occurrences': {u: counts[u] for u in sorted(targets)},
            'carrier_held_form_overlap': sorted(set(additions)&held_forms)}


def balanced_choices(plain):
    seen = Counter(); choices = []
    for word in plain.words:
        for unit in word:
            choices.append(seen[unit] % 2); seen[unit] += 1
    return tuple(choices)


def make_case(fixture, design, rules, expansions, seed, mixed=False, contracted=True):
    selected_rules = rules if contracted else []
    vocabulary = sorted(set(fixture['vocabulary']+design['carriers']))
    dictionary = WordDictionary(tuple(sorted({v for w in vocabulary for v in prior.variants(w, selected_rules)})))
    alphabet = Alphabet(tuple(sorted({u for w in dictionary.words for u in w})))
    encoder, ca = prior.encoder_for(alphabet, 2, mixed, seed)
    train = Text(tuple(canonical(w, selected_rules) for w in design['train']))
    held = Text(tuple(canonical(w, selected_rules) for w in fixture['held']))
    assert set(u for w in held.words for u in w) <= set(alphabet.symbols)
    choices = balanced_choices(train)
    ciphertext = encoder.encode(train, choices)
    held_cipher, held_choices = generate_ciphertext(held, encoder, seed+1)
    seen = {encoder.codebook[u][k] for u,k in zip((u for w in train.words for u in w), choices)}
    coverage = [all(c in seen for u in w for c in encoder.codebook[u]) for w in held.words]
    assert all(coverage), 'Every held unit must have both code alternatives observed'
    q = HiddenRecoveryRequest(ciphertext, alphabet, ca, Bounds('verbose',2,1,2 if mixed else 1),
                              dictionary, timeout_ms=5000, dictionary_encoding='trie')
    truth = {'status':'SAT','verified':True,'encoder':asdict(encoder),
             'plaintext':asdict(train),'choices':choices,'nulls':[]}
    verify(q,truth)
    assert encoder.decode(held_cipher) == held
    full, metadata = typewise_shuffle(Text(ciphertext.words+held_cipher.words), seed+2)
    size = len(train.words)
    segmentation = []; cursor = 0
    for word in train.words:
        offsets = [0]
        for u in word:
            offsets.append(offsets[-1]+len(encoder.codebook[u][choices[cursor]])); cursor += 1
        segmentation.append(offsets)
    case = {'request':asdict(q),'control_request':asdict(replace(q,ciphertext=Text(full.words[:size]))),
        'truth':truth,'held_plaintext':fixture['held'],'held_units':asdict(held),
        'held_cipher':asdict(held_cipher),'control_held_cipher':asdict(Text(full.words[size:])),
        'control_metadata':metadata,'oracle_segmentation':segmentation,
        'coverage_mask':coverage,'training_spellings':design['train'],
        'carriers':design['carriers'],'natural_training_words':32,'vocabulary':vocabulary,
        'held_dictionary_mask':[w in vocabulary for w in fixture['held']],
        'novel_plaintext_mask':[w not in design['train'] for w in fixture['held']],
        'training_letters':sum(map(len,design['train'])),'training_units':train.size,
        'training_glyphs':ciphertext.size,'mixed':mixed,'contracted':contracted,
        'seed':seed,'reference_model':{'counts':fixture['reference_counts'],
                                     'tokens':sum(fixture['reference_counts'].values()),'alpha':1}}
    return json.loads(json.dumps(case))


def prepare():
    previous = prior.prepare()
    source = json.loads(prior.SOURCE.read_text())
    fixtures = dict(previous['fixtures'])
    fixtures['caroli'] = prior.natural_fixture(source['sources']['caroli'],previous['rules'],48004)
    designs = {name:cover_training(f,previous['rules']) for name,f in fixtures.items()}
    cases = {}
    for name, seed in [('caesar',48001),('aquinas',48002),('einhard',48003),('caroli',48004)]:
        mixed = name=='caroli'
        cases[name] = {label:make_case(fixtures[name],designs[name],previous['rules'],previous['expansions'],seed,mixed,contracted)
                       for label,contracted in [('contracted',True),('letters',False)]}
    files = [Path(__file__),Path(prior.__file__),Path('benchmarks/l3_conflict.py'),
             Path('benchmarks/frozen_key_holdout.py'),Path('benchmarks/german_shuffle_controls.py')]
    files += list(Path('src/voynich_smt/solver').glob('*.py'))
    p = {'prior_prepared_sha256':digest(previous),'source_sha256':digest(source),
         'rules':previous['rules'],'expansions':previous['expansions'],
         'fixtures':fixtures,'designs':designs,'cases':cases,
         'code_sha256':{str(f):digest(f.read_text()) for f in files},
         'solver_ms':5000,'worker_wall_seconds':45,
         'protocol': 'Seven bounded stages, frozen27-rule retained-cost core. Same three prior32+8 excerpts plus fresh Caroli midpoint. Greedily append<=16 reference carrier tokens, prefer forms outside heldout, until every contracted heldunit occurs>=2 times; no passage replacements. Encode with alternating perunit choices to expose both H2 codes; recovery remains free, sees no lengths/key/plaintext or coverage design. This is truth-assisted fixture construction, not blind natural passage selection. Wholeword coverage necessarily repeats plaintext forms; report novel forms separately. Same engineered word list in letters comparator. Stage1 audit;2Caesar,3Aquinas,4Einhard H2single;5verified wholeword ownership swap witnesses;6training-only external-frequency ranking of all legal single transpositions from returned keys;7fresh Caroli H2mixed1-2 first-key/letters/control plus oracle contracted only on UNKNOWN, and same frozen frequency ranking if SAT. No timeout ladders, rule additions or key rescue. Score excludes appended carriers, uses first32 natural recovered training words with frozen reference add-one unigram. No truth candidates injected into selection; truth swaps stage5 are separately labeled identifiability proofs. Stable first candidate ties; all single swaps, never multi-swap optimization. Results exploratory, same-author same-source prior; not full manuscript or natural-rate calibration.'}
    p = json.loads(json.dumps(p)); path = OUT/'prepared.json'
    if path.exists(): assert json.loads(path.read_text()) == p, 'Frozen inputs/code changed'
    else: write_json(path,p)
    return p


def evaluate(case,result,p,control=False):
    if result['status']!='SAT': return {'status':'NOT_EVALUATED_NO_SAT'}
    enc = prior.Encoder({u:tuple(tuple(c) for c in cs) for u,cs in result['encoder']['codebook'].items()})
    ciphertext = case['control_held_cipher' if control else 'held_cipher']['words']
    training = {tuple(w) for w in case['control_request' if control else 'request']['ciphertext']['words']}
    rows = []
    for i,word in enumerate(ciphertext):
        decoded = prior.decode_word(tuple(word),enc)
        spelling = prior.expand(decoded['decoded_prefix'],p['expansions']) if decoded['fully_decoded'] else None
        row = {**decoded,'expanded_word':spelling,'novel_ciphertext':tuple(word) not in training,
               'dictionary_hit':spelling in case['vocabulary']}
        if not control: row.update(exact=spelling==case['held_plaintext'][i],novel_plaintext=case['novel_plaintext_mask'][i])
        rows.append(row)
    return {'status':'EVALUATED_FROZEN_KEY','words':rows,'decoded':sum(r['fully_decoded'] for r in rows),
        'dictionary_hits':sum(r['dictionary_hit'] for r in rows),
        'exact':None if control else sum(r['exact'] for r in rows),
        'novel_plaintext_words':None if control else sum(r['novel_plaintext'] for r in rows),
        'novel_plaintext_exact':None if control else sum(r['exact'] and r['novel_plaintext'] for r in rows)}


def fit(p,stage,name,case,control=False,oracle=False):
    folder=OUT/f'iteration-{stage}'; inp=folder/f'{name}-input.json';out=folder/f'{name}-result.json'
    public={'request':case['control_request' if control else 'request']}
    if oracle: public['oracle_segmentation']=case['oracle_segmentation']
    if inp.exists(): assert json.loads(inp.read_text())==public
    else: write_json(inp,public)
    if not out.exists():
        print('Stage',stage,name,'5s solver /45s worker',flush=True);started=perf_counter()
        try:
            run=subprocess.run([sys.executable,'-m','benchmarks.contraction_coverage_calibration','--worker',str(inp),'--output',str(out)],capture_output=True,text=True,timeout=45)
            if run.returncode: raise RuntimeError(run.stderr[-4000:])
        except subprocess.TimeoutExpired:
            write_json(out,{'public_sha256':digest(public),'result':{'status':'WALL_TIMEOUT','verified':False},'fit_wall_seconds':perf_counter()-started})
    row=json.loads(out.read_text()); assert row['public_sha256']==digest(public)
    q=HiddenRecoveryRequest.from_dict(public['request']);verify(q,row['result'])
    if not control and row['result']['status']=='UNSAT':raise RuntimeError('Verified positive returned UNSAT')
    row.update(name=name,control=control,oracle=oracle,case_sha256=digest(case),prediction=evaluate(case,row['result'],p,control))
    print(name,row['result']['status'],'exact',row['prediction'].get('exact'),'novel forms',row['prediction'].get('novel_plaintext_exact'),flush=True)
    return row


def whole_units(p,q):
    singleton={w[0] for w in q.dictionary.words if len(w)==1}
    return sorted(prior.parts(r)[0][0] for r in p['rules'] if r['position']=='whole' and r['units']==1
                  and prior.parts(r)[0][0] in singleton)


def swaps(result,p,q):
    """Proposal generation uses only returned key/training fit and public dictionary."""
    used={u for w in result['plaintext']['words'] for u in w}; proposals=[]
    for a,b in combinations(whole_units(p,q),2):
        if not used.intersection((a,b)):continue
        candidate=deepcopy(result); book=candidate['encoder']['codebook']
        book[a],book[b]=book[b],book[a]
        candidate['plaintext']['words']=[[b if u==a else a if u==b else u for u in w] for w in candidate['plaintext']['words']]
        try: verify(q,candidate)
        except RuntimeError: continue
        proposals.append({'swap':[a,b],'result':candidate})
    return proposals


def frequency_score(result,case,p):
    model=case['reference_model'];counts=model['counts'];denominator=model['tokens']+len(counts)+1
    words=[prior.expand(w,p['expansions']) for w in result['plaintext']['words'][:32]]
    assert len(words)==32
    return sum(math.log((counts.get(w,0)+1)/denominator) for w in words)/len(words)


def rerank(result,case,p):
    q=HiddenRecoveryRequest.from_dict(case['request'])
    candidates=[{'swap':None,'result':result}]+swaps(result,p,q)
    scores=[frequency_score(c['result'],case,p) for c in candidates]
    order=sorted(range(len(candidates)),key=lambda i:(-scores[i],i));selected=order[0]
    # Holdout and truth first inspected only after candidates and selection are frozen.
    evaluations=[evaluate(case,c['result'],p) for c in candidates]
    return {'candidates':candidates,'scores':scores,'order':order,'selected_index':selected,
            'evaluations':evaluations,'scope':'Recovered first key plus valid wholeword single swaps; no truth injection; original32 training words only.'}


def run():
    p=prepare();stages={}
    for i in range(1,8):
        path=OUT/f'iteration-{i}.json'
        if path.exists():stages[i]=json.loads(path.read_text());continue
        plan={'iteration':i,'prepared_sha256':digest(p),'previous_sha256':digest(stages[i-1]) if i>1 else None}
        rows=[];proofs=[];ranked=[]
        if i==1:
            plan['purpose']='Audit both-homophone coverage and inevitable repeated wholeword forms'
            write_json(OUT/f'plan-{i}.json',plan)
            assessment={'sources':{name:{'carriers':design['carriers'],'overlap':design['carrier_held_form_overlap'],
                'novel_held_forms':sum(p['cases'][name]['contracted']['novel_plaintext_mask']),
                'fully_covered':all(p['cases'][name]['contracted']['coverage_mask'])} for name,design in p['designs'].items()},
                'decision':'Coverage guaranteed; proceed to first-key hidden diagnostics; retain repeated and novel denominators'}
        elif i in (2,3,4):
            name={2:'caesar',3:'aquinas',4:'einhard'}[i]
            plan.update(source=name,purpose='Coverage-controlled H2one-glyph first-key recovery; letters comparison and shuffle')
            write_json(OUT/f'plan-{i}.json',plan)
            for label in ('contracted','letters'):
                case=p['cases'][name][label];rows.append(fit(p,i,label+'-positive',case))
                if label=='contracted':rows.append(fit(p,i,'contracted-shuffle',case,control=True))
            assessment={'source':name,'outcomes':{r['name']:{'status':r['result']['status'],**{k:r['prediction'].get(k) for k in ('exact','novel_plaintext_words','novel_plaintext_exact')}} for r in rows},
                'decision':'Next independent excerpt, then test wholeword identifiability without more solver time'}
        elif i==5:
            plan['purpose']='Construct verified alternative wholeword ownerships even with full code coverage'
            write_json(OUT/f'plan-{i}.json',plan)
            for source in ('caesar','aquinas','einhard'):
                case=p['cases'][source]['contracted'];q=HiddenRecoveryRequest.from_dict(case['request'])
                alternatives=swaps(case['truth'],p,q)
                proofs.append({'source':source,'generating':case['truth'],'alternatives':alternatives,
                    'evaluations':[evaluate(case,a['result'],p) for a in alternatives],
                    'scope':'Truth-assisted constructive nonidentifiability witnesses; never candidate inputs to ranking'})
            assessment={'verified_alternatives':{r['source']:len(r['alternatives']) for r in proofs},
                'decision':'Coverage cannot identify wholeword ownership; test frozen soft frequency ranking on recovered keys, not injected truth'}
        elif i==6:
            plan['purpose']='Return to external frequency only for explicit wholeword ownership alternatives'
            write_json(OUT/f'plan-{i}.json',plan)
            for stage,source in ((2,'caesar'),(3,'aquinas'),(4,'einhard')):
                first=next(r for r in stages[stage]['rows'] if r['name']=='contracted-positive')
                if first['result']['status']!='SAT':
                    ranked.append({'source':source,'status':'NOT_EVALUATED_NO_SAT'});continue
                ranked.append({'source':source,'status':'EVALUATED',**rerank(first['result'],p['cases'][source]['contracted'],p)})
            assessment={'outcomes':{r['source']:{'status':r['status'],**({'first_exact':r['evaluations'][0]['exact'],
                'selected_exact':r['evaluations'][r['selected_index']]['exact'],'candidate_count':len(r['candidates'])} if r['status']=='EVALUATED' else {})} for r in ranked},
                'decision':'No generalization claim from three revisited passages; one frozen fresh-source mixed-width diagnostic remains'}
        else:
            plan.update(source='caroli',purpose='Fresh-source H2mixed hidden-boundary recovery; oracle contracted only if hidden UNKNOWN; frequency rule unchanged')
            write_json(OUT/f'plan-{i}.json',plan)
            for label in ('contracted','letters'):
                case=p['cases']['caroli'][label];row=fit(p,i,label+'-positive',case);rows.append(row)
                if label=='contracted':
                    rows.append(fit(p,i,'contracted-shuffle',case,control=True))
                    if row['result']['status'] in ('UNKNOWN','WALL_TIMEOUT'):
                        rows.append(fit(p,i,'contracted-oracle',case,oracle=True))
                    elif row['result']['status']=='SAT':
                        ranked.append({'source':'caroli','status':'EVALUATED',**rerank(row['result'],case,p)})
            assessment={'outcomes':{r['name']:{'status':r['result']['status'],**{k:r['prediction'].get(k) for k in ('exact','novel_plaintext_words','novel_plaintext_exact')}} for r in rows},
                'decision':'Stop after7. Report missing evidence removed, residual ownership ambiguity and mixed-boundary performance separately; no manuscript or timeout escalation'}
        stage={'plan':plan,'rows':rows,'proofs':proofs,'ranked':ranked,'assessment':assessment}
        write_json(path,stage);stages[i]=json.loads(path.read_text());print('Completed stage',i,flush=True)
    report={'prepared_sha256':digest(p),'complete':True,'iterations':[s['assessment'] for s in stages.values()],
            'solver_calls':sum(len(s['rows']) for s in stages.values())}
    write_json(OUT/'report.json',report);return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run',action='store_true');parser.add_argument('--worker');parser.add_argument('--output');args=parser.parse_args()
    if args.worker:prior.worker(args.worker,args.output)
    elif args.run:run()
    else:prepare()
