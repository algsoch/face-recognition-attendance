"""
CRUD operations and business logic for the attendance system
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, extract
from typing import List, Optional
from datetime import date, datetime
import pandas as pd
import json
from backend.models import Teacher, Student, Class, StudentClass, Attendance
from backend.schemas import (
    TeacherCreate, TeacherUpdate, StudentCreate, StudentUpdate,
    ClassCreate, ClassUpdate, AttendanceCreate, AttendanceBulkCreate
)
from backend.auth import get_password_hash


# Teacher CRUD operations
def create_teacher(db: Session, teacher: TeacherCreate):
    """Create a new teacher"""
    hashed_password = get_password_hash(teacher.password)
    db_teacher = Teacher(
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


def get_teacher_by_id(db: Session, teacher_id: int):
    """Get teacher by ID"""
    return db.query(Teacher).filter(Teacher.teacher_id == teacher_id).first()


def update_teacher(db: Session, teacher_id: int, teacher_update: TeacherUpdate):
    """Update teacher information"""
    db_teacher = get_teacher_by_id(db, teacher_id)
    if db_teacher:
        update_data = teacher_update.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_teacher, key, value)
        db_teacher.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_teacher)
    return db_teacher


# Student CRUD operations
def create_student(db: Session, student: StudentCreate, teacher_id: int):
    """Create a new student and assign to teacher"""
    db_student = Student(
        roll_number=student.roll_number,
        name=student.name,
        class_name=student.class_name,
        section=student.section,
        branch=student.branch,
        photo_url=student.photo_url,
        teacher_id=teacher_id
    )
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    return db_student


def get_students(db: Session, skip: int = 0, limit: int = 100, teacher_id: Optional[int] = None):
    """Get list of students filtered by teacher"""
    query = db.query(Student).filter(Student.is_active == True)
    
    if teacher_id:
        query = query.filter(Student.teacher_id == teacher_id)
    
    return query.offset(skip).limit(limit).all()


def get_student_by_id(db: Session, student_id: int):
    """Get student by ID"""
    return db.query(Student).filter(Student.student_id == student_id).first()


def get_student_by_roll_number(db: Session, roll_number: str):
    """Get student by roll number"""
    return db.query(Student).filter(Student.roll_number == roll_number).first()


def update_student(db: Session, student_id: int, student_update: StudentUpdate):
    """Update student information"""
    db_student = get_student_by_id(db, student_id)
    if db_student:
        update_data = student_update.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_student, key, value)
        db_student.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_student)
    return db_student


def delete_student(db: Session, student_id: int):
    """Enhanced soft delete with future-proof error handling and recovery options"""
    try:
        db_student = get_student_by_id(db, student_id)
        if not db_student:
            return {"success": False, "message": "Student not found", "student_id": student_id}
        
        if not db_student.is_active:
            return {"success": False, "message": "Student already deleted", "student_id": student_id}
        
        # Soft delete with timestamp
        db_student.is_active = False
        db_student.updated_at = datetime.utcnow()
        
        # If deleted_at column exists, use it for better tracking
        if hasattr(db_student, 'deleted_at'):
            db_student.deleted_at = datetime.utcnow()
        
        db.commit()
        
        return {
            "success": True, 
            "message": "Student soft-deleted successfully. Can be recovered if needed.",
            "student_id": student_id,
            "deleted_at": db_student.updated_at.isoformat() if db_student.updated_at else None
        }
        
    except Exception as e:
        db.rollback()
        return {
            "success": False, 
            "message": f"Delete operation failed: {str(e)}", 
            "student_id": student_id,
            "error": "database_error"
        }


def recover_student(db: Session, student_id: int):
    """Recover a soft-deleted student"""
    try:
        db_student = get_student_by_id(db, student_id, include_inactive=True)
        if not db_student:
            return {"success": False, "message": "Student not found"}
        
        if db_student.is_active:
            return {"success": False, "message": "Student is already active"}
        
        # Recover the student
        db_student.is_active = True
        db_student.updated_at = datetime.utcnow()
        
        # Clear deleted_at if it exists
        if hasattr(db_student, 'deleted_at'):
            db_student.deleted_at = None
        
        db.commit()
        
        return {
            "success": True,
            "message": "Student recovered successfully",
            "student_id": student_id
        }
        
    except Exception as e:
        db.rollback()
        return {"success": False, "message": f"Recovery failed: {str(e)}"}


def get_student_by_id(db: Session, student_id: int, include_inactive: bool = False):
    """Get student by ID with option to include inactive students"""
    query = db.query(Student).filter(Student.student_id == student_id)
    if not include_inactive:
        query = query.filter(Student.is_active == True)
    return query.first()


def bulk_import_students(db: Session, file_path: str, teacher_id: Optional[int] = None):
    """Import students from CSV/Excel file with photo URL support and teacher isolation
    Expected CSV format: Class, Section, Roll Number, Branch, Name, Photo
    """
    import requests
    import os
    from PIL import Image
    from io import BytesIO
    
    try:
        # Read file based on extension
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)
        
        print(f"CSV columns found: {list(df.columns)}")
        
        imported_count = 0
        duplicate_count = 0
        errors = []
        
        for index, row in df.iterrows():
            try:
                # Handle different possible column names (case-insensitive)
                def get_column_value(possible_names):
                    for name in possible_names:
                        # Try exact match first
                        if name in df.columns:
                            return str(row[name]) if pd.notna(row[name]) else ''
                        # Try case-insensitive match
                        for col in df.columns:
                            if col.lower().strip() == name.lower().strip():
                                return str(row[col]) if pd.notna(row[col]) else ''
                    return ''
                
                # Extract data using flexible column matching
                roll_number = get_column_value(['Roll Number', 'roll_number', 'Roll', 'rollnumber'])
                name = get_column_value(['Name', 'name', 'Student Name', 'student_name'])
                class_name = get_column_value(['Class', 'class', 'class_name', 'Grade'])
                section = get_column_value(['Section', 'section', 'Sec'])
                branch = get_column_value(['Branch', 'branch', 'Stream', 'stream', 'Course'])
                photo_url = get_column_value(['Photo', 'photo', 'Photo URL', 'photo_url', 'Image'])
                
                if not roll_number or not name:
                    errors.append(f"Row {index + 1}: Missing required fields (Roll Number or Name)")
                    continue
                
                # Check if student already exists
                existing_student = get_student_by_roll_number(db, roll_number)
                if existing_student:
                    print(f"Student already exists: {name} (Roll: {roll_number})")
                    duplicate_count += 1
                    continue
                
                photo_path = None
                
                # Handle photo URL if provided
                if photo_url and photo_url.startswith('http'):
                    try:
                        # Create photos directory if it doesn't exist
                        photos_dir = "static/photos"
                        os.makedirs(photos_dir, exist_ok=True)
                        
                        # Download photo
                        response = requests.get(photo_url, timeout=10)
                        if response.status_code == 200:
                            # Create filename from roll number
                            file_extension = photo_url.split('.')[-1].lower()
                            if file_extension not in ['jpg', 'jpeg', 'png', 'gif']:
                                file_extension = 'jpg'
                            
                            filename = f"{roll_number}.{file_extension}"
                            photo_path = os.path.join(photos_dir, filename)
                            
                            # Save and optimize photo
                            img = Image.open(BytesIO(response.content))
                            # Resize if too large
                            if img.width > 300 or img.height > 300:
                                img.thumbnail((300, 300), Image.LANCZOS)
                            img.save(photo_path, quality=85)
                            
                            # Store relative path
                            photo_path = f"photos/{filename}"
                            print(f"Downloaded photo for {name}: {photo_path}")
                            
                    except Exception as photo_error:
                        print(f"Photo download error for {name}: {str(photo_error)}")
                        errors.append(f"Row {index + 1} ({name}): Failed to download photo - {str(photo_error)}")
                        photo_path = None
                
                # Create student record
                student_data = StudentCreate(
                    roll_number=roll_number,
                    name=name,
                    class_name=class_name,
                    section=section,
                    branch=branch,  # Map Branch to branch (not stream)
                    photo_url=photo_url  # Store the original URL
                )
                
                # Only create student if teacher_id is provided (for teacher isolation)
                if teacher_id:
                    new_student = create_student(db, student_data, teacher_id)
                    imported_count += 1
                    print(f"Imported student: {name} (Roll: {roll_number}) for teacher {teacher_id}")
                else:
                    # Legacy support - create without teacher assignment (not recommended)
                    print(f"Warning: No teacher_id provided for student: {name} (Roll: {roll_number})")
                    continue
                
            except Exception as e:
                error_msg = f"Row {index + 1}: {str(e)}"
                errors.append(error_msg)
                print(f"Error importing row {index + 1}: {str(e)}")
        
        result = {
            "imported_count": imported_count,
            "duplicate_count": duplicate_count,
            "errors": errors,
            "total_rows": len(df)
        }
        
        print(f"Import completed: {imported_count}/{len(df)} students imported, {duplicate_count} duplicates skipped")
        return result
    
    except Exception as e:
        error_msg = f"File processing error: {str(e)}"
        print(error_msg)
        return {
            "imported_count": 0,
            "errors": [error_msg],
            "total_rows": 0
        }


# Class CRUD operations
def create_class(db: Session, class_data: ClassCreate):
    """Create a new class"""
    db_class = Class(
        class_name=class_data.class_name,
        section=class_data.section,
        stream=class_data.stream,
        subject=class_data.subject,
        teacher_id=class_data.teacher_id
    )
    db.add(db_class)
    db.commit()
    db.refresh(db_class)
    return db_class


def get_classes(db: Session, teacher_id: Optional[int] = None, skip: int = 0, limit: int = 100):
    """Get list of classes with optional teacher filtering"""
    query = db.query(Class).filter(Class.is_active == True)
    
    if teacher_id:
        query = query.filter(Class.teacher_id == teacher_id)
    
    return query.offset(skip).limit(limit).all()


def get_class_by_id(db: Session, class_id: int):
    """Get class by ID"""
    return db.query(Class).filter(Class.class_id == class_id).first()


def update_class(db: Session, class_id: int, class_update: ClassUpdate):
    """Update class information"""
    db_class = get_class_by_id(db, class_id)
    if db_class:
        update_data = class_update.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_class, key, value)
        db_class.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_class)
    return db_class


def add_student_to_class(db: Session, student_id: int, class_id: int):
    """Add student to a class"""
    # Check if relationship already exists
    existing = db.query(StudentClass).filter(
        and_(StudentClass.student_id == student_id, StudentClass.class_id == class_id)
    ).first()
    
    if not existing:
        student_class = StudentClass(student_id=student_id, class_id=class_id)
        db.add(student_class)
        db.commit()
        db.refresh(student_class)
        return student_class
    return existing


def remove_student_from_class(db: Session, student_id: int, class_id: int):
    """Remove student from a class"""
    student_class = db.query(StudentClass).filter(
        and_(StudentClass.student_id == student_id, StudentClass.class_id == class_id)
    ).first()
    
    if student_class:
        db.delete(student_class)
        db.commit()
        return True
    return False


# Attendance CRUD operations
def mark_attendance(db: Session, attendance: AttendanceCreate, teacher_id: int):
    """Mark attendance for a student"""
    # Check if attendance already exists for this date
    existing_attendance = db.query(Attendance).filter(
        and_(
            Attendance.student_id == attendance.student_id,
            Attendance.attendance_date == (attendance.attendance_date or date.today())
        )
    ).first()
    
    if existing_attendance:
        # Update existing attendance
        existing_attendance.status = attendance.status
        existing_attendance.teacher_id = teacher_id
        existing_attendance.attendance_type = attendance.attendance_type
        existing_attendance.confidence_score = attendance.confidence_score
        existing_attendance.notes = attendance.notes
        existing_attendance.marked_at = datetime.utcnow()
        db.commit()
        db.refresh(existing_attendance)
        return existing_attendance
    else:
        # Create new attendance record
        db_attendance = Attendance(
            student_id=attendance.student_id,
            teacher_id=teacher_id,
            status=attendance.status,
            attendance_type=attendance.attendance_type,
            confidence_score=attendance.confidence_score,
            attendance_date=attendance.attendance_date or date.today(),
            notes=attendance.notes
        )
        db.add(db_attendance)
        db.commit()
        db.refresh(db_attendance)
        return db_attendance


def bulk_mark_attendance(db: Session, bulk_attendance: AttendanceBulkCreate, teacher_id: int):
    """Mark attendance for multiple students"""
    results = []
    attendance_date = bulk_attendance.attendance_date or date.today()
    
    for student_status in bulk_attendance.student_statuses:
        attendance_data = AttendanceCreate(
            student_id=student_status['student_id'],
            status=student_status['status'],
            attendance_date=attendance_date
        )
        
        result = mark_attendance(db, attendance_data, teacher_id)
        results.append(result)
    
    return results


def get_attendance_records(
    db: Session,
    class_id: Optional[int] = None,
    student_id: Optional[int] = None,
    attendance_date: Optional[date] = None,
    skip: int = 0,
    limit: int = 100
):
    """Get attendance records with filtering"""
    query = db.query(Attendance)
    
    if class_id:
        query = query.filter(Attendance.class_id == class_id)
    if student_id:
        query = query.filter(Attendance.student_id == student_id)
    if attendance_date:
        query = query.filter(Attendance.attendance_date == attendance_date)
    
    return query.order_by(Attendance.marked_at.desc()).offset(skip).limit(limit).all()


# Analytics functions
def get_attendance_statistics(db: Session, class_id: Optional[int] = None, teacher_id: Optional[int] = None):
    """Get attendance statistics"""
    today = date.today()
    
    # Base query
    query = db.query(Attendance).filter(Attendance.attendance_date == today)
    
    if class_id:
        query = query.filter(Attendance.class_id == class_id)
    if teacher_id:
        query = query.filter(Attendance.teacher_id == teacher_id)
    
    total_attendance = query.count()
    present_count = query.filter(Attendance.status == 'Present').count()
    absent_count = query.filter(Attendance.status == 'Absent').count()
    
    attendance_percentage = (present_count / total_attendance * 100) if total_attendance > 0 else 0
    
    return {
        "total_students": total_attendance,
        "present_today": present_count,
        "absent_today": absent_count,
        "attendance_percentage": round(attendance_percentage, 2)
    }


def get_student_attendance_stats(db: Session, student_id: int):
    """Get detailed attendance statistics for a student"""
    attendance_records = db.query(Attendance).filter(Attendance.student_id == student_id).all()
    
    total_days = len(attendance_records)
    present_days = len([r for r in attendance_records if r.status == 'Present'])
    absent_days = total_days - present_days
    
    attendance_percentage = (present_days / total_days * 100) if total_days > 0 else 0
    
    return {
        "student_id": student_id,
        "total_days": total_days,
        "present_days": present_days,
        "absent_days": absent_days,
        "attendance_percentage": round(attendance_percentage, 2)
    }
