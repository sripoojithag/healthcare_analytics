import streamlit as st
import pandas as pd
import pickle

st.title("🏥 Healthcare Readmission Risk Predictor")

st.write("Enter patient details to predict readmission risk")

# Input fields
time_in_hospital = st.slider("Time in Hospital", 1, 14)
num_lab_procedures = st.slider("Number of Lab Procedures", 1, 100)
num_medications = st.slider("Number of Medications", 1, 50)

# Example dummy model (until we load your real model)
if st.button("Predict Risk"):
    
    score = (time_in_hospital + num_lab_procedures + num_medications)

    if score > 80:
        st.error("High Risk of Readmission")
    elif score > 40:
        st.warning("Medium Risk")
    else:
        st.success("Low Risk")