#!/usr/bin/env python3
"""
Professional Face Recognition Attendance API
High-performance attendance system with professional face recognition
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import cv2
import numpy as np
import sqlite3
import logging
from datetime import datetime, date
from typing import Optional, Dict, List
import io
from PIL import Image
import uvicorn

# Import professional face recognition
from professional_face_recognition import professional_face_recognizer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app with professional configuration
app = FastAPI(
    title="Professional Face Recognition Attendance System",
    description="High-performance attendance system with advanced face recognition",
    version="3.0.0"
)

# CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection helper
def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect('attendance.db')
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    """Create database tables if they don't exist"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS students (
                student_id TEXT PRIMARY KEY,
                roll_number TEXT UNIQUE,
                name TEXT NOT NULL,
                class_name TEXT,
                section TEXT,
                branch TEXT,
                photo_url TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS attendance (
                attendance_id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT NOT NULL,
                date DATE NOT NULL,
                time TIME NOT NULL,
                status TEXT NOT NULL,
                FOREIGN KEY (student_id) REFERENCES students (student_id)
            )
        ''')
        conn.commit()
        logger.info("Database tables created or verified successfully.")
    except Exception as e:
        logger.error(f"Error creating tables: {e}")
    finally:
        conn.close()

@app.on_event("startup")
async def startup_event():
    """Initialize system on startup"""
    logger.info("🚀 Starting Professional Face Recognition Attendance System")
    
    # Create tables if they don't exist
    create_tables()
    
    # Initialize face recognition for all students
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT student_id, photo_url FROM students WHERE is_active = 1')
        students = cursor.fetchall()
        
        initialization_results = {
            'total_students': len(students),
            'successful_extractions': 0,
            'failed_extractions': 0,
            'details': []
        }
        
        for student in students:
            student_id = student['student_id']
            photo_url = student['photo_url']
            
            logger.info(f"Initializing face recognition for student {student_id}")
            
            # Check if already processed
            if student_id in professional_face_recognizer.face_encodings:
                initialization_results['successful_extractions'] += 1
                initialization_results['details'].append({
                    'student_id': student_id,
                    'status': 'already_processed',
                    'encoding_length': len(professional_face_recognizer.face_encodings[student_id])
                })
                continue
            
            # Extract face encoding
            success = professional_face_recognizer.extract_and_save_face(photo_url, student_id)
            
            if success:
                initialization_results['successful_extractions'] += 1
                initialization_results['details'].append({
                    'student_id': student_id,
                    'status': 'success',
                    'encoding_length': len(professional_face_recognizer.face_encodings.get(student_id, []))
                })
            else:
                initialization_results['failed_extractions'] += 1
                initialization_results['details'].append({
                    'student_id': student_id,
                    'status': 'failed',
                    'reason': 'Could not extract face encoding'
                })
        
        logger.info(f"✅ Face recognition initialization complete: {initialization_results['successful_extractions']}/{initialization_results['total_students']} successful")
        
    except Exception as e:
        logger.error(f"Error during startup: {e}")
    finally:
        conn.close()

@app.get("/")
async def root():
    """Root endpoint with system status"""
    return {
        "message": "Professional Face Recognition Attendance System",
        "version": "3.0.0",
        "status": "operational",
        "face_recognition": "professional",
        "total_registered_faces": len(professional_face_recognizer.face_encodings),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/students")
async def get_all_students():
    """Get all students"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT student_id, roll_number, name, class_name, section, branch, 
                   photo_url, is_active, created_at, updated_at
            FROM students 
            ORDER BY name
        ''')
        students = [dict(row) for row in cursor.fetchall()]
        
        # Add face recognition status
        for student in students:
            student_id = student['student_id']
            student['has_face_encoding'] = student_id in professional_face_recognizer.face_encodings
            student['encoding_info'] = professional_face_recognizer.face_data.get(student_id, {})
        
        return {
            "success": True,
            "students": students,
            "total_count": len(students),
            "face_recognition_ready": len([s for s in students if s['has_face_encoding']])
        }
    except Exception as e:
        logger.error(f"Error getting students: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/students/{student_id}")
async def get_student(student_id: str):
    """Get specific student details"""
    student_details = professional_face_recognizer.get_student_details(student_id)
    
    if not student_details:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Add face recognition info
    student_details['has_face_encoding'] = student_id in professional_face_recognizer.face_encodings
    student_details['encoding_info'] = professional_face_recognizer.face_data.get(student_id, {})
    
    return {
        "success": True,
        "student": student_details
    }

@app.post("/recognize")
async def recognize_face(file: UploadFile = File(...)):
    """
    Professional face recognition endpoint
    Upload an image to identify the student
    """
    try:
        # Validate file
        if not file or not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read and process image
        image_data = await file.read()
        image = Image.open(io.BytesIO(image_data))
        
        # Convert to OpenCV format
        if image.mode != 'RGB':
            image = image.convert('RGB')
        cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        # Professional face recognition
        recognition_result = professional_face_recognizer.recognize_face_from_image(cv_image)
        
        response = {
            "timestamp": datetime.now().isoformat(),
            "filename": file.filename,
            "image_size": f"{cv_image.shape[1]}x{cv_image.shape[0]}",
            "recognition_system": "professional_face_recognition_v3",
            **recognition_result
        }
        
        # Log recognition attempt
        if recognition_result.get('match_found'):
            logger.info(f"✅ Face recognized: {recognition_result.get('student_id')} (confidence: {recognition_result.get('confidence', 0):.1f}%)")
        else:
            logger.warning(f"❌ Face not recognized: {recognition_result.get('reason', 'Unknown reason')}")
        
        return response
        
    except Exception as e:
        logger.error(f"Error during face recognition: {e}")
        raise HTTPException(status_code=500, detail=f"Recognition error: {str(e)}")

