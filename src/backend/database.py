import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("POSTGRES_URL")
if not DATABASE_URL:
    # Use the one provided by user if env is not set
    DATABASE_URL = "postgres://postgres.hqofysaeqglnvdqljvkl:V9DiaDYTnqiTANta@aws-1-us-east-1.pooler.supabase.com:6543/postgres?sslmode=require&supa=base-pooler.x"

# SQLAlchemy fix for postgres:// vs postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Ensure no weird supa=base parameters that confuse SQLAlchemy
if "&supa=" in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.split("&supa=")[0]

from sqlalchemy.orm import declarative_base

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Database:
    @staticmethod
    def get_session():
        return SessionLocal()

    @staticmethod
    def create_user(user_data: dict):
        with engine.connect() as conn:
            columns = ", ".join(user_data.keys())
            values = ", ".join([f":{k}" for k in user_data.keys()])
            sql = text(f"INSERT INTO profiles ({columns}) VALUES ({values}) RETURNING *")
            result = conn.execute(sql, user_data)
            conn.commit()
            return result.fetchone()

    @staticmethod
    def get_user_by_email(email: str):
        with engine.connect() as conn:
            sql = text("SELECT * FROM profiles WHERE email = :email")
            result = conn.execute(sql, {"email": email})
            return result.fetchone()

    @staticmethod
    def get_student_data(roll_no: str):
        with engine.connect() as conn:
            sql = text("SELECT * FROM student_data WHERE roll_no = :roll_no")
            result = conn.execute(sql, {"roll_no": roll_no})
            return result.fetchone()

    @staticmethod
    def upsert_student_data(student_data: dict):
        with engine.connect() as conn:
            cols = ", ".join(student_data.keys())
            placeholders = ", ".join([f":{k}" for k in student_data.keys()])
            updates = ", ".join([f"{k}=EXCLUDED.{k}" for k in student_data.keys()])
            sql = text(f"INSERT INTO student_data ({cols}) VALUES ({placeholders}) ON CONFLICT (roll_no) DO UPDATE SET {updates}")
            conn.execute(sql, student_data)
            conn.commit()

    @staticmethod
    def list_students(search: str = None, filter_type: str = None, sort_by: str = None):
        with engine.connect() as conn:
            base_sql = "SELECT * FROM student_data"
            conditions = []
            params = {}
            
            if search:
                conditions.append("(name ILIKE :search OR roll_no ILIKE :search)")
                params["search"] = f"%{search}%"
            
            if filter_type == "above_average":
                conditions.append("average > 70")
            elif filter_type == "average":
                conditions.append("average >= 40 AND average <= 70")
            elif filter_type == "poor":
                conditions.append("average < 40")
                
            if conditions:
                base_sql += " WHERE " + " AND ".join(conditions)
                
            if sort_by == "name_asc":
                base_sql += " ORDER BY name ASC"
            elif sort_by == "name_desc":
                base_sql += " ORDER BY name DESC"
                
            result = conn.execute(text(base_sql), params)
            return result.fetchall()

    @staticmethod
    def log_alert(roll_no: str, name: str, risk_factor: str):
        with engine.connect() as conn:
            sql = text("INSERT INTO alerts (roll_no, student_name, risk_factor) VALUES (:roll_no, :name, :risk_factor)")
            conn.execute(sql, {"roll_no": roll_no, "name": name, "risk_factor": risk_factor})
            conn.commit()

    @staticmethod
    def delete_student_data(roll_no: str):
        with engine.connect() as conn:
            sql = text("DELETE FROM student_data WHERE roll_no = :roll_no")
            conn.execute(sql, {"roll_no": roll_no})
            conn.commit()
