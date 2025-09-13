"""
Enhanced CRUD operations for string-based IDs and teacher isolation
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, extract
from typing import List, Optional
from datetime import date, datetime, time
import json
import uuid
from backend.models_new import Teacher, Student, Class, AttendanceRecord, AttendanceSession
from backend.schemas_new import (
    TeacherCreate, TeacherUpdate, StudentCreate, StudentUpdate,
    ClassCreate, ClassUpdate, AttendanceCreate
)
from backend.auth import get_password_hash


def generate_teacher_id(name: str, email: str) -> str:
    """Generate unique teacher ID"""
    name_part = name.replace(" ", "_").lower()[:10]
    email_part = email.split("@")[0][:5]
    return f"TCH_{name_part}_{email_part}_{int(datetime.now().timestamp())}"


def generate_class_id(class_name: str, section: str, teacher_id: str) -> str:
    """Generate unique class ID"""
    class_part = class_name.replace(" ", "_").upper()[:10]
    return f"{class_part}_{section}_{teacher_id}"


def generate_student_id(roll_number: str, class_id: str) -> str:
    """Generate unique student ID"""
    return f"STU_{class_id}_{roll_number}"


def generate_attendance_record_id(student_id: str, attendance_date: date) -> str:
    """Generate unique attendance record ID"""
    date_str = attendance_date.strftime("%Y%m%d")
    return f"ATT_{student_id}_{date_str}"


# Teacher CRUD operations
def create_teacher(db: Session, teacher: TeacherCreate):
    """Create a new teacher with string ID"""
    teacher_id = generate_teacher_id(teacher.name, teacher.email)
    hashed_password = get_password_hash(teacher.password)
    
    db_teacher = Teacher(
        teacher_id=teacher_id,
        name=teacher.name,
        email=teacher.email,
        password_hash=hashed_password,
        department=teacher.department,
        phone=teacher.phone
    )
    db.add(db_teacher)
    db.commit()
    db.refresh(db_teacher)
    return db_teacher


def get_teacher_by_email(db: Session, email: str):
    """Get teacher by email"""
    return db.query(Teacher).filter(Teacher.email == email).first()


def get_teacher_by_id(db: Session, teacher_id: str):
    """Get teacher by string ID"""
    return db.query(Teacher).filter(Teacher.teacher_id == teacher_id).first()


# Class CRUD operations
def create_class(db: Session, class_data: ClassCreate, teacher_id: str):
    """Create a new class for a teacher"""
    class_id = generate_class_id(class_data.class_name, class_data.section, teacher_id)
    
    db_class = Class(
        class_id=class_id,
        class_name=class_data.class_name,
        section=class_data.section,
        branch=class_data.branch,
        teacher_id=teacher_id
    )
    db.add(db_class)
    db.commit()
    db.refresh(db_class)
    return db_class


def get_classes_by_teacher(db: Session, teacher_id: str):
    """Get all classes for a specific teacher"""
    return db.query(Class).filter(Class.teacher_id == teacher_id).all()


# Student CRUD operations
def create_student(db: Session, student: StudentCreate, teacher_id: str):
    """Create a new student and assign to teacher's class"""
    # First, find or create the appropriate class
    db_class = db.query(Class).filter(
        and_(
            Class.class_name == student.class_name,
            Class.section == student.section,
            Class.teacher_id == teacher_id
        )
    ).first()
    
    if not db_class:
        # Create new class for this teacher
        class_data = ClassCreate(
            class_name=student.class_name,
            section=student.section,
            branch=student.branch,
            teacher_id=teacher_id
        )
        db_class = create_class(db, class_data, teacher_id)
    
    # Generate student ID
    student_id = generate_student_id(student.roll_number, db_class.class_id)
    
    # Create student
    db_student = Student(
        student_id=student_id,
        roll_number=student.roll_number,
        name=student.name,
        class_id=db_class.class_id,
        class_name=student.class_name,
        section=student.section,
        branch=student.branch,
        email=student.email,
        photo_url=student.photo_url
    )
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    return db_student


