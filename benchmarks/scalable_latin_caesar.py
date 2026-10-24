"""Independent Latin sparse resources, continuous Caesar cipher and anchor audit.

Build takes no target input. Truth is read only by preparation/evaluation, never
by the common public-only search runner. Cached inputs only; no downloads.
"""
import argparse
from collections import Counter, defaultdict
import gzip
import hashlib
from itertools import chain
import json
from pathlib import Path
import re
import time
import unicodedata

from voynich_smt.data.latin import normalize as parse_caesar
from voynich_smt.word_mapping.scalable.config import ModelConfig
from voynich_smt.word_mapping.scalable.data import CipherStream, generate
from voynich_smt.word_mapping.scalable.inventory import Inventory
from voynich_smt.word_mapping.scalable.sparse_lm import SparseBigram
from voynich_smt.word_mapping.scalable.trigram import load_model
from voynich_smt.word_mapping.scalable.search import SearchConfig, peak_rss
from benchmarks.scalable_english_run import run
from benchmarks.scalable_english_evaluate import evaluate
from benchmarks.scalable_english_consensus import collect, evaluate as consensus_evaluate

BASE = Path('experiments/results/scalable-latin-caesar')
ROOT = BASE/'v1'
TREEBANKS = Path('data/latin-grammar-benchmark')
LEXICON = Path('experiments/results/latin-form-inventory/upstream-default.txt.gz')
CAESAR = Path('data/raw/pg218.txt')
TOKENIZATION = 'latin-iu-continuous-v1'
# Explicit source registry: unknown sources fail instead of silently entering LM.
PROIEL = {"Jerome's Vulgate": 'Jerome', 'Epistulae ad Atticum': 'Cicero',
          'Opus agriculturae': 'Palladius', 'De officiis': 'Cicero',
          'Commentarii belli Gallici': 'Caesar'}
PERSEUS = {'phi0975.phi001': 'Phaedrus', 'phi0631.phi001': 'Sallust',
           'phi0620.phi001': 'Propertius', 'phi1348.abo012': 'Suetonius',
           'tlg0031.tlg027': 'Vulgate', 'phi0474.phi013': 'Cicero',
           'phi1351.phi005': 'Tacitus', 'phi1221.phi007': 'Petronius',
           'phi0690.phi003': 'Vergil', 'phi0448.phi001': 'Caesar'}
STRUCTURAL_POS = {'CCONJ','SCONJ','ADP','PRON','DET','PART','AUX','ADV'}


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda:handle.read(1024*1024),b''): h.update(block)
    return h.hexdigest()


