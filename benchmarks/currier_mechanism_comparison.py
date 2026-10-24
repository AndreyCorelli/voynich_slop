"""Paired four-mechanism descriptive comparison, separately for Currier A/B."""
from collections import Counter, defaultdict
from dataclasses import asdict
import hashlib
import json
import math
import os
from pathlib import Path
import random
from statistics import mean

from benchmarks.manuscript_width_audit import clean
from benchmarks.text_generation_comparison import one_edit
from voynich_smt.cipher.base import Encoder
from voynich_smt.data.corpus import digest, write_json
from voynich_smt.models.text import Text

OUT=Path('experiments/results/currier-mechanism-comparison')
EVA=Path('data/processed/zl-eva.json')
NATURAL=Path('experiments/results/contraction-distribution-audit/prepared.json')
SEEDS=(51001,51002,51003)
NULL_RATES=(0.1,0.3)
BOUNDARY_MEANS=(4,6,8)
PROFILES=('preserved', 'independent-null-0.1','positional-null-0.1',
          'independent-null-0.3','positional-null-0.3','renewal-4','renewal-6','renewal-8')


def manuscript_packets(records):
    loci=[]
    for r in records:
        key=(r.get('folio'),r.get('locus'))
        if not loci or loci[-1][0]!=key:loci.append((key,[]))
        loci[-1][1].append(r)
    packets=[];pending=[];folio=None;language=None
    for (f,locus),rs in loci:
        label=rs[0].get('page_variables',{}).get('L')
        valid=(label in ('A','B') and 'P' in locus.split(',')[-1]
               and all(clean(r) and not r.get('uncertain_space_in_locus') for r in rs))
        if f!=folio or label!=language:pending=[]
        folio,language=f,label
        if not valid:continue
        pending.append([tuple(r['tokens']) for r in rs])
        if sum(map(len,pending))>=32:
            packets.append({'folio':f,'currier':label,'lines':pending,'words':sum(map(len,pending))})
            pending=[]
    return packets


def choose_targets(packets):
    selected=[]
    for label in ('A','B'):
        for split in ('development','heldout'):
            pool=[p for p in packets if p['currier']==label and
                ('heldout' if int(hashlib.sha256(p['folio'].encode()).hexdigest()[:8],16)%3==0 else 'development')==split]
            random.Random(51000+(label=='B')*2+(split=='heldout')).shuffle(pool)
            chosen=[];seen=set()
            for p in pool:
                if p['folio'] in seen:continue
                chosen.append({**p,'split':split});seen.add(p['folio'])
                if len(chosen)==6:break
            if len(chosen)!=6:raise ValueError('Insufficient distinct folios; do not replace split rule')
            selected+=chosen
    return selected


def natural_stream(source):
    stream=[]
    for segment in source['segments']:stream+=segment+[None]
    return stream


def take_passage(stream,start,size):
    while start+size<=len(stream):
        selected=stream[start:start+size]
        if all(w is not None for w in selected):return selected,start,start+size
        start+=selected.index(None)+1
    raise ValueError('No unbroken passage at frozen source offset')


def key_for(plain_alphabet,glyphs,seed):
    rng=random.Random(seed);labels=list(glyphs);rng.shuffle(labels)
    nulls=tuple(labels[-2:]);payload=tuple(labels[:-2]);needed=2*len(plain_alphabet)
    singles=min(len(plain_alphabet),len(payload)-2)
    while singles+(len(payload)-singles)*len(payload)<needed:singles-=1
    leaves=[(g,) for g in payload[:singles]]
    doubles=[(a,b) for a in payload[singles:] for b in payload]
    rng.shuffle(doubles);leaves+=doubles[:needed-singles];rng.shuffle(leaves)
    encoder=Encoder({u:tuple(leaves[2*i:2*i+2]) for i,u in enumerate(plain_alphabet)})
    return encoder,nulls


def encode_lines(lines,encoder,seed):
    rng=random.Random(seed);output=[];gaps=[]
    for li,line in enumerate(lines):
        out=[];line_gaps=[]
        for wi,word in enumerate(line):
            emitted=[];offsets=[0]
            for u in word:
                emitted.extend(encoder.codebook[u][rng.randrange(2)]);offsets.append(len(emitted))
            out.append(tuple(emitted))
            line_gaps.append(offsets)
        output.append(out);gaps.append(line_gaps)
    return output,gaps


