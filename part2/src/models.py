from sqlalchemy import Column, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
import pandas as pd

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
    treaty_retention_ppn = Column(Float)  # Note: using treaty_retention_ppn consistently
    treaty_sum_insured = Column(Float)
    treaty_premium = Column(Float)
    facultative_outward_ppn = Column(Float)
    facultative_outward_sum_insured = Column(Float)
    facultative_outward_premium = Column(Float)
    insurance_period_start_date = Column(DateTime)
    insurance_period_end_date = Column(DateTime)

# Use this code snippet to update your CSV
df = pd.read_csv("processed_insurance.csv")

# Rename treaty_retention_ppn to treaty_ppn if needed
if 'treaty_retention_ppn' in df.columns and 'treaty_ppn' not in df.columns:
    df.rename(columns={'treaty_retention_ppn': 'treaty_ppn'}, inplace=True)

# Add missing columns
if 'insured_name' not in df.columns:
    df['insured_name'] = 'Unknown'  # Default value
    
for col in ['facultative_outward_ppn', 'facultative_outward_sum_insured', 'facultative_outward_premium']:
    if col not in df.columns:
        df[col] = 0.0  # Default numeric value
        
df.to_csv("processed_insurance.csv", index=False)