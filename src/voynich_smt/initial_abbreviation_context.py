"""Preserve uppercase single-letter abbreviations without changing segment boundaries."""
import re
from voynich_smt.unlabeled_caesar_context import numbered_prose,normalize


def extract_initials(book,raw):
    sentences=[];changes=[]
    for chapter,text in numbered_prose(raw):
        pieces=re.split(r'([.!?]+)',text)
        for i in range(0,len(pieces),2):
            part=pieces[i];matches=list(re.finditer(r'[^\W\d_]+',part));words=[normalize(m[0]) for m in matches]
            if not words:continue
            sid=f'unlabeled104-{book}-{chapter}-{i//2}'
            # The delimiter is retained in this token's identity, but remains a
            # segment boundary so the comparison isolates identity/anchor matching.
            if i+1<len(pieces) and pieces[i+1].startswith('.') and len(matches[-1][0])==1 and matches[-1][0].isupper() and not part[matches[-1].end():].strip():
                before=words[-1];words[-1]+='.';changes.append(dict(sid=sid,index=len(words)-1,before=before,after=words[-1]))
            sentences.append(dict(sent_id=sid,tokens=[dict(word=w) for w in words]))
    return sentences,changes