def insert_nulls(lines,gaps,nulls,rate,seed):
    budget=round(rate*sum(len(w) for line in lines for w in line))
    points=[(li,wi,j,offset) for li,line in enumerate(gaps) for wi,word in enumerate(line) for j,offset in enumerate(word)]
    if budget>len(points):raise ValueError('Null budget exceeds distinct complete-code gaps')
    random_points=random.Random(seed).sample(points,budget)
    def priority(point):
        li,wi,j,_=point;last=len(gaps[li][wi])-1
        return (0 if j==last else 1 if j==0 else 2+last-j,li,wi)
    positional=sorted(points,key=priority)[:budget]
    identity_rng=random.Random(seed+1)
    identities=[identity_rng.choice(nulls) for _ in range(budget)]
    outputs=[]
    for chosen in (random_points,positional):
        mapping={(li,wi,offset):g for (li,wi,_,offset),g in zip(chosen,identities)}
        out=[]
        for li,line in enumerate(lines):
            words=[]
            for wi,word in enumerate(line):
                result=[]
                for j in range(len(word)+1):
                    if (li,wi,j) in mapping:result.append(mapping[li,wi,j])
                    if j<len(word):result.append(word[j])
                words.append(tuple(result))
            out.append(words)
        outputs.append(out)
    return outputs,budget


def resegment(lines,expected_length,seed):
    rng=random.Random(seed);out=[]
    for line in lines:
        stream=[g for w in line for g in w];words=[];word=[]
        for i,g in enumerate(stream):
            word.append(g)
            if i==len(stream)-1 or rng.random()<1/expected_length:
                words.append(tuple(word));word=[]
        out.append(words)
    return out


def moments(values):
    m=mean(values);v=mean((x-m)**2 for x in values)
    return {'mean':m,'variance':v,'skewness':mean((x-m)**3 for x in values)/v**1.5 if v else None}


def correlation(pairs):
    if len(pairs)<2:return None
    xs,ys=zip(*pairs);a=mean(xs);b=mean(ys)
    denominator=math.sqrt(sum((x-a)**2 for x in xs)*sum((y-b)**2 for y in ys))
    return sum((x-a)*(y-b) for x,y in pairs)/denominator if denominator else None


def position_profiles(lines):
    glyphs=Counter(g for line in lines for w in line for g in w)
    rank={g:i for i,g in enumerate(sorted(glyphs,key=lambda g:(-glyphs[g],g)))}
    tables={'word':Counter(),'line':Counter()}
    for line in lines:
        for wi,w in enumerate(line):
            lb=min(3,int(4*(wi+0.5)/len(line)))
            for gi,g in enumerate(w):
                wb=min(3,int(4*(gi+0.5)/len(w)))
                tables['word'][g,wb]+=1;tables['line'][g,lb]+=1
    result={}
    for kind,table in tables.items():
        bybin=Counter();total=sum(table.values())
        for (_,b),n in table.items():bybin[b]+=n
        mi=sum(n/total*math.log2(n*total/(glyphs[g]*bybin[b])) for (g,b),n in table.items())
        result[kind]={'glyph_counts':[[g,b,n] for (g,b),n in sorted(table.items())],
            'rank_profiles':[{str(rank[g]):n/bybin[b] for (g,k),n in table.items() if k==b} for b in range(4)],
            'mutual_information_bits':mi}
    return result


def measure(lines):
    words=[tuple(w) for line in lines for w in line];n=len(words);types=Counter(words);v=len(types)
    lengths=[len(w) for w in words];pairs=n*(n-1)/2
    adjacent=[(a,b) for line in lines for a,b in zip(line,line[1:])]
    near_pairs=0;near_types=0;unique=list(types)
    for i,a in enumerate(unique):
        for b in unique[i+1:]:
            if one_edit(a,b):near_pairs+=types[a]*types[b];near_types+=1
    return {'word_count':n,'glyph_count':sum(lengths),'type_count':v,
        'token_lengths':dict(Counter(lengths)),'type_lengths':dict(Counter(map(len,types))),
        'token_moments':moments(lengths),'type_moments':moments(list(map(len,types))),
        'adjacent_length_correlation':correlation([(len(a),len(b)) for a,b in adjacent]),
        'adjacent_pairs':len(adjacent),'adjacent_repeat_fraction':sum(a==b for a,b in adjacent)/len(adjacent) if adjacent else None,
        'repeated_token_fraction':1-v/n,'repeat_pair_fraction':sum(c*(c-1)/2 for c in types.values())/pairs,
        'near_variant_token_pair_fraction':near_pairs/pairs,
        'near_variant_type_pair_fraction':near_types/(v*(v-1)/2) if v>1 else None,
        'position':position_profiles(lines)}


def js(a,b):
    a={str(k):v for k,v in a.items()};b={str(k):v for k,v in b.items()}
    ta=sum(a.values());tb=sum(b.values());result=0
    if not ta:a={'__empty__':1};ta=1
    if not tb:b={'__empty__':1};tb=1
    for key in a.keys()|b.keys():
        x=a.get(key,0)/ta;y=b.get(key,0)/tb;m=(x+y)/2
        if x:result+=0.5*x*math.log2(x/m)
        if y:result+=0.5*y*math.log2(y/m)
    return result


