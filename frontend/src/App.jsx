import React, {useMemo, useState} from 'react';
import {
  Activity, Brain, CheckCircle2, ChevronRight, CircleAlert, Download,
  FileImage, FlaskConical, Gauge, Github, Layers3, LoaderCircle, LockKeyhole,
  Network, ScanLine, ShieldCheck, Sparkles, UploadCloud, XCircle
} from 'lucide-react';
import {BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer} from 'recharts';

const API = import.meta.env.VITE_API_URL || '';
const MODS = [
  {key:'t1', label:'T1', note:'Pre-contrast anatomy'},
  {key:'t1ce', label:'T1ce', note:'Post-contrast enhancement'},
  {key:'t2', label:'T2', note:'Fluid-sensitive contrast'},
  {key:'flair', label:'FLAIR', note:'Edema / infiltrative signal'}
];
const classShort = {'Background-dominant':'Background','NCR/NET':'NCR/NET','Edema':'Edema','Enhancing tumor':'Enhancing','Enhancement-dominant':'Enhancement-dom.'};

function FileCard({m, file, setFile}){
  const preview = useMemo(()=> file && file.type?.startsWith('image/') ? URL.createObjectURL(file):null,[file]);
  return <label className={`upload-card ${file?'ready':''}`}>
    <input type="file" accept=".nii,.nii.gz,image/png,image/jpeg" onChange={e=>setFile(e.target.files?.[0]||null)}/>
    <div className="upload-top"><span className="modality-pill">{m.label}</span>{file?<CheckCircle2 size={18}/>:<UploadCloud size={18}/>}</div>
    {preview ? <img src={preview} className="preview"/> : <div className="preview-placeholder"><FileImage size={30}/><span>{file?file.name:'NIfTI, PNG or JPG'}</span></div>}
    <div><strong>{file ? file.name : `Upload ${m.label}`}</strong><small>{m.note}</small></div>
  </label>
}

function StatusPill({status}){
  let cls='neutral', Icon=CircleAlert;
  if(['PASS','UNSAT','SATISFIED','CERTIFIED','OK'].includes(status)){cls='good'; Icon=CheckCircle2}
  if(['SAT','BLOCKED','WEAK'].includes(status)){cls='bad'; Icon=XCircle}
  if(['TIMEOUT','UNCERTIFIED'].includes(status)){cls='warn'; Icon=CircleAlert}
  return <span className={`status ${cls}`}><Icon size={14}/>{status}</span>
}

function Metric({label,value,sub, icon:Icon=Activity}){return <div className="metric"><div className="metric-icon"><Icon size={18}/></div><div><small>{label}</small><strong>{value}</strong>{sub&&<span>{sub}</span>}</div></div>}

