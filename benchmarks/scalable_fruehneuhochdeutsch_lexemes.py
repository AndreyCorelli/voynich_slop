"""Post-hoc lexical-ID diagnostics, distinct from literal/grammar/meaning claims."""
from collections import Counter,defaultdict
import hashlib
import json
from pathlib import Path
import tarfile

from benchmarks.scalable_fruehneuhochdeutsch_long import ROOT,PARENT,RAW
from voynich_smt.word_mapping.scalable.historical_german import parse_cora
from voynich_smt.word_mapping.scalable.inventory import Inventory
from voynich_smt.word_mapping.scalable.latin_corpus import write,sha
from voynich_smt.word_mapping.scalable.data import CipherStream


def main():
    # Fit only generic source annotations; target labels are not opened until the
    # source-majority lexeme table has been frozen and serialized.
    prior=json.loads((PARENT/'resources/training-manifest.json').read_text());by_member=defaultdict(set)
    for row in prior['segments']:by_member[row['member']].add(row['segment'])
    counts=defaultdict(Counter)
    write(ROOT/'lexeme-diagnostic-design.json',{'scope':'Post-hoc evaluation diagnostic, not original selection metric or decoder change',
        'fit':'Parent admitted training segments only; source-majority DWB lemmaId per predicted surface; ties lexicographic, no gold choice among analyses',
        'evaluation':'Compare with private reference lemmaId at each annotated position; separately report manual annoType subset',
        'limits':['Lemma agreement can credit wrong inflection/case and does not establish grammar or meaning.',
            'Some reference annotations are automatic and may be wrong; manual subset has different coverage.',
            'No independent aligned DTA lemma truth is available in these fixtures; do not fabricate DTA lemma accuracy.']})
    with tarfile.open(RAW/'ReF-v1.0.2.tar.gz') as archive:
        for member,segments in sorted(by_member.items()):
            doc=parse_cora(archive.extractfile(member).read())
            for a in doc.annotations:
                if a['segment'] in segments and a['lemmaId'] and a['lemma']:
                    counts[a['surface']][(a['lemmaId'],a['lemma'])]+=1
    lexicon={word:{'lemmaId':pair[0],'lemma':pair[1],'source_count':n}
             for word,values in counts.items() for pair,n in [min(values.items(),key=lambda v:(-v[1],v[0]))]}
    path=ROOT/'source-majority-lexemes.json';write(path,{'source_manifest_sha256':sha(PARENT/'resources/training-manifest.json'),'forms':lexicon})
    frozen=sha(path);rows=[];inventory=Inventory(PARENT/'resources/inventory.sqlite')
    try:
        for name in ('F137','F332','F064'):
            fixture=ROOT/'fixtures'/name;annotations=json.loads((fixture/'evaluation-only/annotations.json').read_text());stream=CipherStream.load(fixture/'public/cipher.json')
            if len(annotations)!=len(stream.documents[0]):raise ValueError('Annotation alignment mismatch')
            for method in ('random','frequency'):
                inference=json.loads((ROOT/'runs'/f'{name}-{method}'/'inference.json').read_text())
                keys={r['seed']:r['joint_archive'][0]['assignments'] for r in inference['runs']};runs=[]
                for seed,key in keys.items():
                    measured={}
                    for role in ('all_annotated','manual_annotated'):
                        eligible=[(i,a) for i,a in enumerate(annotations) if a['lemmaId'] and (role=='all_annotated' or a['annoType']=='manual')]
                        correct=0;known=0;literal=0
                        for i,a in eligible:
                            word=inventory.word(key[stream.documents[0][i]]);pred=lexicon.get(word)
                            literal+=word==a['surface'];known+=pred is not None
                            correct+=pred is not None and pred['lemmaId']==a['lemmaId']
                        measured[role]={'positions':len(eligible),'predicted_lexeme_available':known,'correct':correct,
                            'lexeme_accuracy':correct/len(eligible) if eligible else None,'literal_accuracy_same_positions':literal/len(eligible) if eligible else None}
                    runs.append({'seed':seed,**measured})
                primary=json.loads((ROOT/'runs'/f'{name}-{method}'/'anchors-evaluation.json').read_text())['primary'];anchors=[]
                for a in primary:
                    positions=[row for i,row in enumerate(annotations) if stream.documents[0][i]==a['cipher_type'] and row['lemmaId']]
                    pred=lexicon.get(a['prediction']);matched=sum(pred is not None and pred['lemmaId']==x['lemmaId'] for x in positions)
                    anchors.append({**a,'source_predicted_lexeme':pred,'reference_annotated_positions':len(positions),
                        'correct_lexeme_positions':matched,'reference_lexemes':dict(Counter(x['lemmaId'] for x in positions))})
                rows.append({'id':name,'initialization':method,'runs':runs,'primary_anchors':anchors})
        if sha(path)!=frozen:raise ValueError('Frozen source lexicon changed')
        write(ROOT/'lexeme-diagnostics.json',{'source_lexicon_sha256':frozen,'works':rows,'post_hoc':True,'decoder_changed':False,
            'dta_lemma_accuracy':'not_evaluated','grammar':'not_evaluated','semantics':'not_evaluated'})
        for row in rows:print(row['id'],row['initialization'],[(r['seed'],r['all_annotated']['lexeme_accuracy']) for r in row['runs']],flush=True)
    finally:inventory.close()




