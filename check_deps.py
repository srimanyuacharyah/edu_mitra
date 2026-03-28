try:
    import fastapi
    import uvicorn
    import pandas
    import numpy
    import sklearn
    import shap
    import joblib
    import pydantic
    import email_validator
    from jose import jwt
    import passlib
    import fastapi_mail
    import sqlalchemy
    import psycopg2
    import dotenv
    import xgboost
    print("All backend imports successful!")
except ImportError as e:
    print(f"Missing dependency: {e}")
