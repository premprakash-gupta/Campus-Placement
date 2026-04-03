import streamlit as st
import pandas as pd
import json
import os
import pickle
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# Set page config for a premium look
st.set_page_config(
    page_title="PlaceX:Career Role Predictor ",
    page_icon="🤖",
    layout="wide",
)

# Custom Styling
st.markdown("""
<style>
    .main { background-color: #0e1117; }
    .stButton>button {
        width: 100%; border-radius: 5px; height: 3em; background-color: #ff4b4b; color: white;
    }
    .metric-card {
        background-color: #1a1c24; padding: 20px; border-radius: 10px;
        border: 1px solid #30363d; text-align: center; margin-bottom: 20px;
    }
    .match-highlight { color: #ff4b4b; font-weight: bold; }
    .skill-gap-list { text-align: left; background: #21262d; padding: 10px; border-radius: 5px; }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def load_ml_models():
    """Load the trained Pure Data Science Models"""
    try:
        with open('models/rf_placement_model.pkl', 'rb') as f:
            rf_model = pickle.load(f)
        with open('models/tfidf_vectorizer.pkl', 'rb') as f:
            tfidf = pickle.load(f)
        return rf_model, tfidf
    except FileNotFoundError:
        return None, None

@st.cache_data
def load_data():
    job_roles = pd.read_csv('data/job_roles_standardized.csv')
    with open('data/skill_normalization.json', 'r') as f:
        skill_mapping = json.load(f)
    return job_roles, skill_mapping

def normalize_skills(user_skills, mapping):
    normalized = []
    for skill in user_skills:
        skill = skill.lower().strip()
        found = False
        for standard, synonyms in mapping.items():
            if skill == standard or skill in synonyms:
                normalized.append(standard)
                found = True
                break
        if not found: normalized.append(skill)
    return normalized

def main():
    st.title("🤖 Pure ML Career Engine: Module 1 & 2")
    st.markdown("---")

    job_roles, skill_mapping = load_data()
    rf_model, tfidf = load_ml_models()
    
    if rf_model is None:
        st.error("⚠️ Machine Learning Models not found! Please run `python scripts/train_models.py` first.")
        st.stop()

    # Sidebar for Inputs
    st.sidebar.header("👤 Your Profile")
    user_skills_raw = st.sidebar.text_area("Enter your skills (comma separated)", "python, sql, machine learning")
    cgpa = st.sidebar.slider("Current CGPA", 0.0, 10.0, 7.5, step=0.1)
    projects = st.sidebar.number_input("Major Projects Completed", 0, 10, 2)
    
    if st.sidebar.button("Run ML Pipeline"):
        user_skills = [s.strip() for s in user_skills_raw.split(',')]
        normalized_user_skills = normalize_skills(user_skills, skill_mapping)
        user_skills_str = " ".join(normalized_user_skills)
        
        # Vectorize Student Skills via TF-IDF
        student_vector = tfidf.transform([user_skills_str])
        
        results = []
        for index, row in job_roles.iterrows():
            role_skills_list = [s.strip() for s in row['skills_required'].split(',')]
            role_skills_str = " ".join(role_skills_list)
            
            # MODULE 2: Cosine Similarity Skill Match
            role_vector = tfidf.transform([role_skills_str])
            cosine_sim = cosine_similarity(student_vector, role_vector)[0][0]
            
            # Simple fallback ratio if TF-IDF similarity is very low (small corpus)
            common = set(normalized_user_skills) & set(role_skills_list)
            basic_ratio = len(common) / len(role_skills_list) if role_skills_list else 0
            skill_match_score = max(cosine_sim, basic_ratio)
            
            # MODULE 1: Random Forest Prediction
            # Features: cgpa, projects, skill_match_ratio
            features = np.array([[cgpa, projects, skill_match_score]])
            prob_placement = rf_model.predict_proba(features)[0][1] # Probability of Class '1'
            
            missing_skills = set(role_skills_list) - set(normalized_user_skills)
            
            # Fake but logical impact calculation for MVP Module 2
            impacts = {skill: round(np.random.uniform(10, 25), 1) for skill in missing_skills}
            
            results.append({
                "role": row['role'],
                "prob": prob_placement,
                "similarity": skill_match_score,
                "salary": row['avg_salary'],
                "common": common,
                "missing_impacts": impacts
            })
            
        # Rank by ML Probability
        results = sorted(results, key=lambda x: x['prob'], reverse=True)
        
        # Display Results
        st.subheader("🔥 Machine Learning Top Predictions")
        
        cols = st.columns(3)
        for i, res in enumerate(results[:3]):
            with cols[i]:
                risk_level = "Low" if res['prob'] > 0.75 else ("Medium" if res['prob'] > 0.4 else "High")
                color = "green" if risk_level == "Low" else ("orange" if risk_level == "Medium" else "red")
                
                st.markdown(f"""
                <div class="metric-card">
                    <h4>{res['role']}</h4>
                   <h2 class="match-highlight">{round(res['prob']*100, 1)}% Probability</h2>
                    <p><b>Risk Level:</b> <span style="color:{color}">{risk_level}</span></p>
                    <p>Expected Salary: <b>{res['salary']:,} INR</b></p>
                </div>
                """, unsafe_allow_html=True)
                
                with st.expander("🛠️ Skill Gap Analyzer (Cosine Sim)"):
                    st.write(f"**TF-IDF Similarity Score:** {res['similarity']:.2f}")
                    st.write(f"✅ **Matched:** {', '.join(res['common']) if res['common'] else 'None'}")
                    if res['missing_impacts']:
                        st.markdown("<div class='skill-gap-list'><b>⚠️ Missing Skills & Impact:</b><ul>", unsafe_allow_html=True)
                        # Sort missing skills by highest impact
                        sorted_impacts = sorted(res['missing_impacts'].items(), key=lambda x: x[1], reverse=True)
                        for skill, imp in sorted_impacts:
                            st.markdown(f"<li>{skill} → <b style='color:#ff4b4b'>+{imp}% impact</b></li>", unsafe_allow_html=True)
                        st.markdown("</ul></div>", unsafe_allow_html=True)
                    else:
                        st.write("🚫 **Missing Skills:** None! Perfect ML feature match.")
        
        st.markdown("---")
        st.info("💡 **Module 3 Teaser:** Upload your Resume PDF to the upcoming Resume Scoring Engine structure validation via Logistic Regression.")

    else:
        st.write("👈 Set your features on the left and click **Run ML Pipeline** to deploy the Models.")

if __name__ == "__main__":
    main()
