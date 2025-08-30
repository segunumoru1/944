-- This SQL script creates the 'insurance_policies' table if it doesn't exist.
-- Run this script on your PostgreSQL database before inserting data.
-- Adjust column types or constraints as needed.

CREATE TABLE IF NOT EXISTS insurance_policies (
    policy_number VARCHAR(255),
    sum_insured DOUBLE PRECISION,
    premium DOUBLE PRECISION,
    own_retention_ppn DOUBLE PRECISION,
    own_retention_sum_insured DOUBLE PRECISION,
    own_retention_premium DOUBLE PRECISION,
    treaty_retention_ppn DOUBLE PRECISION,  -- Included based on rename in notebook
    treaty_sum_insured DOUBLE PRECISION,
    treaty_premium DOUBLE PRECISION,
    insurance_period_start_date DATE,
    insurance_period_end_date DATE,
    vector_id VARCHAR(100)
);
-- Add the vector_id column if it doesn't already exist
ALTER TABLE insurance_policies
ADD COLUMN IF NOT EXISTS vector_id VARCHAR(36);  -- UUIDs are 36 characters

-- Optional: Add index for faster lookups
CREATE INDEX IF NOT EXISTS idx_vector_id ON insurance_policies (vector_id);

-- Optional: If you want to ensure uniqueness
ALTER TABLE insurance_policies
ADD CONSTRAINT unique_vector_id UNIQUE (vector_id);