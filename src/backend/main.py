from fastapi import FastAPI, HTTPException, Depends, status, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from pydantic import BaseModel
from sqlalchemy import Column, String, Float, Boolean, DateTime, Text, Integer, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .schemas import UserCreate, UserResponse, Token, StudentData, PredictionResponse
from .auth import (
    get_password_hash, verify_password, create_access_token, 
    get_current_user, check_teacher
)
from .database import Database, engine, Base
from .ml_logic import MLPredictor
from .notifier import Notifier
import os
import uuid
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy.dialects.postgresql import UUID

load_dotenv()

# Ensure tables are mapped to the engine
Base.metadata.create_all(bind=engine)

class Profile(Base):
    __tablename__ = "profiles"
    __table_args__ = {"schema": "public"}
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False)
    full_name = Column(String)
    role = Column(String)
    roll_no = Column(String, unique=True)
    password_hash = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class StudentDB(Base):
    __tablename__ = "student_data"
    __table_args__ = {"schema": "public"}
    roll_no = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    study_hours = Column(Float)
    attendance = Column(Float)
    motivation = Column(String)
    learning_style = Column(String)
    stress_level = Column(Float)
    sem1_marks = Column(Float)
    sem2_marks = Column(Float)
    sem3_marks = Column(Float)
    sem4_marks = Column(Float)
    assignment_score = Column(Float)
    total_marks = Column(Float)
    average = Column(Float)
    momentum = Column(Float)
    predicted_grade = Column(Float)
    risk_level = Column(String)
    is_at_risk = Column(Boolean)
    status = Column(String)
    last_updated = Column(DateTime, default=datetime.utcnow)

class AlertDB(Base):
    __tablename__ = "alerts"
    __table_args__ = {"schema": "public"}
    id = Column(Integer, primary_key=True, index=True)
    roll_no = Column(String, ForeignKey("public.student_data.roll_no"))
    student_name = Column(String)
    risk_factor = Column(String)
    sent_at = Column(DateTime, default=datetime.utcnow)

