"""Independent byte provenance and header-only partition audit; no label inspection."""
from collections import Counter,defaultdict
import hashlib,json,re
from pathlib import Path
ROOT=Path('experiments/datasets/latin-grammar-expansion/v1')

def load(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def expected_role(slug,sid,citation):
    if slug=='ittb':
        prefix,n=sid.split('-s');n=int(n)
        if prefix in ['dev','test'] or n<105:return 'Aquinas','SCG1','development'
        if n<5658:return 'Aquinas','SCG2','development'
        if n<13520:return 'Aquinas','SCG3','development'
        if 16810<=n<=22775:return 'Aquinas','SCG4','development'
        return 'mixed/unknown','ITTB-forma-concordances-or-unregistered','quarantine'
    if slug=='udante':
        work=sid.split('-')[0]
        if work in {'Mon','DVE'}:return 'Dante',work,'reserved_evaluation'
        if work=='Epi' and citation.split(',')[0]!='XIII':return 'Dante-attributed',work,'reserved_evaluation'
        return 'mixed/disputed',work,'quarantine'
    if slug=='circse':
        prefix=sid.rsplit('-',1)[0]
        if 'SenecaYounger' in prefix:return 'Seneca',prefix,'reserved_evaluation'
        assert prefix=='Latin_Tacitus_Ger_prose';return 'Tacitus','Germania','development'
    assert slug=='llct';return 'anonymous/multiple scribes','LLCT-charters','supplemental_development'

def run():
    downloads=load(ROOT/'downloads.json');catalog=load(ROOT/'catalog-freeze.json');design=load(ROOT/'inventory-design.json');assert sha('benchmarks/collect_latin_grammar_expansion.py')==catalog['collector_sha256'];assert sha('benchmarks/inventory_latin_grammar_expansion.py')==design['code_sha256'];rawfiles=metadatafiles=0;license_reconciliation={}
    for source in downloads['sources']:
        assert source['tag']=='r2.17' and re.fullmatch('[0-9a-f]{40}',source['commit'])
        for f in source['files']:
            payload=Path(f['path']).read_bytes();assert hashlib.sha256(payload).hexdigest()==f['sha256'];assert hashlib.sha1(b'blob '+str(len(payload)).encode()+b'\0'+payload).hexdigest()==f['git_blob_sha1'];assert '/'+source['commit']+'/' in f['url'];assert len(payload)==f['bytes'];rawfiles+=1
            if Path(f['path']).name.upper().startswith('LICENSE'):
                text=payload.decode().lower();actual='CC-BY-NC-SA-3.0' if 'by-nc-sa/3.0' in text else 'CC-BY-SA-4.0' if 'by-sa/4.0' in text else None;assert actual;metadatafiles+=1
                readme=Path(f['path']).parent/'README.md';readme_text=readme.read_text().lower();license_reconciliation[source['slug']]=dict(catalog_expected=source['license'],license_file_declares=actual,expected_matches_license_file=actual==source['license'],readme_declares_nc_sa_3=('by-nc-sa/3.0' in readme_text),status='consistent' if actual==source['license'] else 'unresolved_upstream_declaration_conflict',license_path=f['path'],readme_path=str(readme))
    assert {s for s,r in license_reconciliation.items() if not r['expected_matches_license_file']}=={'udante'};assert license_reconciliation['udante']['readme_declares_nc_sa_3'];(ROOT/'license-reconciliation.json').write_text(json.dumps(license_reconciliation,indent=2)+'\n')
    registry=load(ROOT/'sentence-registry.json');files=load(ROOT/'file-inventory.json');expected=[];seen=set();groups=defaultdict(Counter)
    for path,frozen in files.items():
        assert sha(path)==frozen['sha256'];p=Path(path);slug=p.parent.name.split('-r2.17')[0];counts=Counter();block=[]
        def consume(lines):
            if not lines:return
            sid=None;citation='';integer=[];mwt=empty=0
            for line in lines:
                if line.startswith('#'):
                    m=re.match(r'#\s*sent_id\s*=\s*(.+)',line)
                    if m:sid=m[1]
                    m=re.match(r'#\s*citation_hierarchy\s*=\s*(.*)',line)
                    if m:citation=m[1]
                else:
                    cols=line.split('\t');assert len(cols)==10;ident=cols[0]
                    if ident.isdigit():integer.append(int(ident))
                    elif '-' in ident:mwt+=1
                    elif '.' in ident:empty+=1
                    else:raise AssertionError('unknown ID')
            if not integer:return
            assert sid and integer==list(range(1,len(integer)+1));assert (slug,sid) not in seen;seen.add((slug,sid));counts.update(sentences=1,integer_token_rows=len(integer),mwt_rows=mwt,empty_rows=empty)
            if slug in ['ittb','udante','circse','llct']:
                author,work,role=expected_role(slug,sid,citation);r=dict(corpus=slug,path=path,sent_id=sid,author=author,work=work,role=role,integer_token_rows=len(integer),mwt_rows=mwt,empty_rows=empty);expected.append(r);groups[(slug,author,work,role)].update(sentences=1,integer_token_rows=len(integer),mwt_rows=mwt,empty_rows=empty)
        with p.open() as handle:
            for line in handle:
                if line.strip():block.append(line.rstrip('\n'))
                else:consume(block);block=[]
            consume(block)
        assert dict(counts)=={k:v for k,v in frozen.items() if k!='sha256'}
    assert expected==registry;allowed={'corpus','path','sent_id','author','work','role','integer_token_rows','mwt_rows','empty_rows'};assert all(set(r)==allowed for r in registry)
    role_records=[]
    for role in ['development','supplemental_development','reserved_evaluation','quarantine']:
        rows=load(ROOT/(role+'-sentences.json'));assert rows==[r for r in registry if r['role']==role];role_records+=rows
    assert len(role_records)==len(registry)==len({(r['corpus'],r['sent_id']) for r in role_records})
    assert not any(r['author'] in ['Dante','Dante-attributed','Seneca'] and r['role'] in ['development','supplemental_development'] for r in registry)
    total=load(ROOT/'totals.json');assert total['new_integer_token_rows']==sum(r['integer_token_rows'] for r in registry)
    for role,counts in total['per_role'].items():assert counts==dict(sentences=sum(r['role']==role for r in registry),integer_token_rows=sum(r['integer_token_rows'] for r in registry if r['role']==role))
    work=load(ROOT/'work-inventory.json')
    for r in work:
        if r['corpus'] in ['ittb','udante','circse','llct']:assert {k:r[k] for k in ['sentences','integer_token_rows','mwt_rows','empty_rows']}==dict(groups[(r['corpus'],r['author'],r['work'],r['role'])])
    reserve=Path('experiments/holdouts/grammar-construction-next.json');prior=load('experiments/results/grammar-restoration/iteration166/design-freeze.json')['inputs'];assert sha(reserve)==prior[str(reserve)]
    result=dict(download_files_hash_and_git_blob_verified=rawfiles,license_files_verified=metadatafiles,license_metadata_conflicts_flagged=[s for s,r in license_reconciliation.items() if not r['expected_matches_license_file']],conllu_files_structurally_replayed=len(files),new_sentence_role_records_verified=len(registry),all_author_roles_disjoint=True,all_mixed_disputed_sections_quarantined=True,all_new_reserve_annotations_unprojected=True,token_label_fields_and_text_comments_not_inspected=True,all_original_holdout_metadata_unchanged=True,no_graphs_models_or_predictions_run=True)
    (ROOT/'audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
if __name__=='__main__':run()
