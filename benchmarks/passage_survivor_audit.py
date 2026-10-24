"""Inspect exact fixed-screen survivors; no key fitting or solver calls."""
from collections import deque
import hashlib
import json
from pathlib import Path
import re
import tarfile
import xml.etree.ElementTree as ET

from benchmarks.eva_tokenization import corpora, grouped_word, repetition_pairs
from benchmarks.historical_word_lengths import checksum, lexical_tokens, letters, source
from benchmarks.latin_contractions import unitizations, expand
from benchmarks.german_regional_audit import normalized_v2, EXCLUSIONS
from benchmarks.expanded_medieval_latin import Paragraphs, WORKS

OUT=Path('experiments/results/passage-survivor-audit')


def find_candidates(segments,cipher,rules):
    lengths=list(map(len,cipher));pairs=repetition_pairs(cipher);cache={}
    for si,segment in enumerate(segments):
        queue=deque(maxlen=len(cipher))
        for pos,word in enumerate(segment):
            if word is None:queue.clear();continue
            if word not in cache:cache[word]=unitizations(word,rules)
            queue.append((pos,word))
            if len(queue)!=len(cipher):continue
            words=[w for _,w in queue]
            if not all(words[i]==words[j] for i,j in pairs):continue
            counts=[[k for k in cache[w] if k<=c<=3*k] for w,c in zip(words,lengths)]
            if not all(counts):continue
            units=[cache[w][min(k)] for w,k in zip(words,counts)]
            assert all(expand(u,rules)==w for u,w in zip(units,words))
            yield {'segment_index':si,'start_record':queue[0][0],'end_record_exclusive':pos+1,
                   'words':words,'compatible_unit_counts':counts,'one_verified_unitization':units}


def german_records(root,number):
    records=[]
    exclusions={**EXCLUSIONS.get(number,{}),**({'k':'Unexplained prayer instruction','x':'Unexplained prayer instruction'} if number==133 else {})}
    parents={child:node for node in root.iter() for child in node}
    def walk(node):
        if node.tag in {'bibliographie','annotation'}:return
        if node.tag in {'eingriff','ueberschrift'}:records.append({'word':None});return
        if node.tag=='wortform':
            ancestor=node
            while ancestor in parents and ancestor.tag!='zeile':ancestor=parents[ancestor]
            for mi,morph in enumerate(node.findall('morph')):
                raw=''.join(morph.itertext())
                old=list(lexical_tokens(raw,german=True,exclude_unresolved=True))
                corrected,action=normalized_v2(raw)
                projected=[letters(w,german=True) for w in corrected or []]
                safe=projected==old and not any(w in exclusions for w in corrected or [])
                for wi,word in enumerate(old):
                    lexical_flags=[]
                    if number==123 and raw.rstrip('.').lower() in {'par','che','tha','phe'}:
                        lexical_flags.append('Abbreviated speaker label in the Eunuchus dramatic source; excluded in ordinary-prose sensitivity.')
                    if number==123 and word=='etc':
                        lexical_flags.append('Unexpanded etc abbreviation; excluded in full-spelling sensitivity.')
                    records.append({'word':word,'raw_form':raw,'word_number':node.get('nr'),
                        'morph_index':mi,'within_form_index':wi,'line_attributes':dict(ancestor.attrib) if ancestor.tag=='zeile' else {},
                        'corrected_words':corrected,'projected_corrected_words':projected,
                        'normalization_action':action,'normalization_survives':safe,
                        'exclusion_reasons':[exclusions[w] for w in corrected or [] if w in exclusions],
                        'lexical_sensitivity_flags':lexical_flags,
                        'word_xml':ET.tostring(node,encoding='unicode')})
            return
        for child in node:walk(child)
    walk(root)
    return records


def dante_records(raw,encoding):
    try:decoded=raw.decode(encoding)
    except UnicodeDecodeError:decoded=raw.decode('windows-1252')
    parser=Paragraphs();parser.feed(decoded);parser.close();out=[];started=False
    for pi,p in enumerate(parser.rows):
        raw_text=p['text'].strip()
        if any(re.search(r'(?:^|/)medieval\.html$',u) for u in p['links']):break
        if set(p['classes']) & {'pagehead','margin','border','smallborder'} or not raw_text:continue
        if not started:
            started=bool(re.match(r'^[IVXLCDM]+\.\s*1\.',raw_text))
            if not started:continue
        if re.match(r'^(?:Explicit|Explicet|Incipiunt)\b',raw_text,re.I):out.append({'word':None});continue
        text=re.sub(r'^[IVXLCDM]+\.\s*','§ ',raw_text)
        text=re.sub(r'(?<!\w)\d+\.\s*','',text)
        text=re.sub(r'\[[^\]]*\]',' § ',text)
        out.extend({'word':w,'paragraph_index':pi,'within_paragraph_token':i,'raw_paragraph':raw_text}
                   for i,w in enumerate(lexical_tokens(text)))
    return out