@app.post("/mark-attendance")
async def mark_attendance(file: UploadFile = File(...)):
    """
    Mark attendance with professional face recognition
    """
    try:
        # Recognize face first
        image_data = await file.read()
        image = Image.open(io.BytesIO(image_data))
        
        if image.mode != 'RGB':
            image = image.convert('RGB')
        cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        recognition_result = professional_face_recognizer.recognize_face_from_image(cv_image)
        
        if not recognition_result or not recognition_result.get('match_found'):
            return {
                "success": False,
                "message": "Face not recognized",
                "details": recognition_result,
                "timestamp": datetime.now().isoformat()
            }
        
        student_id = recognition_result.get('student_id')
        confidence = recognition_result.get('confidence', 0)
        
        if not student_id:
             return {
                "success": False,
                "message": "Recognized but no student ID found",
                "details": recognition_result,
                "timestamp": datetime.now().isoformat()
            }

        # Professional attendance marking (require high confidence)
        if confidence < 70:  # Higher threshold for attendance
            return {
                "success": False,
                "message": f"Confidence too low for attendance ({confidence:.1f}%). Minimum required: 70%",
                "recognition_details": recognition_result,
                "timestamp": datetime.now().isoformat()
            }
        
        # Mark attendance in database
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            today = date.today().isoformat()
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Check if already marked today
            cursor.execute('''
                SELECT attendance_id FROM attendance 
                WHERE student_id = ? AND date = ?
            ''', (student_id, today))
            
            existing = cursor.fetchone()
            
            if existing:
                return {
                    "success": False,
                    "message": "Attendance already marked for today",
                    "student_details": recognition_result.get('student_details'),
                    "recognition_details": recognition_result,
                    "timestamp": current_time
                }
            
            # Mark attendance
            cursor.execute('''
                INSERT INTO attendance (student_id, date, time, status)
                VALUES (?, ?, ?, ?)
            ''', (student_id, today, current_time, 'present'))
            
            conn.commit()
            attendance_id = cursor.lastrowid
            
            return {
                "success": True,
                "message": "Attendance marked successfully",
                "attendance_id": attendance_id,
                "student_details": recognition_result.get('student_details'),
                "recognition_details": recognition_result,
                "timestamp": current_time
            }
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
        finally:
            conn.close()
            
    except Exception as e:
        logger.error(f"Error marking attendance: {e}")
        raise HTTPException(status_code=500, detail=f"Attendance error: {str(e)}")

@app.get("/attendance/today")
async def get_today_attendance():
    """Get today's attendance records"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        today = date.today().isoformat()
        
        cursor.execute('''
            SELECT a.attendance_id, a.student_id, a.date, a.status, a.marked_at, 
                   a.confidence, a.recognition_method,
                   s.roll_number, s.name, s.class_name, s.section, s.branch
            FROM attendance a
            JOIN students s ON a.student_id = s.student_id
            WHERE a.date = ?
            ORDER BY a.marked_at DESC
        ''', (today,))
        
        records = [dict(row) for row in cursor.fetchall()]
        
        return {
            "success": True,
            "date": today,
            "attendance_records": records,
            "total_present": len(records)
        }
        
    except Exception as e:
        logger.error(f"Error getting attendance: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/system/status")
async def get_system_status():
    """Get comprehensive system status"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Count students
        cursor.execute('SELECT COUNT(*) as total FROM students')
        total_students = cursor.fetchone()['total']
        
        cursor.execute('SELECT COUNT(*) as active FROM students WHERE is_active = 1')
        active_students = cursor.fetchone()['active']
        
        # Count attendance today
        today = date.today().isoformat()
        cursor.execute('SELECT COUNT(*) as present FROM attendance WHERE date = ?', (today,))
        present_today = cursor.fetchone()['present']
        
        return {
            "system_status": "operational",
            "version": "3.0.0",
            "face_recognition": {
                "system": "professional_face_recognition",
                "registered_faces": len(professional_face_recognizer.face_encodings),
                "face_data_entries": len(professional_face_recognizer.face_data)
            },
            "database": {
                "total_students": total_students,
                "active_students": active_students,
                "present_today": present_today
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.post("/reinitialize-faces")
async def reinitialize_face_recognition():
    """Reinitialize face recognition for all students"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT student_id, photo_url FROM students WHERE is_active = 1')
        students = cursor.fetchall()
        conn.close()
        
        results = {
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'details': []
        }
        
        for student in students:
            student_id = student['student_id']
            photo_url = student['photo_url']
            
            success = professional_face_recognizer.extract_and_save_face(photo_url, student_id)
            results['total_processed'] += 1
            
            if success:
                results['successful'] += 1
                results['details'].append({
                    'student_id': student_id,
                    'status': 'success'
                })
            else:
                results['failed'] += 1
                results['details'].append({
                    'student_id': student_id,
                    'status': 'failed'
                })
        
        return {
            "success": True,
            "message": "Face recognition reinitialization complete",
            "results": results,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error reinitializing faces: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(
        "professional_attendance_api:app",
        host="0.0.0.0",
        port=8007,
        reload=True,
        log_level="info"
    )