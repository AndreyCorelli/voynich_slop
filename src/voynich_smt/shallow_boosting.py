"""Small deterministic Newton-boosted classifiers for capacity diagnostics."""
from dataclasses import dataclass
import numpy as np


@dataclass
class ShallowBoostedClassifier:
    intercept: float
    trees: list
    config: dict
    feature_count: int

    @classmethod
    def fit(cls,x,y):
        x=np.asarray(x,dtype=float);y=np.asarray(y,dtype=float)
        if x.ndim!=2 or not len(x) or y.shape!=(len(x),) or not np.all(np.isin(y,[0.,1.])):
            raise ValueError('Nonempty feature matrix and binary labels required')
        config={'rounds':5,'max_depth':2,'min_leaf':20,'leaf_l2':10.,'learning_rate':.2,'max_leaf_update':1.}
        prior=float(np.clip(y.mean(),1e-8,1-1e-8));intercept=float(np.log(prior/(1-prior)))
        logits=np.full(len(x),intercept);thresholds=[]
        for j in range(x.shape[1]):
            unique=np.unique(x[:,j])
            if len(unique)<=1:values=[]
            elif len(unique)<=5:values=((unique[1:]+unique[:-1])/2).tolist()
            else:values=np.unique(np.quantile(x[:,j],[.25,.5,.75])).tolist()
            thresholds.append(values)
        candidates=[(j,float(t)) for j,values in enumerate(thresholds) for t in values]
        masks=np.array([x[:,j]<=t for j,t in candidates],dtype=bool)
        trees=[]
        for _ in range(config['rounds']):
            probability=1/(1+np.exp(-np.clip(logits,-40,40)));gradient=y-probability;hessian=probability*(1-probability)
            def leaf(indices):
                g=float(gradient[indices].sum());h=float(hessian[indices].sum())
                value=float(np.clip(g/(h+config['leaf_l2']),-config['max_leaf_update'],config['max_leaf_update']))
                return {'value':value,'count':len(indices),'gradient_sum':g,'hessian_sum':h}
            def leaf_score(node):return node['gradient_sum']**2/(node['hessian_sum']+config['leaf_l2'])
            def stump(indices):
                parent=leaf(indices)
                if len(indices)<2*config['min_leaf'] or not candidates:return parent,leaf_score(parent)
                selected=masks[:,indices];counts=selected.sum(axis=1)
                g=parent['gradient_sum'];h=parent['hessian_sum'];l2=config['leaf_l2']
                gl=selected@gradient[indices];hl=selected@hessian[indices]
                score=gl*gl/(hl+l2)+(g-gl)**2/(h-hl+l2)
                valid=(counts>=config['min_leaf'])&(len(indices)-counts>=config['min_leaf'])
                score[~valid]=-np.inf;k=int(np.argmax(score));gain=float(score[k]-leaf_score(parent))
                if gain<=1e-12:return parent,leaf_score(parent)
                mask=selected[k];j,t=candidates[k]
                return {'feature':j,'threshold':t,'count':len(indices),'gain':gain,
                    'left':leaf(indices[mask]),'right':leaf(indices[~mask])},float(score[k])
            indices=np.arange(len(x));best=leaf(indices);base_score=leaf_score(best);best_gain=1e-12
            # Joint two-level search can capture an interaction even when its
            # first split alone has zero gain (e.g. XOR).
            for k,(j,t) in enumerate(candidates):
                mask=masks[k]
                if min(int(mask.sum()),int((~mask).sum()))<config['min_leaf']:continue
                left,ls=stump(indices[mask]);right,rs=stump(indices[~mask]);gain=ls+rs-base_score
                if gain>best_gain+1e-12:
                    best_gain=gain;best={'feature':j,'threshold':t,'count':len(x),'gain':gain,'left':left,'right':right}
            trees.append(best)
            logits += config['learning_rate']*cls.tree_values(best,x)
        return cls(intercept,trees,config,int(x.shape[1]))

    @staticmethod
    def tree_values(tree,x):
        result=[]
        for row in x:
            node=tree
            while 'feature' in node:node=node['left'] if row[node['feature']]<=node['threshold'] else node['right']
            result.append(node['value'])
        return np.array(result)

    def logits(self,x):
        x=np.asarray(x,dtype=float)
        if not len(x):return np.array([])
        if x.ndim!=2 or x.shape[1]!=self.feature_count:raise ValueError('Feature dimension mismatch')
        result=np.full(len(x),self.intercept)
        for tree in self.trees:result+=self.config['learning_rate']*self.tree_values(tree,x)
        return result

    def probability(self,x):return 1/(1+np.exp(-np.clip(self.logits(x),-40,40)))
