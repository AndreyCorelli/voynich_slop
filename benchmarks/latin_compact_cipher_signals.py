"""Export ordinary ciphertext-only signals for other decoders; never read truth."""
import hashlib,json
from collections import defaultdict
from pathlib import Path
import numpy as np
from benchmarks.latin_compact_cipher import OUT,resource,TAGS
from voynich_smt.letter_discovery import ALPHABET,SPACE,prepare
from voynich_smt.data.corpus import digest,write_json


def run():
    rows,words,model,*_=resource();fixtures=[f for f in json.loads((OUT/'fixtures.json').read_text()) if f['split']=='test'];report=json.loads((OUT/'report.json').read_text());(OUT/'candidate-inventory.txt').write_text('\n'.join(words)+'\n')
    for f in fixtures:
        key=next(x['hypothesis']['decryption_permutation'] for x in report['runs'] if x['fixture']==f['id'] and x['arm']=='baseline');prepared=prepare([w for s in f['discovery'] for w in s],words);prob=defaultdict(list);where=defaultdict(list)
        for si,s in enumerate(f['discovery']):
            p=model.predict(s)
            for i,w in enumerate(s):prob[w].append(p[i]);where[w].append([si,i])
        tokens=[]
        for i,w in enumerate(prepared['unique']):
            tokens.append({'cipherword':w,'occurrences':where[w],'candidate_word_ids':prepared['candidate_ids'][prepared['ptr'][i]:prepared['ptr'][i+1]].tolist(),'mean_pos_distribution':dict(zip(TAGS,np.mean(prob[w],axis=0).tolist())),'baseline_decoded_surface':''.join(ALPHABET[key[ALPHABET.index(c)]] for c in w),'allow_outside_inventory':True})
        observed={c for s in f['discovery'] for w in s for c in w};unobserved=[c for c in ALPHABET if c not in observed];alternatives=[ALPHABET[key[ALPHABET.index(c)]] for c in unobserved]
        signal={'fixture':f['id'],'candidate_inventory':'../candidate-inventory.txt','word_types':tokens,'unobserved_cipher_symbol_candidates':{c:alternatives for c in unobserved},'scope':'Ciphertext-only pattern candidates and POS distributions; baseline key supplied separately. No gold roles, word mappings, function anchors or relationship claims. Unobserved key-symbol choices are logically unresolved within the permutation family.'}
        write_json(OUT/'signals'/f"{digest(f['id'])}.json",signal)
    paths=[Path(__file__),OUT/'candidate-inventory.txt',OUT/'pos-model.json',OUT/'pos-weights.npy',OUT/'report.json'];write_json(OUT/'signals-manifest.json',{'sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},'exported_fixtures':len(fixtures),'truth_files_read':0});print('EXPORTED CIPHERTEXT-ONLY SIGNALS',len(fixtures))
if __name__=='__main__':run()
