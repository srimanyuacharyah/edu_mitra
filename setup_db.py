import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("POSTGRES_URL")
if not DATABASE_URL:
    DATABASE_URL = "postgres://postgres.hqofysaeqglnvdqljvkl:V9DiaDYTnqiTANta@aws-1-us-east-1.pooler.supabase.com:6543/postgres?sslmode=require"

# SQLAlchemy fix for postgres:// vs postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Ensure no weird supa=base parameters that confuse SQLAlchemy if they are invalid
if "&supa=" in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.split("&supa=")[0]

engine = create_engine(DATABASE_URL)

import pandas as pd
import numpy as np

def setup():
    with engine.connect() as conn:
        print("Connected to database...")
        
        # 1. Create Profiles Table (Teacher/Student)
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS profiles (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                email TEXT UNIQUE NOT NULL,
                full_name TEXT,
                role TEXT CHECK (role IN ('Admin', 'Student', 'Teacher')) DEFAULT 'Student',
                roll_no TEXT UNIQUE,
                password_hash TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
            );
        """))
        print("Profiles table verified.")

        # 2. Create Student Data Table
        conn.execute(text("""
            DROP TABLE IF EXISTS alerts;
            DROP TABLE IF EXISTS student_data CASCADE;
            
            CREATE TABLE student_data (
                roll_no TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                study_hours FLOAT DEFAULT 5,
                attendance FLOAT DEFAULT 85,
                motivation TEXT DEFAULT 'Medium',
                learning_style TEXT DEFAULT 'Visual',
                stress_level FLOAT DEFAULT 3,
                sem1_marks FLOAT DEFAULT 75,
                sem2_marks FLOAT DEFAULT 78,
                sem3_marks FLOAT DEFAULT 80,
                sem4_marks FLOAT DEFAULT 82,
                assignment_score FLOAT DEFAULT 0,
                total_marks FLOAT DEFAULT 0,
                average FLOAT DEFAULT 0,
                momentum FLOAT DEFAULT 0,
                predicted_grade FLOAT DEFAULT 0,
                risk_level TEXT DEFAULT 'Low Risk',
                is_at_risk BOOLEAN DEFAULT FALSE,
                status TEXT DEFAULT 'Pass',
                last_updated TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
            );
        """))
        print("Student data table recreated with enhanced schema.")

        # 3. Create Alerts Table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS alerts (
                id SERIAL PRIMARY KEY,
                roll_no TEXT REFERENCES student_data(roll_no) ON DELETE CASCADE,
                student_name TEXT,
                risk_factor TEXT,
                sent_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
            );
        """))
        print("Alerts table verified.")

        # 4. Load & Seed from Excel
        excel_path = r'C:\Users\Lenovo\edu_mitra\data\student_performance_enhanced.xlsx'
        if os.path.exists(excel_path):
            print(f"Loading data from {excel_path}...")
            df = pd.read_excel(excel_path)
            
            # Column mapping: Excel -> SQL
            # Excel columns: RollNo, Name, StudyHours, Attendance, Motivation, LearningStyle, StressLevel, 
            # Sem1, Sem2, Sem3, Sem4, AssignmentScore, TotalMarks, Average, Momentum, PredictedGrade, RiskLevel, IsAtRisk, Status
            
            data_list = []
            for index, row in df.iterrows():
                name_val = row.get('Name', f"Student {index + 1}")
                sem1_val = row.get('Sem1', row.get('Sem1_Marks', 75))
                sem2_val = row.get('Sem2', row.get('Sem2_Marks', 75))
                sem3_val = row.get('Sem3', row.get('Sem3_Marks', 75))
                sem4_val = row.get('Sem4', row.get('Sem4_Marks', 75))
                assignment_val = row.get('AssignmentScore', row.get('AssignmentCompletion', 0))
                total_val = row.get('TotalMarks', row.get('Total_Marks', 300))
                avg_val = row.get('Average', 75)
                mom_val = row.get('Momentum', 0)
                pred_val = row.get('PredictedGrade', row.get('FinalGrade', 0))
                risk_val = row.get('RiskLevel', 'Low Risk')
                is_risk_val = row.get('IsAtRisk', False)
                status_val = row.get('Status', row.get('Pass_Fail', 'Pass'))

                data_list.append({
                    "roll_no": str(row['RollNo']), "name": name_val,
                    "study_hours": float(row['StudyHours']), "attendance": float(row['Attendance']),
                    "motivation": str(row['Motivation']), "learning_style": str(row['LearningStyle']),
                    "stress_level": float(row.get('StressLevel', 3.0)), 
                    "sem1": float(sem1_val), "sem2": float(sem2_val), "sem3": float(sem3_val), "sem4": float(sem4_val),
                    "assignment": float(assignment_val),
                    "total": float(total_val), "avg": float(avg_val),
                    "mom": float(mom_val), "pred": float(pred_val),
                    "risk": str(risk_val), "is_at_risk": bool(is_risk_val),
                    "status": str(status_val)
                })

            if data_list:
                conn.execute(text("""
                    INSERT INTO student_data (
                        roll_no, name, study_hours, attendance, motivation, learning_style, 
                        stress_level, sem1_marks, sem2_marks, sem3_marks, sem4_marks, 
                        assignment_score, total_marks, average, momentum, 
                        predicted_grade, risk_level, is_at_risk, status
                    ) VALUES (
                        :roll_no, :name, :study_hours, :attendance, :motivation, :learning_style,
                        :stress_level, :sem1, :sem2, :sem3, :sem4,
                        :assignment, :total, :avg, :mom,
                        :pred, :risk, :is_at_risk, :status
                    )
                """), data_list)
            
            print(f"Successfully seeded {len(df)} students from Excel.")
        else:
            print("Excel file not found, skipping seed.")

        conn.commit()
        print("Database setup complete!")

if __name__ == "__main__":
    setup()
