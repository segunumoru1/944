--- This SQL script creates the 'insurance_policies' table if it doesn't exist.
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
    insurance_period_end_date DATE
);

-- Optional: Add primary key or indexes if needed
-- ALTER TABLE insurance_policies ADD PRIMARY KEY (policy_number);
-- CREATE INDEX idx_start_date ON insurance_policies (insurance_period_start_date);