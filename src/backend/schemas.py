from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    role: str = "Student"
    roll_no: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    id: Optional[str] = None
    role: Optional[str] = None

class StudentData(BaseModel):
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

class PredictionResponse(BaseModel):
    roll_no: str
    predicted_grade: float
    risk_level: str
    explanation: str

class StudentProfile(StudentData):
    total_marks: float
    average: float
    momentum: float
    is_at_risk: bool
    last_updated: datetime
