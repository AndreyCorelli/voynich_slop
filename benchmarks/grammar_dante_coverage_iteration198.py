"""Frozen FORM-only admission/overlap/coverage for reserved Dante; no gold labels."""
import re,unicodedata,hashlib
from collections import Counter,defaultdict
from benchmarks.grammar_multi_author_iteration193 import ROOT,Path,load,save,digest,graph
OUT=ROOT/'iteration198';BASE=ROOT/'iteration193';CAT=Path('experiments/datasets/latin-grammar-expansion/v1')
POLICY='FORM-only reserved Dante coverage, no POS/Case/LEMMA/HEAD/DEPREL access. Primary explicit collection reserved authorDante: DVE andMon only, secure prose; authorDante-attributed letters remain unprojected alongside all quarantined/disputed/mixed works. UDante06fbba3 pinned bytes; licensing declarations conflict retained unresolved, no rights/publication claim. Same197 ID/FORM-only parsing and193 normalization/MWT rejection/punctuation/sentence boundaries; exact lexical sentence or within-sentence12word overlap with all six193 admitted development authors excludes reserved sentence only. First within-Dante exact duplicate retained in sorted-file order; same sorted-work roundrobin30000/work and30000total, frequency5 and>=2distinctshared lexical-neighbor frames. Freeze preoverlap/postoverlap/final and single-work diagnostics including support multiplicity histograms; never select better stage/relax rules. >=10pairs means possible later top10 attempt, not accuracy; smaller/empty explicit. No models/predictions/new gold/reserved-label scoring. Dante prior raw exposure remains; annotation/current-model reserve, not globally unseen literature. Future scoring needs independently frozen protocol/models; no Case/POS decoding now.'


def normalize(s):
    s=''.join(c for c in unicodedata.normalize('NFD',s.lower()) if unicodedata.category(c)!='Mn').replace('j','i').replace('v','u')
    return s if re.fullmatch('[a-z]+',s) else None

def sentence_form_rows(path):
    sid=None;rows=[]
    with path.open() as handle:
        for line in handle:
            if line.startswith('# sent_id ='):sid=line.split('=',1)[1].strip()
            elif line.startswith('#'):continue
            elif line.strip():rows.append(line.rstrip('\n'))
            elif rows:
                yield sid,rows;sid=None;rows=[]
    if rows:yield sid,rows

def signature(words):return hashlib.sha256(' '.join(words).encode()).hexdigest()
def windows(words):return {signature(words[i:i+12]) for i in range(max(0,len(words)-11))}

def coverage(rows,name):
    ids,positions,dd=graph(rows,name);counts=Counter(ids);lexical={ids[i] for i,p in enumerate(positions) if p};types={e[k] for e in dd for k in ['a','b']};compared={p for e in dd for f in e['frames'] for k in ['a_positions','b_positions'] for p in f[k]}
    return dict(sentences=len(rows),lexical_tokens=sum(r['n'] for r in rows),lexical_types=len(lexical),floor5_types=sum(counts[w]>=5 for w in lexical),candidate_pairs=len(dd),candidate_endpoint_types=len(types),distinct_shared_frames=len({tuple(f['frame']) for e in dd for f in e['frames']}),shared_frame_occurrences=len(compared),top10_candidate_coverage='sufficient_candidates_only' if len(dd)>=10 else ('empty' if not dd else 'insufficient_candidates')),dict(ids=ids,positions=positions,descriptors=dd)

