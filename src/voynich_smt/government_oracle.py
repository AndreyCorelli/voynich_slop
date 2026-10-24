"""Source-only structural oracles; never read Case or subject/object roles."""
INHERIT=frozenset({'amod','conj','flat','fixed'})
def dist(i,j):
    d=abs(i-j);return ('left' if j<i else 'right')+':'+('1' if d==1 else '2' if d==2 else '3-4' if d<=4 else '5-8' if d<=8 else 'far')
def bundles(tokens,pos,i):
    cur=i;seen=set();adps=[];depth=0
    while cur not in seen and len(seen)<9:
        seen.add(cur)
        adps=[j for j,t in enumerate(tokens) if t.get('head')==cur and t['rel'].split(':')[0]=='case' and t['pos']=='ADP']
        if adps:break
        t=tokens[cur];h=t.get('head')
        if t['rel'].split(':')[0] not in INHERIT or h is None or not 0<=h<len(tokens):break
        cur=h;depth+=1
    pp=['oraclePP:present='+str(bool(adps))]
    for j in adps:pp.extend(['oraclePP:word='+tokens[j]['word'],'oraclePP:distance='+dist(i,j),'oraclePP:inherited='+str(depth>0)])
    h=tokens[i].get('head');head=[]
    if h is None:head=['oracleHead:ROOT']
    elif 0<=h<len(tokens):head=['oracleHead:pos='+pos[h],'oracleHead:distance='+dist(i,h)]
    else:raise ValueError('Invalid source head')
    return pp,pp+head
