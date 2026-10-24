"""Evaluation-only score decomposition, fixed excerpts and trajectory attribution."""
import argparse
from collections import Counter
import gzip
import json
import math
from pathlib import Path

from voynich_smt.word_mapping.scalable.data import CipherStream
from voynich_smt.word_mapping.scalable.inventory import Inventory
from voynich_smt.word_mapping.scalable.trigram import load_model
from voynich_smt.word_mapping.scalable.sparse_lm import BOS


def band(count):
    return '1' if count == 1 else '2-4' if count < 5 else '5-19' if count < 20 else '20-99' if count < 100 else '100+'


def decomposition(model, stream, key):
    score = sum(model.score(key[c] for c in d) for d in stream.documents)
    base, observed, events = 0., 0, 0
    for doc in stream.documents:
        previous = BOS
        for cipher in doc:
            word = key[cipher]
            base += math.log(model.base_probability(word))
            observed += (previous, word) in model.edges
            previous, events = word, events + 1
        base += math.log(model.base_probability(model.eos))
        observed += (previous, model.eos) in model.edges
        events += 1
    return {'source_score': score, 'scoring_order':getattr(model,'order',2),
            'observed_edge_scope':'bigram projection', 'base_frequency_component': base,
            'context_component': score - base, 'prediction_events': events,
            'observed_edge_fraction': observed/events}


def attribution(events, truth_ids, final_key, counts):
    n = len(truth_ids)
    flags = {name: [False]*n for name in ('offered', 'active', 'proposed', 'accepted', 'ever_correct', 'visited')}
    best_rank, lost = [None]*n, [0]*n
    key, owner, moves, pools = None, {}, 0, 0
    offered_evaluations = 0
    proposed_by_source, accepted_by_source = Counter(), Counter()
    displacement_events = []
    for event in events:
        if event['kind'] == 'initial':
            key = list(event['assignments'])
            owner = {word:c for c,word in enumerate(key)}
            flags['ever_correct'] = [word == true for word,true in zip(key,truth_ids)]
        elif event['kind'] == 'pool':
            assert key is not None
            pools += 1
            offered_evaluations += len(event['offered'])
            cipher = event['cipher']
            active = set(event['active'])
            for rank, (word, delta) in enumerate(event['offered'], 1):
                implied = {cipher: word}
                other = owner.get(word)
                if other is not None and other != cipher:
                    implied[other] = key[cipher]
                for c,w in implied.items():
                    if w == truth_ids[c]:
                        flags['offered'][c] = True
                        flags['active'][c] |= word in active
                        best_rank[c] = min(best_rank[c] or rank, rank)
        elif event['kind'] == 'move':
            moves += 1
            proposed_by_source[event.get('source','unknown')] += 1
            accepted_by_source[event.get('source','unknown')] += bool(event['accepted'])
            cipher = event['cipher']
            flags['visited'][cipher] = True
            changes = dict(event['changes'])
            proposed = {cipher: event['word_id'], **changes}
            for c,w in proposed.items():
                if w == truth_ids[c]:
                    flags['offered'][c] = flags['proposed'][c] = True
            if event['accepted']:
                for c,w in changes.items():
                    displaced = key[c] == truth_ids[c] and w != truth_ids[c]
                    lost[c] += displaced
                    if displaced:
                        displacement_events.append({'step': event.get('step'), 'cipher': c,
                            'old_word_id': key[c], 'new_word_id': w, 'move_delta': event.get('delta'),
                            'source': event.get('source')})
                    if w == truth_ids[c]:
                        flags['accepted'][c] = flags['ever_correct'][c] = True
                    del owner[key[c]]
                for c,w in changes.items():
                    key[c], owner[w] = w,c
    assert key is not None
    categories = Counter()
    rows = []
    for c,true in enumerate(truth_ids):
        if true is None:
            reason = 'inventory_absent'
        elif final_key[c] == true:
            reason = 'recovered'
        elif flags['ever_correct'][c]:
            reason = 'acquired_then_lost'
        elif not flags['offered'][c]:
            reason = 'never_offered'
        elif not flags['proposed'][c]:
            reason = 'active_not_chosen' if flags['active'][c] else 'offered_not_active'
        else:
            reason = 'proposed_not_accepted'
        categories[reason] += 1
        rows.append({'cipher':c, 'count':counts[c], 'band':band(counts[c]), 'category':reason,
                     **{name: values[c] for name,values in flags.items()},
                     'best_offered_rank':best_rank[c], 'correct_assignment_displacements':lost[c]})
    return {'categories':dict(categories), 'rows':rows, 'moves':moves, 'pool_refreshes':pools,
            'offered_evaluations':offered_evaluations,
            'proposed_by_source':dict(proposed_by_source),'accepted_by_source':dict(accepted_by_source),
            'visited_types':sum(flags['visited']), 'displacement_events': displacement_events, 'final_trajectory_key':key,
            'accounting':'Offers include direct pool assignments and the implied other row of candidate swaps. Initial correctness and all accepted displacements are tracked. Categories describe the saved score-selected key, not a causal proof.'}


