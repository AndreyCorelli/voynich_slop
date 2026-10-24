"""Explicit admission of complete scored segments, without expanding candidates."""
from voynich_smt.data.corpus import digest


def screen_complete_segments(stream, candidate_forms, *, minimum_words=5):
    if type(minimum_words) is not int or minimum_words < 1:
        raise ValueError('minimum_words must be positive')
    forms = frozenset(candidate_forms)
    runs, current, previous = [], [], None
    for record in stream.records:
        key = record.source_id, record.segment_id
        if record.boundary_before or previous != key or record.surface is None:
            if current:
                runs.append(tuple(current))
                current = []
        if record.surface is not None:
            current.append(record)
        previous = key
    if current:
        runs.append(tuple(current))
    accepted, audit = set(), []
    for index, records in enumerate(runs):
        words = tuple(r.surface for r in records)
        missing = sorted(set(words) - forms)
        reason = 'missing candidates' if missing else 'below minimum segment length' if len(words) < minimum_words else None
        identities = [(r.source_id, r.record_index) for r in records]
        if reason is None:
            accepted.update(identities)
        audit.append({'segment_index': index, 'tokens': len(words), 'record_ids': identities,
            'surface_sha256': digest(words), 'missing_forms': missing, 'excluded_reason': reason})
    selected = stream.select(lambda r: (r.source_id, r.record_index) in accepted,
        description={'policy': 'entire scored segments; candidate-covered; minimum word count',
                     'minimum_words': minimum_words, 'candidate_forms_sha256': digest(sorted(forms))})
    report = {'source_stream_sha256': stream.identity, 'candidate_forms_sha256': digest(sorted(forms)),
        'selected_stream_sha256': selected.identity, 'minimum_words': minimum_words,
        'input_segments': len(runs), 'admitted_segments': sum(a['excluded_reason'] is None for a in audit),
        'input_tokens': sum(len(r) for r in runs), 'admitted_tokens': len(accepted), 'segments': audit,
        'scope': 'coverage-screened calibration cohort; not unbiased recovery sampling; no words removed within admitted segments'}
    if selected.segments() != tuple(tuple(r.surface for r in run) for run, row in zip(runs, audit) if row['excluded_reason'] is None):
        raise ValueError('Coverage screening altered admitted segment boundaries')
    return selected, report
