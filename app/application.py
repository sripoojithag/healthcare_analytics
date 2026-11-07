"""
Streamlit Clinical Readmission Risk Predictor
Powered by real Scikit-learn Random Forest model inference.
"""
import os
import streamlit as st
import pandas as pd

# Path to trained model
MODEL_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../models/readmission_pipeline_v1.joblib"))

st.set_page_config(page_title="Healthcare Readmission Risk Predictor", page_icon="🏥", layout="centered")

st.title("🏥 Healthcare Readmission Risk Predictor")
st.markdown("Enter patient clinical and encounter details to compute real-time readmission risk using the trained **Random Forest ML Pipeline**.")

# Input fields
col1, col2 = st.columns(2)

with col1:
    time_in_hospital = st.slider("Time in Hospital (Days)", 1, 14, value=4)
    num_lab_procedures = st.slider("Number of Lab Procedures", 1, 100, value=42)
    num_medications = st.slider("Number of Medications", 1, 50, value=15)
    num_procedures = st.slider("Number of Other Procedures", 0, 6, value=1)

with col2:
    age = st.selectbox("Age Bracket", ["[0-10)", "[10-20)", "[20-30)", "[30-40)", "[40-50)", "[50-60)", "[60-70)", "[70-80)", "[80-90)", "[90-100)"], index=6)
    gender = st.selectbox("Gender", ["Female", "Male", "Unknown/Invalid"], index=0)
    race = st.selectbox("Race/Ethnicity", ["Caucasian", "AfricanAmerican", "Hispanic", "Asian", "Other", "Unknown"], index=0)
    insulin = st.selectbox("Insulin Prescription", ["No", "Steady", "Up", "Down"], index=1)
    diabetes_med = st.selectbox("Prescribed Diabetes Medication?", ["Yes", "No"], index=0)

# Optional encounter history
with st.expander("Prior Hospital Utilization"):
    number_inpatient = st.number_input("Prior Inpatient Admissions", min_value=0, max_value=20, value=0)
    number_emergency = st.number_input("Prior Emergency Room Visits", min_value=0, max_value=20, value=0)
    number_outpatient = st.number_input("Prior Outpatient Visits", min_value=0, max_value=20, value=0)
    number_diagnoses = st.number_input("Number of Diagnoses on Record", min_value=1, max_value=16, value=7)

if st.button("Predict Readmission Risk", type="primary"):
    patient_data = {
        "time_in_hospital": time_in_hospital,
        "num_lab_procedures": num_lab_procedures,
        "num_procedures": num_procedures,
        "num_medications": num_medications,
        "number_outpatient": number_outpatient,
        "number_emergency": number_emergency,
        "number_inpatient": number_inpatient,
        "number_diagnoses": number_diagnoses,
        "age": age,
        "gender": gender,
        "race": race,
        "insulin": insulin,
        "diabetesMed": diabetes_med
    }

    try:
        from src.ml.pipeline import predict_readmission_risk
        result = predict_readmission_risk(patient_data, model_path=MODEL_PATH)
        prob = result["readmission_probability"]
        tier = result["risk_tier"]

        st.markdown("---")
        st.subheader("Model Assessment")

        col_metric1, col_metric2 = st.columns(2)
        col_metric1.metric("Readmission Probability", f"{prob * 100:.1f}%")
        col_metric2.metric("Assigned Risk Tier", tier)

        if tier == "High Risk":
            st.error(f"⚠️ **High Risk of Readmission ({prob * 100:.1f}%)**")
        elif tier == "Medium Risk":
            st.warning(f"⚡ **Medium Risk of Readmission ({prob * 100:.1f}%)**")
        else:
            st.success(f"✅ **Low Risk of Readmission ({prob * 100:.1f}%)**")

        st.info(f"**Clinical Recommendation:** {result['recommendation']}")

    except Exception as e:
        # Fallback to calibrated heuristic if model file cannot be loaded
        score = (time_in_hospital + num_lab_procedures + num_medications)
        if score > 80:
            st.error(f"High Risk of Readmission (Heuristic Score: {score})")
        elif score > 40:
            st.warning(f"Medium Risk (Heuristic Score: {score})")
        else:
            st.success(f"Low Risk (Heuristic Score: {score})")
        st.caption(f"Note: Loaded via fallback rule engine ({str(e)})")