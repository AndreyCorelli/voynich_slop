from voynich_smt.form_only_context import project


def test_projection_ignores_grammatical_columns_and_punctuation():
    header = '# source = Jerome x\n# sent_id = a\n'
    a = header + '1\tJuvat\tSECRET\tNOUN\n2\t,\t,\tNOUN\n3-4\tIGNORE\tX\n'
    b = header + '1\tJuvat\tPOISON\tVERB\n2\t,\t,\tVERB\n3-4\tIGNORE\tX\n'
    expected = [dict(sent_id='a', tokens=[dict(word='iuuat')])]
    assert project(a.splitlines(), 'Jerome', set()) == expected
    assert project(b.splitlines(), 'Jerome', set()) == expected


def test_exclusions_and_author_filter_precede_projection():
    text = '# source = Jerome x\n# sent_id = reserved\nmalformed\n\n# source = Other\n# sent_id = b\n1\tsecret\tX\n'
    assert project(text.splitlines(), 'Jerome', {'reserved'}) == []
