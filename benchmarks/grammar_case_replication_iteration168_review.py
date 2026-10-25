"""Independent passage deduplication, descriptor completeness and case replay."""
from benchmarks.grammar_case_replication_iteration168 import *
import re,unicodedata

def sig(words):
    out=[]
    for token in words:
        text=''.join(c for c in unicodedata.normalize('NFD',token.lower()) if unicodedata.category(c)!='Mn').replace('v','u').replace('j','i');out.extend(re.findall('[a-z]+',text))
    return tuple(out)

def run():
    hc=ec=pc=mc=0
    for name in ['design-freeze','input-freeze','descriptors-freeze','scores-freeze']:
        for p,h in load(OUT/(name+'.json'))['inputs'].items():assert digest(p)==h,p;hc+=1
    old=load(ROOT/'iteration40/data-truth.json');source=load(ROOT/'iteration44/annotations-truth.json');background=load(ROOT/'iteration40/manifest.json')['split_ids']['source'];fit=load(ROOT/'iteration49/manifest.json')['partitions']['0']['fit'];previous={**load(ROOT/'iteration158/selection.json'),**load(ROOT/'iteration159/selection.json')};reserved={r['sent_id'] for rr in load('experiments/holdouts/grammar-construction-next.json')['authors'].values() for r in rr};views=load(ROOT/'iteration160/word-views.json');seen={sig(s['words']) for vv in views.values() for ss in vv.values() for s in ss};seenids={sid for r in previous.values() for sid in r['sent_ids']};authors={}
    for path in RAW:
        headers={}
        for line in path.open():
            if line.startswith('# source = '):headers['source']=line.strip().split(' = ',1)[1].split(',')[0]
            elif line.startswith('# sent_id = '):headers['sent_id']=line.strip().split(' = ',1)[1]
            elif not line.strip():
                if headers.get('sent_id') in background:authors[headers['sent_id']]={"Jerome's Vulgate":'Jerome','Opus agriculturae':'Palladius'}[headers['source']]
                headers={}
    assert set(authors)==set(background);selection=load(OUT/'selection.json');wordinputs=load(OUT/'word-inputs.json');streams=load(OUT/'streams.json');transforms=load(OUT/'transforms.json');caseinputs=load(OUT/'case-inputs.json');descriptors=load(OUT/'descriptors.json');details=load(OUT/'details.json');eligibility=load(OUT/'eligibility.json');summary=load(OUT/'summary.json');contrasts=load(OUT/'contrasts.json')
    for key in STREAMS:
        author=key.split('-',1)[1];pool=[sid for sid in (background if key.startswith('background-') else fit) if (authors[sid] if key.startswith('background-') else source[sid]['author'])==author];kept=[];rejected=[];ss=[];cases=[]
        for sid in pool:
            reason='reserved' if sid in reserved else 'sentence_id_overlap' if sid in seenids else None
            if reason:rejected.append(dict(sent_id=sid,reason=reason));continue
            tt=old[sid] if key.startswith('background-') else source[sid]['tokens'];signature=sig([t['word'] for t in tt])
            if signature in seen:rejected.append(dict(sent_id=sid,reason='normalized_sequence_overlap'));continue
            seen.add(signature);seenids.add(sid);kept.append(sid);ss.append(dict(sent_id=sid,words=[t['word'] for t in tt]));cases.extend(t.get('case','') for t in tt)
        selected=selection[key];assert selected['candidate_sentences']==len(pool) and selected['sent_ids']==kept and selected['rejected']==rejected;assert wordinputs[key]==ss and cases==caseinputs[key];words=[w for s in ss for w in s['words']];ids=[hashlib.sha256(('replication168-'+key+'|'+w).encode()).hexdigest() for w in words];assert streams[key]==ids and selected['tokens']==len(words) and selected['types']==len(set(words));counts=Counter(ids)
        for floor in [5,2]:
            f=str(floor);eligible={w for w,n in counts.items() if n>=floor};assert eligibility[key][f]==len(eligible)
            for view,ix in transforms[key].items():
                if view=='original':assert ix is None;seq=ids;cc=cases
                else:assert ix==np.random.default_rng(int(view[4:])).permutation(len(ids)).tolist();seq=[ids[k] for k in ix];cc=[cases[k] for k in ix]
                assert Counter(seq)==counts;locations={};middles={}
                for j in range(1,len(seq)-1):
                    if seq[j] in eligible:
                        frame=(seq[j-1],seq[j+1]);locations.setdefault(seq[j],{}).setdefault(frame,[]).append(j);middles.setdefault(frame,set()).add(seq[j])
                dd=descriptors[key][f][view];assert len({(e['a'],e['b']) for e in dd})==len(dd);assert sum(e['shared_frames'] for e in dd)==sum(len(ww)*(len(ww)-1)//2 for ww in middles.values());computed=[]
                for e in dd:
                    a,b=e['a'],e['b'];assert a<b and a in eligible and b in eligible;frames=sorted(set(locations[a])&set(locations[b]));assert e['shared_frames']==len(frames);assert e['frames']==[dict(frame=list(frame),a_positions=locations[a][frame],b_positions=locations[b][frame]) for frame in frames];fractions=[];total=valid=matched=0
                    for frame in e['frames']:
                        pairs=[(cc[a],cc[b]) for a in frame['a_positions'] for b in frame['b_positions']];both=[(a,b) for a,b in pairs if a in CASES and b in CASES];right=sum(a==b for a,b in both);total+=len(pairs);valid+=len(both);matched+=right;pc+=len(pairs)
                        if both:fractions.append(right/len(both))
                    computed.append(dict(a=a,b=b,shared_frames=len(frames),case_frames=len(fractions),all_occurrence_pairs=total,case_occurrence_pairs=valid,matching_case_pairs=matched,frame_macro_case_agreement=sum(fractions)/len(fractions) if fractions else None,no_case_conflicts=matched==valid if valid else None));ec+=1
                assert computed==details[key][f][view];assert summary[key][f][view]==summarize_cases(computed,len(eligible));mc+=2
        for f,tt in contrasts[key].items():
            for threshold,r in tt.items():
                actual=summary[key][f]['original'][threshold];pp=[summary[key][f]['word'+str(seed)][threshold]['edge_macro_frame_case_agreement'] for seed in SEEDS if summary[key][f]['word'+str(seed)][threshold]['case_edges']];v=actual['edge_macro_frame_case_agreement'];assert r==dict(actual=actual,null_with_case=len(pp),null_mean=float(np.mean(pp)) if pp else None,null_max=max(pp) if pp else None,null_at_least_actual=sum(p>=v for p in pp) if v is not None else None)
    save(OUT/'audit.json',dict(input_hashes_verified=hc,selection_and_global_deduplication_independently_verified=True,streams_verified=4,view_floor_combinations_verified=136,edge_records_independently_verified=ec,cartesian_occurrence_pairs_checked=pc,metric_groups_verified=mc,no_prior_sentence_id_or_normalized_sequence_overlap=True,reserve_overlap=0,header_only_author_provenance_verified=True,no_new_annotations_or_fitting=True))
if __name__=='__main__':run()