def analyze(resources, root, truth_path, traces, output):
    inference = json.loads((root/'inference.json').read_text())
    stream = CipherStream.load(root/'public/cipher.json')
    truth = json.loads(truth_path.read_text())
    assert truth['public_sha256'] == stream.identity
    trace_report = json.loads((traces/'trace-report.json').read_text())
    assert trace_report['protocol'] == inference['protocol']
    inventory = Inventory(resources/'inventory.sqlite')
    output.mkdir(parents=True, exist_ok=False)
    try:
        model = load_model(resources/'model.sqlite',inventory)
        assert model.identity == inference['protocol']['model_sha256']
        counts = Counter(c for d in stream.documents for c in d)
        true_ids = []
        for word in truth['decoding']:
            try: true_ids.append(inventory.id(word))
            except KeyError: true_ids.append(None)
        rank = sorted(counts,key=lambda c:(-counts[c],c))
        source_rank = sorted(range(model.size),key=lambda w:(-model.counts[w],w))
        frequency = [0]*stream.type_count
        for c,w in zip(rank,source_rank): frequency[c]=w
        keys = {'frequency':frequency}
        keys.update({f'seed-{r["seed"]}':r['joint_archive'][0]['assignments'] for r in inference['runs']})
        if all(w is not None for w in true_ids): keys['truth_diagnostic']=true_ids
        methods = {}
        for name,key in keys.items():
            correct = {c for c,w in enumerate(key) if w == true_ids[c]}
            groups = {}
            for label in ('1','2-4','5-19','20-99','100+'):
                members = [c for c in counts if band(counts[c])==label]
                tokens = sum(counts[c] for c in members)
                hits = sum(c in correct for c in members)
                groups[label] = {'types':len(members),'tokens':tokens,'correct_types':hits,
                    'token_accuracy':sum(counts[c] for c in members if c in correct)/tokens if tokens else None}
            methods[name] = {**decomposition(model,stream,key),'correct_types':len(correct),
                'token_accuracy':sum(counts[c] for c in correct)/sum(counts.values()),'frequency_bands':groups}
        attributions = {}
        for run in inference['runs']:
            path = traces/f'seed-{run["seed"]}.jsonl.gz'
            with gzip.open(path,'rt',encoding='utf-8') as handle:
                result = attribution((json.loads(line) for line in handle),true_ids,run['joint_archive'][0]['assignments'],counts)
            checkpoint = json.loads((root/f'seed-{run["seed"]}/checkpoint.json').read_text())['payload']
            assert result['final_trajectory_key'] == checkpoint['assignments']
            assert result['moves'] == run['step']
            assert result['categories'].get('recovered',0) == methods[f'seed-{run["seed"]}']['correct_types']
            attributions[str(run['seed'])] = result
        # Freeze five equally spaced corpus positions, 40 words each, without
        # looking at score differences or original grammatical annotations.
        total = sum(map(len,stream.documents))
        samples=[]
        for number in range(5):
            offset = number*total//5
            doc_id,local = 0,offset
            while local >= len(stream.documents[doc_id]):
                local -= len(stream.documents[doc_id]); doc_id += 1
            ids = stream.documents[doc_id][local:local+40]
            samples.append({'global_offset':offset,'document':doc_id,'local_offset':local,
                'tokens':len(ids),'truth':' '.join(truth['decoding'][c] for c in ids),
                'decoded':{name:' '.join(inventory.word(key[c]) for c in ids) for name,key in keys.items() if name!='truth_diagnostic'}})
        top = [{'cipher':c,'count':counts[c],'truth':truth['decoding'][c],
                'decoded':{name:inventory.word(key[c]) for name,key in keys.items() if name!='truth_diagnostic'}} for c in rank[:30]]
        report={'scope':'post-hoc engineering diagnostics, not grammatical/semantic adjudication',
            'cipher_sha256':stream.identity,'model_sha256':model.identity,'methods':methods,
            'attribution':attributions,'fixed_samples':samples,'frequent_mappings':top,
            'grammar':'unscored; excerpts prepared for qualitative review', 'semantics':'unscored',
            'limitations':['Truth is diagnostic/evaluation only; resource overlap/coverage requires the preparation audit.',
                'Candidate/move traces are observational and checked against saved final keys, not fresh validation.',
                'A counterexample between two wrong keys does not show the true key is disfavored.',
                'No grammar or meaning score is inferred from literal recovery or LM decomposition.']}
        (output/'diagnostics.json').write_text(json.dumps(report,indent=2)+'\n')
        lines=['# Fixed decoding inspection set','',
               'Evaluation-only EWT excerpts. Five predeclared quantile positions; up to 40 words without crossing a document endpoint.',
               'Attribution: UD English EWT contributors and original source creators; source/license manifest: data/raw/scalable-english/.',
               'No human adjudication or grammatical/semantic score is claimed.','']
        if model.config.language == 'la':
            lines[2] = 'Evaluation-only Latin excerpts at five fixed quantile positions; up to 40 words.'
            lines[3] = 'Attribution and original source/license manifests: see docs/scalable_latin_caesar.md.'
        for i,sample in enumerate(samples,1):
            lines += [f'## Sample {i}: offset {sample["global_offset"]}', '', '**Reference**', '', sample['truth'],'']
            for name,text in sample['decoded'].items(): lines += [f'**{name}**','',text,'']
        (output/'inspection.md').write_text('\n'.join(lines)+'\n')
        return report
    finally: inventory.close()


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--resources',type=Path,default=Path('experiments/results/scalable-english/foundations-ewt-v1'))
    parser.add_argument('--run',type=Path,default=Path('experiments/results/scalable-english/search-ewt-v1'))
    parser.add_argument('--truth',type=Path,default=Path('experiments/results/scalable-english/retrieval-ewt-v2/evaluation-only/truth.json'))
    parser.add_argument('--traces',type=Path,default=Path('experiments/results/scalable-english/search-ewt-diagnostics-v1/traces'))
    parser.add_argument('--output',type=Path,default=Path('experiments/results/scalable-english/search-ewt-diagnostics-v1/analysis-v2'))
    args=parser.parse_args()
    result=analyze(args.resources,args.run,args.truth,args.traces,args.output)
    print(json.dumps({'methods':{k:{p:v[p] for p in ('source_score','base_frequency_component','context_component','correct_types','token_accuracy')} for k,v in result['methods'].items()},'failures':{k:v['categories'] for k,v in result['attribution'].items()}},indent=2))
