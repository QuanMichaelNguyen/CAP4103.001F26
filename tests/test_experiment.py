import json
import numpy as np
from src.experiment import load_demo,split_data,Matcher,score_claims,rates,evaluate

def test_splits_are_disjoint():
    faces,_,_=load_demo()
    s=split_data(faces)
    for u in faces:
        assert sum(len(s[k][u]) for k in s)==len(faces[u])

def test_label_balance():
    f,_,_=load_demo(5)
    s=split_data(f)
    labels,scores=score_claims(Matcher(s['enroll'],True),s['test'])
    assert np.sum(labels)==len(s['test'][0])*5
    assert len(scores)==5*len(s['test'][0])*5

def test_perfect_separation():
    y=np.array([1,1,0,0]);z=np.array([3,2,-2,-3])
    assert rates(y,z)['eer']==0

def test_pipeline(tmp_path):
    f,k,_=load_demo(6)
    result=evaluate(f,k,tmp_path)
    assert result['protocol']['n_users']==6
    assert (tmp_path/'metrics.json').exists()
    assert len(result['rq3'])==7
    assert all(0<=result['rq3'][str(w)]['test']['eer']<=1 for w in [0.,.25,.5,.75,1.])
