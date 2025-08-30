from sqlalchemy import Column, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class InsurancePolicy(Base):
    __tablename__ = "insurance_policies"
    
    policy_number = Column(String, primary_key=True)
    insured_name = Column(String)
    sum_insured = Column(Float)
    premium = Column(Float)
    own_retention_ppn = Column(Float)
    own_retention_sum_insured = Column(Float)
    own_retention_premium = Column(Float)
    treaty_ppn = Column(Float)
    treaty_sum_insured = Column(Float)
    treaty_premium = Column(Float)
    insurance_period_start_date = Column(DateTime)
    insurance_period_end_date = Column(DateTime)
    vector_id = Column(String)