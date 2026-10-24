"""Post-result representation diagnostic, not a new policy or word exception."""
from benchmarks.grammar_full_context_bank_iteration106 import *
from voynich_smt.unlabeled_caesar_context import numbered_prose
import re


def run():
    paths=[Path(__file__),ROOT/'iteration44/annotations-truth.json',ROOT/'iteration49/manifest.json',CONTEXT/'context-selection.json',OUT/'diagnostic-summary.json',OUT/'pair-cases.json']
    books=load(CONTEXT/'context-selection.json')['views']['expanded']['added_books'];paths += [Path(f'data/raw/word-mapping-caesar/voinich-caesar-{b}.html') for b in books]
    save(OUT/'collision-inputs.json',dict(inputs={str(p):digest(p) for p in paths},scope='POSTRESULT mechanismdiagnostic; no policychange/exclusion/recalibration. Sourcecachedfitannotations andallowedrawbooks ONLY.'))
    data=load(ROOT/'iteration44/annotations-truth.json');ids=load(ROOT/'iteration49/manifest.json')['partitions']['0']['fit'];source=[]
    for sid in ids:
        ts=data[sid]['tokens']
        for i,t in enumerate(ts):
            if t['word']=='c':source.append(dict(sid=sid,pos=t['pos'],preceded_by_ne=i>0 and ts[i-1]['word']=='ne',context=[z['word'] for z in ts[max(0,i-3):i+4]]))
    raw={}
    for book in books:
        chapters=numbered_prose(Path(f'data/raw/word-mapping-caesar/voinich-caesar-{book}.html').read_bytes());matches=[(chapter,text,m) for chapter,text in chapters for m in re.finditer(r'\bc\b',text,re.I)];raw[book]=dict(standalone_c=len(matches),followed_by_period=sum(text[m.end():].lstrip().startswith('.') for _,text,m in matches),examples=[dict(chapter=chapter,text=text[max(0,m.start()-40):m.end()+65]) for chapter,text,m in matches[:3]])
    cases=load(OUT/'pair-cases.json');summary=load(OUT/'diagnostic-summary.json');profiles={};wrong={}
    for view in ['civil','expanded']:
        row=next(c for c in cases if c['block']==view and c['case']=='correct');payload=np.load(OUT/view/'correct.npz');profiles[view]=[]
        for j,p in enumerate(row['pairs']):
            if 'c' not in [row['identities'][i] for i in p['pair']]:continue
            k=next(k for k,i in enumerate(p['pair']) if row['identities'][i]=='c');n=float(payload['counts'][j,:,k].sum());mean=float(payload['sums'][j,:,k].sum()/n);profiles[view].append(dict(partner=[row['identities'][i] for i in p['pair'] if row['identities'][i]!='c'][0],n=int(n),p_cconj=mean,log_adp_over_cconj=float(np.log((1-mean+1e-12)/(mean+1e-12)))))
        for arm in ['frozen95','gain_gap']:
            rows=[r for r in summary['all_wrong_actions'] if r['arm']==arm and r['case'].startswith(view+'/')];wrong[view+'/'+arm]=dict(wrong=len(rows),involves_c=sum('c' in r['selected_words'] for r in rows),rank_stability90=sum(r['features']['stability']>=.9 for r in rows),stability_min=min(r['features']['stability'] for r in rows) if rows else None,stability_max=max(r['features']['stability'] for r in rows) if rows else None)
    save(OUT/'collision-diagnostic.json',dict(source_fit_c_count=len(source),source_fit_c_pos=dict(Counter(r['pos'] for r in source)),source_fit_c_preceded_by_ne=sum(r['preceded_by_ne'] for r in source),source_fit_cconj_preceded_by_ne=sum(r['pos']=='CCONJ' and r['preceded_by_ne'] for r in source),source_examples=source[:8],raw_books=raw,c_masked_class_profiles=profiles,wrong_rank_stability=wrong,interpretation='Observedsourcec predominantlyne+c conjunctioncomponent; addedrawstandalonec fromC.periodabbreviations withheuristicsegmentboundary. Normalizationmergessurfaceinitialwithsyntacticcomponent, suppliedCCONJassignmentdoesnottransfer. Mechanismdiagnosticnotproofgeneralpolicy; no c blacklist or rerun selectedafteroutcomes.'))
    print(json.dumps(load(OUT/'collision-diagnostic.json'),indent=2))
if __name__=='__main__':run()
