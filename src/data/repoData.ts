export interface SQLQuery {
  id: string;
  title: string;
  purpose: string;
  sql: string;
  category: 'demographics' | 'risk' | 'clinical';
  mockResults?: { columns: string[]; rows: (string | number)[][] };
}

export const REPO_META = {
  name: "healthcare_analytics",
  owner: "sripoojithag",
  repoUrl: "https://github.com/sripoojithag/healthcare_analytics",
  liveDemoUrl: "https://healthcare-readmission-ai.streamlit.app/",
  title: "Healthcare Readmission Risk Prediction",
  tagline: "Predicting 30-day hospital readmission risk using Machine Learning, SQL, and Power BI",
  modelName: "Random Forest Classifier",
  modelAccuracy: "88%",
  techStack: [
    { name: "Python", category: "Core Language", color: "bg-blue-500/10 text-blue-600 border-blue-200 dark:border-blue-800 dark:text-blue-400" },
    { name: "Pandas", category: "Data Manipulation", color: "bg-indigo-500/10 text-indigo-600 border-indigo-200 dark:border-indigo-800 dark:text-indigo-400" },
    { name: "Scikit-Learn", category: "Machine Learning", color: "bg-amber-500/10 text-amber-600 border-amber-200 dark:border-amber-800 dark:text-amber-400" },
    { name: "Streamlit", category: "Web Application", color: "bg-rose-500/10 text-rose-600 border-rose-200 dark:border-rose-800 dark:text-rose-400" },
    { name: "Power BI", category: "BI Dashboard", color: "bg-yellow-500/10 text-yellow-700 border-yellow-200 dark:border-yellow-800 dark:text-yellow-400" },
    { name: "SQL", category: "Database Queries", color: "bg-emerald-500/10 text-emerald-600 border-emerald-200 dark:border-emerald-800 dark:text-emerald-400" },
  ],
  architectureSteps: [
    { step: 1, name: "Raw Data", description: "Hospital inpatient admissions dataset with patient history, medications, and lab tests" },
    { step: 2, name: "Data Cleaning", description: "Handling missing values, data normalization, categorical encoding with Pandas" },
    { step: 3, name: "Feature Engineering", description: "Length of stay, lab counts, polypharmacy indicators, age grouping" },
    { step: 4, name: "Machine Learning Model", description: "Random Forest Classifier trained to predict readmission (88% accuracy)" },
    { step: 5, name: "Interactive Dashboard", description: "Power BI visual exploration of risk factors, demographics, and length of stay" },
    { step: 6, name: "Web App Deployment", description: "Streamlit clinical interface for real-time risk assessment and score calculation" },
  ],
  keyInsights: [
    {
      title: "Hospital Stay Duration",
      detail: "Patients with longer hospital stays have a statistically higher readmission risk.",
      badge: "High Impact",
      icon: "Clock"
    },
    {
      title: "Lab Procedure Volume",
      detail: "Higher number of lab procedures strongly correlates with acute condition severity and subsequent readmission.",
      badge: "Clinical Indicator",
      icon: "Activity"
    },
    {
      title: "Age Demographics",
      detail: "Older age cohorts (e.g. 70-80 and 80-90) show significantly elevated readmission probability.",
      badge: "Demographic",
      icon: "Users"
    },
    {
      title: "Medication Complexity",
      detail: "Medication count and complex polypharmacy directly influence the likelihood of complication post-discharge.",
      badge: "Pharmacotherapy",
      icon: "Pill"
    },
    {
      title: "Medical Specialties",
      detail: "Certain medical specialties and diagnosis chapters exhibit distinct, clustered readmission patterns.",
      badge: "Specialty",
      icon: "Stethoscope"
    }
  ],
  futureRoadmap: [
    "Deploy model API using FastAPI for scalable microservice architecture",
    "Add Deep Learning architectures (e.g. Neural Networks, LSTM for longitudinal records)",
    "Real-time EHR / hospital EHR interface streaming integration",
    "Automated model retraining pipeline with drift detection"
  ],
  rawReadme: `# Healthcare Readmission Risk Prediction

## Project Overview
This project analyzes hospital patient data to predict the risk of patient readmission. The goal is to help hospitals identify high-risk patients early and reduce readmission rates.

This project includes:
- Data Cleaning & Analysis (Python, Pandas)
- Machine Learning Model (Random Forest)
- Interactive Dashboard (Power BI)
- Risk Prediction Web App (Streamlit)

---

## Project Architecture
Raw Data → Data Cleaning → Feature Engineering → Machine Learning Model → Dashboard → Web App

---

## Tech Stack
Python  
Pandas  
Scikit-Learn  
Streamlit  
Power BI  
sql  

---

## Key Insights
• Patients with longer hospital stays have higher readmission risk  
• Higher number of lab procedures correlates with readmission  
• Older age groups show higher risk  
• Medication count influences readmission probability  
• Certain medical specialties have higher readmission cases  

---

## SQL Analysis
SQL queries were used to explore the dataset and derive key insights such as:
- Total patient count
- Readmission distribution
- Age group analysis
- Hospital stay patterns
- Medication complexity

## Machine Learning Model
Algorithm used:
Random Forest Classifier

Model Accuracy:
88%

---

## Risk Categories
Low Risk  
Medium Risk  
High Risk  

Risk score is calculated using:
- Time in hospital
- Number of lab procedures
- Number of medications

---

## Streamlit Web Application
The Streamlit app allows hospitals to input patient information and predict readmission risk.

Example inputs:
- Time in hospital
- Number of medications
- Lab procedures

The model outputs:
Low Risk / Medium Risk / High Risk

---

## Dashboard
Power BI dashboard provides insights into:
- Readmission distribution
- Risk category breakdown
- Age group vs readmission
- Hospital stay vs risk

---

## Future Improvements
- Deploy model API using FastAPI
- Add deep learning models
- Real-time hospital data integration
- Automated retraining pipeline

## Live demo app
https://healthcare-readmission-ai.streamlit.app/`
};

