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

@face_router.get("/students-with-photos")
async def get_students_with_photos(
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Get all students who have photos for the current teacher"""
    teacher_id = getattr(current_teacher, 'teacher_id')
    
    students = db.query(Student).filter(
        Student.teacher_id == teacher_id,
        Student.is_active == True,
        Student.photo_url.isnot(None),
        Student.photo_url != ""
    ).all()
    
    return {
        "students": [
            {
                "student_id": student.student_id,
                "name": student.name,
                "roll_number": student.roll_number,
                "class_name": student.class_name,
                "section": student.section,
                "photo_url": student.photo_url,
                "has_encoding": enhanced_face_recognizer.has_encoding(str(student.student_id))
            }
            for student in students
        ],
        "total_count": len(students)
    }

@face_router.post("/recognize-from-camera")
async def recognize_from_camera(
    file: UploadFile = File(...),
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Recognize face from camera/webcam image"""
    
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
                "success": False,
                "message": "No face recognition result",
                "confidence": 0.0
            }
        
        # Get student details if recognized
        student_details = None
        if recognition_result.get('student_id'):
            student = db.query(Student).filter(
                Student.student_id == int(recognition_result['student_id'])
            ).first()
            if student:
                student_details = {
                    "student_id": student.student_id,
                    "name": student.name,
                    "roll_number": student.roll_number,
                    "class_name": student.class_name,
                    "section": student.section
                }
        
        return {
            "success": True,
            "recognition_result": recognition_result,
            "student_details": student_details,
            "timestamp": date.today().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Recognition failed: {str(e)}")

@face_router.get("/test")
async def test_face_recognition_system(
    db: Session = Depends(get_db)
):
    """Test face recognition system status and basic functionality (no auth required)"""
    
    # Get overall system statistics
    total_students = db.query(Student).filter(Student.is_active == True).count()
    
    # Get students with photos count
    students_with_photos = db.query(Student).filter(
        Student.is_active == True,
        Student.photo_url.isnot(None),
        Student.photo_url != ""
    ).count()
    
    # Get face recognition statistics
    face_stats = enhanced_face_recognizer.get_statistics()
    
    # Test basic face recognition functionality
    system_status = {
        "face_recognizer_loaded": enhanced_face_recognizer is not None,
        "total_students": total_students,
        "students_with_photos": students_with_photos,
        "face_encodings_stored": face_stats.get('total_faces', 0),
        "recognition_ready": students_with_photos > 0,
        "authentication_required": False  # This endpoint doesn't require auth
    }
    
    return {
        "status": "ok",
        "message": "Face recognition system test completed",
        "system_status": system_status,
        "face_statistics": face_stats,
        "timestamp": date.today().isoformat()
    }

@face_router.get("/student-photo/{student_id}")
async def get_student_photo(
    student_id: int,
    db: Session = Depends(get_db)
):
    """Get student photo by student ID"""
    
    # Get student
    student = db.query(Student).filter(Student.student_id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    if not student.photo_url:
        raise HTTPException(status_code=404, detail="Student has no photo")
    
    # If it's a local file path, serve from static directory
    if not student.photo_url.startswith('http'):
        from fastapi.responses import FileResponse
        import os
        
        # Construct full path
        if student.photo_url.startswith('photos/'):
            file_path = os.path.join("static", student.photo_url)
        else:
            file_path = student.photo_url
            
        if os.path.exists(file_path):
            return FileResponse(file_path)
        else:
            raise HTTPException(status_code=404, detail="Photo file not found")
    
    # If it's a URL, redirect to it
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url=student.photo_url)