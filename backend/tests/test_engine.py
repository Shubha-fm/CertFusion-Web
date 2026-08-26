import numpy as np
from backend.app.engine import rule_values, robust_rule_status, conformal_like_set

def test_rule_vector_size():
    p={k:0.7 for k in ['Enh','FLAIRAbn','Strong','Core','Peripheral','Diffuse','Ring','LowT1']}
    probs=np.array([.1,.1,.2,.5,.1])
    assert len(rule_values(p,probs)) == 7
    assert len(robust_rule_status(p,probs,0.031)) == 7

def test_prediction_set_nonempty():
    probs=np.array([.05,.1,.1,.65,.1])
    assert len(conformal_like_set(probs,.1)) >= 1
