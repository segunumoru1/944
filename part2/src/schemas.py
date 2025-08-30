from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class InsurancePolicyBase(BaseModel):
    policy_number: str
    insured_name: Optional[str] = None
    sum_insured: float
    premium: float
    own_retention_ppn: float
    own_retention_sum_insured: float
    own_retention_premium: float
    treaty_ppn: float
    treaty_sum_insured: float
    treaty_premium: float
    insurance_period_start_date: datetime
    insurance_period_end_date: datetime

class InsurancePolicyCreate(InsurancePolicyBase):
    pass

class InsurancePolicy(InsurancePolicyBase):
    vector_id: Optional[str] = None
    
    class Config:
        from_attributes = True

class QueryRequest(BaseModel):
    question: str

class QueryResponse(BaseModel):
    answer: str
    sources: List[str]

class IngestionResponse(BaseModel):
    status: str
    message: str
    records_processed: int

class HealthResponse(BaseModel):
    status: str
    database: str
    error: Optional[str] = None

class MetricsResponse(BaseModel):
    total_policies: int
    average_premium: float
    total_premium: float
    earliest_policy: Optional[datetime]
    latest_policy: Optional[datetime]