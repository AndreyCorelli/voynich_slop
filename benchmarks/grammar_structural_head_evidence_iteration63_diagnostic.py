"""Post hoc distance description of frozen baseline outrankers; no fitting."""
from benchmarks.grammar_structural_head_evidence_iteration63 import OUT,load,save


def run():
    rows=load(OUT/'cue-predictions.json');n=closer=equal=farther=gd=wd=0
    for r in rows:
        h=r['gold'][1];v=r['gold'][2];g=next(c for c in r['candidates'] if c['head']==h)
        for c in r['candidates']:
            if c['head']==h or c['score']<=g['score']+1e-10:continue
            a=abs(h-v);b=abs(c['head']-v);n+=1;closer+=b<a;equal+=b==a;farther+=b>a;gd+=a;wd+=b
    save(OUT/'outranker-distance-diagnostic.json',dict(posthoc=True,scope='gold copular endpoints, same-type baseline outrankers; no retuning',n=n,wrong_closer=closer,equal_distance=equal,wrong_farther=farther,mean_gold_distance=gd/n,mean_wrong_distance=wd/n))
if __name__=='__main__':run()
