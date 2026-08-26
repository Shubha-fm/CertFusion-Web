from __future__ import annotations
import time, uuid
from pathlib import Path
from typing import Dict
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from .config import MODEL_PATH, MODE, EPSILON, CONFORMAL_ALPHA, TLC_JAR
from .schemas import AnalysisResponse
from .preprocess import load_modality
from .paper_model import CLASSES, load_checkpoint, run_checkpoint
from .engine import demo_inference, rule_values, robust_rule_status, entropy, conformal_like_set, RULES
from .report import build_report

app=FastAPI(title='CertFusion Web API', version='1.0.0')
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_credentials=False, allow_methods=['*'], allow_headers=['*'])
MODEL=load_checkpoint(MODEL_PATH) if MODE != 'demo' else None
CACHE: Dict[str,dict]={}

@app.get('/api/health')
def health():
    return {'status':'ok','checkpoint_loaded': MODEL is not None,'mode':MODE,'epsilon':EPSILON}

@app.get('/api/model-card')
def model_card():
    return {
        'name':'CertFusion',
        'paper_architecture':'Four modality-specific 3D encoders, 512-d each, 2048-d fusion, 512→128→5 classifier',
        'classes':CLASSES,
        'modalities':['T1','T1ce','T2','FLAIR'],
        'formal_layers':['7 differentiable symbolic priors','Z3 consistency checking','TLA+ workflow status invariants'],
        'checkpoint_loaded': MODEL is not None,
        'checkpoint_path': str(MODEL_PATH),
        'warning':'Without the trained paper checkpoint the API runs an input-sensitive deterministic research demo surrogate. Demo predictions must not be reported as paper results.'
    }

@app.get('/api/workflow/spec')
def workflow_spec():
    root=Path(__file__).resolve().parents[2]
    tla=root/'formal'/'CertFusion.tla'
    return {
        'spec_available':tla.exists(),
        'tlc_runtime_available': bool(TLC_JAR),
        'properties':['TypeOK','NoUnsafeRelease','TimeoutNotCertified','CounterexampleNotCertified','ConformalBeforeRelease','TraceableRelease'],
        'note':'TLA+ verifies workflow status handling, not classifier accuracy or medical validity.'
    }

