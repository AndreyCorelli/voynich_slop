"""Versioned Gutenberg prose extraction for work-disjoint development pilots."""
import re

PARSER_VERSION = 'gutenberg-english-v1'
STARTS = {'1342': 'It is a truth universally acknowledged,',
          '11': 'Alice was beginning to get very tired'}


def extract(text, book_id):
    """Keep prose after a pinned incipit, strip editorial illustrations/headings.

    Sentence breaks are punctuation heuristics, not gold annotations. Apostrophes
    inside words survive; other punctuation is removed. Paragraph boundaries also
    end segments, preventing chapter/verse joins. No length-based sentence filter.
    """
    if book_id not in STARTS:
        raise ValueError('Unsupported work')
    marker = '*** END OF THE PROJECT GUTENBERG EBOOK'
    if marker not in text or STARTS[book_id] not in text:
        raise ValueError('Missing expected Gutenberg anchors')
    text = text.split(marker, 1)[0].split(STARTS[book_id], 1)[1]
    text = STARTS[book_id] + text
    text = re.sub(r'\[Illustration:.*?\]', '\n\n', text, flags=re.S)
    text = re.sub(r'^CHAPTER [IVXLCDM]+\..*$', '\n', text, flags=re.M)
    segments = []
    for paragraph in re.split(r'\n\s*\n', text):
        for sentence in re.split(r'[.!?]+', paragraph):
            words = tuple(re.findall(r"[a-z]+(?:'[a-z]+)*", sentence.lower().replace('’', "'")))
            if words:
                segments.append(words)
    return tuple(segments)


def prefix_segments(segments, token_limit):
    """Select a contiguous prefix of whole segments without overshooting."""
    if type(token_limit) is not int or token_limit < 1:
        raise ValueError('token_limit must be positive')
    result, count = [], 0
    for segment in segments:
        if count + len(segment) > token_limit:
            break
        result.append(segment)
        count += len(segment)
    if not result:
        raise ValueError('Token limit does not admit the first segment')
    return tuple(result)


def source_loss(source, segments):
    """Evaluation-only genuine-text source loss, including BOS and EOS events."""
    import math
    encoded = source.encode(segments)
    score = 0.
    for s in encoded:
        score += math.log(source.initial[s[0]]) + math.log(source.final[s[-1]])
        score += sum(math.log(source.transition[a][b]) for a, b in zip(s, s[1:]))
    tokens = sum(map(len, encoded))
    events = tokens + len(encoded)
    return {'log_probability': score, 'prediction_events': events, 'tokens': tokens,
            'nats_per_event': -score / events,
            'unknown_tokens': sum(w == 0 for s in encoded for w in s)}
