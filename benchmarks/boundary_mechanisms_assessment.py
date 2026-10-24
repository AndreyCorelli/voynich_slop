"""Fixed interpretation of known boundary mechanism fixtures; no classifier fitting."""
import json
from benchmarks import boundary_mechanisms as b
from voynich_smt.data.corpus import write_json


def assess():
    p=b.prepare(); reports=[json.loads((b.OUT/f'iteration-{i}.json').read_text()) for i in range(1,8)]; summary={n:s for r in reports for n,s in r['summary'].items()}; structural=reports[-1]['structure']
    ranges={}
    for kind in ('encoder','generator'):
        for dose in (.25,.5):
            values=[summary[f'{kind}-{dose:g}-{seed}']['gain_position_per_character'] for seed in b.SEEDS]
            ranges[f'{kind}-{dose:g}']={'minimum':min(values),'maximum':max(values),'positive_runs':sum(v>0 for v in values)}
    result={'gain_ranges':ranges,'summary':summary,'structure':structural,
            'assessment':'Both known mechanisms generate suffix prediction gains; these fixtures overshoot manuscript scale and do not discriminate their causes. Generator null without explicit dependence still gains0.00330, so absolute gain is not an adequate mechanism diagnostic. Positional baseline smoothing/finite-sample effects are possible, not isolated explanations. Structural differences are descriptive and confounded by generator access to manuscript vocabulary.',
            'limitations':['Encoder prefix schedule is a constructed reversible rule, not claimed historical practice.','Generator samples observed development words rather than inventing novel lexical forms; vocabulary advantage prevents historical ranking.','Encoder and generator dose definitions differ; no matched effect-size selection or powers claimed.','Encoder random-prefix null preserves lengths/schedule, not true prefix marginals; generator null changes word distribution through removal of preference. Only one null seed per mechanism.','Same source German plaintext under all keys, three generator streams; not independent corpora.','Structural metrics block-equal, predictor folio-equal; no combined distance or classifier fitted.','Source and manuscript words reused; fixtures are calibration, not fresh manuscript tests.'],
            'next':'Use frequency/position/length-preserving refitted shuffles for each fixture, compare excess gain over these nulls, and use preset weaker doses near manuscript scale before treating any structural contrast as a mechanism discriminator.'}
    write_json(b.OUT/'assessment.json',result); print(json.dumps({'gain_ranges':ranges,'assessment':result['assessment'],'next':result['next']},indent=2))

if __name__=='__main__': assess()
