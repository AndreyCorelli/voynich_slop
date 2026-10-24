from dataclasses import asdict
import json
from pathlib import Path

import pytest

from voynich_smt.cli import main
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.cipher.base import Bounds
from voynich_smt.language.dictionary import WordDictionary
from voynich_smt.models.alphabet import Alphabet
from voynich_smt.models.settings import NullBounds
from voynich_smt.models.text import Text


def write_request(path):
    request = HiddenRecoveryRequest(Text.from_string("xnx"), Alphabet(("a",)), Alphabet(tuple("xn")),
                                    Bounds("monoalphabetic", 1, 1, 1), WordDictionary.from_strings(("aa",)),
                                    nulls=NullBounds(True, 1, 1, 1))
    path.write_text(json.dumps(asdict(request)))


def test_solve_replay_optimization_sweep_compare_and_info(tmp_path, capsys):
    source, result, sweep = tmp_path / "request.json", tmp_path / "result.json", tmp_path / "sweep.json"
    write_request(source)
    assert main(["solve", str(source), "--optimize", "lexicographic", "--output", str(result)]) == 0
    document = json.loads(result.read_text())
    assert document["result"]["verified"] and document["result"]["optimization"]["optimality_proven"]
    assert document["request"]["ciphertext"]["words"] == [["x", "n", "x"]]
    assert document["request_sha256"] and document["environment"]["z3"]
    assert main(["sweep", str(source), "--null-symbols", "0", "1", "--output", str(sweep)]) == 0
    data = json.loads(sweep.read_text())
    assert data["complete"]
    assert [d["result"]["status"] for d in data["experiments"]] == ["UNSAT", "SAT"]
    assert main(["compare", str(result), str(sweep)]) == 0
    assert main(["corpus", "info", str(source)]) == 0
    assert '"tokens": 3' in capsys.readouterr().out


def test_generation_and_ground_truth_paths(tmp_path):
    config = Path(__file__).parents[2] / "experiments/configs/nulls-demo.json"
    public, truth = tmp_path / "public.json", tmp_path / "truth.json"
    assert main(["synthetic", "generate", "--config", str(config), "--words", "2", "--seed", "7",
                 "--output", str(public), "--ground-truth", str(truth)]) == 0
    assert "plaintext" not in json.loads(public.read_text())
    assert "plaintext" in json.loads(truth.read_text())
    with pytest.raises(SystemExit) as error:
        main(["synthetic", "generate", "--config", str(config), "--output", str(public),
              "--ground-truth", str(public)])
    assert error.value.code == 2


def test_invalid_input_does_not_overwrite_source(tmp_path):
    source = tmp_path / "request.json"
    write_request(source)
    original = source.read_bytes()
    with pytest.raises(SystemExit):
        main(["solve", str(source), "--output", str(source)])
    assert source.read_bytes() == original
    result = tmp_path / "result.json"
    with pytest.raises(SystemExit):
        main(["solve", str(source), "--timeout-ms", "0", "--output", str(result)])
    assert not result.exists()


def test_unknown_is_saved_and_returns_distinct_exit_code(tmp_path, monkeypatch):
    from voynich_smt.solver.recovery import Recovery
    source, output = tmp_path / "request.json", tmp_path / "result.json"
    write_request(source)
    monkeypatch.setattr(HiddenRecoveryRequest, "solve", lambda self: Recovery("UNKNOWN", 0.01, "timeout"))
    assert main(["solve", str(source), "--output", str(output)]) == 3
    result = json.loads(output.read_text())["result"]
    assert result["status"] == "UNKNOWN" and not result["verified"]


def test_compare_nested_frontier_preserves_unknown_and_feasibility(tmp_path,capsys):
    report=tmp_path/'frontier.json'
    report.write_text(json.dumps({'stages':[{'name':'wide','policies':[{
        'selection':{'mode':'cycle','reset':'text'},'synthetic_gate_passed':False,
        'experiments':[{'dataset':'voynich','result':{'status':'UNKNOWN','runtime_seconds':1.0,'verified':False},
                        'inherited_feasibility':{'status':'SAT','verified':True}}]}]}]}))
    assert main(['compare',str(report)])==0
    text=capsys.readouterr().out
    assert '\tUNKNOWN\t' in text and 'wide/cycle-text/voynich' in text
    assert text.splitlines()[-1].endswith('\tFalse\tTrue')