def augment_labels():
    from voynich_smt.word_mapping.scalable.data import CipherStream
    root=ROOT
    path=root/'lexeme-diagnostics.json';report=json.loads(path.read_text());lexicon=json.loads((root/'source-majority-lexemes.json').read_text())['forms']
    assert sha(root/'source-majority-lexemes.json')==report['source_lexicon_sha256']
    if not (root/'lexeme-diagnostics-raw-ids.json').exists():write(root/'lexeme-diagnostics-raw-ids.json',report)
    inv=Inventory(PARENT/'resources/inventory.sqlite')
    try:
     for row in report['works']:
      name=row['id'];method=row['initialization'];fixture=root/'fixtures'/name
      labels=json.loads((fixture/'evaluation-only/annotations.json').read_text());stream=CipherStream.load(fixture/'public/cipher.json')
      inference=json.loads((root/'runs'/f'{name}-{method}'/'inference.json').read_text());keys={r['seed']:r['joint_archive'][0]['assignments'] for r in inference['runs']}
      for r in row['runs']:
       key=keys[r['seed']]
       for role in ('all_annotated','manual_annotated'):
        eligible=[(i,a) for i,a in enumerate(labels) if a['lemma'] and (role=='all_annotated' or a['annoType']=='manual')]
        good=0;literal=0
        for i,a in eligible:
         word=inv.word(key[stream.documents[0][i]]);pred=lexicon.get(word);good+=pred is not None and pred['lemma']==a['lemma'];literal+=word==a['surface']
        r[role].update(lemma_label_positions=len(eligible),lemma_label_correct=good,lemma_label_accuracy=good/len(eligible) if eligible else None,literal_accuracy_lemma_label_positions=literal/len(eligible) if eligible else None)
      for a in row['primary_anchors']:
       eligible=[x for i,x in enumerate(labels) if stream.documents[0][i]==a['cipher_type'] and x['lemma']];pred=lexicon.get(a['prediction'])
       a.update(reference_lemma_labels=dict(Counter(x['lemma'] for x in eligible)),reference_lemma_label_positions=len(eligible),correct_lemma_label_positions=sum(pred is not None and pred['lemma']==x['lemma'] for x in eligible))
     report['lemma_label_diagnostic_note']='Same frozen source-most-frequent (lemmaId,lemma) analysis, compared by lemma label without choosing among alternatives. Raw-ID results retained: reference contains malformed IDs, e.g. F064 und has both [GU05758] and [G0U5758]. Labels can conflate homographs and wrong inflections; neither metric establishes grammar or meaning. Post-hoc descriptive diagnostic, no decoder/selection changes.'
     write(path,report)
    finally:inv.close()


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--labels-only',action='store_true');args=parser.parse_args()
    if not args.labels_only:main()
    augment_labels()