def get_students_by_teacher(db: Session, teacher_id: str, skip: int = 0, limit: int = 100):
    """Get all students for a specific teacher"""
    return db.query(Student).join(Class).filter(
        and_(
            Class.teacher_id == teacher_id,
            Student.is_active == True
        )
    ).offset(skip).limit(limit).all()


def get_student_by_id(db: Session, student_id: str):
    """Get student by string ID"""
    return db.query(Student).filter(Student.student_id == student_id).first()


def get_student_by_roll_and_teacher(db: Session, roll_number: str, teacher_id: str):
    """Get student by roll number within teacher's classes"""
    return db.query(Student).join(Class).filter(
        and_(
            Student.roll_number == roll_number,
            Class.teacher_id == teacher_id,
            Student.is_active == True
        )
    ).first()


# Attendance CRUD operations
def mark_attendance(db: Session, student_id: str, teacher_id: str, 
                   attendance_date: Optional[date] = None, 
                   status: str = "present", notes: Optional[str] = None):
    """Mark attendance for a student on a specific date"""
    if attendance_date is None:
        attendance_date = date.today()
    
    # Get student and verify teacher access
    student = db.query(Student).join(Class).filter(
        and_(
            Student.student_id == student_id,
            Class.teacher_id == teacher_id
        )
    ).first()
    
    if not student:
        return None
    
    # Generate record ID
    record_id = generate_attendance_record_id(student_id, attendance_date)
    
    # Check if record already exists
    existing_record = db.query(AttendanceRecord).filter(
        AttendanceRecord.record_id == record_id
    ).first()
    
    if existing_record:
        # Update existing record
        db.query(AttendanceRecord).filter(
            AttendanceRecord.record_id == record_id
        ).update({
            AttendanceRecord.status: status,
            AttendanceRecord.notes: notes,
            AttendanceRecord.updated_at: datetime.utcnow()
        })
        db.commit()
        return existing_record
    else:
        # Create new record
        attendance_record = AttendanceRecord(
            record_id=record_id,
            student_id=student_id,
            class_id=student.class_id,
            teacher_id=teacher_id,
            attendance_date=attendance_date,
            status=status,
            notes=notes,
            check_in_time=datetime.now().time() if status == "present" else None
        )
        db.add(attendance_record)
        db.commit()
        db.refresh(attendance_record)
        return attendance_record


def get_attendance_by_date_and_teacher(db: Session, teacher_id: str, 
                                     attendance_date: Optional[date] = None):
    """Get all attendance records for a teacher on a specific date"""
    if attendance_date is None:
        attendance_date = date.today()
    
    return db.query(AttendanceRecord).filter(
        and_(
            AttendanceRecord.teacher_id == teacher_id,
            AttendanceRecord.attendance_date == attendance_date
        )
    ).all()


def get_student_attendance_history(db: Session, student_id: str, teacher_id: str, 
                                 start_date: Optional[date] = None, 
                                 end_date: Optional[date] = None):
    """Get attendance history for a student"""
    query = db.query(AttendanceRecord).filter(
        and_(
            AttendanceRecord.student_id == student_id,
            AttendanceRecord.teacher_id == teacher_id
        )
    )
    
    if start_date:
        query = query.filter(AttendanceRecord.attendance_date >= start_date)
    if end_date:
        query = query.filter(AttendanceRecord.attendance_date <= end_date)
    
    return query.order_by(AttendanceRecord.attendance_date.desc()).all()


def get_class_attendance_summary(db: Session, class_id: str, teacher_id: str, 
                               start_date: Optional[date] = None, 
                               end_date: Optional[date] = None):
    """Get attendance summary for a class"""
    query = db.query(AttendanceRecord).filter(
        and_(
            AttendanceRecord.class_id == class_id,
            AttendanceRecord.teacher_id == teacher_id
        )
    )
    
    if start_date:
        query = query.filter(AttendanceRecord.attendance_date >= start_date)
    if end_date:
        query = query.filter(AttendanceRecord.attendance_date <= end_date)
    
    return query.all()
