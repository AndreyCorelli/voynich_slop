"""First-order contextual class probes with the target evidence removed."""
import numpy as np


def local_distribution(chain,left=None,right=None,emission=None):
    transition=np.asarray(chain['transition'])
    values=np.array(chain['start']) if left is None else transition[left].copy()
    values*=np.array(chain['stop']) if right is None else transition[:,right]
    if emission is not None:values*=emission
    return values/values.sum()


def masked_context(chain,evidence):
    """For every target, exact cavity posterior and cavity-neighbor MAP states.

    Prefix/suffix messages exclude the target's evidence without refitting.
    Neighbor marginals are inferred separately for each masked target.
    """
    e=np.asarray(evidence);n,k=e.shape;t=np.asarray(chain['transition']);start=np.asarray(chain['start']);stop=np.asarray(chain['stop'])
    alpha=np.zeros_like(e);beta=np.zeros_like(e);alpha[0]=start*e[0];alpha[0]/=alpha[0].sum();beta[-1]=stop/stop.sum()
    for i in range(1,n):alpha[i]=(alpha[i-1]@t)*e[i];alpha[i]/=alpha[i].sum()
    for i in range(n-2,-1,-1):beta[i]=t@(e[i+1]*beta[i+1]);beta[i]/=beta[i].sum()
    posterior=[];lefts=[];rights=[];neighbor=[]
    for i in range(n):
        left=start if i==0 else alpha[i-1]@t
        values=left*beta[i];posterior.append(values/values.sum());lp=rp=None
        if i:
            values=alpha[i-1]*(t@beta[i]);values/=values.sum();lp=int(values.argmax())
        if i+1<n:
            values=(left@t)*e[i+1]*beta[i+1];values/=values.sum();rp=int(values.argmax())
        lefts.append(lp);rights.append(rp);neighbor.append(local_distribution(chain,lp,rp))
    return dict(posterior=np.array(posterior),neighbor_distribution=np.array(neighbor),left=lefts,right=rights)


def probability_metrics(probabilities,gold,mask):
    p=np.asarray(probabilities)[mask];y=np.asarray(gold)[mask];n=len(y)
    if not n:return dict(tokens=0,accuracy=None,balanced_accuracy=None,top2=None,top3=None,gold_probability=None,log_loss=None,confusion=None)
    order=np.argsort(-p,axis=1,kind='stable');pred=order[:,0];cm=np.zeros((p.shape[1],p.shape[1]),int);np.add.at(cm,(y,pred),1);counts=cm.sum(axis=1);present=counts>0
    gp=p[np.arange(n),y]
    return dict(tokens=n,accuracy=float((pred==y).mean()),balanced_accuracy=float(np.mean(cm.diagonal()[present]/counts[present])),
        top2=float(np.any(order[:,:2]==y[:,None],axis=1).mean()),top3=float(np.any(order[:,:3]==y[:,None],axis=1).mean()),
        gold_probability=float(gp.mean()),log_loss=float(-np.log(np.maximum(gp,1e-300)).mean()),confusion=cm.tolist())