def distances(generated,target):
    out={'token_length_js':js(generated['token_lengths'],target['token_lengths']),
         'type_length_js':js(generated['type_lengths'],target['type_lengths'])}
    for name in ('mean','variance','skewness'):
        a=generated['token_moments'][name];b=target['token_moments'][name]
        out['token_'+name+'_absolute']=abs(a-b) if a is not None and b is not None else None
    for name in ('adjacent_length_correlation','adjacent_repeat_fraction','repeat_pair_fraction',
                 'near_variant_token_pair_fraction','near_variant_type_pair_fraction','repeated_token_fraction'):
        a=generated[name];b=target[name];out[name+'_absolute']=abs(a-b) if a is not None and b is not None else None
    for kind in ('word','line'):
        out[kind+'_position_rank_js']=mean(js(a,b) for a,b in zip(generated['position'][kind]['rank_profiles'],target['position'][kind]['rank_profiles']))
        out[kind+'_position_mi_absolute']=abs(generated['position'][kind]['mutual_information_bits']-target['position'][kind]['mutual_information_bits'])
    return out


def prepare():
    raw=json.loads(EVA.read_text());natural=json.loads(NATURAL.read_text())
    packets=manuscript_packets(raw['records']);targets=choose_targets(packets)
    glyphs=sorted({g for r in raw['records'] if clean(r) for g in r['tokens']})
    sources={name:natural['sources'][name] for name in ('caesar','aquinas','german-113')}
    passages={}
    for name,source in sources.items():
        stream=natural_stream(source);pointers={'development':0,'heldout':len(stream)//2};chosen=[]
        for target in targets:
            words,start,end=take_passage(stream,pointers[target['split']],target['words']);pointers[target['split']]=end
            chosen.append({'words':words,'start':start,'end':end})
        assert pointers['development']<len(stream)//2
        passages[name]=chosen
    p={'source_sha256':{str(EVA):digest(raw),str(NATURAL):digest(natural)},'targets':targets,
        'eligible_packets':Counter(x['currier'] for x in packets),'glyphs':glyphs,
        'sources':sources,'passages':passages,'seeds':SEEDS,'null_rates':NULL_RATES,'boundary_means':BOUNDARY_MEANS,
        'code_sha256':{str(f):digest(f.read_text()) for f in (Path(__file__),Path('benchmarks/manuscript_width_audit.py'),Path('benchmarks/text_generation_comparison.py'))},
        'protocol':'Atomic lowercase EVA code points count as glyph proxies; L=A/B metadata, paragraph loci only; reject whole uncertain/invalid lines and unlabelled loci, aggregate complete clean lines within a folio, ignoring excluded lines; adjacency never crosses lines or folios. One32+word whole-line packet per selected folio, six development/six heldout per Currier class. SHA256 folio bucket0 modulo3 heldout; fixed sampling. Target line word-count geometry conditions all generators: same real source passage, key, free iid homophone choices and payload across four mechanisms. Natural passages nonoverlapping per source/split, half-stream separation; three key seeds, alphabet public union of clean EVA labels, two reserved null labels, all plaintext units H2prefix-free mixed widths1-2, no contractions. Null rates0.1/0.3 of payload glyph count, exact same budget and identities for uniform complete-code gaps versus end/start/backward positional gap schedule. Resegmentation preserves payload/lines, removes spaces, independent renewal cuts with mean4/6/8; not reversible for original spacing. Freeze all parameters; no tuning/selection, report entire grid separately A/B and development/heldout. Position comparisons include raw labelled profiles, rank-based label-invariant profiles and mutual information. Adjacent pairs within lines only; one-edit excludes exact repeats; pair rates token- and type-weighted. Undefined correlations remain missing. No composite score, posterior likelihood or inferred mechanism classifier; sample-size and empirical-MI biases remain. Source German legacy normalization unchanged. No Z3.'}
    p=json.loads(json.dumps(p));path=OUT/'prepared.json'
    if path.exists():assert json.loads(path.read_text())==p,'Frozen protocol changed'
    else:write_json(path,p)
    return p


def layout(words,line_sizes):
    lines=[];cursor=0
    for size in line_sizes:lines.append([tuple(w) for w in words[cursor:cursor+size]]);cursor+=size
    assert cursor==len(words);return lines


def generate(p,source,index,seed):
    target=p['targets'][index];words=p['passages'][source][index]['words']
    alphabet=sorted({u for w in natural_stream(p['sources'][source]) if w is not None for u in w})
    encoder,nulls=key_for(alphabet,p['glyphs'],seed)
    plain=layout(words,list(map(len,target['lines'])))
    payload,gaps=encode_lines(plain,encoder,seed+10)
    assert encoder.decode(Text(tuple(w for line in payload for w in line)))==Text(tuple(w for line in plain for w in line))
    profiles={'preserved':payload};budgets={}
    for rate in NULL_RATES:
        null_outputs,budget=insert_nulls(payload,gaps,nulls,rate,seed+20)
        budgets[str(rate)]=budget
        for kind,lines in zip(('independent','positional'),null_outputs):
            profiles[f'{kind}-null-{rate}']=lines
            stripped=[[tuple(g for g in w if g not in nulls) for w in line] for line in lines]
            assert stripped==payload
    for expected in BOUNDARY_MEANS:
        lines=resegment(payload,expected,seed+30);profiles[f'renewal-{expected}']=lines
        assert [[g for w in line for g in w] for line in lines]==[[g for w in line for g in w] for line in payload]
    return {'source':source,'target_index':index,'seed':seed,'null_glyphs':nulls,'encoder':asdict(encoder),
            'payload':payload,'budgets':budgets,'profiles':profiles}


def summarize(p,rows):
    groups=defaultdict(list)
    for r in rows:
        t=p['targets'][r['target_index']];groups[t['currier'],t['split'],r['source'],r['profile']].append(r)
    summary=[]
    for key,rs in sorted(groups.items()):
        values={}
        for metric in rs[0]['distances']:
            xs=[r['distances'][metric] for r in rs if r['distances'][metric] is not None]
            values[metric]={'mean':mean(xs) if xs else None,'minimum':min(xs) if xs else None,'maximum':max(xs) if xs else None,'cases':len(xs)}
        summary.append({'currier':key[0],'split':key[1],'source':key[2],'profile':key[3],'distances':values,
            'cases':len(rs),'mean_generated_word_count':mean(r['metrics']['word_count'] for r in rs),
            'mean_generated_word_length':mean(r['metrics']['token_moments']['mean'] for r in rs)})
    return summary


def plots(p,target_metrics,rows):
    os.environ.setdefault('MPLCONFIGDIR',str(OUT/'matplotlib-cache'))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(2,3,figsize=(14,8),sharex=True,sharey=True)
    for ri,label in enumerate(('A','B')):
        for ci,source in enumerate(p['sources']):
            ax=axes[ri,ci]
            indices=[i for i,t in enumerate(p['targets']) if t['currier']==label and t['split']=='heldout']
            def curve(ms):return [mean(sum(n for k,n in m['token_lengths'].items() if int(k)<=x)/m['word_count'] for m in ms) for x in range(1,26)]
            ax.plot(range(1,26),curve([target_metrics[i] for i in indices]),'k-',linewidth=3,label='Voynich')
            for profile in PROFILES:
                ms=[r['metrics'] for r in rows if r['target_index'] in indices and r['source']==source and r['profile']==profile]
                ax.plot(range(1,26),curve(ms),label=profile,alpha=.8)
            ax.set_title(f'Currier {label} / {source}');ax.set_xlabel('Atomic output units per word');ax.set_ylabel('Mean packet CDF');ax.grid(alpha=.2)
    axes[0,0].legend(fontsize=7);fig.tight_layout();fig.savefig(OUT/'heldout-length-cdf.png',dpi=150);plt.close(fig)


def run():
    p=prepare();target_metrics=[measure(t['lines']) for t in p['targets']]
    rows=[]
    for source in p['sources']:
        for i,target in enumerate(p['targets']):
            for seed in SEEDS:
                path=OUT/'cases'/f'{source}-target-{i}-seed-{seed}.json'
                if path.exists():record=json.loads(path.read_text());assert record['prepared_sha256']==digest(p)
                else:
                    generated=generate(p,source,i,seed);results=[]
                    for profile,lines in generated['profiles'].items():
                        metrics=measure(lines);results.append({'source':source,'target_index':i,'seed':seed,'profile':profile,
                            'metrics':metrics,'distances':distances(metrics,target_metrics[i])})
                    record={'prepared_sha256':digest(p),'generation':generated,'results':results};write_json(path,record)
                rows+=record['results']
            print(source,'packet',i+1,'/',len(p['targets']),target['currier'],target['split'],flush=True)
    summary=summarize(p,rows)
    report={'prepared_sha256':digest(p),'target_metrics':target_metrics,'summary':summary,
        'paired_payloads':len(p['sources'])*len(p['targets'])*len(SEEDS),'generated_metric_cases':len(rows),'complete':True,'solver_calls':0}
    write_json(OUT/'report.json',report)
    plots(p,target_metrics,rows)
    import csv
    with (OUT/'comparison.csv').open('w') as stream:
        fields=['currier','split','source','profile','mean_generated_word_count','mean_generated_word_length']+list(summary[0]['distances'])
        writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader()
        for row in summary:writer.writerow({**{k:row[k] for k in fields[:6]},**{k:v['mean'] for k,v in row['distances'].items()}})
    return report


if __name__=='__main__':run()
