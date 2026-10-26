"""Independent raw Case and scalar frame-comparison audit of admitted development only."""
import json,re,hashlib
from pathlib import Path
CASES={'Nom','Gen','Dat','Acc','Abl','Voc','Loc'}
ROOT=Path('experiments/results/grammar-restoration')
def load(p):return json.loads(p.read_text())
def run(folder):
    out=ROOT/folder;ad=load(out/'admission.json');graphs=load(out/'graphs.json');refs=load(out/'development-references.json');wanted={(r['path'],r['sent_id']) for rows in ad.values() for r in rows};labels={}
    for path,h in load(out/'admission-audit.json')['raw_hashes'].items():
        assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==h
        for block in Path(path).read_text().strip().split('\n\n'):
            sid=next((line.split('=',1)[1].strip() for line in block.splitlines() if line.startswith('# sent_id =')),None)
            if (path,sid) not in wanted:continue
            for line in block.splitlines():
                if not line or line.startswith('#'):continue
                c=line.split('\t')
                if c[0].isdigit():
                    match=re.search(r'(?:^|\|)Case=([^|]+)',c[5]);labels[(path,sid,int(c[0]))]=match[1] if match and match[1] in CASES else None
    checked=0
    for a,g in graphs.items():
        for e,r in zip(g['descriptors'],refs[a],strict=True):
            total=valid=match=cf=0;fractions=[]
            for f in e['frames']:
                fv=fm=0
                for i in f['a_positions']:
                    for j in f['b_positions']:
                        total+=1;x=labels[tuple(g['positions'][i])];y=labels[tuple(g['positions'][j])]
                        if x and y:fv+=1;fm+=int(x==y)
                valid+=fv;match+=fm
                if fv:cf+=1;fractions.append(fm/fv)
            assert (r['all_occurrence_pairs'],r['case_occurrence_pairs'],r['matching_case_pairs'],r['case_frames'])==(total,valid,match,cf)
            value=sum(fractions)/len(fractions) if fractions else None
            assert r['frame_macro_case_agreement']==value;assert r['no_case_conflicts']==(match==valid if valid else None);checked+=1
    result=dict(passed=True,raw_selected_case_rows_replayed=len(labels),scalar_edge_scores_replayed=checked,only_admitted_development_labels_decoded=True,all_raw_hashes_verified=True)
    (out/'case-audit.json').write_text(json.dumps(result,indent=2)+'\n');print(folder,result)
if __name__=='__main__':
    for folder in ['iteration192-retry','iteration193']:run(folder)
