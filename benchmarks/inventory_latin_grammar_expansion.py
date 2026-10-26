"""Structural/header-only corpus inventory and explicit author-level admission roles."""
from collections import Counter,defaultdict
import hashlib,json,re
from pathlib import Path
from benchmarks.collect_latin_grammar_expansion import OUT,RAW,save,sha

PROIEL={"Jerome's Vulgate":'Jerome','Opus agriculturae':'Palladius','Epistulae ad Atticum':'Cicero','De officiis':'Cicero','Commentarii belli Gallici':'Caesar'}
PERSEUS={'phi0975.phi001':'Phaedrus','phi1221.phi007':'Augustus','phi1348.abo012':'Suetonius','phi1351.phi005':'Tacitus','tlg0031.tlg027':'Jerome','phi0448.phi001':'Caesar','phi0474.phi013':'Cicero','phi0620.phi001':'Propertius','phi0631.phi001':'Sallust','phi0690.phi003':'Vergil','phi0959.phi006':'Ovid','phi0972.phi001':'Petronius'}

def records(path):
    metadata={};ids=[];mwt=empty=0
    with path.open() as handle:
        for line in handle:
            if line.startswith('#'):
                m=re.match(r'#\s*([\w ]+?)\s*=\s*(.*)',line.rstrip('\n'))
                if m and m[1] in {'sent_id','source','citation_hierarchy'}:metadata[m[1]]=m[2]
            elif line.strip():
                cells=line.rstrip('\n').split('\t');assert len(cells)==10,(path,'column_count');key=cells[0]
                if key.isdigit():ids.append(int(key))
                elif re.fullmatch(r'\d+-\d+',key):mwt+=1
                elif re.fullmatch(r'\d+\.\d+',key):empty+=1
                else:raise ValueError((path,'bad_id',key))
            elif ids:
                assert ids==list(range(1,len(ids)+1)),(path,metadata.get('sent_id'),'ids');assert metadata.get('sent_id');yield metadata,len(ids),mwt,empty;metadata={};ids=[];mwt=empty=0
            else:metadata={}
    if ids:
        assert ids==list(range(1,len(ids)+1));yield metadata,len(ids),mwt,empty

def attribution(slug,meta):
    sid=meta['sent_id']
    if slug=='ittb':
        match=re.fullmatch(r'(train|dev|test)-s(\d+)',sid);assert match,sid;split,n=match[1],int(match[2])
        if split!='train' or n<=104:return 'Aquinas','SCG1','development'
        if 105<=n<=5657:return 'Aquinas','SCG2','development'
        if 5658<=n<=13519:return 'Aquinas','SCG3','development'
        if 16810<=n<=22775:return 'Aquinas','SCG4','development'
        return 'mixed/unknown','ITTB-forma-concordances-or-unregistered','quarantine'
    if slug=='udante':
        work=sid.split('-')[0]
        if work in ['DVE','Mon']:return 'Dante',work,'reserved_evaluation'
        if work=='Epi' and not re.match(r'XIII(?:,|$)',meta.get('citation_hierarchy','')):return 'Dante-attributed',work,'reserved_evaluation'
        return 'mixed/disputed',work,'quarantine'
    if slug=='circse':
        work=sid.rsplit('-',1)[0]
        if work.startswith('Latin_SenecaYounger_'):return 'Seneca',work,'reserved_evaluation'
        if work=='Latin_Tacitus_Ger_prose':return 'Tacitus','Germania','development'
        return 'unknown',work,'quarantine'
    if slug=='llct':return 'anonymous/multiple scribes','LLCT-charters','supplemental_development'
    if slug=='proiel':
        work=meta.get('source','').split(',')[0];return PROIEL.get(work,'unknown'),work,'legacy_existing_policy_only'
    if slug=='perseus':
        work=sid.split('.perseus-')[0];return PERSEUS.get(work,'unknown'),work,'legacy_existing_policy_only'
    raise ValueError(slug)

