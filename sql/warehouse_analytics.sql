-- ==============================================================================
-- Healthcare Data Warehouse Advanced Analytics Queries
-- Features: Joins across Star Schema, CTEs, Window Functions, Grouped Aggregations
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- 1. Readmission Rate by Age Cohort (CTE + Dimensional Join)
-- Analyzes short-term (<30 days) and total readmission proportions by patient age group.
-- ------------------------------------------------------------------------------
WITH AgeCohortMetrics AS (
    SELECT 
        p.age_group,
        COUNT(f.encounter_key) AS total_encounters,
        COUNT(DISTINCT p.patient_key) AS unique_patients,
        SUM(f.readmitted_30d) AS readmitted_under_30,
        SUM(f.readmitted_binary) AS readmitted_total,
        ROUND(AVG(f.time_in_hospital), 2) AS avg_hospital_stay,
        ROUND(AVG(f.num_medications), 2) AS avg_medications
    FROM fact_encounter f
    JOIN dim_patient p ON f.patient_key = p.patient_key
    GROUP BY p.age_group
)
SELECT 
    age_group,
    total_encounters,
    unique_patients,
    readmitted_under_30,
    ROUND((CAST(readmitted_under_30 AS FLOAT) / total_encounters) * 100.0, 2) AS readmission_30d_pct,
    readmitted_total,
    ROUND((CAST(readmitted_total AS FLOAT) / total_encounters) * 100.0, 2) AS readmission_total_pct,
    avg_hospital_stay,
    avg_medications
FROM AgeCohortMetrics
ORDER BY readmission_30d_pct DESC;


-- ------------------------------------------------------------------------------
-- 2. Disease Category Readmission Risk Ranking (Window Function: RANK & DENSE_RANK)
-- Ranks primary diagnostic chapters by total 30-day readmissions.
-- ------------------------------------------------------------------------------
WITH DiagnosisRisk AS (
    SELECT 
        d.category AS diagnosis_category,
        COUNT(f.encounter_key) AS encounters,
        SUM(f.readmitted_30d) AS readmissions_under_30,
        ROUND(AVG(f.num_lab_procedures), 1) AS avg_lab_tests,
        ROUND(AVG(f.time_in_hospital), 1) AS avg_length_of_stay
    FROM fact_encounter f
    JOIN dim_diagnosis d ON f.primary_diag_key = d.diagnosis_key
    GROUP BY d.category
)
SELECT 
    diagnosis_category,
    encounters,
    readmissions_under_30,
    ROUND((CAST(readmissions_under_30 AS FLOAT) / encounters) * 100.0, 2) AS readmission_rate_pct,
    avg_lab_tests,
    avg_length_of_stay,
    RANK() OVER (ORDER BY (CAST(readmissions_under_30 AS FLOAT) / encounters) DESC) AS risk_rank,
    DENSE_RANK() OVER (ORDER BY encounters DESC) AS volume_rank
FROM DiagnosisRisk
WHERE encounters >= 10
ORDER BY risk_rank;


-- ------------------------------------------------------------------------------
-- 3. Length of Hospital Stay Correlation with 30-Day Readmission
-- Evaluates whether longer hospitalization escalates readmission likelihood.
-- ------------------------------------------------------------------------------
SELECT 
    f.time_in_hospital AS stay_days,
    COUNT(f.encounter_key) AS total_patients,
    SUM(f.readmitted_30d) AS readmitted_30d,
    ROUND((CAST(SUM(f.readmitted_30d) AS FLOAT) / COUNT(f.encounter_key)) * 100.0, 2) AS readmission_30d_rate_pct,
    ROUND(AVG(f.num_lab_procedures), 2) AS avg_labs,
    ROUND(AVG(f.num_medications), 2) AS avg_meds
FROM fact_encounter f
GROUP BY f.time_in_hospital
ORDER BY stay_days ASC;


-- ------------------------------------------------------------------------------
-- 4. Medication Complexity & Polypharmacy Impact
-- Stratifies encounters by medication count brackets and insulin usage.
-- ------------------------------------------------------------------------------
WITH MedBands AS (
    SELECT 
        encounter_key,
        readmitted_30d,
        insulin,
        metformin,
        CASE 
            WHEN num_medications <= 10 THEN 'Low (1-10 meds)'
            WHEN num_medications <= 20 THEN 'Moderate (11-20 meds)'
            WHEN num_medications <= 30 THEN 'High (21-30 meds)'
            ELSE 'Severe Polypharmacy (31+ meds)'
        END AS medication_tier
    FROM fact_encounter
)
SELECT 
    medication_tier,
    insulin,
    COUNT(*) AS encounter_count,
    SUM(readmitted_30d) AS readmissions_30d,
    ROUND((CAST(SUM(readmitted_30d) AS FLOAT) / COUNT(*)) * 100.0, 2) AS readmission_rate_pct
FROM MedBands
GROUP BY medication_tier, insulin
ORDER BY medication_tier, readmission_rate_pct DESC;
