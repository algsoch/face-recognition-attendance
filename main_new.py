"""
New FastAPI main application with string-based IDs and proper teacher isolation
"""
from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.security import HTTPBearer
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, timedelta
import os
import shutil
from pathlib import Path
import pandas as pd
import tempfile

from backend.database_new import get_db, test_db_connection, engine
from backend.models_new import Base, Teacher
from backend.schemas_new import *
from backend.crud_new import *
from backend.auth import authenticate_teacher, create_access_token, get_current_teacher
from backend.csv_import import import_students_from_csv

# Create tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="Enhanced Attendance Management System",
    description="A comprehensive attendance management system with teacher isolation and string-based IDs",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Security
security = HTTPBearer()

# Create uploads directory if it doesn't exist
os.makedirs("uploads", exist_ok=True)

@app.on_event("startup")
async def startup_event():
    """Test database connection on startup"""
    if test_db_connection():
        print("✅ Database connection successful")
    else:
        print("❌ Database connection failed")


# Root endpoint - redirect to login
@app.get("/")
async def root():
    """Redirect to login page"""
    return RedirectResponse(url="/login")


# Authentication endpoints
@app.post("/teachers/register", response_model=TeacherResponse)
async def register_teacher(teacher: TeacherCreate, db: Session = Depends(get_db)):
    """Register a new teacher"""
    # Check if teacher already exists
    existing_teacher = get_teacher_by_email(db, teacher.email)
    if existing_teacher:
        raise HTTPException(
            status_code=400,
            detail="Teacher with this email already exists"
        )
    
    # Create new teacher
    db_teacher = create_teacher(db, teacher)
    return db_teacher


@app.post("/teachers/login", response_model=Token)
async def login_teacher(login_data: UserLogin, db: Session = Depends(get_db)):
    """Login teacher and return access token"""
    teacher = authenticate_teacher(db, login_data.email, login_data.password)
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": teacher.email})
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/teachers/me", response_model=TeacherResponse)
async def get_current_teacher_info(current_teacher: Teacher = Depends(get_current_teacher)):
    """Get current teacher information"""
    return current_teacher


