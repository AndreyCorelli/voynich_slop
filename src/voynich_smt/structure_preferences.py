"""Label-free diagnostic preferences over already saved argument structures.

These inspected-development probes are not a trained or validated Latin parser.
Ties are returned explicitly; candidate order never breaks them.
"""


def features(tokens,unit,structure):
    counts={key:0 for key in ('marked_clauses','participial_clauses','governed_arguments','fragments',
        'matrix_adjuncts','infinitive_adjuncts','frame_preferred_adjuncts','shared_objects','dependency_distance')}
    edges={(h,t) for h,t,role in structure['links']}
    reporting=unit['kind']=='passive_reporting'
    for segment in structure['witness']:
        if 'clause' in segment:
            c=segment['clause'];counts['participial_clauses']+=1;counts['marked_clauses']+=c['marker'] is not None
            counts['fragments']+=1
        elif 'phrases' in segment:
            counts['fragments']+=1
            counts['governed_arguments']+=segment['role'] in ('object','dative_argument','genitive_argument','ablative_argument','embedded_subject')
            if segment['role']=='object':counts['shared_objects']+=len(segment['targets'])>1
            # Include nominal-internal edges in the distance probe, so a
            # participial subject edge is not penalized merely for being explicit.
            for phrase in segment['phrases']:
                head=phrase['head']
                edges.update((int(p),head) for p in phrase['analyses'] if int(p)!=head)
            if segment['markers']:
                edges.update((p,segment['phrases'][0]['head']) for p in segment['markers'])
        else:continue
        if segment['role'] in ('unresolved_ablative','ablative_participial_clause','prepositional_oblique'):
            for target in segment['targets']:
                matrix=target==unit['parent']
                counts['matrix_adjuncts']+=matrix;counts['infinitive_adjuncts']+=not matrix
                counts['frame_preferred_adjuncts']+=(not matrix if reporting else matrix)
    counts['dependency_distance']=sum(abs(a-b) for a,b in edges)
    return counts


POLICIES=('all','distance','construction','construction_matrix','construction_infinitive','construction_frame')
FAMILIES={
    'construction':('marked_clauses','participial_clauses','governed_arguments','fragments'),
    'frame':('marked_clauses','participial_clauses','governed_arguments','fragments','matrix_adjuncts','infinitive_adjuncts','frame_preferred_adjuncts','shared_objects'),
    'frame_distance':('marked_clauses','participial_clauses','governed_arguments','fragments','matrix_adjuncts','infinitive_adjuncts','frame_preferred_adjuncts','shared_objects','dependency_distance'),
}


def score(values,policy):
    if policy=='all':return ()
    if policy=='distance':return (-values['dependency_distance'],)
    primary=(values['marked_clauses'],values['participial_clauses'],values['governed_arguments'],-values['fragments'])
    if policy=='construction':return primary
    key={'construction_matrix':'matrix_adjuncts','construction_infinitive':'infinitive_adjuncts','construction_frame':'frame_preferred_adjuncts'}[policy]
    return (*primary,values[key])


def select(vectors,policy):
    if not vectors:return []
    scores=[score(v,policy) for v in vectors];best=max(scores)
    return [i for i,value in enumerate(scores) if value==best]


def collisions(vectors,labels,names):
    """Positive/negative candidate pairs indistinguishable in named features."""
    return [[i,j] for i,good in enumerate(labels) if good for j,bad in enumerate(labels) if not bad and all(vectors[i][n]==vectors[j][n] for n in names)]
