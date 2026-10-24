"""Prepare a footer-free corpus and an otherwise unchanged Voynich retry."""
from dataclasses import asdict, replace
import hashlib
import json
from pathlib import Path

from voynich_smt.data.corpus import Corpus, digest, write_json
from voynich_smt.data.latin import LatinNormalization, normalize
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.language.dictionary import WordDictionary


def prepare():
    old_path=Path('data/processed/caesar-latin.json')
    old=Corpus.load(old_path)
    manifest=json.loads(Path('data/raw/pg218.txt.manifest.json').read_text())
    raw=Path('data/raw')/manifest['raw_filename']
    content=raw.read_bytes()
    if hashlib.sha256(content).hexdigest()!=manifest['sha256'] or old.source['sha256']!=manifest['sha256']:
        raise ValueError('Raw source checksum disagrees with preserved corpus')
    settings=LatinNormalization(**{k:old.normalization[k] for k in LatinNormalization.__dataclass_fields__})
    clean=normalize(old.source,content.decode(manifest['encoding']),settings)
    clean_path=Path('data/processed/caesar-latin-v2.json')
    clean.save(clean_path)
    source_path=Path('data/generated/observed-codes-voynich/inputs/words-23.json')
    source=json.loads(source_path.read_text())
    if set(source)!={'request','codeword_domains'} or source['codeword_domains']!='observed':
        raise ValueError('Expected the original observed-domain public request')
    base=HiddenRecoveryRequest.from_dict(source['request'])
    config=json.loads(Path('experiments/configs/sample-scaling.json').read_text())
    whitelist=set(config['single_letter_words'])
    words=[];seen=set()
    for record in clean.records:
        word=tuple(record['tokens'])
        if word and word not in seen and (len(word)>1 or word[0] in whitelist):
            words.append(word);seen.add(word)
    old_words=set(base.dictionary.words)
    if not seen<=old_words:
        raise ValueError('Footer cleanup unexpectedly added vocabulary entries')
    request=replace(base,dictionary=WordDictionary(tuple(words)),timeout_ms=30000)
    public={'request':asdict(request),'codeword_domains':'observed'}
    if replace(request,dictionary=base.dictionary,timeout_ms=base.timeout_ms)!=base:
        raise ValueError('Retry changed scientific parameters beyond the dictionary')
    input_path=Path('data/generated/clean-latin-voynich/inputs/words-23.json')
    write_json(input_path,public)
    witness=json.loads(Path('experiments/results/voynich-observed-codes-23-30min.json').read_text())
    rejected=sorted({''.join(w) for w in witness['result']['plaintext']['words'] if tuple(w) not in seen})
    # Existing records before the footer must retain their exact tokens and offsets.
    if tuple(old.records[:len(clean.records)])!=clean.records:
        raise ValueError('Cleanup changed pre-footer records')
    report={'schema_version':1,'old_corpus':str(old_path),'old_corpus_sha256':old.identity,
            'clean_corpus':str(clean_path),'clean_corpus_sha256':clean.identity,
            'source_sha256':manifest['sha256'],'source_input':str(source_path),
            'source_input_sha256':digest(source),'public_input':str(input_path),
            'input_sha256':digest(public),'single_letter_words':sorted(whitelist),
            'old_vocabulary_size':len(old_words),'clean_vocabulary_size':len(seen),
            'removed_vocabulary':sorted(''.join(w) for w in old_words-seen),
            'excluded_footer_records':len(old.records)-len(clean.records),
            'old_witness_rejected_words':rejected,'old_witness_valid_in_clean_dictionary':not rejected,
            'scope':'Only footer exclusion; Roman numerals, names and independent word membership retained. No grammar or Latin-only word classifier.',
            'complete':True}
    write_json(Path('experiments/results/clean-latin-preparation.json'),report)
    print(json.dumps(report,indent=2))
    return report


if __name__=='__main__':
    prepare()
