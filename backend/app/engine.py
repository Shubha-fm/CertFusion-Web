from __future__ import annotations
from typing import Dict, Tuple, List
import numpy as np
from .paper_model import CLASSES
from .preprocess import feature_vector

PREDICATE_NAMES = ['Enh','FLAIRAbn','Strong','Core','Peripheral','Diffuse','Ring','LowT1']

RULES = [
    ('φ1', 'Enhancement + FLAIR abnormality', 'Enh ∧ FLAIR → not Background'),
    ('φ2', 'Absent FLAIR and enhancement', '¬FLAIR ∧ ¬Enh → Background'),
    ('φ3', 'Ring + low T1', 'Ring ∧ LowT1 → Edema'),
    ('φ4', 'Peripheral FLAIR without strong enhancement', 'Peripheral ∧ ¬Strong → Edema'),
    ('φ5', 'Core abnormality', 'Core → not Background'),
    ('φ6', 'Strong enhancement', 'Strong → Enhancing tumor'),
    ('φ7', 'Diffuse FLAIR', 'Diffuse → not Background'),
]

def _sigmoid(x): return 1/(1+np.exp(-x))

def _softmax(x):
    x=np.asarray(x,dtype=np.float64); x=x-np.max(x); e=np.exp(x); return e/e.sum()

def demo_inference(modalities: Dict[str,np.ndarray]) -> Tuple[np.ndarray, Dict[str,float]]:
    feats = np.concatenate([feature_vector(modalities[m]) for m in ['T1','T1ce','T2','FLAIR']])
    rng = np.random.default_rng(314159)
    W = rng.normal(0, 0.38, size=(5, feats.size))
    b = np.array([0.15,-0.05,0.08,0.10,-0.02])
    logits = W @ feats + b
    probs = _softmax(logits)
    f={m:feature_vector(modalities[m]) for m in modalities}
    pred={
        'Enh': float(_sigmoid(1.1*f['T1ce'][8] + 0.4*f['T1ce'][6] - 0.2)),
        'FLAIRAbn': float(_sigmoid(1.2*f['FLAIR'][8] + 0.5*f['FLAIR'][7] - 0.1)),
        'Strong': float(_sigmoid(1.7*f['T1ce'][8] + 0.2*f['T1ce'][1] - 0.7)),
        'Core': float(_sigmoid(0.8*f['T1'][9] + 0.5*f['T2'][8] - 0.1)),
        'Peripheral': float(_sigmoid(0.9*f['FLAIR'][1] + 0.4*f['FLAIR'][8] - 0.5)),
        'Diffuse': float(_sigmoid(0.7*f['FLAIR'][7] + 0.6*f['FLAIR'][1] - 0.4)),
        'Ring': float(_sigmoid(0.9*f['T1ce'][1] + 0.5*f['T1ce'][8] - 0.55)),
        'LowT1': float(_sigmoid(0.8*f['T1'][9] + 0.4*f['T1'][1] - 0.35)),
    }
    return probs, pred

def implication(a: float, b: float) -> float:
    return float(np.clip(1-a+a*b,0,1))

def rule_values(pred: Dict[str,float], probs: np.ndarray) -> List[float]:
    pbg, pncr, ped, pet, pdominant = probs
    return [
        implication(pred['Enh']*pred['FLAIRAbn'], 1-pbg),
        implication((1-pred['FLAIRAbn'])*(1-pred['Enh']), pbg),
        implication(pred['Ring']*pred['LowT1'], ped),
        implication(pred['Peripheral']*(1-pred['Strong']), ped),
        implication(pred['Core'], 1-pbg),
        implication(pred['Strong'], pet),
        implication(pred['Diffuse'], 1-pbg),
    ]

def robust_rule_status(pred: Dict[str,float], probs: np.ndarray, epsilon: float) -> List[str]:
    try:
        from z3 import Real, Solver, And
        has_z3 = True
    except Exception:
        has_z3 = False
    threshold = 0.5
    if not has_z3:
        I={n:(max(0.0,pred[n]-epsilon),min(1.0,pred[n]+epsilon)) for n in PREDICATE_NAMES}
        Q=[(max(0.0,float(v)-epsilon),min(1.0,float(v)+epsilon)) for v in probs]
        can_true=lambda r: r[1] >= threshold
        can_false=lambda r: r[0] < threshold
        pbg,pncr,ped,pet,pdom=Q
        feasible=[
            can_true(I['Enh']) and can_true(I['FLAIRAbn']) and can_true(pbg),
            can_false(I['FLAIRAbn']) and can_false(I['Enh']) and can_false(pbg),
            can_true(I['Ring']) and can_true(I['LowT1']) and can_false(ped),
            can_true(I['Peripheral']) and can_false(I['Strong']) and can_false(ped),
            can_true(I['Core']) and can_true(pbg),
            can_true(I['Strong']) and can_false(pet),
            can_true(I['Diffuse']) and can_true(pbg),
        ]
        return ['SAT' if x else 'UNSAT' for x in feasible]
    statuses=[]
    for ri in range(7):
        s=Solver(); s.set(timeout=2500)
        pv={n:Real(n) for n in PREDICATE_NAMES}; q=[Real(f'p{i}') for i in range(5)]
        for n in PREDICATE_NAMES:
            lo=max(0.0,pred[n]-epsilon); hi=min(1.0,pred[n]+epsilon)
            s.add(pv[n] >= lo, pv[n] <= hi)
        for i,v in enumerate(probs):
            lo=max(0.0,float(v)-epsilon); hi=min(1.0,float(v)+epsilon)
            s.add(q[i] >= lo, q[i] <= hi)
        pbg,pncr,ped,pet,pdom=q
        E=pv['Enh']>=threshold; F=pv['FLAIRAbn']>=threshold; Strong=pv['Strong']>=threshold
        Core=pv['Core']>=threshold; Peripheral=pv['Peripheral']>=threshold; Diffuse=pv['Diffuse']>=threshold
        Ring=pv['Ring']>=threshold; LowT1=pv['LowT1']>=threshold
        BG=pbg>=threshold; ED=ped>=threshold; ET=pet>=threshold
        violations=[
            And(E,F,BG),
            And(pv['FLAIRAbn']<threshold,pv['Enh']<threshold,pbg<threshold),
            And(Ring,LowT1,ped<threshold),
            And(Peripheral,pv['Strong']<threshold,ped<threshold),
            And(Core,BG),
            And(Strong,pet<threshold),
            And(Diffuse,BG),
        ]
        s.add(violations[ri])
        r=s.check()
        if str(r)=='unsat': statuses.append('UNSAT')
        elif str(r)=='sat': statuses.append('SAT')
        else: statuses.append('TIMEOUT')
    return statuses

def entropy(probs: np.ndarray) -> float:
    p=np.clip(probs,1e-12,1)
    return float(-(p*np.log(p)).sum())

def conformal_like_set(probs: np.ndarray, alpha: float) -> List[str]:
    order=np.argsort(probs)[::-1]
    cumulative=0.0; chosen=[]
    target=1-alpha
    for idx in order:
        chosen.append(CLASSES[int(idx)])
        cumulative += float(probs[idx])
        if cumulative >= target: break
    return chosen
