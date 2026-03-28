import os
import joblib
import pandas as pd
import numpy as np
import shap
from typing import Tuple

# Load models and artifacts globally
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
MODEL_DIR = os.path.join(BASE_DIR, 'models')

class MLPredictor:
    def __init__(self):
        try:
            self.preprocessor = joblib.load(os.path.join(MODEL_DIR, 'preprocessor.pkl'))
            self.reg_model = joblib.load(os.path.join(MODEL_DIR, 'regressor.pkl'))
            self.clf_model = joblib.load(os.path.join(MODEL_DIR, 'classifier.pkl'))
            self.explainer = joblib.load(os.path.join(MODEL_DIR, 'explainer.pkl'))
            self.feature_names = joblib.load(os.path.join(MODEL_DIR, 'feature_names.pkl'))
        except Exception as e:
            print(f"Error loading models: {e}")
            self.models_loaded = False
        else:
            self.models_loaded = True

    def calculate_momentum(self, s1, s2, s3, s4) -> float:
        # Academic Momentum Slope: (1.5*S4 + 0.5*S3 - 0.5*S2 - 1.5*S1) / 5.0
        return (1.5 * s4 + 0.5 * s3 - 0.5 * s2 - 1.5 * s1) / 5.0

    def predict(self, data: dict) -> Tuple[float, str, str]:
        if not self.models_loaded:
            return 0.0, "Unknown", "Models not loaded"

        df_input = pd.DataFrame([data])
        df_input['Academic_Momentum'] = self.calculate_momentum(
            data['sem1_marks'], data['sem2_marks'], data['sem3_marks'], data['sem4_marks']
        )
        
        try:
            processed_data = self.preprocessor.transform(df_input)
            df_processed = pd.DataFrame(processed_data.toarray() if hasattr(processed_data, 'toarray') else processed_data, columns=self.feature_names)
            
            # Predict
            grade_pred = self.reg_model.predict(df_processed)[0]
            
            # Predict Risk probability
            try:
                probs = self.clf_model.predict_proba(df_processed)[0]
                prob_risk = probs[1] if len(probs) > 1 else 0.0
            except:
                prob_risk = 0.0
            
            risk_level = "High Risk" if prob_risk > 0.6 else ("Average" if prob_risk > 0.3 else "Low Risk")
            
            # SHAP Explanation
            fi = self.get_shap_explanation(df_processed)
            top_risks = fi[fi['SHAP_Value'] > 0].head(2)['Feature'].tolist()
            top_strengths = fi[fi['SHAP_Value'] < 0].head(2)['Feature'].tolist()
            
            explanation = f"Risk factors: {', '.join(top_risks)}. Strengths: {', '.join(top_strengths)}."
            if not top_risks:
                explanation = f"Student is in excellent standing. Strengths: {', '.join(top_strengths)}."

            return round(grade_pred, 2), risk_level, explanation
        except Exception as e:
            print(f"Prediction error: {e}")
            return 0.0, "Error", str(e)

    def get_shap_explanation(self, df_processed):
        shap_values = self.explainer.shap_values(df_processed)
        if isinstance(shap_values, list):
            sv = shap_values[1][0]
        else:
            sv = shap_values[0]
            
        return pd.DataFrame({
            'Feature': self.feature_names,
            'SHAP_Value': sv
        }).sort_values(by='SHAP_Value', ascending=False)
