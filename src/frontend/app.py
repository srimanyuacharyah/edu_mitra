import streamlit as st
import pandas as pd
import requests
import matplotlib.pyplot as plt

st.set_page_config(page_title="EDUMITRA Dashboard", layout="wide")

st.title("🎓 EDUMITRA: Student Performance Prediction & Monitoring")

# Sidebar for inputs
st.sidebar.header("Enter Student Data")

col1, col2 = st.sidebar.columns(2)
with col1:
    study_hours = st.number_input("Study Hours/Week", value=10.0, step=1.0)
    attendance = st.number_input("Attendance (%)", value=85.0, step=1.0)
    resources = st.number_input("Resources Accessed", value=50.0, step=1.0)
    extracurricular = st.selectbox("Extracurricular", ["Yes", "No"])
    motivation = st.selectbox("Motivation Level", ["High", "Medium", "Low"])
    internet = st.selectbox("Internet Quality", ["Good", "Average", "Poor"])
    gender = st.selectbox("Gender", ["Male", "Female"])

with col2:
    age = st.number_input("Age", min_value=15, max_value=30, value=18)
    learning_style = st.selectbox("Learning Style", ["Visual", "Auditory", "Kinesthetic"])
    online_courses = st.number_input("Online Courses Completed", value=2.0, step=1.0)
    discussions = st.number_input("Discussion Participation", value=50.0, step=1.0)
    assignment = st.number_input("Assignment Completion (%)", value=85.0, step=1.0)
    edutech = st.selectbox("EduTech Tools Used", ["Yes", "No"])
    stress = st.number_input("Stress Level (1-10)", min_value=1.0, max_value=10.0, value=5.0)

st.sidebar.subheader("Exam & Semester Marks")
exam_score = st.sidebar.number_input("Recent Exam Score", value=75.0, step=1.0)
sem1 = st.sidebar.number_input("Sem 1 Marks", value=70.0, step=1.0)
sem2 = st.sidebar.number_input("Sem 2 Marks", value=72.0, step=1.0)
sem3 = st.sidebar.number_input("Sem 3 Marks", value=74.0, step=1.0)
sem4 = st.sidebar.number_input("Sem 4 Marks", value=75.0, step=1.0)

# Build the payload
payload = {
    "StudyHours": study_hours,
    "Attendance": attendance,
    "Resources": resources,
    "Extracurricular": extracurricular,
    "Motivation": motivation,
    "Internet": internet,
    "Gender": gender,
    "Age": age,
    "LearningStyle": learning_style,
    "OnlineCourses": online_courses,
    "Discussions": discussions,
    "AssignmentCompletion": assignment,
    "EduTech": edutech,
    "ExamScore": exam_score,
    "StressLevel": stress,
    "Sem1_Marks": sem1,
    "Sem2_Marks": sem2,
    "Sem3_Marks": sem3,
    "Sem4_Marks": sem4
}

st.header("Academic Momentum Visualization")
# Calculate simple momentum for visualization
momentum = (-1.5 * sem1 - 0.5 * sem2 + 0.5 * sem3 + 1.5 * sem4) / 5.0

fig, ax = plt.subplots(figsize=(8,3))
semesters = ["Sem 1", "Sem 2", "Sem 3", "Sem 4"]
marks = [sem1, sem2, sem3, sem4]
ax.plot(semesters, marks, marker='o', linestyle='-', color='b')
ax.set_ylim(0, 100)
ax.set_ylabel("Marks")
ax.set_title(f"Performance Trend (Momentum: {momentum:.2f})")
st.pyplot(fig)

st.divider()

if st.button("Predict Performance & Analyze Risk"):
    API_URL = "http://localhost:8000"
    
    with st.spinner("Analyzing..."):
        try:
            # Predict Endpoint
            res_pred = requests.post(f"{API_URL}/predict", json=payload)
            res_pred.raise_for_status()
            data_pred = res_pred.json()
            
            # Recommend Endpoint
            res_rec = requests.post(f"{API_URL}/recommend", json=payload)
            res_rec.raise_for_status()
            data_rec = res_rec.json()
            
            col_a, col_b = st.columns(2)
            
            with col_a:
                st.subheader("Prediction Results")
                st.metric("Predicted Final Grade", data_pred["FinalGrade"])
                
                risk_color = "red" if data_pred["RiskLevel"] == "High Risk" else "green"
                st.markdown(f"**Risk Level:** <span style='color:{risk_color}; font-size:24px;'>{data_pred['RiskLevel']}</span>", unsafe_allow_html=True)
                st.write(f"**Pass/Fail Probability:** {data_pred['Pass_Fail_Probability'] * 100:.1f}%")
                
            with col_b:
                st.subheader("Explainable AI (SHAP)")
                st.info(data_pred["Explanation"])
                
            st.subheader("Recommended Interventions")
            for intervention in data_rec["Interventions"]:
                st.markdown(f"- {intervention}")
                
        except requests.exceptions.RequestException as e:
            st.error(f"Error connecting to backend API: {e}")
            st.info("Make sure the FastAPI backend is running on http://localhost:8000")
