from pydantic import BaseModel
from typing import Dict, List, Optional

class RuleResult(BaseModel):
    id: str
    name: str
    description: str
    satisfaction: float
    status: str
    robust_status: str

class WorkflowProperty(BaseModel):
    name: str
    status: str
    meaning: str

class AnalysisResponse(BaseModel):
    request_id: str
    mode: str
    mode_note: str
    predicted_class: str
    confidence: float
    probabilities: Dict[str, float]
    conformal_set: List[str]
    entropy: float
    uncertainty_level: str
    predicates: Dict[str, float]
    rules: List[RuleResult]
    rule_satisfaction_rate: float
    verification_status: str
    verification_counts: Dict[str, int]
    workflow_properties: List[WorkflowProperty]
    tlc_runtime_available: bool
    preprocessing: Dict[str, object]
    timings_ms: Dict[str, float]
    audit: List[Dict[str, str]]
    disclaimer: str
