import json

import pytest

from voynich_smt.cli import main
from voynich_smt.data.corpus import Corpus


def test_corpus_cli_import_normalize_sample_and_info(tmp_path, capsys):
    source = tmp_path / 'download.txt'
    source.write_text('#=IVTFF Eva- 2.0\n<f1r> <! $I=H>\n<f1r.1,@P0> cho.ar,or.[a:o]r')
    raw = tmp_path / 'raw'
    processed = tmp_path / 'processed.json'
    sample = tmp_path / 'sample.json'
    assert main(['corpus','fetch','zl-eva','--local',str(source),'--raw-dir',str(raw)]) == 0
    manifest = raw / 'ZL3b-n.txt.manifest.json'
    assert main(['corpus','normalize',str(manifest),'--output',str(processed)]) == 0
    assert main(['corpus','sample',str(processed),'--words','2','--folio','f1r','--output',str(sample)]) == 0
    assert json.loads(sample.read_text())['text']['words'] == [list('cho'), list('ar')]
    capsys.readouterr()
    assert main(['corpus','info',str(processed)]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data['statistics']['words'] == 3 and data['excluded_records'] == 1
    assert data['corpus_sha256'] == Corpus.load(processed).identity
    original = processed.read_bytes()
    with pytest.raises(SystemExit) as error:
        main(['corpus','sample',str(processed),'--output',str(processed)])
    assert error.value.code == 2
    assert processed.read_bytes() == original
    with pytest.raises(SystemExit) as error:
        main(['corpus','normalize',str(manifest),'--output',str(raw/'ZL3b-n.txt')])
    assert error.value.code == 2
    with pytest.raises(SystemExit) as error:
        main(['corpus','normalize',str(manifest),'--uv','v_to_u','--output',str(processed)])
    assert error.value.code == 2


def test_checkpointed_corpus_pilot_with_separate_truth(tmp_path):
    import importlib.util
    from pathlib import Path
    spec = importlib.util.spec_from_file_location('corpus_pilot', Path(__file__).parents[2] / 'benchmarks/corpus_comparison.py')
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    latin = Corpus('latin', {'sha256':'latin'}, {'alphabet':'ab'},
                   ({'tokens':['a','b'], 'raw':'ab'}, {'tokens':['b','a'], 'raw':'ba'}))
    voynich = Corpus('voynich-eva', {'sha256':'eva'}, {},
                     ({'tokens':['x','y'], 'folio':'f1r'}, {'tokens':['y','x'], 'folio':'f1r'}))
    report = runner.run(voynich, latin, tmp_path/'results.json', words=2, vocabulary_size=2,
                        artifact_dir=tmp_path/'artifacts')
    assert report['complete'] and report['synthetic_gate_passed']
    assert len(report['experiments']) == 7
    assert (tmp_path/'artifacts/ground_truth.json').exists()
    for experiment in report['experiments']:
        public = json.loads(Path(experiment['public_input']).read_text())
        assert 'plaintext' not in public and 'encoder' not in public
        assert experiment['result']['status'] in {'SAT', 'UNSAT'}
        if experiment['result']['status'] == 'SAT':
            assert experiment['result']['verified']
    assert report['experiments'][1]['result']['status'] == 'SAT'
    assert report['experiments'][-1]['result']['status'] == 'UNSAT'
