"""
Updated Pydantic schemas for string-based IDs and teacher isolation
"""
from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal


# Teacher Schemas
class TeacherBase(BaseModel):
    name: str
    email: EmailStr
    department: Optional[str] = None
    phone: Optional[str] = None

class TeacherCreate(TeacherBase):
    password: str

class TeacherUpdate(BaseModel):
    name: Optional[str] = None
    department: Optional[str] = None
    phone: Optional[str] = None

class TeacherResponse(TeacherBase):
    teacher_id: int  # Changed back to int to match database
    created_at: datetime
    
    class Config:
        from_attributes = True


# Class Schemas
class ClassBase(BaseModel):
    class_name: str
    section: str
    branch: Optional[str] = None

class ClassCreate(ClassBase):
    teacher_id: Optional[int] = None  # Optional for internal use

class ClassResponse(ClassBase):
    class_id: int
    teacher_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# Student Schemas
class StudentBase(BaseModel):
    roll_number: str
    name: str
    class_name: str     # Maps to 'Class' column in CSV
    section: str        # Maps to 'Section' column in CSV
    branch: Optional[str] = None         # Maps to 'Branch' column in CSV - made optional for compatibility

class StudentCreate(StudentBase):
    photo_url: Optional[str] = None
    teacher_id: Optional[int] = None  # Will be set automatically during upload

class StudentUpdate(BaseModel):
    name: Optional[str] = None
    class_name: Optional[str] = None
    section: Optional[str] = None
    branch: Optional[str] = None
    is_active: Optional[bool] = None

class StudentResponse(StudentBase):
    student_id: int
    photo_url: Optional[str] = None
    teacher_id: Optional[int] = None
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# Class Schemas
class ClassBase(BaseModel):
    class_name: str
    section: Optional[str] = None
    stream: Optional[str] = None
    subject: Optional[str] = None

class ClassCreate(ClassBase):
    teacher_id: int

class ClassUpdate(BaseModel):
    class_name: Optional[str] = None
    section: Optional[str] = None
    stream: Optional[str] = None
    subject: Optional[str] = None
    teacher_id: Optional[int] = None
    is_active: Optional[bool] = None

class ClassResponse(ClassBase):
    class_id: int
    teacher_id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# Attendance Schemas
class AttendanceBase(BaseModel):
    status: str
    attendance_type: Optional[str] = "Manual"
    confidence_score: Optional[Decimal] = None
    notes: Optional[str] = None
    
    @validator('status')
    def validate_status(cls, v):
        if v not in ['Present', 'Absent']:
            raise ValueError('Status must be Present or Absent')
        return v

class AttendanceCreate(AttendanceBase):
    student_id: int
    attendance_date: Optional[date] = None

class AttendanceBulkCreate(BaseModel):
    class_id: int
    attendance_date: Optional[date] = None
    student_statuses: List[dict]  # [{"student_id": 1, "status": "Present"}, ...]

class AttendanceUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None

class AttendanceResponse(AttendanceBase):
    attendance_id: int
    student_id: int
    teacher_id: int
    class_id: int
    attendance_date: date
    marked_at: datetime
    
    class Config:
        from_attributes = True


# Authentication Schemas
class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None


# File Upload Schemas
class FileUploadResponse(BaseModel):
    filename: str
    message: str
    records_processed: Optional[int] = None


# Dashboard/Analytics Schemas
class AttendanceStats(BaseModel):
    total_students: int
    present_today: int
    absent_today: int
    attendance_percentage: float

class StudentAttendanceStats(BaseModel):
    student_id: int
    student_name: str
    roll_number: str
    total_days: int
    present_days: int
    absent_days: int
    attendance_percentage: float

class ClassAttendanceStats(BaseModel):
    class_id: int
    class_name: str
    section: Optional[str]
    total_students: int
    average_attendance: float

# CSV Import Schema
class StudentCSVImport(BaseModel):
    roll_number: str
    name: str
    class_name: Optional[str] = None
    section: Optional[str] = None
    stream: Optional[str] = None
    email: Optional[str] = None
