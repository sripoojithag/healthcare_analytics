# Healthcare Readmission Risk Prediction

## Project Overview
This project analyzes hospital patient data to predict the risk of patient readmission. 
The goal is to help hospitals identify high-risk patients early and reduce readmission rates.

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

---

## Key Insights

• Patients with longer hospital stays have higher readmission risk  
• Higher number of lab procedures correlates with readmission  
• Older age groups show higher risk  
• Medication count influences readmission probability  
• Certain medical specialties have higher readmission cases  

---

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

---

## Live demo app
https://healthcare-readmission-ai.streamlit.app/

## Author

Sri Poojitha Garine  
Computer Science Student  
Data Science & AI Enthusiast
