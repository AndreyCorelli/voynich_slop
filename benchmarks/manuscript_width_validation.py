"""Independent divisibility and barrier checks for the width audit."""
from collections import Counter
import hashlib
import json
from pathlib import Path
from voynich_smt.data.corpus import write_json


def validate():
    root=Path('experiments/results/manuscript-width-audit')
    report=json.loads((root/'report.json').read_text())
    raw_path=Path(report['source_path'])
    assert hashlib.sha256(raw_path.read_bytes()).hexdigest()==report['source_sha256']
    raw=json.loads(raw_path.read_text())
    prior=json.loads(Path('experiments/results/eva-tokenization/report.json').read_text())
    assert hashlib.sha256(Path('benchmarks/eva_tokenization.py').read_bytes()).hexdigest()==prior['code_sha256']
    for path,row in report['previous_artifacts'].items(): assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==row['sha256']
    for name,grouped in [('atomic',False),('existing-grouped',True)]:
        lengths=[]; runs=[]; run=[]; folio=None; excluded=0
        for r in raw['records']:
            if r.get('folio')!=folio:
                runs.append(run); run=[]; folio=r.get('folio')
            tokens=r['tokens']
            if r.get('excluded_reason') is not None or not tokens or any(len(s)!=1 or not s.isascii() or not s.isalpha() or not s.islower() for s in tokens):
                excluded+=1; runs.append(run); run=[]; continue
            if grouped:
                text=''.join(tokens); count=0
                while text:
                    match=next((g for g in prior['grouped_sequences'] if text.startswith(g)),text[0])
                    text=text[len(match):]; count+=1
                length=count
            else: length=len(tokens)
            lengths.append(length); run.append(length)
        runs.append(run)
        row=report[name]
        assert row['included_word_occurrences']==len(lengths) and row['excluded_records']==excluded
        assert row['word_length_histogram']=={str(k):v for k,v in sorted(Counter(lengths).items())}
        windows=[run[i:i+22] for run in runs for i in range(len(run)-21)]
        assert len(windows)==row['windows']
        for width in (1,2,3):
            result=row['profiles'][f'fixed-{width}']
            assert result['compatible_word_occurrences']==sum(n%width==0 for n in lengths)
            assert result['compatible_22_word_windows']==sum(all(n%width==0 for n in w) for w in windows)
        for profile in ('mixed-1-2','mixed-1-2-3'):
            assert row['profiles'][profile]['compatible_word_occurrences']==len(lengths)
            assert row['profiles'][profile]['compatible_22_word_windows']==len(windows)
        assert row['profiles']['mixed-2-3']['compatible_word_occurrences']==sum(n>=2 for n in lengths)
        assert row['profiles']['mixed-2-3']['compatible_22_word_windows']==sum(all(n>=2 for n in w) for w in windows)
    write_json(root/'validation.json',{'verified':True,'unitizations':2,'profiles':6,'solver_calls':0})


if __name__=='__main__': validate()
