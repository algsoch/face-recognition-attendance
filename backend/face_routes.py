"""
Facial recognition API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import cv2
import numpy as np
import base64
import json
from io import BytesIO
from PIL import Image
import os
from pathlib import Path

from backend.database import get_db
from backend.models import Student
from backend.schemas import AttendanceCreate
from backend.crud import mark_attendance, get_student_by_id
from backend.face_recognition_module import (
    face_recognition_system, 
    detect_faces_in_frame, 
    draw_face_boxes
)

# Create router for facial recognition endpoints
face_router = APIRouter(prefix="/face", tags=["Facial Recognition"])


@face_router.post("/upload-student-photo/{student_id}")
async def upload_student_photo(
    student_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload and process student photo for facial recognition"""
    try:
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only image files are allowed"
            )
        
        # Check if student exists
        student = get_student_by_id(db, student_id)
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student not found"
            )
        
        # Create uploads directory if it doesn't exist
        upload_dir = Path("uploads/student_photos")
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Save uploaded file
        file_path = upload_dir / f"student_{student_id}_{file.filename}"
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Extract and save face encoding
        success = face_recognition_system.save_student_face_encoding(
            student_id, str(file_path), db
        )
        
        if success:
            # Update student photo URL
            student.photo_url = f"/uploads/student_photos/{file_path.name}"
            db.commit()
            
            return {
                "message": "Photo uploaded and face encoding saved successfully",
                "photo_url": student.photo_url
            }
        else:
            # Remove uploaded file if face encoding failed
            os.unlink(file_path)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No face detected in the image or face encoding failed"
            )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing photo: {str(e)}"
        )


@face_router.post("/recognize-attendance")
async def recognize_attendance_from_image(
    image_data: dict,  # {"image": "base64_string", "class_id": 1}
    db: Session = Depends(get_db)
):
    """Recognize student from uploaded image and mark attendance"""
    try:
        base64_image = image_data.get("image")
        class_id = image_data.get("class_id")
        
        if not base64_image or not class_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Image data and class_id are required"
            )
        
        # Extract face encoding from uploaded image
        face_encoding = face_recognition_system.encode_face_from_base64(base64_image)
        
        if face_encoding is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No face detected in the image"
            )
        
        # Load known faces and find best match
        face_recognition_system.load_student_faces(db)
        
        best_match = None
        best_confidence = 0.0
        
        for student_id, student_data in face_recognition_system.known_faces.items():
            is_match, confidence = face_recognition_system.compare_faces(
                student_data['encoding'], 
                face_encoding
            )
            
            if is_match and confidence > best_confidence:
                best_match = {
                    'student_id': student_id,
                    'name': student_data['name'],
                    'roll_number': student_data['roll_number'],
                    'confidence': confidence
                }
                best_confidence = confidence
        
        if best_match:
            # Mark attendance
            attendance_data = AttendanceCreate(
                student_id=best_match['student_id'],
                class_id=class_id,
                status="Present",
                attendance_type="Facial",
                confidence_score=best_match['confidence']
            )
            
            # Use system user for facial recognition attendance
            attendance_record = mark_attendance(db, attendance_data, teacher_id=1)  # System teacher
            
            return {
                "success": True,
                "student": best_match,
                "attendance_id": attendance_record.attendance_id,
                "message": f"Attendance marked for {best_match['name']} with {best_match['confidence']:.1f}% confidence"
            }
        else:
            return {
                "success": False,
                "message": "Student not recognized. Please try again or contact administrator."
            }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error during recognition: {str(e)}"
        )


@face_router.get("/webcam-stream")
async def webcam_stream():
    """Stream webcam feed for real-time face detection"""
    def generate_frames():
        cap = cv2.VideoCapture(0)  # Use default camera
        
        try:
            while True:
                success, frame = cap.read()
                if not success:
                    break
                
                # Detect faces in frame
                face_locations = detect_faces_in_frame(frame)
                
                # Draw bounding boxes around faces
                frame_with_boxes = draw_face_boxes(frame, face_locations)
                
                # Encode frame as JPEG
                ret, buffer = cv2.imencode('.jpg', frame_with_boxes)
                frame_bytes = buffer.tobytes()
                
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        
        except Exception as e:
            print(f"Error in webcam stream: {e}")
        finally:
            cap.release()
    
    return StreamingResponse(
        generate_frames(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )


@face_router.post("/capture-attendance")
async def capture_attendance_from_webcam(
    class_id: int,
    db: Session = Depends(get_db)
):
    """Capture image from webcam and mark attendance"""
    try:
        # Initialize webcam
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Cannot access webcam"
            )
        
        # Capture frame
        ret, frame = cap.read()
        cap.release()
        
        if not ret:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to capture image from webcam"
            )
        
        # Recognize student from frame
        recognized_student = face_recognition_system.recognize_student(frame, db)
        
        if recognized_student:
            # Mark attendance
            attendance_data = AttendanceCreate(
                student_id=recognized_student['student_id'],
                class_id=class_id,
                status="Present",
                attendance_type="Facial",
                confidence_score=recognized_student['confidence']
            )
            
            attendance_record = mark_attendance(db, attendance_data, teacher_id=1)
            
            return {
                "success": True,
                "student": recognized_student,
                "attendance_id": attendance_record.attendance_id,
                "message": f"Attendance marked for {recognized_student['name']}"
            }
        else:
            return {
                "success": False,
                "message": "No student recognized. Please ensure your face is clearly visible."
            }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error capturing attendance: {str(e)}"
        )


@face_router.get("/student/{student_id}/face-status")
async def check_student_face_status(
    student_id: int,
    db: Session = Depends(get_db)
):
    """Check if student has face encoding registered"""
    student = get_student_by_id(db, student_id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    
    has_face_encoding = student.face_encoding is not None
    
    return {
        "student_id": student_id,
        "name": student.name,
        "roll_number": student.roll_number,
        "has_face_encoding": has_face_encoding,
        "photo_url": student.photo_url
    }


@face_router.delete("/student/{student_id}/face-encoding")
async def delete_student_face_encoding(
    student_id: int,
    db: Session = Depends(get_db)
):
    """Delete student's face encoding"""
    student = get_student_by_id(db, student_id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    
    student.face_encoding = None
    db.commit()
    
    # Remove from memory cache
    if student_id in face_recognition_system.known_faces:
        del face_recognition_system.known_faces[student_id]
    
    return {"message": "Face encoding deleted successfully"}