# Student endpoints with teacher isolation
@app.get("/students", response_model=List[StudentResponse])
async def list_students(
    skip: int = 0,
    limit: int = 100,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Get list of students for current teacher only"""
    students = get_students_by_teacher(db, current_teacher.teacher_id, skip=skip, limit=limit)
    return students


@app.get("/students/{student_id}", response_model=StudentResponse)
async def get_student_details(
    student_id: str,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Get student details (only if student belongs to current teacher)"""
    # Verify student belongs to this teacher
    students = get_students_by_teacher(db, current_teacher.teacher_id)
    student = next((s for s in students if s.student_id == student_id), None)
    
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    return student


@app.post("/students", response_model=StudentResponse)
async def create_new_student(
    student: StudentCreate,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Create a new student for current teacher"""
    # Check if student with same roll number already exists for this teacher
    existing_student = get_student_by_roll_and_teacher(db, student.roll_number, current_teacher.teacher_id)
    if existing_student:
        raise HTTPException(
            status_code=400,
            detail=f"Student with roll number {student.roll_number} already exists"
        )
    
    db_student = create_student(db, student, current_teacher.teacher_id)
    return db_student


@app.post("/students/upload-csv")
async def upload_students_csv(
    file: UploadFile = File(...),
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Upload students from CSV file for current teacher"""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")
    
    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp_file:
        content = await file.read()
        tmp_file.write(content)
        tmp_file_path = tmp_file.name
    
    try:
        # Import students for this teacher
        result = import_students_from_csv(tmp_file_path, current_teacher.teacher_id)
        
        if result['success']:
            return {
                "message": result['message'],
                "imported_count": result['imported_count'],
                "duplicate_count": result['duplicate_count'],
                "error_count": result['error_count'],
                "errors": result.get('errors', [])
            }
        else:
            raise HTTPException(status_code=400, detail=result['error'])
    
    finally:
        # Clean up temporary file
        os.unlink(tmp_file_path)


# Class endpoints
@app.get("/classes", response_model=List[ClassResponse])
async def list_classes(
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Get classes for current teacher"""
    classes = get_classes_by_teacher(db, current_teacher.teacher_id)
    return classes


# Attendance endpoints with date-wise tracking
@app.post("/attendance/mark")
async def mark_student_attendance(
    attendance: AttendanceCreate,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Mark attendance for a student"""
    # Verify student belongs to this teacher
    students = get_students_by_teacher(db, current_teacher.teacher_id)
    student = next((s for s in students if s.student_id == attendance.student_id), None)
    
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    attendance_record = mark_attendance(
        db=db,
        student_id=attendance.student_id,
        teacher_id=current_teacher.teacher_id,
        attendance_date=attendance.attendance_date,
        status=attendance.status,
        notes=attendance.notes
    )
    
    if not attendance_record:
        raise HTTPException(status_code=400, detail="Failed to mark attendance")
    
    return {"message": "Attendance marked successfully", "record_id": attendance_record.record_id}


@app.get("/attendance/date/{attendance_date}")
async def get_attendance_by_date(
    attendance_date: date,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Get attendance records for a specific date"""
    records = get_attendance_by_date_and_teacher(db, current_teacher.teacher_id, attendance_date)
    return records


@app.get("/attendance/student/{student_id}")
async def get_student_attendance_history_endpoint(
    student_id: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Get attendance history for a student"""
    # Verify student belongs to this teacher
    students = get_students_by_teacher(db, current_teacher.teacher_id)
    student = next((s for s in students if s.student_id == student_id), None)
    
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    records = get_student_attendance_history(
        db, student_id, current_teacher.teacher_id, start_date, end_date
    )
    return records


# Photo endpoint with direct URL support
@app.get("/student-photo/{student_id}")
async def get_student_photo(
    student_id: str,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Get student photo (redirect to Google Drive direct URL)"""
    # Verify student belongs to this teacher
    students = get_students_by_teacher(db, current_teacher.teacher_id)
    student = next((s for s in students if s.student_id == student_id), None)
    
    if not student or not student.photo_url:
        raise HTTPException(status_code=404, detail="Student photo not found")
    
    # Redirect to Google Drive direct URL
    return RedirectResponse(url=student.photo_url)


# Static pages
@app.get("/login", response_class=HTMLResponse)
async def login_page():
    """Serve login page"""
    with open("frontend/login.html", "r") as f:
        return HTMLResponse(content=f.read())


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page():
    """Serve dashboard page"""
    with open("frontend/dashboard.html", "r") as f:
        return HTMLResponse(content=f.read())


@app.get("/register", response_class=HTMLResponse)
async def register_page():
    """Serve registration page"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Teacher Registration</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
        <div class="container mt-5">
            <div class="row justify-content-center">
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">
                            <h3 class="text-center">Teacher Registration</h3>
                        </div>
                        <div class="card-body">
                            <form id="registerForm">
                                <div class="mb-3">
                                    <label for="name" class="form-label">Full Name</label>
                                    <input type="text" class="form-control" id="name" required>
                                </div>
                                <div class="mb-3">
                                    <label for="email" class="form-label">Email</label>
                                    <input type="email" class="form-control" id="email" required>
                                </div>
                                <div class="mb-3">
                                    <label for="password" class="form-label">Password</label>
                                    <input type="password" class="form-control" id="password" required>
                                </div>
                                <div class="mb-3">
                                    <label for="department" class="form-label">Department</label>
                                    <input type="text" class="form-control" id="department">
                                </div>
                                <div class="mb-3">
                                    <label for="phone" class="form-label">Phone</label>
                                    <input type="tel" class="form-control" id="phone">
                                </div>
                                <button type="submit" class="btn btn-primary w-100">Register</button>
                            </form>
                            <div class="text-center mt-3">
                                <a href="/login">Already have an account? Login here</a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <script>
        document.getElementById('registerForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const formData = {
                name: document.getElementById('name').value,
                email: document.getElementById('email').value,
                password: document.getElementById('password').value,
                department: document.getElementById('department').value,
                phone: document.getElementById('phone').value
            };
            
            try {
                const response = await fetch('/teachers/register', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(formData)
                });
                
                if (response.ok) {
                    alert('Registration successful! Please login.');
                    window.location.href = '/login';
                } else {
                    const error = await response.json();
                    alert('Registration failed: ' + error.detail);
                }
            } catch (error) {
                alert('Registration failed: ' + error.message);
            }
        });
        </script>
    </body>
    </html>
    """


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
