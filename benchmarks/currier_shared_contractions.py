"""Fixed contraction extension after the shared-letter audit; no B parameter fitting."""
from collections import Counter
import json
from pathlib import Path
from statistics import mean
from benchmarks import currier_shared_parameters as baseline
from benchmarks import currier_mechanism_comparison as base
from benchmarks.latin_contractions import unitizations,expand
from voynich_smt.cipher.base import Encoder
from voynich_smt.data.corpus import digest,write_json
OUT=Path('experiments/results/currier-shared-contractions')
CONFIG=Path('experiments/configs/latin-contractions.json')

def compact_key(alphabet,frequencies,glyphs,seed):
    import random
    rng=random.Random(seed);labels=list(glyphs);rng.shuffle(labels)
    # Keep high-frequency units short; public inventory must fit prefix capacity.
    singles=min(len(alphabet),len(labels)-1)
    while singles+(len(labels)-singles)*len(labels)<len(alphabet):singles-=1
    order=sorted(alphabet,key=lambda u:(-frequencies[u],u));book={u:((g,),) for u,g in zip(order[:singles],labels[:singles])}
    doubles=[(a,b) for a in labels[singles:] for b in labels];rng.shuffle(doubles)
    book.update({u:(c,) for u,c in zip(order[singles:],doubles)})
    return Encoder(book)

def run():
    old=json.loads((baseline.OUT/'report.json').read_text());parent=json.loads(base.OUT.joinpath('prepared.json').read_text());config=json.loads(CONFIG.read_text())
    p={'baseline_sha256':digest(old),'parent_sha256':digest(parent),'config_sha256':digest(config),
       'code_sha256':{str(f):digest(f.read_text()) for f in [Path(__file__),Path(baseline.__file__),Path('benchmarks/latin_contractions.py'),Path(base.__file__)]},
       'protocol':'Extension specified after seeing shared-letter results; not a new independently blinded A/B replication. B data never sets contraction/key parameters. Existing bounded-seven inventory only, minimum-unit witness per word, shared deterministic unitization both halves. Caesar/Aquinas only. Shared25-label prefix-free H1 mixed key with A-source-frequency short-code assignment, plus shared mixedH2 iid/deterministic from original key generator. Every seed91001..3 reported. Public full-source unit alphabet, A-source-half frequencies/key fixed across halves. Same empirical iid word-distribution contrast assumptions as baseline. Rank old and new candidates by A-development mean error only. No contractions invented, learned usage probabilities, B tuning, nulls, boundary edits or Z3.'}
    path=OUT/'prepared.json'
    if path.exists():assert json.loads(path.read_text())==p
    else:write_json(path,p)
    rules=[r for r in config['rules'] if r['id'] in config['profiles']['bounded-seven']];rows=[];books={};unitization={}
    for source in ('caesar','aquinas'):
        stream=base.natural_stream(parent['sources'][source]);half=len(stream)//2;raw={l:[w for w in ws if w is not None] for l,ws in [('A',stream[:half]),('B',stream[half:])]}
        paths={w:min(unitizations(w,rules).items())[1] for ws in raw.values() for w in ws}
        assert all(expand(path,rules)==word for word,path in paths.items());unitization[source]=paths
        words={l:[paths[w] for w in ws] for l,ws in raw.items()};alphabet=sorted({u for ws in words.values() for w in ws for u in w});counts=Counter(u for w in words['A'] for u in w)
        for model in ('contracted-h1-mixed','contracted-h2-independent','contracted-h2-deterministic'):
            selection='independent' if model.endswith('independent') else 'word-deterministic'
            for seed in baseline.SEEDS:
                enc=compact_key(alphabet,counts,parent['glyphs'],seed) if model=='contracted-h1-mixed' else base.key_for(alphabet,parent['glyphs'],seed)[0]
                predictions={l:baseline.expected(ws,enc,selection,seed+10) for l,ws in words.items()}
                delta={k:predictions['B'][k]-predictions['A'][k] for k in predictions['A']};identity=f'{source}-{model}-{seed}';books[identity]=enc.codebook
                rows.append({'id':identity,'source':source,'model':model,'seed':seed,'unit_alphabet':len(alphabet),'predictions':predictions,'delta':delta,
                  'A_development_mean_absolute_error':abs(predictions['A']['mean_word_length']-old['observed']['development']['A']['mean_word_length']),
                  'delta_inside_evaluation_interval':{k:old['evaluation_contrast_intervals'][k][0]<=v<=old['evaluation_contrast_intervals'][k][1] for k,v in delta.items()}})
    allrows=old['conditional_source_half_candidates']+rows;selected=min(allrows,key=lambda r:(r['A_development_mean_absolute_error'],r['id']))
    write_json(OUT/'report.json',{'prepared_sha256':digest(p),'candidates':rows,'all_candidate_count':len(allrows),'selected_on_A_mean_only':selected,'encoders':books,'unitizations':unitization,'complete':True,'solver_calls':0})
    print(json.dumps({'selected':selected,'contraction_candidates_passing_both_contrasts':[r['id'] for r in rows if all(r['delta_inside_evaluation_interval'].values())]},indent=2))

if __name__=='__main__':run()
