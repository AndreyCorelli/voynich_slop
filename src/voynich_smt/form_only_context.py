"""Project admitted CoNLL-U sentences without consulting grammatical columns."""


def project(lines, author_prefix, excluded):
    result = []
    sid = source = None
    words = []

    def finish():
        if sid is not None and source and source.startswith(author_prefix) and sid not in excluded and words:
            result.append(dict(sent_id=sid, tokens=[dict(word=w) for w in words]))

    for line in lines:
        line = line.rstrip('\n\r')
        if not line:
            finish()
            sid = source = None
            words = []
        elif line.startswith('# sent_id = '):
            sid = line[len('# sent_id = '):]
        elif line.startswith('# source = '):
            source = line[len('# source = '):]
        elif not line.startswith('#'):
            # Exclude reserved IDs BEFORE even projecting their FORM column.
            if sid is None or sid in excluded or not source or not source.startswith(author_prefix):
                continue
            ident, sep, rest = line.partition('\t')
            if sep and ident.isdecimal():
                form = rest.partition('\t')[0]
                if any(c.isalpha() for c in form):
                    words.append(form.lower().replace('v', 'u').replace('j', 'i'))
    finish()
    return result
