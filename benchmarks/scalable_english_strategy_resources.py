"""Build controlled larger-corpus resources and a baseline-trained trigram model."""
from itertools import chain
import json
from pathlib import Path
import shutil

from benchmarks.scalable_english_independent import cmu_forms, resource_documents, sha
from voynich_smt.word_mapping.scalable.data import tokenize
from voynich_smt.word_mapping.scalable.inventory import Inventory
from voynich_smt.word_mapping.scalable.sparse_lm import SparseBigram
from voynich_smt.word_mapping.scalable.trigram import InterpolatedTrigram

BOOKS = [
    ('84','To Mrs. Saville, England.','Frankenstein','Mary Shelley'),
    ('1260','There was no possibility of taking a walk that day.','Jane Eyre','Charlotte Bronte'),
    ('2701','Call me Ishmael.','Moby Dick','Herman Melville'),
    ('514','Christmas','Little Women','Louisa May Alcott'),
    ('1400','My father','Great Expectations','Charles Dickens'),
]


def report(output,protocol,inventory,model):
    (output/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
    result = {'benchmark_role':'independent-source-resources','protocol':protocol,
              'inventory_forms':inventory.size,'inventory_sha256':inventory.identity,
              'model_sha256':model.identity,'training_tokens':sum(model.counts[:-1]),
              'training_documents':model.counts[-1],'observed_edges':len(model.edges),
              'dictionary_only_forms':model.unseen,'order':getattr(model,'order',2)}
    if getattr(model,'order',2) == 3:
        result['observed_trigrams'] = len(model.triples)
    (output/'report.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


def build_expanded(base,raw,output):
    original = json.loads((base/'protocol.json').read_text())
    extra=[]
    for book,incipit,title,author in BOOKS:
        path=raw/f'{book}.txt'
        extra.append({'path':str(path),'sha256':sha(path),'incipit':incipit,'title':title,'author':author})
    manifest={'sources':[{**r,'url':f'https://www.gutenberg.org/ebooks/{book}.txt.utf-8',
                          'catalog':f'https://www.gutenberg.org/ebooks/{book}',
                          'rights':'Public-domain original; retain Gutenberg notices and terms.'}
                         for (book,*_),r in zip(BOOKS,extra)]}
    (raw/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    output.mkdir(parents=True,exist_ok=False)
    expanded=json.loads(json.dumps(original))
    expanded['additional_sources']=extra
    expanded['inventory_policy']='Same CMU + all original and expanded training forms for both corpus variants; no target input'
    for i,r in enumerate(extra):
        expanded['sources'][f'inventory_book_{i}']={'path':r['path'],'sha256':r['sha256']}
    control=json.loads(json.dumps(expanded)); control['additional_sources']=[]
    results={}
    for name,protocol in (('corpus_control',control),('corpus_expanded',expanded)):
        destination=output/name; destination.mkdir()
        if name=='corpus_control':
            inventory=Inventory.build(destination/'inventory.sqlite',
                chain(cmu_forms(Path(original['sources']['lexicon']['path'])),
                      (w for doc in resource_documents(expanded) for w in doc)))
        else:
            shutil.copyfile(output/'corpus_control/inventory.sqlite',destination/'inventory.sqlite')
            inventory=Inventory(destination/'inventory.sqlite')
        try:
            model=SparseBigram.train(inventory,((inventory.id(w) for w in doc) for doc in resource_documents(protocol)))
            model.save(destination/'model.sqlite')
            results[name]=report(destination,protocol,inventory,model)
        finally:
            inventory.close()
    return results


def build_trigram(base,output):
    protocol=json.loads((base/'protocol.json').read_text())
    protocol['scoring']='50% interpolated absolute-discount trigram; original bigram retrieval projection'
    output.mkdir(parents=True,exist_ok=False)
    shutil.copyfile(base/'inventory.sqlite',output/'inventory.sqlite')
    inventory=Inventory(output/'inventory.sqlite')
    try:
        model=InterpolatedTrigram.train(inventory,
            lambda: ((inventory.id(w) for w in doc) for doc in resource_documents(protocol)))
        model.save(output/'model.sqlite')
        return report(output,protocol,inventory,model)
    finally:
        inventory.close()


if __name__ == '__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base',type=Path,required=True)
    parser.add_argument('--raw',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps(build_expanded(args.base,args.raw,args.output),indent=2),flush=True)
    print(json.dumps(build_trigram(args.base,args.output/'trigram'),indent=2),flush=True)
