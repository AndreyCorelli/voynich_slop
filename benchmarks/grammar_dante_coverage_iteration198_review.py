"""Independent ID/FORM-only admission, budget and occurrence-first graph audit."""
import json,re,unicodedata,hashlib,itertools
from pathlib import Path
from collections import Counter,defaultdict
OUT=Path('experiments/results/grammar-restoration/iteration198');BASE=OUT.parent/'iteration193';CAT=Path('experiments/datasets/latin-grammar-expansion/v1')
def load(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
def signature(words):return hashlib.sha256(' '.join(words).encode()).hexdigest()
def normalize(form):
    txt=''.join(x for x in unicodedata.normalize('NFD',form.lower()) if not unicodedata.category(x).startswith('M')).translate(str.maketrans({'j':'i','v':'u'}))
    return txt if txt and all('a'<=c<='z' for c in txt) else None

def replay_graph(rows):
    boundary=signature(['Dante|BOUNDARY']);ids=[];pos=[]
    for r in rows:
        ids.append(boundary);pos.append(None)
        for t in r['tokens']:
            ids.append(signature(['Dante|'+t['word']]) if t['word'] else boundary);pos.append([r['path'],r['sent_id'],t['row']] if t['word'] else None)
    ids.append(boundary);pos.append(None);counts=Counter(ids);lexical={w for w,p in zip(ids,pos) if p};wordframes=defaultdict(lambda:defaultdict(list))
    for i,p in enumerate(pos):
        if p and counts[ids[i]]>=5 and pos[i-1] and pos[i+1]:wordframes[ids[i]][(ids[i-1],ids[i+1])].append(i)
    descriptors=[];support=Counter()
    for a,b in itertools.combinations(sorted(wordframes),2):
        common=sorted(set(wordframes[a])&set(wordframes[b]))
        if common:support[len(common)]+=1
        if len(common)>=2:descriptors.append(dict(a=a,b=b,shared_frames=len(common),frames=[dict(frame=list(f),a_positions=wordframes[a][f],b_positions=wordframes[b][f]) for f in common]))
    types={e[k] for e in descriptors for k in ['a','b']};compared={i for e in descriptors for f in e['frames'] for k in ['a_positions','b_positions'] for i in f[k]};summary=dict(sentences=len(rows),lexical_tokens=sum(r['n'] for r in rows),lexical_types=len(lexical),floor5_types=sum(counts[w]>=5 for w in lexical),candidate_pairs=len(descriptors),candidate_endpoint_types=len(types),distinct_shared_frames=len({tuple(f['frame']) for e in descriptors for f in e['frames']}),shared_frame_occurrences=len(compared),top10_candidate_coverage='sufficient_candidates_only' if len(descriptors)>=10 else ('insufficient_candidates' if descriptors else 'empty'))
    return dict(ids=ids,positions=pos,descriptors=descriptors),summary,dict(support)

def run():
    assert not (OUT/'audit.json').exists();save(OUT/'review-design.json',dict(code_sha256=sha(Path(__file__)),policy='Independent FORM-only replay, no reserved label fields decoded. Predeclared FORM-only support multiplicity counts, no changed eligibility or model evaluation.'))
    hashes=0
    for p,h in load(OUT/'design-freeze.json')['inputs'].items():assert sha(Path(p))==h;hashes+=1
    for p,h in load(OUT/'coverage-freeze.json').items():assert sha(OUT/p)==h;hashes+=1
    for f in load(CAT/'udante-provenance.json')['files']:assert sha(Path(f['path']))==f['sha256'];hashes+=1
    registry=load(OUT/'allowed-sentences.json');assert registry==[r for r in load(CAT/'reserved_evaluation-sentences.json') if r['author']=='Dante'];assert {r['work'] for r in registry}=={'DVE','Mon'};assert load(OUT/'provenance-status.json')==load(CAT/'license-reconciliation.json')['udante'];allow={(r['path'],r['sent_id']):r for r in registry}
    development=load(BASE/'admission.json');exact=defaultdict(list);shingles=defaultdict(set)
    for a,rows in development.items():
        for r in rows:
            words=[t['word'] for t in r['tokens'] if t['word']];exact[signature(words)].append(dict(author=a,path=r['path'],sent_id=r['sent_id']))
            for i in range(len(words)-11):shingles[signature(words[i:i+12])].add((a,r['path'],r['sent_id']))
    pre=[];clean=[];seen=set();records=[];loss=Counter();found=set()
    for path in sorted({r['path'] for r in registry}):
        # Decode only sent_id and the first two token fields for allowlisted blocks.
        for block in Path(path).read_text().strip().split('\n\n'):
            lines=block.splitlines();sid=next((line[len('# sent_id ='):].strip() for line in lines if line.startswith('# sent_id =')),None)
            if (path,sid) not in allow:continue
            found.add((path,sid));entry=allow[(path,sid)];record=dict(path=path,sent_id=sid,author='Dante',work=entry['work']);forms=[];mwt=False
            for line in lines:
                if not line or line.startswith('#'):continue
                key,_,tail=line.partition('\t')
                if re.fullmatch(r'\d+-\d+',key):mwt=True
                elif key.isdigit():form,_,_=tail.partition('\t');forms.append(dict(row=int(key),word=normalize(form)))
            if mwt:record['status']='mwt_sentence';loss['mwt_sentence']+=1;records.append(record);continue
            words=[t['word'] for t in forms if t['word']]
            if not words:record['status']='no_lexical_words';loss['no_lexical_words']+=1;records.append(record);continue
            key=signature(words);row=dict(**record,key=key,tokens=forms,n=len(words));pre.append(row);hits=sorted({signature(words[i:i+12]) for i in range(len(words)-11)}&shingles.keys());exacthits=exact.get(key,[])
            record.update(n=len(words),key=key,exact_development_matches=exacthits,overlapping_12word_hashes=hits,shingle_source_sentences=[dict(author=a,path=p,sent_id=s) for a,p,s in sorted({x for h in hits for x in shingles[h]})])
            if exacthits or hits:record['status']='development_overlap';loss['development_overlap']+=1
            elif key in seen:record['status']='within_dante_duplicate';loss['within_dante_duplicate']+=1
            else:record['status']='clean_before_budget';clean.append(row);loss['clean_before_budget']+=1
            seen.add(key);records.append(record)
    assert found==set(allow);assert records==load(OUT/'overlap-and-admission.json')
    queues={w:[r for r in clean if r['work']==w] for w in sorted({r['work'] for r in clean})};used=Counter();selected=[];total=0
    for i in range(max(map(len,queues.values()),default=0)):
        for w,rows in queues.items():
            if i>=len(rows):continue
            r=rows[i]
            if used[w]+r['n']<=30000 and total+r['n']<=30000:selected.append(r);used[w]+=r['n'];total+=r['n']
            else:loss['budget_sentence']+=1
    assert selected==load(OUT/'admitted-sentences.json');saved=load(OUT/'summary.json');assert dict(loss)==saved['loss_counts'];assert len(registry)==saved['allowlisted_sentences']
    stages={};graphs=load(OUT/'graphs.json');histograms={}
    for stage,rows in [('pre_overlap',pre),('post_overlap_pre_budget',clean),('primary',selected)]:
        g,s,hist=replay_graph(rows);assert g==graphs[stage];stages[stage]=s;histograms[stage]=hist
    assert stages==saved['stages']
    for work,s in saved['individual_work_diagnostics'].items():assert replay_graph([r for r in selected if r['work']==work])[1]==s
    assert saved['development_comparator_sentences']==sum(map(len,development.values()));assert not saved['reserved_gold_fields_decoded'];assert not saved['models_or_predictions_run']
    save(OUT/'support-histogram-diagnostic.json',dict(disclosure='Predeclared FORM-only support histogram; no changed graph eligibility or model fit.',shared_frame_support_histograms=histograms))
    save(OUT/'audit.json',dict(passed=True,hashes_verified=hashes,allowlisted_sentences_replayed=len(registry),admitted_sentences_replayed=len(selected),stage_graphs_replayed=3,individual_work_graphs_replayed=len(saved['individual_work_diagnostics']),exact_and_12word_overlap_replayed=True,all_form_budget_and_dedup_records_replayed=True,reserved_case_pos_and_other_gold_fields_not_decoded=True,no_models_or_predictions_run=True))
    print(load(OUT/'audit.json'));print(histograms)
if __name__=='__main__':run()