export default function App(){
 const [files,setFiles]=useState({}); const [result,setResult]=useState(null); const [loading,setLoading]=useState(false); const [error,setError]=useState(''); const [tab,setTab]=useState('prediction');
 const allReady=MODS.every(m=>files[m.key]);
 async function analyze(){
   if(!allReady) return;
   setLoading(true); setError(''); setResult(null);
   try{
     const fd=new FormData(); MODS.forEach(m=>fd.append(m.key,files[m.key]));
     const r=await fetch(`${API}/api/analyze`,{method:'POST',body:fd});
     const data=await r.json(); if(!r.ok) throw new Error(data.detail||'Analysis failed'); setResult(data); setTab('prediction');
   }catch(e){setError(e.message)} finally{setLoading(false)}
 }
 const probData=result?Object.entries(result.probabilities).map(([name,value])=>({name:classShort[name]||name,value:Math.round(value*1000)/10})):[];
 return <div className="app-shell">
   <header className="topbar">
     <div className="brand"><div className="brand-mark"><Brain size={25}/></div><div><b>CertFusion</b><span>Verification-aware neurosymbolic MRI research system</span></div></div>
     <div className="header-actions"><span className="research-badge"><FlaskConical size={15}/> Research prototype</span><a href="https://github.com/Shubha-fm/CertFusion-Web" target="_blank" rel="noreferrer"><Github size={19}/></a></div>
   </header>
   <main>
     <section className="hero">
       <div><span className="eyebrow">MULTIMODAL AI + SYMBOLIC REASONING + FORMAL ASSURANCE</span><h1>From four MRI sequences to an <span>auditable prediction</span>.</h1><p>Upload T1, T1ce, T2 and FLAIR. CertFusion processes the case, fuses modality-specific evidence, evaluates imaging-informed symbolic constraints, checks bounded consistency, and exposes the complete release trail.</p></div>
       <div className="hero-flow">
         {[['1','MRI input',ScanLine],['2','Fusion',Layers3],['3','Rules',Network],['4','SMT',ShieldCheck],['5','Release',LockKeyhole]].map(([n,t,I],i)=><React.Fragment key={t}><div className="flow-node"><span>{n}</span><I size={22}/><b>{t}</b></div>{i<4&&<ChevronRight className="flow-arrow"/>}</React.Fragment>)}
       </div>
     </section>

     <section className="workspace">
       <div className="section-head"><div><span>01</span><div><h2>Case input</h2><p>Four co-registered sequences are required for the paper pipeline.</p></div></div><span className="privacy"><LockKeyhole size={14}/> Processed in the configured backend</span></div>
       <div className="upload-grid">{MODS.map(m=><FileCard key={m.key} m={m} file={files[m.key]} setFile={f=>setFiles(x=>({...x,[m.key]:f}))}/>)}</div>
       <div className="run-row"><div><b>{Object.values(files).filter(Boolean).length}/4 modalities loaded</b><span>For paper-checkpoint mode, upload 3D NIfTI volumes.</span></div><button className="primary" disabled={!allReady||loading} onClick={analyze}>{loading?<><LoaderCircle className="spin" size={18}/> Running full pipeline…</>:<><Sparkles size={18}/> Analyze & verify</>}</button></div>
       {error&&<div className="error"><CircleAlert size={18}/>{error}</div>}
     </section>

     {result && <>
       <section className="result-hero">
         <div className="result-title"><div className="result-icon"><Brain size={33}/></div><div><span>Predicted lesion-compartment class</span><h2>{result.predicted_class}</h2><p>Request #{result.request_id} · {result.mode}</p></div></div>
         <div className="confidence-ring" style={{'--p':`${Math.round(result.confidence*100)*3.6}deg`}}><div><strong>{Math.round(result.confidence*100)}%</strong><span>confidence</span></div></div>
         <div className="result-cert"><span>Formal consistency</span><StatusPill status={result.verification_status}/><small>{result.verification_counts.UNSAT}/7 properties exclude an encoded violation</small></div>
       </section>
       {result.mode==='research-demo' && <div className="demo-banner"><CircleAlert size={18}/><div><b>Running in research-demo mode</b><span>{result.mode_note}</span></div></div>}

       <section className="metrics-grid">
        <Metric label="Confidence" value={`${(result.confidence*100).toFixed(1)}%`} sub="Top-class probability" icon={Gauge}/>
        <Metric label="Rule satisfaction" value={`${(result.rule_satisfaction_rate*100).toFixed(1)}%`} sub="Mean soft prior value" icon={Network}/>
        <Metric label="Uncertainty" value={result.uncertainty_level} sub={`Entropy ${result.entropy.toFixed(3)}`} icon={Activity}/>
        <Metric label="Prediction set" value={`${result.conformal_set.length} class${result.conformal_set.length>1?'es':''}`} sub={result.conformal_set.join(', ')} icon={Layers3}/>
       </section>

       <section className="results-panel">
        <nav className="tabs">{[['prediction','Prediction'],['rules','Symbolic rules'],['verification','Formal assurance'],['audit','Audit trail']].map(([k,l])=><button className={tab===k?'active':''} onClick={()=>setTab(k)} key={k}>{l}</button>)}</nav>
        {tab==='prediction'&&<div className="tab-content two-col">
          <div className="chart-card"><h3>Class probabilities</h3><p>The complete five-class model output, not only the winning label.</p><div className="chart"><ResponsiveContainer width="100%" height="100%"><BarChart data={probData} layout="vertical" margin={{left:20,right:22}}><CartesianGrid strokeDasharray="3 3" horizontal={false}/><XAxis type="number" domain={[0,100]} unit="%"/><YAxis type="category" dataKey="name" width={112}/><Tooltip formatter={v=>`${v}%`}/><Bar dataKey="value" radius={[0,7,7,0]}/></BarChart></ResponsiveContainer></div></div>
          <div className="detail-card"><h3>Uncertainty-aware release</h3><div className="set-box"><span>Prediction set (α = 0.10)</span>{result.conformal_set.map(x=><b key={x}>{x}</b>)}</div><div className="info-row"><span>Normalized entropy</span><b>{(result.entropy/Math.log(5)).toFixed(3)}</b></div><div className="info-row"><span>Total response time</span><b>{result.timings_ms.total.toFixed(0)} ms</b></div><div className="info-row"><span>Verification time</span><b>{result.timings_ms.verification.toFixed(0)} ms</b></div></div>
        </div>}
        {tab==='rules'&&<div className="tab-content"><div className="rule-grid">{result.rules.map(r=><div className="rule-card" key={r.id}><div className="rule-head"><span>{r.id}</span><StatusPill status={r.robust_status}/></div><h3>{r.name}</h3><code>{r.description}</code><div className="progress"><i style={{width:`${r.satisfaction*100}%`}}/></div><small>Soft satisfaction {(r.satisfaction*100).toFixed(1)}%</small></div>)}</div></div>}
        {tab==='verification'&&<div className="tab-content two-col">
           <div className="verification-card"><div className="shield"><ShieldCheck size={40}/></div><h3>SMT consistency result</h3><StatusPill status={result.verification_status}/><p>Only UNSAT excludes the encoded violation inside the bounded web verification abstraction. SAT indicates a counterexample in the abstraction; TIMEOUT is inconclusive.</p><div className="counts"><div><b>{result.verification_counts.UNSAT}</b><span>UNSAT</span></div><div><b>{result.verification_counts.SAT}</b><span>SAT</span></div><div><b>{result.verification_counts.TIMEOUT}</b><span>TIMEOUT</span></div></div></div>
           <div className="workflow-list"><h3>TLA+ workflow invariants</h3><p>Workflow-level status handling is separated from classifier correctness.</p>{result.workflow_properties.map(x=><div key={x.name}><CheckCircle2 size={18}/><span><b>{x.name}</b><small>{x.meaning}</small></span><StatusPill status={x.status}/></div>)}</div>
        </div>}
        {tab==='audit'&&<div className="tab-content"><div className="audit-list">{result.audit.map((a,i)=><div key={i}><span className="audit-index">{String(i+1).padStart(2,'0')}</span><div><b>{a.stage}</b><p>{a.detail}</p></div><StatusPill status={a.status==='MODEL-CHECKED ARTIFACT'?'PASS':a.status}/></div>)}</div><div className="preprocess"><h3>Input provenance</h3>{Object.entries(result.preprocessing.modalities).map(([m,v])=><div key={m}><b>{m}</b><span>{v.filename}</span><span>{v.source_type}</span><span>{v.shape.join(' × ')}</span></div>)}</div></div>}
       </section>
       <section className="download-row"><div><Download size={24}/><div><b>Export the analysis record</b><span>Prediction, uncertainty, symbolic rules, verification status and disclaimer.</span></div></div><a className="secondary" href={`${API}/api/report/${result.request_id}`} target="_blank" rel="noreferrer"><Download size={17}/> Download PDF report</a></section>
     </>}

     <section className="architecture">
       <div className="section-head"><div><span>02</span><div><h2>What this application implements</h2><p>The web system mirrors the paper as an inspectable software pipeline.</p></div></div></div>
       <div className="architecture-grid">{[
        ['Multimodal perception','Four modality-specific 3D encoder interfaces with 512-dimensional latent representations.',Brain],
        ['Neurosymbolic layer','Seven differentiable imaging-informed prior templates and eight predicate scores.',Network],
        ['Bounded verification','Per-rule robust consistency checks with Z3-style UNSAT / SAT / TIMEOUT semantics.',ShieldCheck],
        ['Workflow assurance','Bundled TLA+ state-machine model for safe result and certificate handling.',LockKeyhole],
        ['Uncertainty output','Entropy and a set-valued output using the paper’s α = 0.10 interface.',Gauge],
        ['Reproducible artifact','API health, model card, audit records, Docker, CI and explicit checkpoint mode.',Github]
       ].map(([t,d,I])=><div className="arch-card" key={t}><I size={22}/><h3>{t}</h3><p>{d}</p></div>)}</div>
     </section>
   </main>
   <footer><div><Brain size={20}/><b>CertFusion</b><span>Research software accompanying verification-aware multimodal learning.</span></div><p>Not a medical device. Not for diagnosis, treatment, triage or patient management.</p></footer>
 </div>
}
