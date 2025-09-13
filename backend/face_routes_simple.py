"""
Facial recognition API routes using simple OpenCV-based recognition
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Form
from sqlalchemy.orm import Session
from typing import List
import shutil
import os
from pathlib import Path
import json
import base64

from backend.database import get_db
from backend.models import Student, Teacher
from backend.auth import get_current_teacher
from backend.face_recognition_simple import face_recognizer

face_router = APIRouter(prefix="/face", tags=["facial-recognition"])

@face_router.post("/upload-student-photo/{student_id}")
async def upload_student_photo(
    student_id: int,
    file: UploadFile = File(...),
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Upload and process student photo for facial recognition"""
    
    # Verify student exists
    student = db.query(Student).filter(Student.student_id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Validate file type
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Save uploaded file temporarily
    temp_dir = Path("temp")
    temp_dir.mkdir(exist_ok=True)
    temp_file_path = temp_dir / f"student_{student_id}_{file.filename}"
    
    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Try to extract face from image with better error handling
        try:
            success = face_recognizer.extract_face_from_image(str(temp_file_path))
            
            if not success:
                # If face detection fails, still save the image for manual processing
                faces_dir = Path("faces")
                faces_dir.mkdir(exist_ok=True)
                final_path = faces_dir / f"{student_id}_face.jpg"
                
                # Copy the original image
                shutil.copy2(temp_file_path, final_path)
                
                return {
                    "message": "Photo uploaded successfully (no face detected for recognition, but saved for manual processing)",
                    "student_id": student_id,
                    "student_name": student.name,
                    "face_detected": False
                }
            else:
                return {
                    "message": "Student photo uploaded and processed successfully",
                    "student_id": student_id,
                    "student_name": student.name,
                    "face_detected": True
                }
                
        except Exception as face_error:
            # If face processing fails, still save the original image
            faces_dir = Path("faces")
            faces_dir.mkdir(exist_ok=True)
            final_path = faces_dir / f"{student_id}_original.jpg"
            
            shutil.copy2(temp_file_path, final_path)
            
            return {
                "message": f"Photo uploaded but face processing failed: {str(face_error)}",
                "student_id": student_id,
                "student_name": student.name,
                "face_detected": False
            }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")
    
    finally:
        # Clean up temp file
        if temp_file_path.exists():
            os.unlink(temp_file_path)

@face_router.post("/recognize")
async def recognize_face(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Recognize student from uploaded image"""
    
    # Validate file type
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Save uploaded file temporarily
    temp_dir = Path("temp")
    temp_dir.mkdir(exist_ok=True)
    temp_file_path = temp_dir / f"recognize_{file.filename}"
    
    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Get all students with stored faces
        stored_faces = face_recognizer.get_all_stored_faces()
        
        if not stored_faces:
            raise HTTPException(status_code=404, detail="No student faces stored for recognition")
        
        best_match = None
        best_confidence = 0.0
        
        # Compare with all stored faces
        for face_id in stored_faces:
            try:
                student_id = int(face_id)
                confidence = face_recognizer.recognize_student(str(temp_file_path), face_id)
                
                if confidence > best_confidence and confidence > 0.5:  # Minimum confidence threshold
                    best_confidence = confidence
                    best_match = student_id
            except ValueError:
                continue
        
        if best_match:
            # Get student details
            student = db.query(Student).filter(Student.student_id == best_match).first()
            if student:
                return {
                    "recognized": True,
                    "student_id": best_match,
                    "student_name": student.name,
                    "roll_number": student.roll_number,
                    "confidence": float(best_confidence),
                    "class_info": f"{student.class_name} - {student.section}"
                }
        
        return {
            "recognized": False,
            "message": "No matching student found",
            "confidence": 0.0
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error recognizing face: {str(e)}")
    
    finally:
        # Clean up temp file
        if temp_file_path.exists():
            os.unlink(temp_file_path)

@face_router.post("/recognize-from-camera")
async def recognize_from_camera(
    image_data: str = Form(...),
    db: Session = Depends(get_db)
):
    """Recognize student from camera capture (base64 image data)"""
    try:
        # Decode base64 image
        image_data = image_data.split(',')[1] if ',' in image_data else image_data
        image_bytes = base64.b64decode(image_data)
        
        # Save temporarily
        temp_dir = Path("temp")
        temp_dir.mkdir(exist_ok=True)
        temp_file_path = temp_dir / "camera_capture.jpg"
        
        with open(temp_file_path, "wb") as f:
            f.write(image_bytes)
        
        # Get all students with stored faces
        stored_faces = face_recognizer.get_all_stored_faces()
        
        if not stored_faces:
            return {
                "recognized": False,
                "message": "No student faces stored for recognition",
                "confidence": 0.0
            }
        
        best_match = None
        best_confidence = 0.0
        
        # Compare with all stored faces
        for face_id in stored_faces:
            try:
                student_id = int(face_id)
                confidence = face_recognizer.recognize_student(str(temp_file_path), face_id)
                
                if confidence > best_confidence and confidence > 0.4:  # Lower threshold for camera
                    best_confidence = confidence
                    best_match = student_id
            except ValueError:
                continue
        
        if best_match:
            # Get student details
            student = db.query(Student).filter(Student.student_id == best_match).first()
            if student:
                return {
                    "recognized": True,
                    "student_id": best_match,
                    "student_name": student.name,
                    "roll_number": student.roll_number,
                    "confidence": float(best_confidence),
                    "class_info": f"{student.class_name} - {student.section}"
                }
        
        return {
            "recognized": False,
            "message": "No matching student found",
            "confidence": 0.0
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing camera image: {str(e)}")
    
    finally:
        # Clean up temp file
        if temp_file_path.exists():
            os.unlink(temp_file_path)

@face_router.get("/students-with-photos")
async def get_students_with_photos(db: Session = Depends(get_db)):
    """Get list of students who have photos stored"""
    
    students_with_photos = []
    
    # Get all students with photo_url or actual photo files
    students = db.query(Student).filter(Student.is_active == True).all()
    
    for student in students:
        has_photo = False
        
        # Check for face recognition processed photos
        face_path = Path("faces") / f"{student.student_id}_face.jpg"
        original_path = Path("faces") / f"{student.student_id}_original.jpg"
        
        # Check for downloaded photos
        downloaded_jpg = Path("static") / "photos" / f"{student.student_id}.jpg"
        downloaded_png = Path("static") / "photos" / f"{student.student_id}.png"
        
        # Check if student has any photo file or photo URL
        if (face_path.exists() or original_path.exists() or 
            downloaded_jpg.exists() or downloaded_png.exists() or
            (student.photo_url and student.photo_url.strip())):
            has_photo = True
        
        if has_photo:
            students_with_photos.append({
                "student_id": student.student_id,
                "name": student.name,
                "roll_number": student.roll_number,
                "class_info": f"{student.class_name or 'N/A'} - {student.section or 'N/A'}"
            })
    
    return students_with_photos

@face_router.get("/student-photo/{student_id}")
async def get_student_photo(
    student_id: int,
    db: Session = Depends(get_db)
):
    """Get student photo for display"""
    from fastapi.responses import FileResponse
    
    # Verify student exists
    student = db.query(Student).filter(Student.student_id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Priority order for photo locations:
    # 1. Face recognition processed photos
    # 2. Downloaded photos from CSV import
    # 3. Original uploaded photos
    
    face_path = Path("faces") / f"{student_id}_face.jpg"
    original_path = Path("faces") / f"{student_id}_original.jpg"
    downloaded_path = Path("static") / "photos" / f"{student_id}.jpg"
    downloaded_path_png = Path("static") / "photos" / f"{student_id}.png"
    
    # Check each location in priority order
    for photo_path in [face_path, downloaded_path, downloaded_path_png, original_path]:
        if photo_path.exists():
            return FileResponse(photo_path, media_type="image/jpeg")
    
    # If student has photo_url but no local file, return URL for frontend to handle
    if student.photo_url and student.photo_url.strip():
        # Check if it's a remote URL
        if student.photo_url.startswith('http'):
            # Return error - frontend should handle remote URLs differently
            raise HTTPException(status_code=404, detail="Remote photo URL - use direct URL access")
        else:
            # Local file path
            photo_path = Path(student.photo_url)
            if photo_path.exists():
                return FileResponse(photo_path, media_type="image/jpeg")
    
    raise HTTPException(status_code=404, detail="No photo found for this student")

@face_router.delete("/remove-student-photo/{student_id}")
async def remove_student_photo(
    student_id: int,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Remove student photo"""
    
    # Verify student exists
    student = db.query(Student).filter(Student.student_id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Remove face file
    face_path = Path("faces") / f"{student_id}_face.jpg"
    original_path = Path("faces") / f"{student_id}_original.jpg"
    
    removed = False
    if face_path.exists():
        face_path.unlink()
        removed = True
    if original_path.exists():
        original_path.unlink() 
        removed = True
        
    if removed:
        return {"message": "Student photo removed successfully"}
    else:
        raise HTTPException(status_code=404, detail="No photo found for this student")

@face_router.get("/system-status")
async def get_face_recognition_status():
    """Get facial recognition system status"""
    stored_faces = face_recognizer.get_all_stored_faces()
    students_count = len(stored_faces)
    
    return {
        "status": "active",
        "students_enrolled": students_count,
        "face_recognition_ready": students_count > 0,
        "system_type": "OpenCV Basic Recognition"
    }
