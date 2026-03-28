import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder
import shap
import joblib
import os
import __main__

def calculate_momentum(row):
    # Calculate slope over 4 semesters (x = 1, 2, 3, 4)
    # y = mx + c. Slope formula: sum((x - mean_x) * y) / sum((x - mean_x)^2)
    # where x-mean_x are [-1.5, -0.5, 0.5, 1.5], sum squared = 5.0
    s1, s2, s3, s4 = row['Sem1_Marks'], row['Sem2_Marks'], row['Sem3_Marks'], row['Sem4_Marks']
    return (-1.5 * s1 - 0.5 * s2 + 0.5 * s3 + 1.5 * s4) / 5.0

def main():
    print("Loading dataset...")
    df = pd.read_excel('data/student_performance_enhanced.xlsx')

    print("Handling missing values...")
    # Fill numeric columns with median, object columns with mode
    num_cols = df.select_dtypes(include=[np.number]).columns
    cat_cols = df.select_dtypes(include=['object']).columns

    df[num_cols] = df[num_cols].fillna(df[num_cols].median())
    for col in cat_cols:
        df[col] = df[col].fillna(df[col].mode()[0])

    print("Feature Engineering: Academic Momentum...")
    df['Academic_Momentum'] = df.apply(calculate_momentum, axis=1)

    # Features and Targets
    target_class = 'Pass_Fail'
    target_reg = 'FinalGrade'
    
    # Exclude leakage features and identifiers
    exclude_cols = ['RollNo', 'Total_Marks', 'Average', 'Grade', 'FinalGrade', 'Pass_Fail']
    feature_cols = [c for c in df.columns if c not in exclude_cols]

    X = df[feature_cols]
    
    y_reg = df[target_reg]
    # Assuming Pass_Fail might be strings like "Pass", "Fail"
    if df[target_class].dtype == object:
        y_class = (df[target_class] == 'Fail').astype(int) # 1 string for Fail, High Risk
    else:
        y_class = df[target_class]

    # Preprocessing
    numeric_features = X.select_dtypes(include=[np.number]).columns.tolist()
    categorical_features = X.select_dtypes(exclude=[np.number]).columns.tolist()

    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), numeric_features),
            ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_features)
        ])

    print("Training models...")
    X_train, X_test, y_reg_train, y_reg_test, y_class_train, y_class_test = train_test_split(
        X, y_reg, y_class, test_size=0.2, random_state=42
    )

    # We will fit the preprocessor separately so we can use SHAP properly on transformed features
    X_train_processed = preprocessor.fit_transform(X_train)
    X_test_processed = preprocessor.transform(X_test)
    
    # Get feature names after one hot encoding
    feature_names_full = preprocessor.get_feature_names_out()
    feature_names = [f.split('__', 1)[-1] for f in feature_names_full]

    # Convert sparse matrix to dense dataframe for SHAP compatibility
    X_train_processed_df = pd.DataFrame(
        X_train_processed.toarray() if hasattr(X_train_processed, 'toarray') else X_train_processed, 
        columns=feature_names
    )
    X_test_processed_df = pd.DataFrame(
        X_test_processed.toarray() if hasattr(X_test_processed, 'toarray') else X_test_processed, 
        columns=feature_names
    )

    reg_model = RandomForestRegressor(n_estimators=100, random_state=42)
    reg_model.fit(X_train_processed_df, y_reg_train)

    clf_model = RandomForestClassifier(n_estimators=100, random_state=42)
    clf_model.fit(X_train_processed_df, y_class_train)

    print("Initializing SHAP Explainer...")
    # Use the TreeExplainer on the classifier for Risk explanations
    explainer = shap.TreeExplainer(clf_model)
    
    # Save artifacts
    os.makedirs('models', exist_ok=True)
    print("Saving models and preprocessor...")
    joblib.dump(preprocessor, 'models/preprocessor.pkl')
    joblib.dump(reg_model, 'models/regressor.pkl')
    joblib.dump(clf_model, 'models/classifier.pkl')
    # Save explainer directly using joblib or shap
    joblib.dump(explainer, 'models/explainer.pkl')
    joblib.dump(feature_names, 'models/feature_names.pkl')
    
    print("Pipeline completed successfully!")

if __name__ == '__main__':
    main()