def write(path, value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n')


def words(text):
    text = ''.join(c for c in unicodedata.normalize('NFD',text.lower()) if unicodedata.category(c)!='Mn')
    return tuple(re.findall('[a-z]+',text.replace('j','i').replace('v','u')))


def sentences(path, corpus, *, registry=None):
    """Read surface rows in treebank order; never use lemmas or split enclitics."""
    for block in path.read_text().strip().split('\n\n'):
        metadata = {}; rows = []
        for line in block.splitlines():
            if line.startswith('# ') and ' = ' in line:
                key,value = line[2:].split(' = ',1); metadata[key] = value
            elif line and not line.startswith('#'):
                columns = line.split('\t')
                if columns[0].isdigit(): rows.append(columns)
        if not rows: continue
        if corpus == 'proiel':
            source = metadata.get('source','').split(',')[0]
            if source not in PROIEL: raise ValueError(f'Unregistered PROIEL source: {source}')
            author = PROIEL[source]
        elif corpus == 'perseus':
            identity = metadata.get('sent_id','').split('.perseus-')[0]
            known = PERSEUS if registry is None else registry
            if identity not in known: raise ValueError(f'Unregistered Perseus source: {identity}')
            source,author = identity,known[identity]
        else: raise ValueError('Unknown corpus')
        # Multiword-token surface replaces its syntactic components. Most cached
        # Latin rows have no MWTs; implementing this keeps future clitics attached.
        mwt = {}
        for line in block.splitlines():
            columns = line.split('\t')
            if len(columns)>1 and re.fullmatch(r'\d+-\d+',columns[0]):
                a,b = map(int,columns[0].split('-')); mwt[a]=(b,columns[1])
        tokens=[]; skip_until=0
        for row in rows:
            i=int(row[0])
            if i<=skip_until: continue
            if i in mwt:
                skip_until,form=mwt[i]; tags={'MWT'}
            else:
                form=row[1]; tags={row[3]}
            if row[3]=='PUNCT': continue
            for word in words(form): tokens.append((word,tags))
        if tokens: yield source,author,tokens


def training(paths):
    docs = {}; pos = defaultdict(Counter); audit = defaultdict(Counter)
    for corpus,path in paths:
        for source,author,tokens in sentences(path,corpus):
            audit[f'{corpus}:{source}']['excluded_tokens' if author=='Caesar' else 'included_tokens']+=len(tokens)
            audit[f'{corpus}:{source}']['sentences']+=1
            if author=='Caesar': continue
            key=f'{corpus}:{source}'
            docs.setdefault(key,[]).extend(w for w,_ in tokens)
            for word,tags in tokens:
                for tag in tags: pos[word][tag]+=1
    return tuple(tuple(doc) for doc in docs.values()), dict(pos), dict(audit)


def lexicon_words(path):
    with gzip.open(path,'rt') as handle:
        for line in handle:
            normalized=words(line.strip())
            if len(normalized)!=1: raise ValueError('Unexpected generated lexicon entry')
            yield normalized[0]


def build(output, *, paths=None, lexicon=LEXICON):
    started=time.monotonic()
    paths = paths or [(c,TREEBANKS/f'{c}-r2.17/la_{c}-ud-train.conllu') for c in ('proiel','perseus')]
    output.mkdir(parents=True,exist_ok=False)
    protocol={'language':'la','tokenization':TOKENIZATION,
              'training_sources':[{'corpus':c,'path':str(p),'sha256':sha(p)} for c,p in paths],
              'lexicon':{'path':str(lexicon),'sha256':sha(lexicon)},
              'inventory_policy':'Entire default generated lexicon union non-Caesar training forms; no target access',
              'training_policy':'Train splits only; explicit source registry excludes all Caesar; concatenate sentences by work in recorded order',
              'normalization':'lowercase, strip diacritics, j to i, v to u, non-ASCII-letter separators; attached enclitics; no sentence resets',
              'registry':{'proiel':PROIEL,'perseus':PERSEUS}}
    write(output/'protocol.json',protocol)
    docs,pos,audit=training(paths)
    write(output/'source-audit.json',audit); write(output/'training-pos.json',pos)
    inventory=Inventory.build(output/'inventory.sqlite',chain(lexicon_words(lexicon),(w for doc in docs for w in doc)))
    try:
        model=SparseBigram.train(inventory,((inventory.id(w) for w in doc) for doc in docs),
                                 config=ModelConfig(language='la',tokenization=TOKENIZATION))
        model.save(output/'model.sqlite')
        report={'benchmark_role':'independent-latin-source-resources','protocol':protocol,
                'inventory_forms':inventory.size,'inventory_sha256':inventory.identity,
                'model_sha256':model.identity,'training_tokens':sum(map(len,docs)),
                'training_documents':len(docs),'observed_edges':len(model.edges),'dictionary_only_forms':model.unseen,
                'excluded_caesar_tokens':sum(r.get('excluded_tokens',0) for r in audit.values()),
                'elapsed_seconds':time.monotonic()-started,'peak_rss_bytes':peak_rss(),
                'limitations':['Small mixed classical/biblical/agricultural corpus; domain mismatch.',
                               'Work streams concatenate disjoint annotated passages in treebank order.',
                               'Generated forms include unattested and potentially overpermissive morphology.']}
        write(output/'report.json',report); return report
    finally: inventory.close()


def frozen_documents(resources):
    protocol=json.loads((resources/'protocol.json').read_text())
    for record in protocol['training_sources']:
        if sha(Path(record['path']))!=record['sha256']: raise ValueError('Training source changed')
    return training([(r['corpus'],Path(r['path'])) for r in protocol['training_sources']])[0]


def prepare(resources, output, *, source=CAESAR, tokens=35000, seed=83):
    if type(tokens) is not int or tokens < 1:
        raise ValueError('tokens must be a positive integer')
    source_manifest=json.loads(source.with_suffix(source.suffix+'.manifest.json').read_text())
    if sha(source)!=source_manifest['sha256']: raise ValueError('Caesar raw hash mismatch')
    parsed=parse_caesar(source_manifest,source.read_text(encoding='utf-8-sig'))
    plaintext=tuple(w for record in parsed.records if record['tokens'] for w in words(record['raw']))[:tokens]
    if not plaintext: raise ValueError('Empty target')
    stream,truth=generate((plaintext,),seed=seed,tokenization=TOKENIZATION)
    docs=frozen_documents(resources)
    windows=lambda doc:(tuple(doc[i:i+12]) for i in range(max(0,len(doc)-11)))
    target=set(windows(plaintext)); overlaps=set()
    for doc in docs: overlaps.update(w for w in windows(doc) if w in target)
    if overlaps: raise ValueError('Training/target 12-word overlap; audit before inference')
    output.mkdir(parents=True,exist_ok=False)
    stream.save(output/'public/cipher.json'); truth.save(output/'evaluation-only/truth.json')
    audit={'source':source_manifest,'source_path':str(source),'normalization':TOKENIZATION,
           'tokens':len(plaintext),'requested_maximum':tokens,'selection':f'First up to {tokens} tokens from cached Gallic War I-IV; no repeats or vocabulary filtering',
           'cipher_sha256':stream.identity,'types':stream.type_count,'documents':1,
           'exact_12_word_overlap_count':len(overlaps),'limits':'Exact normalized overlap only; no paraphrase guarantee.'}
    write(output/'evaluation-only/provenance.json',audit); return audit


def anchor_evaluate(resources, root, truth_path):
    """Evaluation only: public frequency/consensus rules fixed before truth access."""
    stream=CipherStream.load(root/'public/cipher.json')
    inference=json.loads((root/'inference.json').read_text())
    saved=json.loads((root/'consensus-public.json').read_text())
    truth=json.loads(truth_path.read_text())
    if stream.identity!=truth['public_sha256'] or saved['protocol']!=inference['protocol']:
        raise ValueError('Anchor evaluation binding mismatch')
    counts=Counter(c for doc in stream.documents for c in doc); total=sum(counts.values())
    inventory=Inventory(resources/'inventory.sqlite')
    try:
        if inventory.identity!=inference['protocol']['inventory_sha256']: raise ValueError('Inventory mismatch')
        keys=[r['joint_archive'][0]['assignments'] for r in inference['runs']]
        pos=json.loads((resources/'training-pos.json').read_text())
        rows=[]
        for r in saved['rows']:
            c=r['cipher']; proposed=inventory.word(r['word_id']); original=truth['decoding'][c]
            rows.append({**r,'count':counts[c],'proposed':proposed,'original':original,'correct':proposed==original,
                         'per_run':[{'seed':run['seed'],'word':inventory.word(key[c])} for run,key in zip(inference['runs'],keys)],
                         'possible_training_pos':sorted(pos.get(original,{})),
                         'possibly_structural':bool(set(pos.get(original,{})) & STRUCTURAL_POS)})
        rows.sort(key=lambda r:(-r['count'],r['cipher']))
        def measure(selected):
            n=sum(r['count'] for r in selected); correct=[r for r in selected if r['correct']]
            good=sum(r['count'] for r in correct)
            return {'types':len(selected),'correct_types':len(correct),'tokens':n,
                    'type_precision':len(correct)/len(selected) if selected else None,
                    'token_precision':good/n if n else None,'token_coverage':n/total,
                    'correct_token_coverage':good/total}
        grid={f'votes>={votes},count>={minimum}':measure([r for r in rows if r['votes']>=votes and r['count']>=minimum])
              for votes in (2,3) for minimum in (1,20,50,100)}
        primary=[r for r in rows if len(keys)>=3 and r['votes']==len(keys) and r['count']>=100]
        top={}
        for n in (10,20,50):
            selected=rows[:n]
            top[str(n)]={'types':len(selected),'public_token_coverage':sum(r['count'] for r in selected)/total,
                        'runs':[{'seed':run['seed'],
                                 'correct_types':sum(inventory.word(key[r['cipher']])==r['original'] for r in selected),
                                 'token_precision':sum(r['count'] for r in selected if inventory.word(key[r['cipher']])==r['original'])/sum(r['count'] for r in selected)}
                                for run,key in zip(inference['runs'],keys)]}
        bands={}
        for label,predicate in [('1',lambda n:n==1),('2-4',lambda n:2<=n<=4),('5-19',lambda n:5<=n<=19),
                                ('20-99',lambda n:20<=n<=99),('100+',lambda n:n>=100)]:
            selected=[r for r in rows if predicate(r['count'])]
            n=sum(r['count'] for r in selected)
            bands[label]={'types':len(selected),'tokens':n,
                          'runs':[{'seed':run['seed'],'token_accuracy':sum(r['count'] for r in selected if inventory.word(key[r['cipher']])==r['original'])/n if n else None}
                                  for run,key in zip(inference['runs'],keys)]}
        result={'scope':'Evaluation-only literal anchor calibration, not a grammatical or semantic score',
                'primary_rule':'Unanimous across at least 3 runs, public count >=100',
                'initialization':inference['protocol']['search']['initialization'],
                'primary':measure(primary),'primary_rows':primary,'exploratory_grid':grid,
                'primary_possible_class_groups':{
                    'possibly_structural':measure([r for r in primary if r['possibly_structural']]),
                    'other_observed':measure([r for r in primary if r['possible_training_pos'] and not r['possibly_structural']]),
                    'unobserved_in_training':measure([r for r in primary if not r['possible_training_pos']])},
                'top_frequency':top,'frequency_bands':bands,'rows':rows,
                'category_scope':'Possible POS from independent training only, not Caesar contextual gold; ADV is broad and includes content adverbs.',
                'shared_initialization_warning':inference['protocol']['search']['initialization']=='frequency',
                'grammar':'not_evaluated','semantics':'not_evaluated'}
        write(root/'anchors-evaluation.json',result)
        chosen=next(r for r in inference['runs'] if r['seed']==inference['selected_seed'])['joint_archive'][0]['assignments']
        original=truth['plaintext'][0]
        lines=['# Fixed Caesar excerpts','',f"Selected seed: {inference['selected_seed']}. Normalized i/u spelling; punctuation absent.",
               'Positions fixed before evaluation; no selection for recovery. Bold restored words are correct primary anchors.',
               'These are 100-token windows, not recovered paragraph or sentence boundaries.','']
        primary_ids={r['cipher'] for r in primary if r['correct']}
        for offset in (0,len(original)//5,2*len(original)//5,3*len(original)//5,4*len(original)//5):
            document=stream.documents[0][offset:offset+100]
            restored=[inventory.word(chosen[c]) for c in document]
            marked=[f'**{w}**' if c in primary_ids else w for c,w in zip(document,restored)]
            lines.extend([f'## Offset {offset}','','Original:','', ' '.join(original[offset:offset+100]),'',
                          'Restored:','',' '.join(marked),''])
        (root/'inspection.md').write_text('\n'.join(lines)+'\n')
        return result
    finally: inventory.close()


def search(resources, fixture, output, *, initialization='random', proposals=4000, seeds=(3,5,7), budget=600):
    return run(resources,fixture/'public/cipher.json',output,seeds=seeds,
               config=SearchConfig(initialization=initialization,proposals=proposals,budget_seconds=budget,reserve_seconds=10),
               trace=True)


def measure(resources,fixture,output):
    truth=fixture/'evaluation-only/truth.json'
    literal=evaluate(resources,output,truth)
    consensus_path=output/'consensus-public.json'
    if consensus_path.exists():
        from voynich_smt.data.corpus import digest
        saved=json.loads(consensus_path.read_text())
        if saved['input_inference_sha256'] != digest(json.loads((output/'inference.json').read_text())):
            raise ValueError('Saved consensus has different inference input')
    else: collect(output,consensus_path)
    if not (output/'consensus-evaluation.json').exists():
        consensus_evaluate(resources,output,truth,output/'consensus-evaluation.json')
    anchors=anchor_evaluate(resources,output,truth)
    return {'mean_token_accuracy':literal['mean_score_selected_token_accuracy'],
            'selected_token_accuracy':literal['selected_token_accuracy'],'primary_anchors':anchors['primary']}


def main():
    parser=argparse.ArgumentParser(__doc__)
    parser.add_argument('action',choices=('build','prepare','smoke','search-random','search-frequency','measure'))
    args=parser.parse_args(); resources=ROOT/'resources'; fixture=ROOT/'fixture'
    if args.action=='build':
        ROOT.mkdir(parents=True,exist_ok=False)
        write(ROOT/'design.json',{'target':'First up to 35000 tokens, cached Gallic War I-IV, no repeats',
             'main':'3 random starts, seeds 3/5/7, 4000 proposals each',
             'diagnostic':'3 frequency starts, same seeds/cap; shared initial agreement reported separately',
             'primary_anchor':'Unanimous across 3 starts, public count>=100',
             'evaluation':'Top10/20/50 public types; frequency bands; exploratory votes2/3 x count1/20/50/100',
             'inspection':'100 tokens at 0,1/5,2/5,3/5,4/5 of stream',
             'budget_seconds_per_chain':600,'discount':.5,'unseen_mass':.01,
             'model':'Original untempered bigram, entire default generated lexicon plus independent training forms',
             'limits':'Single author/work, normalized i/u, synthetic whole-word substitution; not a Voynich test'})
        print(json.dumps(build(resources),indent=2))
    elif args.action=='prepare': print(json.dumps(prepare(resources,fixture),indent=2))
    elif args.action=='smoke':
        stream=CipherStream.load(fixture/'public/cipher.json')
        # Public prefix only; reindex opaque IDs without reading plaintext.
        first=stream.documents[0][:2000]; ids={c:i for i,c in enumerate(sorted(set(first)))}
        public=CipherStream((tuple(ids[c] for c in first),),len(ids),tokenization=TOKENIZATION)
        smoke=ROOT/'smoke-fixture'; public.save(smoke/'public/cipher.json')
        result=search(resources,smoke,ROOT/'smoke',proposals=100,seeds=(3,))
        print(json.dumps({'steps':result['runs'][0]['step'],'stop_reason':result['runs'][0]['stop_reason']}))
    elif args.action.startswith('search-'):
        mode=args.action.split('-')[1]; search(resources,fixture,ROOT/mode,initialization=mode)
    else:
        results={}
        for mode in ('random','frequency'):
            results[mode]=measure(resources,fixture,ROOT/mode)
            print(mode,json.dumps(results[mode]))
        write(ROOT/'summary.json',results)


if __name__=='__main__': main()
