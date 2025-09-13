"""
Enhanced face recognition API routes
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Form
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
import shutil
import cv2
import numpy as np
from pathlib import Path
from PIL import Image
import io

from backend.database import get_db
from backend.models import Student, Teacher, Attendance
from backend.auth import get_current_teacher
from backend.robust_face_recognition import enhanced_face_recognizer
from backend.crud import mark_attendance
from backend.schemas import AttendanceCreate
from datetime import date

face_router = APIRouter(prefix="/face", tags=["face-recognition"])

@face_router.post("/recognize")
async def recognize_face(
    file: UploadFile = File(...),
    auto_mark_attendance: bool = Form(False),
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Recognize a face from uploaded image and optionally mark attendance"""
    
    # Validate file type
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    try:
        # Read uploaded image
        contents = await file.read()
        
        # Convert to OpenCV format
        image = Image.open(io.BytesIO(contents))
        if image.mode != 'RGB':
            image = image.convert('RGB')
        opencv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        # Recognize face
        recognition_result = enhanced_face_recognizer.recognize_face_from_image(opencv_image)
        
        if not recognition_result:
            return {
                "recognized": False,
                "message": "No face recognized or confidence too low",
                "confidence": 0
            }
        
        student_id = int(recognition_result['student_id'])
        confidence = recognition_result['confidence']
        
        # Get student details
        student = db.query(Student).filter(Student.student_id == student_id).first()
        if not student:
            return {
                "recognized": False,
                "message": "Recognized student not found in database",
                "confidence": confidence
            }
        
        result = {
            "recognized": True,
            "student_id": student_id,
            "student_name": student.name,
            "roll_number": student.roll_number,
            "class_name": student.class_name,
            "branch": student.branch,
            "confidence": confidence,
            "attendance_marked": False
        }
        
        # Mark attendance if requested
        if auto_mark_attendance:
            try:
                # Check if attendance already exists for today
                today = date.today()
                existing_attendance = db.query(Attendance).filter(
                    Attendance.student_id == student_id,
                    Attendance.attendance_date == today
                ).first()
                
                if existing_attendance:
                    result["attendance_marked"] = False
                    result["attendance_message"] = "Attendance already marked for today"
                else:
                    # Mark attendance
                    attendance_data = AttendanceCreate(
                        student_id=student_id,
                        attendance_date=today,
                        status="Present"
                    )
                    
                    marked_attendance = mark_attendance(db, attendance_data)
                    if marked_attendance:
                        result["attendance_marked"] = True
                        result["attendance_message"] = "Attendance marked successfully"
                    else:
                        result["attendance_marked"] = False
                        result["attendance_message"] = "Failed to mark attendance"
                        
            except Exception as e:
                result["attendance_marked"] = False
                result["attendance_message"] = f"Error marking attendance: {str(e)}"
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")

@face_router.get("/statistics")
async def get_face_recognition_statistics(
    current_teacher: Teacher = Depends(get_current_teacher)
):
    """Get face recognition system statistics"""
    stats = enhanced_face_recognizer.get_statistics()
    return stats

@face_router.post("/rebuild-database")
async def rebuild_face_database(
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Rebuild face recognition database from current students"""
    
    # Get all students for current teacher
    students = db.query(Student).filter(Student.teacher_id == current_teacher.teacher_id).all()
    
    students_data = []
    for student in students:
        students_data.append({
            'student_id': student.student_id,
            'name': student.name,
            'photo_url': student.photo_url
        })
    
    # Process all students
    results = enhanced_face_recognizer.process_all_students_from_db(students_data)
    
    return {
        "message": "Face database rebuild completed",
        "results": results,
        "statistics": enhanced_face_recognizer.get_statistics()
    }

@face_router.get("/test-student-photo/{student_id}")
async def test_student_photo(
    student_id: int,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Test face recognition with a student's own photo"""
    
    # Get student
    student = db.query(Student).filter(Student.student_id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    if not student.photo_url:
        raise HTTPException(status_code=400, detail="Student has no photo URL")
    
    # Test recognition with student's own photo
    recognition_result = enhanced_face_recognizer.recognize_face_from_url(student.photo_url)
    
    return {
        "student_id": student_id,
        "student_name": student.name,
        "photo_url": student.photo_url,
        "recognition_result": recognition_result,
        "self_recognition": recognition_result and int(recognition_result['student_id']) == student_id
    }