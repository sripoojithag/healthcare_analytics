

--Total Number of Patients
SELECT COUNT(*) AS total_patients
FROM patient_data;

--Purpose:
--Find the total number of patient records.

-- Readmission Under 30 Days by Age Group
SELECT age,
SUM(readmitted = '<30') AS readmitted_under_30
FROM patient_data
GROUP BY age
ORDER BY age;

--Purpose:
--Identify which age groups have higher short-term readmission risk.

--Distribution of Hospital Stay Duration
SELECT time_in_hospital,
COUNT(*) AS patients
FROM patient_data
GROUP BY time_in_hospital
ORDER BY time_in_hospital;

--Purpose:
--Understand how long patients typically stay in the hospital.

-- Patient Count by Age Group
SELECT age,
COUNT(*) AS patients
FROM patient_data
GROUP BY age
ORDER BY age;

--Purpose:
--Analyze patient demographics by age group.

-- Medication Usage Analysis (Metformin)
SELECT metformin,
COUNT(*) AS patients
FROM patient_data
GROUP BY metformin;

--Purpose:
--Analyze how often Metformin medication is prescribed.

--Hospital Stay vs Readmission
SELECT time_in_hospital,
SUM(readmitted = '<30') AS readmitted_under_30,
COUNT(*) AS total_patients
FROM patient_data
GROUP BY time_in_hospital
ORDER BY time_in_hospital;

--Purpose:
--Analyze whether longer hospital stays affect readmission rates.