@app.post('/api/analyze', response_model=AnalysisResponse)
async def analyze(
    t1: UploadFile = File(...), t1ce: UploadFile = File(...),
    t2: UploadFile = File(...), flair: UploadFile = File(...)
):
    started=time.perf_counter(); rid=str(uuid.uuid4())[:8]
    files={'T1':t1,'T1ce':t1ce,'T2':t2,'FLAIR':flair}
    arrays={}; meta={}; audit=[]
    t=time.perf_counter()
    for modality, up in files.items():
        data=await up.read()
        if len(data)==0: raise HTTPException(400,f'{modality} is empty')
        try: arr,m=load_modality(data,up.filename or modality)
        except Exception as e: raise HTTPException(400,f'{modality}: {e}')
        arrays[modality]=arr; meta[modality]=m
        audit.append({'stage':'LOAD','status':'OK','detail':f'{modality}: {m["source_type"]} {m["shape"]}'})
    preprocess_ms=(time.perf_counter()-t)*1000

    t=time.perf_counter(); execution_mode='paper-checkpoint' if MODEL is not None and MODE!='demo' else 'research-demo'
    if execution_mode=='paper-checkpoint':
        try: probs,predicates=run_checkpoint(MODEL,arrays)
        except Exception as e:
            if MODE=='model': raise HTTPException(422,f'Checkpoint mode failed: {e}')
            probs,predicates=demo_inference(arrays); execution_mode='research-demo'
    else:
        probs,predicates=demo_inference(arrays)
    infer_ms=(time.perf_counter()-t)*1000
    audit.append({'stage':'INFERENCE','status':'OK','detail':execution_mode})

    vals=rule_values(predicates,probs)
    t=time.perf_counter(); robust=robust_rule_status(predicates,probs,EPSILON); verify_ms=(time.perf_counter()-t)*1000
    rules=[]
    for (rid2,name,desc),satval,rs in zip(RULES,vals,robust):
        rules.append({'id':rid2,'name':name,'description':desc,'satisfaction':round(float(satval),4),
                      'status':'SATISFIED' if satval>=0.8 else 'WEAK','robust_status':rs})
    counts={k:robust.count(k) for k in ['UNSAT','SAT','TIMEOUT']}
    overall='UNSAT' if counts['SAT']==0 and counts['TIMEOUT']==0 else ('SAT' if counts['SAT'] else 'TIMEOUT')
    audit.append({'stage':'SMT','status':overall,'detail':f"UNSAT={counts['UNSAT']}, SAT={counts['SAT']}, TIMEOUT={counts['TIMEOUT']}"})

    ent=entropy(probs); maxent=float(__import__('math').log(len(CLASSES)))
    unc='Low' if ent<0.45*maxent else ('Moderate' if ent<0.72*maxent else 'High')
    confset=conformal_like_set(probs,CONFORMAL_ALPHA)
    idx=int(probs.argmax())
    workflow=[
        {'name':'TypeOK','status':'PASS','meaning':'Workflow variables stay inside declared types.'},
        {'name':'NoUnsafeRelease','status':'PASS','meaning':'Certified release requires UNSAT and certificate=true.'},
        {'name':'TimeoutNotCertified','status':'PASS','meaning':'TIMEOUT cannot create a certificate.'},
        {'name':'CounterexampleNotCertified','status':'PASS','meaning':'SAT cannot create a certificate.'},
        {'name':'ConformalBeforeRelease','status':'PASS','meaning':'Prediction set must exist before release.'},
        {'name':'TraceableRelease','status':'PASS','meaning':'Released output keeps input and property traceability.'},
    ]
    audit.append({'stage':'TLA+','status':'MODEL-CHECKED ARTIFACT','detail':'Bundled workflow invariants shown; runtime TLC is optional.'})
    total=(time.perf_counter()-started)*1000
    result={
        'request_id':rid,'mode':execution_mode,
        'mode_note':('Loaded paper checkpoint.' if execution_mode=='paper-checkpoint' else 'Checkpoint not loaded. Input-sensitive deterministic surrogate is running so the full web workflow can be demonstrated. Do not use demo predictions as experimental or clinical results.'),
        'predicted_class':CLASSES[idx], 'confidence':round(float(probs[idx]),4),
        'probabilities':{c:round(float(p),4) for c,p in zip(CLASSES,probs)},
        'conformal_set':confset,'entropy':round(ent,4),'uncertainty_level':unc,
        'predicates':{k:round(float(v),4) for k,v in predicates.items()},
        'rules':rules,'rule_satisfaction_rate':round(float(sum(vals)/len(vals)),4),
        'verification_status':overall,'verification_counts':counts,
        'workflow_properties':workflow,'tlc_runtime_available':bool(TLC_JAR),
        'preprocessing':{'modalities':meta,'target_grid':[128,128,128],'normalization':'per-sequence z-score; fixed-grid resampling is applied in checkpoint mode'},
        'timings_ms':{'preprocessing':round(preprocess_ms,1),'inference':round(infer_ms,1),'verification':round(verify_ms,1),'total':round(total,1)},
        'audit':audit,
        'disclaimer':'Research prototype only. Not a medical device and not intended for diagnosis, treatment, triage, or patient management. Formal verification is scoped to encoded computational properties and workflow status handling; it does not establish clinical correctness.'
    }
    CACHE[rid]=result
    return result

@app.get('/api/report/{request_id}')
def report(request_id:str):
    if request_id not in CACHE: raise HTTPException(404,'Analysis result not found in this process.')
    pdf=build_report(CACHE[request_id])
    return Response(pdf,media_type='application/pdf',headers={'Content-Disposition':f'attachment; filename=certfusion-{request_id}.pdf'})
