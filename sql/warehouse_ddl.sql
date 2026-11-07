-- ==============================================================================
-- Healthcare Data Warehouse Star Schema DDL
-- Platform: Azure SQL Database / ANSI SQL Compatible
-- Source Dataset: UCI Diabetes 130-US Hospitals (1999-2008)
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- 1. Dimension: Patient Profile
-- Captures demographic and patient-level attributes across hospital admissions.
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dim_patient (
    patient_key INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_nbr VARCHAR(50) NOT NULL UNIQUE,
    race VARCHAR(50) DEFAULT 'Unknown',
    gender VARCHAR(50) DEFAULT 'Unknown/Invalid',
    age_group VARCHAR(20) DEFAULT 'Unknown',
    weight VARCHAR(50) DEFAULT 'Unknown',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_dim_patient_nbr ON dim_patient(patient_nbr);
CREATE INDEX IF NOT EXISTS idx_dim_patient_demographics ON dim_patient(race, gender, age_group);

-- ------------------------------------------------------------------------------
-- 2. Dimension: Clinical Diagnoses
-- Maps ICD-9 codes to clinical disease categories (Circulatory, Diabetes, etc.)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dim_diagnosis (
    diagnosis_key INTEGER PRIMARY KEY AUTOINCREMENT,
    diag_code VARCHAR(50) NOT NULL UNIQUE,
    category VARCHAR(100) NOT NULL,
    description VARCHAR(255) DEFAULT 'Clinical Diagnosis Code',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_dim_diagnosis_code ON dim_diagnosis(diag_code);
CREATE INDEX IF NOT EXISTS idx_dim_diagnosis_category ON dim_diagnosis(category);

-- ------------------------------------------------------------------------------
-- 3. Dimension: Encounter Context & Administration
-- Captures admission source, discharge status, payer, and medical specialty.
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dim_encounter_context (
    context_key INTEGER PRIMARY KEY AUTOINCREMENT,
    admission_type_id INTEGER DEFAULT 0,
    discharge_disposition_id INTEGER DEFAULT 0,
    admission_source_id INTEGER DEFAULT 0,
    payer_code VARCHAR(50) DEFAULT 'Unknown',
    medical_specialty VARCHAR(100) DEFAULT 'Unknown',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_dim_context_specialty ON dim_encounter_context(medical_specialty);

-- ------------------------------------------------------------------------------
-- 4. Fact: Hospital Encounters
-- Central grain: One record per hospital inpatient admission episode.
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS fact_encounter (
    encounter_key INTEGER PRIMARY KEY AUTOINCREMENT,
    encounter_id VARCHAR(50) NOT NULL UNIQUE,
    patient_key INTEGER NOT NULL,
    primary_diag_key INTEGER,
    context_key INTEGER,
    
    -- Numerical utilization metrics
    time_in_hospital INTEGER NOT NULL DEFAULT 1,
    num_lab_procedures INTEGER NOT NULL DEFAULT 0,
    num_procedures INTEGER NOT NULL DEFAULT 0,
    num_medications INTEGER NOT NULL DEFAULT 0,
    number_outpatient INTEGER NOT NULL DEFAULT 0,
    number_emergency INTEGER NOT NULL DEFAULT 0,
    number_inpatient INTEGER NOT NULL DEFAULT 0,
    number_diagnoses INTEGER NOT NULL DEFAULT 0,
    
    -- Lab & Glycemic markers
    max_glu_serum VARCHAR(20) DEFAULT 'None',
    a1c_result VARCHAR(20) DEFAULT 'None',
    
    -- Key Medication administrations
    metformin VARCHAR(20) DEFAULT 'No',
    insulin VARCHAR(20) DEFAULT 'No',
    change VARCHAR(10) DEFAULT 'No',
    diabetes_med VARCHAR(10) DEFAULT 'No',
    
    -- Readmission outcomes (Target measures)
    readmitted VARCHAR(20) NOT NULL DEFAULT 'NO',
    readmitted_binary INTEGER NOT NULL DEFAULT 0,  -- 1 if readmitted (<30 or >30), 0 otherwise
    readmitted_30d INTEGER NOT NULL DEFAULT 0,     -- 1 if readmitted under 30 days, 0 otherwise
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (patient_key) REFERENCES dim_patient(patient_key),
    FOREIGN KEY (primary_diag_key) REFERENCES dim_diagnosis(diagnosis_key),
    FOREIGN KEY (context_key) REFERENCES dim_encounter_context(context_key)
);

-- Crucial fact indexes for high-throughput analytics
CREATE INDEX IF NOT EXISTS idx_fact_encounter_id ON fact_encounter(encounter_id);
CREATE INDEX IF NOT EXISTS idx_fact_patient_key ON fact_encounter(patient_key);
CREATE INDEX IF NOT EXISTS idx_fact_readmitted ON fact_encounter(readmitted_30d, readmitted_binary);
CREATE INDEX IF NOT EXISTS idx_fact_utilization ON fact_encounter(time_in_hospital, num_lab_procedures, num_medications);
