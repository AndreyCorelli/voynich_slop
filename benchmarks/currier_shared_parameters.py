"""Shared-key expected A/B contrasts; explicit stationary and source-half scenarios."""
from collections import Counter
import json
from pathlib import Path
import random
from statistics import mean
from benchmarks import currier_structural_constraints as census
from benchmarks import currier_mechanism_comparison as base
from benchmarks import currier_alphabet_comparison as cipher
from benchmarks import currier_mechanism_discrimination as diagnostic
from voynich_smt.data.corpus import digest,write_json
OUT=Path('experiments/results/currier-shared-parameters')
SEEDS=(91001,91002,91003)
MODELS=('mono','sparse-independent','sparse-deterministic','mixed-h2-independent','mixed-h2-deterministic')

def split_folios(folios):
    import hashlib
    return {split:{f:ws for f,ws in folios.items() if ('evaluation' if int(hashlib.sha256(f.encode()).hexdigest()[:8],16)%3==0 else 'development')==split} for split in ('development','evaluation')}

def observable(folios):
    words=[w for ws in folios.values() for w in ws]
    equal=sum(sum(n*(n-1)//2 for n in Counter(ws).values()) for ws in folios.values())
    pairs=sum(len(ws)*(len(ws)-1)//2 for ws in folios.values())
    return {'mean_word_length':mean(map(len,words)),'within_folio_repeat_pair_rate':equal/pairs,'folios':len(folios),'tokens':len(words)}

def intervals(a,b):
    rng=random.Random(93001);values=[];aa=list(a.items());bb=list(b.items())
    for _ in range(1000):
        # Unique keys retain multiplicity as sampled clusters, not duplicate text.
        av=observable({str(i):ws for i,(_,ws) in enumerate(rng.choices(aa,k=len(aa)))})
        bv=observable({str(i):ws for i,(_,ws) in enumerate(rng.choices(bb,k=len(bb)))})
        values.append({k:bv[k]-av[k] for k in ('mean_word_length','within_folio_repeat_pair_rate')})
    return {k:[sorted(v[k] for v in values)[24],sorted(v[k] for v in values)[974]] for k in values[0]}

def expected(words,encoder,selection,seed):
    freq=Counter(words);n=len(words);length=0;repeat=0
    for word,count in freq.items():
        p=count/n
        if selection=='independent':
            length+=p*sum(mean(map(len,encoder.codebook[u])) for u in word)
            repeat+=p*p*__import__('math').prod(1/len(encoder.codebook[u]) for u in word)
        else:
            payload=encode_word(word,encoder,seed);length+=p*len(payload);repeat+=p*p
    return {'mean_word_length':length,'within_folio_repeat_pair_rate':repeat}

def encode_word(word,encoder,seed):
    import hashlib
    out=[]
    for i,u in enumerate(word):
        key=json.dumps([seed,list(word),i],separators=(',',':'))
        choice=int(hashlib.sha256(key.encode()).hexdigest()[:8],16)%len(encoder.codebook[u]);out.extend(encoder.codebook[u][choice])
    return tuple(out)

def prepare():
    parent=json.loads(cipher.PARENT.read_text());source=json.loads(census.SOURCE.read_text());deps=[Path(__file__),Path(census.__file__),Path(base.__file__),Path(cipher.__file__),Path('benchmarks/eva_tokenization.py'),Path('benchmarks/manuscript_width_audit.py')]
    p={'source_sha256':digest(source),'parent_sha256':digest(parent),'code_sha256':{str(f):digest(f.read_text()) for f in deps},'seeds':SEEDS,'models':MODELS,
       'protocol':'Atomic EVA,clean-word paragraph cohort,folioSHA256 bucket0 modulo3 evaluation. Only A development selects nearest candidate expected mean among frozen sources/models/3keys; no B fitting, repeat fitting, null rates or hidden composition fit. Stationary shared plaintext distribution/shared cipher predicts population delta0 for length and repeat rate. Conditional source-half scenario: A draws iid words from first-half empirical source distribution, B from second-half, shared full-source public alphabet/key and development-source homophone allocation. Compare expected deltas and absolute A/B evaluation observables to1000folio-bootstrap contrast intervals. Repeat expectations under iid word draws use empirical probabilities squared (with replacement), not actual finite-source pair counts; manuscript dependence and line geometry unmodelled. This is assumption-conditioned moment prediction, not key recovery or validated selection of a language. No contractions, nulls, spacing changes, Z3 or historical mark assertions. Existing three cached sources only; no new independent text sources.'}
    path=OUT/'prepared.json'
    if path.exists():assert json.loads(path.read_text())==p
    else:write_json(path,p)
    return p,parent,source

def run():
    p,parent,raw=prepare();folios,_,_=census.extract(raw['records'],'clean-words');splits={l:split_folios(folios[l]) for l in ('A','B')}
    observed={split:{l:observable(splits[l][split]) for l in ('A','B')} for split in ('development','evaluation')}
    ci=intervals(splits['A']['evaluation'],splits['B']['evaluation']);rows=[];encoders={}
    for source,data in parent['sources'].items():
        stream=base.natural_stream(data);half=len(stream)//2;words={l:[w for w in part if w is not None] for l,part in [('A',stream[:half]),('B',stream[half:])]}
        alphabet=sorted({u for w in words['A']+words['B'] for u in w})
        counts=Counter(u for w in words['A'] for u in w)
        for model in MODELS:
            kind='allocated' if model.startswith('sparse') else 'mono';allocation=cipher.allocation(alphabet,counts,25,kind=='allocated')
            selection='independent' if model.endswith('independent') else 'word-deterministic'
            for seed in SEEDS:
                encoder=base.key_for(alphabet,parent['glyphs'],seed)[0] if model.startswith('mixed') else cipher.key_for(allocation,parent['glyphs'],seed)
                predictions={l:expected(ws,encoder,selection,seed+10) for l,ws in words.items()}
                delta={k:predictions['B'][k]-predictions['A'][k] for k in predictions['A']}
                identity=f'{source}-{model}-{seed}';encoders[identity]=encoder.codebook
                rows.append({'id':identity,'source':source,'model':model,'seed':seed,'predictions':predictions,'delta':delta,
                 'A_development_mean_absolute_error':abs(predictions['A']['mean_word_length']-observed['development']['A']['mean_word_length']),
                 'delta_inside_evaluation_interval':{k:ci[k][0]<=v<=ci[k][1] for k,v in delta.items()}})
    selected=min(rows,key=lambda r:(r['A_development_mean_absolute_error'],r['id']))
    stationary={k:{'predicted_delta':0,'inside_evaluation_interval':a<=0<=b} for k,(a,b) in ci.items()}
    write_json(OUT/'report.json',{'prepared_sha256':digest(p),'observed':observed,'evaluation_B_minus_A':{k:observed['evaluation']['B'][k]-observed['evaluation']['A'][k] for k in ci},
      'evaluation_contrast_intervals':ci,'stationary_shared_model':stationary,'conditional_source_half_candidates':rows,'selected_on_A_only':selected,'encoders':encoders,'complete':True,'solver_calls':0})
    print(json.dumps({'observed':observed,'intervals':ci,'stationary':stationary,'selected':selected},indent=2))

if __name__=='__main__':run()
