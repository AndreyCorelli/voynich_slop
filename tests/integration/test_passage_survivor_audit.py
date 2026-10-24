import xml.etree.ElementTree as ET
from benchmarks.passage_survivor_audit import german_records,dante_records,find_candidates


def test_bracket_fragments_rejected_but_plain_forms_and_evidence_retained():
    root=ET.fromstring('<root><zeile nr="3"><wortform nr="1"><morph>[T]U</morph></wortform>'
        '<wortform nr="2"><morph>wort</morph></wortform></zeile></root>')
    records=german_records(root,123)
    assert [r['word'] for r in records]==['t','u','wort']
    assert not records[0]['normalization_survives']
    assert records[0]['projected_corrected_words']==['tu']
    assert records[-1]['normalization_survives']
    assert records[-1]['line_attributes']=={'nr':'3'}


def test_lexical_sensitivity_separate_from_normalization_and_exclusions():
    root=ET.fromstring('<root><wortform nr="1"><morph>Che</morph></wortform>'
        '<wortform nr="2"><morph>etc</morph></wortform></root>')
    records=german_records(root,123)
    assert all(r['normalization_survives'] for r in records)
    assert all(r['lexical_sensitivity_flags'] for r in records)
    root=ET.fromstring('<root><wortform nr="1"><morph>k</morph></wortform></root>')
    assert not german_records(root,133)[0]['normalization_survives']


def test_exact_candidate_positions_gap_and_optional_contraction_witness():
    rules=[{'id':'est','expansion':'est','position':'whole'}]
    hits=list(find_candidates([['x',None,'est','a','est']],(('c',),('d',),('c',)),rules))
    assert len(hits)==1
    assert hits[0]['start_record']==2 and hits[0]['end_record_exclusive']==5
    assert hits[0]['one_verified_unitization']==[('<est>',),('a',),('<est>',)]


def test_dante_paragraph_coordinates_and_bracket_barrier():
    raw=b'<p class="pagehead">Title</p><p>I. 1. hiis [gap] est</p><p><a href="medieval.html">Footer</a></p>'
    records=dante_records(raw,'utf-8')
    assert [r['word'] for r in records]==[None,'hiis',None,'est']
    assert records[-1]['paragraph_index']==1
    assert records[-1]['raw_paragraph']=='I. 1. hiis [gap] est'