export const REPO_SQL_QUERIES: SQLQuery[] = [
  {
    id: "q1",
    title: "Total Number of Patients",
    purpose: "Find the total number of patient records in the dataset.",
    category: "demographics",
    sql: `-- Total Number of Patients
SELECT COUNT(*) AS total_patients
FROM patient_data;`,
    mockResults: {
      columns: ["total_patients"],
      rows: [["101,766"]]
    }
  },
  {
    id: "q2",
    title: "Readmission Under 30 Days by Age Group",
    purpose: "Identify which age groups have higher short-term (<30 days) readmission risk.",
    category: "risk",
    sql: `-- Readmission Under 30 Days by Age Group
SELECT 
    age,
    SUM(readmitted = '<30') AS readmitted_under_30
FROM patient_data
GROUP BY age
ORDER BY age;`,
    mockResults: {
      columns: ["age", "readmitted_under_30"],
      rows: [
        ["[0-10)", "3"],
        ["[10-20)", "41"],
        ["[20-30)", "236"],
        ["[30-40)", "428"],
        ["[40-50)", "1,079"],
        ["[50-60)", "1,984"],
        ["[60-70)", "2,763"],
        ["[70-80)", "3,114"],
        ["[80-90)", "1,532"],
        ["[90-100)", "177"]
      ]
    }
  },
  {
    id: "q3",
    title: "Distribution of Hospital Stay Duration",
    purpose: "Understand how long patients typically stay in the hospital.",
    category: "clinical",
    sql: `-- Distribution of Hospital Stay Duration
SELECT 
    time_in_hospital,
    COUNT(*) AS patients
FROM patient_data
GROUP BY time_in_hospital
ORDER BY time_in_hospital;`,
    mockResults: {
      columns: ["time_in_hospital (days)", "patients"],
      rows: [
        ["1", "14,208"],
        ["2", "17,224"],
        ["3", "17,754"],
        ["4", "13,924"],
        ["5", "9,966"],
        ["6", "7,539"],
        ["7", "5,859"],
        ["8", "4,391"],
        ["9", "3,002"],
        ["10", "2,342"],
        ["11", "1,855"],
        ["12", "1,448"],
        ["13", "1,210"],
        ["14", "1,044"]
      ]
    }
  },
  {
    id: "q4",
    title: "Patient Count by Age Group",
    purpose: "Analyze overall patient demographics by age cohort.",
    category: "demographics",
    sql: `-- Patient Count by Age Group
SELECT 
    age,
    COUNT(*) AS patients
FROM patient_data
GROUP BY age
ORDER BY age;`,
    mockResults: {
      columns: ["age", "patients"],
      rows: [
        ["[0-10)", "161"],
        ["[10-20)", "691"],
        ["[20-30)", "1,657"],
        ["[30-40)", "3,775"],
        ["[40-50)", "9,685"],
        ["[50-60)", "17,256"],
        ["[60-70)", "22,483"],
        ["[70-80)", "26,068"],
        ["[80-90)", "17,197"],
        ["[90-100)", "2,793"]
      ]
    }
  },
  {
    id: "q5",
    title: "Medication Usage Analysis (Metformin)",
    purpose: "Analyze how frequently diabetes medication Metformin is prescribed.",
    category: "clinical",
    sql: `-- Medication Usage Analysis (Metformin)
SELECT 
    metformin,
    COUNT(*) AS patients
FROM patient_data
GROUP BY metformin;`,
    mockResults: {
      columns: ["metformin_status", "patients"],
      rows: [
        ["No", "81,778"],
        ["Steady", "18,346"],
        ["Up", "1,067"],
        ["Down", "575"]
      ]
    }
  },
  {
    id: "q6",
    title: "Hospital Stay vs Readmission",
    purpose: "Analyze whether longer hospital stays affect 30-day readmission counts and proportions.",
    category: "risk",
    sql: `-- Hospital Stay vs Readmission
SELECT 
    time_in_hospital,
    SUM(readmitted = '<30') AS readmitted_under_30,
    COUNT(*) AS total_patients
FROM patient_data
GROUP BY time_in_hospital
ORDER BY time_in_hospital;`,
    mockResults: {
      columns: ["time_in_hospital (days)", "readmitted_<30", "total_patients"],
      rows: [
        ["1", "1,241", "14,208"],
        ["2", "1,755", "17,224"],
        ["3", "1,982", "17,754"],
        ["4", "1,634", "13,924"],
        ["5", "1,278", "9,966"],
        ["7", "843", "5,859"],
        ["10", "398", "2,342"],
        ["14", "232", "1,044"]
      ]
    }
  },
  {
    id: "q7",
    title: "Rank Age Groups by Readmission Rate",
    purpose: "Ranks age groups by highest 30-day readmission risk using SQL window functions.",
    category: "risk",
    sql: `-- Rank Age Groups by Readmission Rate
SELECT 
    age,
    COUNT(*) AS total_patients,
    SUM(readmitted = '<30') AS readmitted_under_30,
    RANK() OVER (ORDER BY SUM(readmitted = '<30') DESC) AS risk_rank
FROM patient_data
GROUP BY age;`,
    mockResults: {
      columns: ["age", "total_patients", "readmitted_<30", "risk_rank"],
      rows: [
        ["[70-80)", "26,068", "3,114", "1"],
        ["[60-70)", "22,483", "2,763", "2"],
        ["[50-60)", "17,256", "1,984", "3"],
        ["[80-90)", "17,197", "1,532", "4"],
        ["[40-50)", "9,685", "1,079", "5"],
        ["[30-40)", "3,775", "428", "6"],
        ["[20-30)", "1,657", "236", "7"]
      ]
    }
  }
];

export const REPO_STRUCTURE = [
  { path: "README.md", type: "file", size: "2.1 KB", desc: "Project documentation, architecture, insights, model accuracy, and live demo link." },
  { path: "requirements.txt", type: "file", size: "43 B", desc: "Dependencies including streamlit, pandas, scikit-learn, etc." },
  { path: "app/application.py", type: "file", size: "695 B", desc: "Streamlit web application with sliders for hospital stay, lab procedures, and medications." },
  { path: "sql/analytics_queries.sql", type: "file", size: "1.5 KB", desc: "SQL analytical queries for demographic segmentation, readmission rates, and stay correlation." },
  { path: "dashboard/", type: "dir", size: "-", desc: "Power BI dashboard files and visual specifications." },
  { path: "data/", type: "dir", size: "-", desc: "Hospital patient dataset and preprocessed records." },
  { path: "notebooks/", type: "dir", size: "-", desc: "Jupyter notebooks for EDA, data cleaning, feature engineering, and model training." },
];
