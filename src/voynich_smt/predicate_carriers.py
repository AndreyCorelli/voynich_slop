"""Annotation-derived carrier targets for supervised training and evaluation only."""
from copy import deepcopy


def target(tokens,subject):
    token=tokens[subject];head=token['head']
    if token['pos'] not in ('NOUN','PROPN','PRON') or token['rel']!='nsubj' or head is None:
        return dict(direct=None,carrier=None,kind='none',ambiguous=False,choices=[])
    governor=tokens[head];form=governor['features'].get('VerbForm','')
    if governor['pos'] in ('VERB','AUX') and form=='Fin':
        return dict(direct=head,carrier=head,kind='direct',ambiguous=False,choices=[head])
    if governor['pos'] in ('VERB','AUX') and (not form or ',' in form):
        return dict(direct=None,carrier=None,kind='unknown_governor_form',ambiguous=False,choices=[])
    choices=[i for i,t in enumerate(tokens) if t['head']==head and t['rel'] in ('cop','aux') and t['pos'] in ('VERB','AUX') and t['features'].get('VerbForm')=='Fin']
    if len(choices)>1:return dict(direct=None,carrier=None,kind='ambiguous_carrier',ambiguous=True,choices=choices)
    if not choices:return dict(direct=None,carrier=None,kind='no_finite_carrier',ambiguous=False,choices=[])
    carrier=choices[0];kind='copula' if tokens[carrier]['rel']=='cop' else 'auxiliary'
    return dict(direct=None,carrier=carrier,kind=kind,ambiguous=False,choices=choices)


def relabel(frames,tokens,task):
    if task not in ('direct','carrier'):raise ValueError(task)
    result=[];audit=[]
    for frame in frames:
        truth=target(tokens,frame['subject']);audit.append(dict(subject=frame['subject'],**truth))
        if task=='carrier' and truth['ambiguous']:continue
        r=deepcopy(frame);r['gold']=truth[task];result.append(r)
    return result,audit