def run():
    assert not OUT.exists();OUT.mkdir();(OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    registry=[r for r in load(CAT/'reserved_evaluation-sentences.json') if r['author']=='Dante'];assert registry and {r['corpus'] for r in registry}=={'udante'};paths=sorted({r['path'] for r in registry});inputs=[Path(__file__),Path('benchmarks/grammar_multi_author_iteration193.py'),CAT/'verification-manifest.json',CAT/'reserved_evaluation-sentences.json',CAT/'udante-provenance.json',BASE/'verification-manifest.json',BASE/'admission.json',CAT/'license-reconciliation.json']+[Path(p) for p in paths]
    save(OUT/'design-freeze.json',dict(policy=POLICY,inputs={str(p):digest(p) for p in inputs}))
    for p,h in load(BASE/'verification-manifest.json').items():assert digest(Path(p))==h
    provenance=load(CAT/'udante-provenance.json')
    for f in provenance['files']:assert digest(Path(f['path']))==f['sha256']
    assert {r['work'] for r in registry}=={'DVE','Mon'}
    save(OUT/'provenance-status.json',load(CAT/'license-reconciliation.json')['udante'])
    allow={(r['path'],r['sent_id']):r for r in registry};save(OUT/'allowed-sentences.json',registry)
    development=load(BASE/'admission.json');exact=defaultdict(list);shingles=defaultdict(set)
    for author,rr in development.items():
        for r in rr:
            words=[t['word'] for t in r['tokens'] if t['word']];key=signature(words);exact[key].append(dict(author=author,path=r['path'],sent_id=r['sent_id']))
            for h in windows(words):shingles[h].add((author,r['path'],r['sent_id']))
    pre=[];clean=[];seen=set();records=[];counts=Counter();found=set()
    for path in paths:
        for sid,raw in sentence_form_rows(Path(path)):
            if (path,sid) not in allow:continue
            found.add((path,sid));entry=allow[(path,sid)];cells=[line.split('\t',2) for line in raw];record=dict(path=path,sent_id=sid,author='Dante',work=entry['work'])
            if any('-' in c[0] for c in cells):record['status']='mwt_sentence';counts['mwt_sentence']+=1;records.append(record);continue
            tokens=[dict(row=int(c[0]),word=normalize(c[1])) for c in cells if c[0].isdigit()];words=[t['word'] for t in tokens if t['word']]
            if not words:record['status']='no_lexical_words';counts['no_lexical_words']+=1;records.append(record);continue
            key=signature(words);r=dict(**record,key=key,tokens=tokens,n=len(words));pre.append(r)
            hits=sorted(windows(words)&set(shingles));exacthits=exact.get(key,[]);record.update(n=len(words),key=key,exact_development_matches=exacthits,overlapping_12word_hashes=hits,shingle_source_sentences=[dict(author=a,path=p,sent_id=s) for a,p,s in sorted({item for h in hits for item in shingles[h]})])
            if exacthits or hits:record['status']='development_overlap';counts['development_overlap']+=1
            elif key in seen:record['status']='within_dante_duplicate';counts['within_dante_duplicate']+=1
            else:record['status']='clean_before_budget';clean.append(r);counts['clean_before_budget']+=1
            seen.add(key);records.append(record)
    assert found==set(allow)
    works={w:iter([r for r in clean if r['work']==w]) for w in sorted({r['work'] for r in clean})};used=Counter();total=0;selected=[]
    while works:
        for w in list(works):
            r=next(works[w],None)
            if r is None:del works[w];continue
            if used[w]+r['n']>30000 or total+r['n']>30000:counts['budget_sentence']+=1;continue
            selected.append(r);used[w]+=r['n'];total+=r['n']
    save(OUT/'overlap-and-admission.json',records);save(OUT/'admitted-sentences.json',selected)
    stages={};graphs={}
    for name,rows in [('pre_overlap',pre),('post_overlap_pre_budget',clean),('primary',selected)]:stages[name],graphs[name]=coverage(rows,'Dante')
    perwork={}
    for work in sorted({r['work'] for r in registry}):perwork[work],_=coverage([r for r in selected if r['work']==work],'Dante')
    save(OUT/'graphs.json',graphs);save(OUT/'summary.json',dict(allowlisted_sentences=len(registry),loss_counts=dict(counts),stages=stages,individual_work_diagnostics=perwork,development_comparator_sentences=sum(map(len,development.values())),development_comparator_authors=list(development),reserved_gold_fields_decoded=False,models_or_predictions_run=False))
    save(OUT/'coverage-freeze.json',{n:digest(OUT/n) for n in ['allowed-sentences.json','admitted-sentences.json','overlap-and-admission.json','graphs.json','summary.json','provenance-status.json']})
    print(load(OUT/'summary.json'))
if __name__=='__main__':run()