app = FastAPI(title="EduMitra Platinum API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

predictor = MLPredictor()
notifier = Notifier()

class MockGradeInput(BaseModel):
    roll_no: str
    target_study_hours: float
    target_attendance: float

class StudentCreateSchema(BaseModel):
    roll_no: str
    name: str
    study_hours: float
    attendance: float
    motivation: str
    learning_style: str
    stress_level: float
    sem1_marks: float
    sem2_marks: float
    sem3_marks: float
    sem4_marks: float
    assignment_score: float

@app.get("/")
def read_root():
    return {"message": "EduMitra Platinum API Operational"}

# --- AUTH ENDPOINTS ---

@app.post("/register/teacher", response_model=UserResponse)
def register_teacher(user: UserCreate):
    db = Database.get_session()
    try:
        existing = db.query(Profile).filter(Profile.email == user.email).first()
        if existing:
            db.close()
            raise HTTPException(status_code=400, detail="Email already registered")
        
        print(f"DEBUG: Registering teacher {user.email}, password length: {len(user.password)}")
        new_teacher = Profile(
            email=user.email,
            full_name=user.full_name,
            role="Teacher",
            password_hash=get_password_hash(user.password[:72])
        )
        db.add(new_teacher)
        db.commit()
        db.refresh(new_teacher)
        
        res = UserResponse(
            id=str(new_teacher.id),
            email=new_teacher.email,
            full_name=new_teacher.full_name,
            role=new_teacher.role,
            created_at=new_teacher.created_at
        )
        return res
    except Exception as e:
        print(f"DEBUG: Signup Error: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.post("/login/teacher", response_model=Token)
def login_teacher(form_data: UserCreate): 
    db = Database.get_session()
    user = db.query(Profile).filter(Profile.email == form_data.email).first()
    db.close()
    
    if not user or user.role != 'Teacher' or not verify_password(form_data.password, user.password_hash): 
        raise HTTPException(status_code=401, detail="Invalid teacher credentials")
    
    access_token = create_access_token(data={"sub": user.email, "role": "Teacher", "name": user.full_name})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/login/student", response_model=Token)
def login_student(roll_no: str = Query(...), password: str = Query(...)):
    student = Database.get_student_data(roll_no)
    if not student:
        raise HTTPException(status_code=404, detail="Student record not found")
        
    access_token = create_access_token(data={"sub": roll_no, "role": "Student", "name": student[1]})
    return {"access_token": access_token, "token_type": "bearer"}

# --- STUDENT DATA CRUD ---

@app.get("/students", dependencies=[Depends(check_teacher)])
def list_students(
    search: Optional[str] = None,
    filter_type: Optional[str] = None,
    sort_by: Optional[str] = None
):
    result = Database.list_students(search, filter_type, sort_by)
    students = []
    for r in result:
        # roll_no(0), name(1), ..., average(12), momentum(13), predicted(14), risk(15), is_at_risk(16), status(17)
        students.append({
            "roll_no": r[0], "name": r[1], "average": r[12], "momentum": r[13], 
            "predicted_grade": r[14], "risk_level": r[15], "is_at_risk": r[16], "status": r[17]
        })
    return students

@app.post("/students", dependencies=[Depends(check_teacher)])
def create_student(data: StudentCreateSchema):
    # Recalculate ML fields
    avg = (data.sem1_marks + data.sem2_marks + data.sem3_marks + data.sem4_marks) / 4.0
    total = data.sem1_marks + data.sem2_marks + data.sem3_marks + data.sem4_marks
    mom = (1.5 * data.sem4_marks + 0.5 * data.sem3_marks - 0.5 * data.sem2_marks - 1.5 * data.sem1_marks) / 5.0
    
    # Predict
    ml_data = data.dict()
    grade, risk, explanation = predictor.predict(ml_data)
    
    student_dict = data.dict()
    student_dict.update({
        "total_marks": total,
        "average": avg,
        "momentum": mom,
        "predicted_grade": grade,
        "risk_level": risk,
        "is_at_risk": True if risk == "High Risk" else False,
        "status": "Pass" if avg > 40 else "Fail"
    })
    
    Database.upsert_student_data(student_dict)
    if student_dict["is_at_risk"]:
        Database.log_alert(data.roll_no, data.name, risk)
        
    return {"message": "Student created/updated successfully"}

@app.delete("/students/{roll_no}", dependencies=[Depends(check_teacher)])
def delete_student(roll_no: str):
    Database.delete_student_data(roll_no)
    return {"message": "Student deleted"}

@app.get("/students/{roll_no}")
def get_student(roll_no: str, current_user: dict = Depends(get_current_user)):
    if current_user["role"] == "Student" and current_user["sub"] != roll_no:
        raise HTTPException(status_code=403, detail="Unauthorized access")
        
    r = Database.get_student_data(roll_no)
    if not r:
        raise HTTPException(status_code=404, detail="Student not found")
        
    return {
        "roll_no": r[0], "name": r[1], "study_hours": r[2], "attendance": r[3],
        "motivation": r[4], "learning_style": r[5], "stress_level": r[6],
        "sem1_marks": r[7], "sem2_marks": r[8], "sem3_marks": r[9], "sem4_marks": r[10],
        "assignment_score": r[11], "total_marks": r[12], "average": r[13], "momentum": r[14],
        "predicted_grade": r[15], "risk_level": r[16], "is_at_risk": r[17], "status": r[18]
    }

@app.post("/predict/what-if")
def mock_prediction(data: MockGradeInput, current_user: dict = Depends(get_current_user)):
    student = Database.get_student_data(data.roll_no)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    params = {
        "roll_no": student[0], "study_hours": data.target_study_hours, 
        "attendance": data.target_attendance, "motivation": student[4],
        "learning_style": student[5], "stress_level": student[6],
        "sem1_marks": student[7], "sem2_marks": student[8], 
        "sem3_marks": student[9], "sem4_marks": student[10]
    }
    
    grade, risk, explanation = predictor.predict(params)
    return {
        "predicted_grade": grade,
        "risk_level": risk,
        "impact": "Positive" if grade > student[14] else "Negative"
    }

@app.post("/chatbot")
def chatbot_interaction(query: str, roll_no: str, current_user: dict = Depends(get_current_user)):
    student = Database.get_student_data(roll_no)
    if not student:
        return {"response": "Record missing."}
    
    q = query.lower()
    if "how am i doing" in q:
        return {"response": f"Your current momentum is {student[13]:.2f}. You are classified as {student[15]}."}
    if "tips" in q:
        return {"response": f"Based on your {student[15]} status, prioritize your Sem 4 weak areas. Increasing study hours by 2/week could boost your grade significantly."}
            
    return {"response": "I'm your AI tutor. Ask me for study tips or performance insights!"}