def run():
    screen_path=Path('experiments/results/cross-window-passages/report.json')
    saved=json.loads(screen_path.read_text());selection=json.loads(Path('experiments/results/cross-window-passages/selection.json').read_text())
    if checksum(selection)!=saved['selection_sha256']:raise ValueError('Selection changed')
    inventory=json.loads(Path('experiments/configs/latin-contractions.json').read_text())
    if checksum(inventory)!=saved['inventory_sha256']:raise ValueError('Inventory changed')
    sources={i:(s,m,c) for i,s,m,c in corpora()};provenance={};source_meta={}
    german_ids={int(row['source_id'].split('-')[1]) for row in saved['rows'] if row['source_id'].startswith('german-') and any(row[m]['length_and_repetition_compatible'] for m in ('atomic','grouped'))}
    source('german-corpus.tar.xz')
    with tarfile.open('data/raw/historical-lengths/german-corpus.tar.xz') as archive:
        for n in sorted(german_ids):
            raw=archive.extractfile(f'XML/{n}.xml').read();records=german_records(ET.fromstring(raw),n)
            identifier=f'german-{n}'
            assert [r['word'] for r in records]==sources[identifier][0][0]
            provenance[identifier]=[records];source_meta[identifier]={'xml_sha256':hashlib.sha256(raw).hexdigest(),'member':f'XML/{n}.xml'}
    work=next(w for w in WORKS if w['id']=='dante');records=[];parts=[]
    for file,url in work['parts']:
        raw,meta=source(file);records.append(dante_records(raw,meta['encoding']));parts.append(meta)
    assert [[r['word'] for r in s] for s in records]==sources['dante'][0]
    provenance['dante']=records;source_meta['dante']={'parts':parts}
    report={'screen_sha256':checksum(saved),'selection_sha256':checksum(selection),
        'inventory_sha256':checksum(inventory),'code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'source_metadata':source_meta,'matches':[],'solver_calls':0,
        'semantics':'Audit fixed surviving passages only. German corrected forms projected to legacy historical-length letter normalization for paired validation; this is not a corrected whole-corpus rescan. Changed source forms reject the old candidate rather than silently shifting its positions. Dante raw paragraphs retained; no inferred spelling corrections. Length/equality necessary filters are not shared-key fits.'}
    for row in saved['rows']:
        if not any(row[m]['length_and_repetition_compatible'] for m in ('atomic','grouped')):continue
        identifier=row['source_id'];segments=sources[identifier][0]
        assert checksum(segments)==row['records_sha256']
        window=next(w for w in selection['windows'] if w['id']==row['window_id'])
        atomic=tuple(map(tuple,window['atomic_words']));rules=[r for r in inventory['rules'] if r['id'] in inventory['profiles'][row['profile']]]
        for mode,cipher in [('atomic',atomic),('grouped',tuple(grouped_word(w) for w in atomic))]:
            found=list(find_candidates(segments,cipher,rules))
            assert len(found)==row[mode]['length_and_repetition_compatible']
            for candidate in found:
                evidence=provenance[identifier][candidate['segment_index']][candidate['start_record']:candidate['end_record_exclusive']]
                assert [e['word'] for e in evidence]==candidate['words']
                passed=all(e.get('normalization_survives',True) for e in evidence)
                flags=[e for e in evidence if e.get('lexical_sensitivity_flags')]
                report['matches'].append({'window_id':row['window_id'],'source_id':identifier,
                    'profile':row['profile'],'tokenization':mode,**candidate,'source_records':evidence,
                    'audit_status':('rejected_normalization' if not passed else 'flagged_lexical_sensitivity' if flags else 'retained'),
                    'lexical_flagged_records':flags,
                    'changed_records':[e for e in evidence if not e.get('normalization_survives',True)]})
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('Matches',len(report['matches']),'retained',sum(m['audit_status']=='retained' for m in report['matches']),flush=True)
    for m in report['matches']:
        print(m['window_id'],m['source_id'],m['profile'],m['tokenization'],m['audit_status'],' '.join(m['words']),flush=True)
    return report


if __name__=='__main__':run()