def run():
    assert not (OUT/'inventory-design.json').exists();save(OUT/'inventory-design.json',dict(date='2026-10-26',code_sha256=sha(Path(__file__)),policy='Metadata/structural validation only: integer token IDs, 10-column row shape, MWT/empty IDs and sentence IDs. Never access FORM/LEMMA/UPOS/FEATS/HEAD/DEPREL fields or text comments; no model/graph/projection/evaluation. Roles fixed by README attribution and ID ranges, not outcomes. All Seneca and secure/attributed Dante labels reserved irrespective upstream train/dev/test. UDante Que/Egl/EpiXIII and ITTB mixedauthor concordances quarantined. LLCT supplemental genre not counted independent namedauthor. Existing PROIEL/Perseus inventoried only; their prior train/holdout reservations take precedence. No legacy heldout sentences or sealed raw works used as features.',upstream_policies={'ittb':'r2.17 README documented train sentence boundaries for SCG1–4; others quarantine','udante':'r2.17 README work/citation IDs and authorship caveats','circse':'r2.17 README and sent_id author/work prefixes','llct':'anonymous/multiple scribes, supplemental development'},prior_exposure='Aquinas/Dante/Tacitus appear in older project experiments/raw corpora; reserve means new annotation/current applicability-model embargo, not globally unseen authors. Seneca is absent from current Cicero model, but no global raw-library novelty claim.'))
    downloads=json.loads((OUT/'downloads.json').read_text());files={};sentences=[];groups=defaultdict(lambda:dict(sentences=0,integer_token_rows=0,mwt_rows=0,empty_rows=0));seen=set()
    for slug in ['ittb','udante','circse','llct','proiel','perseus']:
        folder=RAW/(slug+'-r2.17')
        for path in sorted(folder.glob('*.conllu')):
            total=Counter()
            for meta,n,m,e in records(path):
                sid=meta['sent_id'];assert (slug,sid) not in seen,(slug,sid);seen.add((slug,sid));author,work,role=attribution(slug,meta);entry=dict(corpus=slug,path=str(path),sent_id=sid,author=author,work=work,role=role,integer_token_rows=n,mwt_rows=m,empty_rows=e)
                if slug in ['ittb','udante','circse','llct']:sentences.append(entry)
                k=(slug,author,work,role);groups[k]['sentences']+=1;groups[k]['integer_token_rows']+=n;groups[k]['mwt_rows']+=m;groups[k]['empty_rows']+=e;total.update(sentences=1,integer_token_rows=n,mwt_rows=m,empty_rows=e)
            files[str(path)]=dict(sha256=sha(path),**dict(total))
    summary=[dict(corpus=k[0],author=k[1],work=k[2],role=k[3],**v) for k,v in sorted(groups.items())];save(OUT/'file-inventory.json',files);save(OUT/'work-inventory.json',summary);save(OUT/'sentence-registry.json',sentences)
    for role in ['development','supplemental_development','reserved_evaluation','quarantine']:save(OUT/(role+'-sentences.json'),[r for r in sentences if r['role']==role])
    newtokens=sum(r['integer_token_rows'] for r in sentences);existingtokens=sum(v['integer_token_rows'] for p,v in files.items() if '/proiel-' in p or '/perseus-' in p);legacy_authors=sorted({r['author'] for r in summary if r['corpus'] in ['proiel','perseus'] and r['author']!='unknown'});totals=dict(new_treebanks=4,new_sentence_records=len(sentences),new_integer_token_rows=newtokens,existing_treebanks=2,existing_integer_token_rows=existingtokens,total_integer_token_rows=newtokens+existingtokens,legacy_named_author_groups=legacy_authors,new_principal_named_author_groups=['Aquinas','Dante','Seneca','Tacitus'],new_named_authors_relative_to_existing_treebanks=['Aquinas','Dante','Seneca'],tokens_are='Syntactic integer-ID rows, including punctuation/split clitics; not normalized model-word count',per_role={role:dict(sentences=sum(r['role']==role for r in sentences),integer_token_rows=sum(r['integer_token_rows'] for r in sentences if r['role']==role)) for role in ['development','supplemental_development','reserved_evaluation','quarantine']});save(OUT/'totals.json',totals);print(json.dumps(totals),flush=True)
    for slug in ['ittb','udante','circse','llct']:print(slug,sum(v['integer_token_rows'] for k,v in groups.items() if k[0]==slug),flush=True)
if __name__=='__main__':run()
