"""
Updated Pydantic schemas for string-based IDs and teacher isolation
"""
from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List
from datetime import datetime, date, time
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
    teacher_id: str  # Changed to string
    created_at: datetime
    
    class Config:
        from_attributes = True


# Class Schemas
class ClassBase(BaseModel):
    class_name: str
    section: str
    branch: Optional[str] = None

class ClassCreate(ClassBase):
    teacher_id: Optional[str] = None  # Optional for internal use

class ClassUpdate(BaseModel):
    class_name: Optional[str] = None
    section: Optional[str] = None
    branch: Optional[str] = None

class ClassResponse(ClassBase):
    class_id: str
    teacher_id: str
    created_at: datetime
    
    class Config:
        from_attributes = True


# Student Schemas
class StudentBase(BaseModel):
    roll_number: str
    name: str
    class_name: str  # Made required
    section: str     # Made required
    branch: Optional[str] = None
    email: Optional[EmailStr] = None

class StudentCreate(StudentBase):
    photo_url: Optional[str] = None

class StudentUpdate(BaseModel):
    name: Optional[str] = None
    class_name: Optional[str] = None
    section: Optional[str] = None
    branch: Optional[str] = None
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None

class StudentResponse(StudentBase):
    student_id: str  # Changed to string
    class_id: str
    photo_url: Optional[str] = None
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# Attendance Schemas
class AttendanceBase(BaseModel):
    status: str
    notes: Optional[str] = None
    
    @validator('status')
    def validate_status(cls, v):
        if v not in ['present', 'absent', 'late', 'excused']:
            raise ValueError('Status must be present, absent, late, or excused')
        return v

class AttendanceCreate(AttendanceBase):
    student_id: str
    attendance_date: Optional[date] = None

class AttendanceUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None

class AttendanceResponse(AttendanceBase):
    record_id: str
    student_id: str
    teacher_id: str
    class_id: str
    attendance_date: date
    check_in_time: Optional[time] = None
    check_out_time: Optional[time] = None
    marked_by_method: str
    created_at: datetime
    
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
    student_id: str  # Changed to string
    student_name: str
    roll_number: str
    total_days: int
    present_days: int
    absent_days: int
    attendance_percentage: float


# CSV Import Schemas
class CSVStudentImport(BaseModel):
    """Schema for CSV student import"""
    Class: str
    Section: str
    Roll_Number: str
    Branch: str
    Name: str
    Photo: str
    
    class Config:
        # Allow field names with spaces to match CSV headers
        allow_population_by_field_name = True
        fields = {
            'Class': 'class_name',
            'Section': 'section', 
            'Roll_Number': 'roll_number',
            'Branch': 'branch',
            'Name': 'name',
            'Photo': 'photo_url'
        }
