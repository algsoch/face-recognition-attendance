"""
FastAPI main application with all routes and endpoints
"""
from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.security import HTTPBearer
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, timedelta
import os
import shutil
from pathlib import Path

from backend.database import get_db, test_db_connection, engine
from backend.models import Base
from backend.schemas import *
from backend.crud import *
from backend.auth import authenticate_teacher, create_access_token, get_current_teacher
# from backend.face_routes import face_router  # Commented out until dependencies are resolved
from backend.enhanced_face_routes import face_router
from backend.analytics import (
    generate_attendance_report, generate_daily_attendance_trends,
    generate_class_wise_summary, get_top_performers, 
    get_students_needing_attention, export_attendance_to_excel,
    get_monthly_attendance_summary
)
from decouple import config

# Create tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="Attendance Management System",
    description="A comprehensive attendance management system with facial recognition",
    version="1.0.0"
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Include facial recognition routes
# app.include_router(face_router)  # Commented out until dependencies are resolved
app.include_router(face_router)

# Security
security = HTTPBearer()

# Startup event
@app.on_event("startup")
async def startup_event():
    """Test database connection on startup"""
    if test_db_connection():
        print("✅ Database connection successful")
    else:
        print("❌ Database connection failed")


# Root endpoint
@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the advanced main dashboard"""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Attendance Management System</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
        <style>
            .hero-section {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 100px 0;
                min-height: 100vh;
                display: flex;
                align-items: center;
            }
            .feature-card {
                transition: transform 0.3s ease;
                border: none;
                box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            }
            .feature-card:hover {
                transform: translateY(-5px);
            }
            .navbar-brand {
                font-weight: bold;
                font-size: 1.5rem;
            }
            .btn-custom {
                padding: 12px 30px;
                font-weight: 600;
                border-radius: 50px;
                margin: 10px;
            }
            .stats-card {
                background: white;
                border-radius: 15px;
                padding: 30px;
                text-align: center;
                box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            }
            .footer {
                background-color: #2c3e50;
                color: white;
                padding: 40px 0;
            }
        </style>
    </head>
    <body>
        <!-- Navigation -->
        <nav class="navbar navbar-expand-lg navbar-dark fixed-top" style="background-color: rgba(0,0,0,0.9);">
            <div class="container">
                <a class="navbar-brand" href="/">
                    <i class="fas fa-graduation-cap me-2"></i>
                    Attendance Pro
                </a>
                <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                    <span class="navbar-toggler-icon"></span>
                </button>
                <div class="collapse navbar-collapse" id="navbarNav">
                    <ul class="navbar-nav ms-auto">
                        <li class="nav-item">
                            <a class="nav-link" href="#features">Features</a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link" href="#about">About</a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link btn btn-outline-light btn-sm ms-2" href="/login">Login</a>
                        </li>
                    </ul>
                </div>
            </div>
        </nav>

        <!-- Hero Section -->
        <section class="hero-section">
            <div class="container">
                <div class="row align-items-center">
                    <div class="col-lg-6">
                        <h1 class="display-4 fw-bold mb-4">
                            Smart Attendance Management System
                        </h1>
                        <p class="lead mb-4">
                            Revolutionary attendance tracking with AI-powered facial recognition, 
                            real-time analytics, and comprehensive reporting for modern educational institutions.
                        </p>
                        <div class="d-flex flex-wrap">
                            <a href="/login" class="btn btn-light btn-custom">
                                <i class="fas fa-user-graduate me-2"></i>Teacher Login
                            </a>
                            <a href="/dashboard" class="btn btn-outline-light btn-custom">
                                <i class="fas fa-chart-line me-2"></i>Dashboard
                            </a>
                            <a href="/docs" class="btn btn-outline-light btn-custom">
                                <i class="fas fa-code me-2"></i>API Docs
                            </a>
                        </div>
                    </div>
                    <div class="col-lg-6">
                        <div class="stats-card">
                            <h3 class="text-primary mb-3">System Status</h3>
                            <div class="row">
                                <div class="col-6">
                                    <h4 class="text-success"><i class="fas fa-check-circle"></i></h4>
                                    <p>API Active</p>
                                </div>
                                <div class="col-6">
                                    <h4 class="text-info"><i class="fas fa-camera"></i></h4>
                                    <p>Face Recognition</p>
                                </div>
                                <div class="col-6">
                                    <h4 class="text-warning"><i class="fas fa-chart-bar"></i></h4>
                                    <p>Analytics</p>
                                </div>
                                <div class="col-6">
                                    <h4 class="text-danger"><i class="fas fa-mobile-alt"></i></h4>
                                    <p>Mobile Ready</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </section>

        <!-- Features Section -->
        <section id="features" class="py-5">
            <div class="container">
                <div class="row">
                    <div class="col-12 text-center mb-5">
                        <h2 class="display-5 fw-bold">Powerful Features</h2>
                        <p class="text-muted">Everything you need for efficient attendance management</p>
                    </div>
                </div>
                <div class="row">
                    <div class="col-md-4 mb-4">
                        <div class="card feature-card h-100">
                            <div class="card-body text-center p-4">
                                <div class="mb-3">
                                    <i class="fas fa-camera fa-3x text-primary"></i>
                                </div>
                                <h5 class="card-title">AI Face Recognition</h5>
                                <p class="card-text">Advanced facial recognition technology for quick and accurate student identification.</p>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4 mb-4">
                        <div class="card feature-card h-100">
                            <div class="card-body text-center p-4">
                                <div class="mb-3">
                                    <i class="fas fa-chart-line fa-3x text-success"></i>
                                </div>
                                <h5 class="card-title">Real-time Analytics</h5>
                                <p class="card-text">Comprehensive attendance analytics with visual charts and performance insights.</p>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4 mb-4">
                        <div class="card feature-card h-100">
                            <div class="card-body text-center p-4">
                                <div class="mb-3">
                                    <i class="fas fa-users fa-3x text-info"></i>
                                </div>
                                <h5 class="card-title">Class Management</h5>
                                <p class="card-text">Efficient class-wise attendance tracking with bulk operations and filtering.</p>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4 mb-4">
                        <div class="card feature-card h-100">
                            <div class="card-body text-center p-4">
                                <div class="mb-3">
                                    <i class="fas fa-file-excel fa-3x text-warning"></i>
                                </div>
                                <h5 class="card-title">Excel Integration</h5>
                                <p class="card-text">Easy CSV import/export functionality for seamless data management.</p>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4 mb-4">
                        <div class="card feature-card h-100">
                            <div class="card-body text-center p-4">
                                <div class="mb-3">
                                    <i class="fas fa-mobile-alt fa-3x text-danger"></i>
                                </div>
                                <h5 class="card-title">Mobile Responsive</h5>
                                <p class="card-text">Fully responsive design that works perfectly on all devices.</p>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4 mb-4">
                        <div class="card feature-card h-100">
                            <div class="card-body text-center p-4">
                                <div class="mb-3">
                                    <i class="fas fa-lock fa-3x text-secondary"></i>
                                </div>
                                <h5 class="card-title">Secure Access</h5>
                                <p class="card-text">JWT-based authentication ensuring secure access to your data.</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </section>

        <!-- Quick Access Section -->
        <section class="py-5 bg-light">
            <div class="container">
                <div class="row">
                    <div class="col-12 text-center mb-4">
                        <h3>Quick Access</h3>
                        <p class="text-muted">Jump right into the system</p>
                    </div>
                </div>
                <div class="row justify-content-center">
                    <div class="col-md-3 col-sm-6 mb-3">
                        <a href="/login" class="btn btn-primary btn-lg w-100">
                            <i class="fas fa-sign-in-alt me-2"></i>Teacher Login
                        </a>
                    </div>
                    <div class="col-md-3 col-sm-6 mb-3">
                        <a href="/dashboard" class="btn btn-success btn-lg w-100">
                            <i class="fas fa-tachometer-alt me-2"></i>Dashboard
                        </a>
                    </div>
                    <div class="col-md-3 col-sm-6 mb-3">
                        <a href="/face-demo" class="btn btn-danger btn-lg w-100">
                            <i class="fas fa-camera me-2"></i>Face Recognition Demo
                        </a>
                    </div>
                    <div class="col-md-3 col-sm-6 mb-3">
                        <a href="/student-portal" class="btn btn-info btn-lg w-100">
                            <i class="fas fa-user-graduate me-2"></i>Student Portal
                        </a>
                    </div>
                </div>
                <div class="row justify-content-center mt-2">
                    <div class="col-md-3 col-sm-6 mb-3">
                        <a href="/docs" class="btn btn-warning btn-lg w-100">
                            <i class="fas fa-book me-2"></i>API Documentation
                        </a>
                    </div>
                </div>
            </div>
        </section>

        <!-- Footer -->
        <footer class="footer">
            <div class="container">
                <div class="row">
                    <div class="col-md-6">
                        <h5><i class="fas fa-graduation-cap me-2"></i>Attendance Pro</h5>
                        <p>Modern attendance management solution for educational institutions.</p>
                    </div>
                    <div class="col-md-6 text-md-end">
                        <p>&copy; 2025 Attendance Management System. All rights reserved.</p>
                        <p>Powered by FastAPI & AI Technology</p>
                    </div>
                </div>
            </div>
        </footer>

        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    """


@app.get("/login", response_class=HTMLResponse)
async def login_page():
    """Serve the login page"""
    with open("frontend/login_new.html", "r", encoding="utf-8") as f:
        return f.read()


@app.get("/register", response_class=HTMLResponse)
async def register_page():
    """Serve the registration page"""
    with open("frontend/register.html", "r", encoding="utf-8") as f:
        return f.read()


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page():
    """Serve the teacher dashboard"""
    with open("frontend/dashboard.html", "r") as f:
        return f.read()


@app.get("/dashboard/students")
async def get_dashboard_students(
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Get all students for the current teacher's dashboard"""
    teacher_id = getattr(current_teacher, 'teacher_id')
    
    students = db.query(Student).filter(
        Student.teacher_id == teacher_id,
        Student.is_active == True
    ).all()
    
    # Get recent attendance for each student
    student_data = []
    for student in students:
        recent_attendance = db.query(Attendance).filter(
            Attendance.student_id == student.student_id
        ).order_by(Attendance.date.desc()).limit(5).all()
        
        attendance_summary = {
            "present_days": len([a for a in recent_attendance if a.status == "Present"]),
            "total_days": len(recent_attendance),
            "attendance_percentage": round(
                (len([a for a in recent_attendance if a.status == "Present"]) / len(recent_attendance) * 100) 
                if recent_attendance else 0, 1
            )
        }
        
        student_data.append({
            "student_id": student.student_id,
            "name": student.name,
            "roll_number": student.roll_number,
            "class_name": student.class_name,
            "section": student.section,
            "photo_url": student.photo_url,
            "phone": student.phone,
            "is_active": student.is_active,
            "attendance_summary": attendance_summary
        })
    
    return {
        "students": student_data,
        "total_count": len(student_data),
        "teacher_id": teacher_id
    }


@app.get("/student-portal", response_class=HTMLResponse)
async def student_portal_page():
    """Serve the student portal"""
    with open("frontend/student-portal.html", "r") as f:
        return f.read()


# Authentication endpoints
@app.post("/auth/register", response_model=TeacherResponse)
async def register_teacher(teacher: TeacherCreate, db: Session = Depends(get_db)):
    """Register a new teacher"""
    # Check if teacher already exists
    existing_teacher = get_teacher_by_email(db, teacher.email)
    if existing_teacher:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Teacher with this email already exists"
        )
    
    db_teacher = create_teacher(db, teacher)
    return db_teacher


@app.post("/auth/login", response_model=Token)
async def login_teacher(user_credentials: UserLogin, db: Session = Depends(get_db)):
    """Login teacher and return JWT token"""
    teacher = authenticate_teacher(db, user_credentials.email, user_credentials.password)
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": teacher.email})
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/auth/me", response_model=TeacherResponse)
async def get_current_teacher_info(current_teacher: Teacher = Depends(get_current_teacher)):
    """Get current teacher information"""
    return current_teacher


# Teacher endpoints
@app.get("/teachers/profile", response_model=TeacherResponse)
async def get_teacher_profile(current_teacher: Teacher = Depends(get_current_teacher)):
    """Get teacher profile"""
    return current_teacher


@app.put("/teachers/profile", response_model=TeacherResponse)
async def update_teacher_profile(
    teacher_update: TeacherUpdate,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Update teacher profile"""
    teacher_id = getattr(current_teacher, 'teacher_id')
    updated_teacher = update_teacher(db, teacher_id, teacher_update)
    return updated_teacher


# Student endpoints
@app.post("/students", response_model=StudentResponse)
async def create_new_student(
    student: StudentCreate,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Create a new student"""
    teacher_id = getattr(current_teacher, 'teacher_id')
    
    # Check if student with roll number already exists for this teacher
    existing_student = get_student_by_roll_number(db, student.roll_number, teacher_id)
    if existing_student:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student with this roll number already exists for your class"
        )
    
    db_student = create_student(db, student, teacher_id)
    return db_student


@app.get("/students", response_model=List[StudentResponse])
async def list_students(
    skip: int = 0,
    limit: int = 100,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Get list of students for current teacher only"""
    # Get the actual teacher_id value
    teacher_id = getattr(current_teacher, 'teacher_id')
    students = get_students(db, skip=skip, limit=limit, teacher_id=teacher_id)
    return students


@app.get("/students/{student_id}", response_model=StudentResponse)
async def get_student_details(
    student_id: int,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Get student details by ID"""
    student = get_student_by_id(db, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student


@app.put("/students/{student_id}", response_model=StudentResponse)
async def update_student_details(
    student_id: int,
    student_update: StudentUpdate,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Update student details"""
    student = update_student(db, student_id, student_update)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student


@app.delete("/students/{student_id}")
async def delete_student_record(
    student_id: int,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Delete (deactivate) student"""
    student = delete_student(db, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return {"message": "Student deactivated successfully"}


@app.post("/students/upload", response_model=FileUploadResponse)
async def upload_students_file(
    file: UploadFile = File(...),
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Upload students from CSV/Excel file"""
    # Validate file type
    if not file.filename.endswith(('.csv', '.xlsx', '.xls')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only CSV and Excel files are supported"
        )
    
    # Save uploaded file
    upload_dir = Path(config('UPLOAD_DIR', default='uploads'))
    upload_dir.mkdir(exist_ok=True)
    file_path = upload_dir / file.filename
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Process file with teacher isolation
    teacher_id = getattr(current_teacher, 'teacher_id')
    result = bulk_import_students(db, str(file_path), teacher_id=teacher_id)
    
    # Clean up uploaded file
    os.unlink(file_path)
    
    return FileUploadResponse(
        filename=file.filename,
        message=f"Found {result['total_rows']} students, imported {result['imported_count']} new students, {result['duplicate_count']} duplicates skipped",
        records_processed=result['imported_count']
    )


@app.put("/students/{student_id}", response_model=StudentResponse)
async def update_student_endpoint(
    student_id: int,
    student_update: StudentUpdate,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Update student details"""
    student = get_student_by_id(db, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    updated_student = update_student(db, student_id, student_update)
    return updated_student


@app.delete("/students/{student_id}")
async def delete_student_endpoint(
    student_id: int,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Enhanced delete student with future-proof error handling"""
    try:
        # Check if student exists
        student = get_student_by_id(db, student_id)
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
        
        # Use enhanced delete function
        result = delete_student(db, student_id)
        
        if result.get("success"):
            return {
                "success": True,
                "message": result["message"],
                "student_id": student_id,
                "deleted_at": result.get("deleted_at"),
                "recovery_available": True
            }
        else:
            raise HTTPException(
                status_code=400, 
                detail=result.get("message", "Delete operation failed")
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Internal server error during delete: {str(e)}"
        )


@app.post("/students/{student_id}/recover")
async def recover_student_endpoint(
    student_id: int,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Recover a soft-deleted student"""
    from backend.crud import recover_student
    
    try:
        result = recover_student(db, student_id)
        
        if result.get("success"):
            return {
                "success": True,
                "message": result["message"],
                "student_id": student_id
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=result.get("message", "Recovery failed")
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error during recovery: {str(e)}"
        )


@app.post("/attendance/bulk-mark")
async def bulk_mark_attendance(
    attendance_data: dict,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Bulk mark attendance for multiple students"""
    date = attendance_data.get('date', datetime.now().date().isoformat())
    status = attendance_data.get('status', 'Present')
    student_ids = attendance_data.get('student_ids', [])
    class_id = attendance_data.get('class_id', 1)
    
    if not student_ids:
        raise HTTPException(status_code=400, detail="No students selected")
    
    results = []
    for student_id in student_ids:
        try:
            teacher_id = getattr(current_teacher, 'teacher_id')
            attendance = mark_attendance(db, AttendanceCreate(
                student_id=student_id,
                class_id=class_id,
                status=status,
                attendance_date=date
            ), teacher_id)
            results.append({"student_id": student_id, "status": "success"})
        except Exception as e:
            results.append({"student_id": student_id, "status": "error", "message": str(e)})
    
    return {
        "message": f"Bulk attendance marking completed",
        "total_students": len(student_ids),
        "successful": len([r for r in results if r["status"] == "success"]),
        "results": results
    }


# Class endpoints
@app.post("/classes", response_model=ClassResponse)
async def create_new_class(
    class_data: ClassCreate,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Create a new class"""
    db_class = create_class(db, class_data)
    return db_class


@app.get("/classes", response_model=List[ClassResponse])
async def list_classes(
    skip: int = 0,
    limit: int = 100,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Get list of classes for current teacher"""
    teacher_id = getattr(current_teacher, 'teacher_id')
    classes = get_classes(db, teacher_id=teacher_id, skip=skip, limit=limit)
    return classes


@app.get("/classes/{class_id}", response_model=ClassResponse)
async def get_class_details(
    class_id: int,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Get class details by ID"""
    class_obj = get_class_by_id(db, class_id)
    if not class_obj:
        raise HTTPException(status_code=404, detail="Class not found")
    return class_obj


@app.post("/classes/{class_id}/students/{student_id}")
async def add_student_to_class_endpoint(
    class_id: int,
    student_id: int,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Add student to a class"""
    # Verify class belongs to teacher
    class_obj = get_class_by_id(db, class_id)
    teacher_id = getattr(current_teacher, 'teacher_id')
    if not class_obj or class_obj.teacher_id != teacher_id:
        raise HTTPException(status_code=404, detail="Class not found or access denied")
    
    # Verify student exists
    student = get_student_by_id(db, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    student_class = add_student_to_class(db, student_id, class_id)
    return {"message": "Student added to class successfully"}


# Attendance endpoints
@app.post("/attendance", response_model=AttendanceResponse)
async def mark_student_attendance(
    attendance: AttendanceCreate,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Mark attendance for a student"""
    teacher_id = getattr(current_teacher, 'teacher_id')
    db_attendance = mark_attendance(db, attendance, teacher_id)
    return db_attendance


@app.post("/attendance/bulk")
async def mark_bulk_attendance(
    bulk_attendance: AttendanceBulkCreate,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Mark attendance for multiple students"""
    teacher_id = getattr(current_teacher, 'teacher_id')
    results = bulk_mark_attendance(db, bulk_attendance, teacher_id)
    return {
        "message": f"Attendance marked for {len(results)} students",
        "records": len(results)
    }


@app.get("/attendance", response_model=List[AttendanceResponse])
async def get_attendance_records_endpoint(
    class_id: Optional[int] = None,
    student_id: Optional[int] = None,
    attendance_date: Optional[date] = None,
    skip: int = 0,
    limit: int = 100,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Get attendance records with filtering"""
    attendance_records = get_attendance_records(
        db, class_id=class_id, student_id=student_id, 
        attendance_date=attendance_date, skip=skip, limit=limit
    )
    return attendance_records


# Additional attendance endpoints for frontend compatibility
@app.get("/attendance/statistics")
async def get_attendance_statistics_endpoint(
    class_id: Optional[int] = None,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Get attendance statistics (frontend compatible endpoint)"""
    teacher_id = getattr(current_teacher, 'teacher_id')
    stats = get_attendance_statistics(db, class_id=class_id, teacher_id=teacher_id)
    return stats


@app.post("/attendance/mark")
async def mark_attendance_endpoint(
    attendance: AttendanceCreate,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Mark attendance (frontend compatible endpoint)"""
    teacher_id = getattr(current_teacher, 'teacher_id')
    db_attendance = mark_attendance(db, attendance, teacher_id)
    return db_attendance


@app.get("/attendance/date/{attendance_date}")
async def get_attendance_by_date(
    attendance_date: date,
    class_id: Optional[int] = None,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Get attendance records for a specific date"""
    attendance_records = get_attendance_records(
        db, class_id=class_id, attendance_date=attendance_date
    )
    return attendance_records


# Analytics endpoints
@app.get("/analytics/daily-trends")
async def get_daily_trends_endpoint(
    class_id: Optional[int] = None,
    days: int = 30,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Get daily attendance trends (frontend compatible endpoint)"""
    trends = generate_daily_attendance_trends(db, class_id, days)
    return trends


@app.get("/analytics/students-needing-attention")
async def get_students_needing_attention_endpoint(
    threshold: float = 75.0,
    class_id: Optional[int] = None,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Get students needing attention (frontend compatible endpoint)"""
    students = get_students_needing_attention(db, threshold, class_id)
    return students


@app.get("/analytics/attendance-stats", response_model=AttendanceStats)
async def get_attendance_stats(
    class_id: Optional[int] = None,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Get attendance statistics"""
    teacher_id = getattr(current_teacher, 'teacher_id')
    stats = get_attendance_statistics(db, class_id=class_id, teacher_id=teacher_id)
    return AttendanceStats(**stats)


@app.get("/analytics/student/{student_id}/stats", response_model=StudentAttendanceStats)
async def get_student_stats(
    student_id: int,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Get detailed attendance statistics for a student"""
    student = get_student_by_id(db, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    stats = get_student_attendance_stats(db, student_id)
    stats['student_name'] = student.name
    stats['roll_number'] = student.roll_number
    
    return StudentAttendanceStats(**stats)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    db_status = test_db_connection()
    return {
        "status": "healthy" if db_status else "unhealthy",
        "database": "connected" if db_status else "disconnected",
        "timestamp": datetime.utcnow().isoformat()
    }


# Analytics and Reporting Endpoints
@app.get("/analytics/report")
async def get_attendance_report(
    class_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Generate comprehensive attendance report"""
    report = generate_attendance_report(db, class_id, start_date, end_date)
    return report


@app.get("/analytics/trends")
async def get_attendance_trends(
    class_id: Optional[int] = None,
    days: int = 30,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Get daily attendance trends for visualization"""
    trends = generate_daily_attendance_trends(db, class_id, days)
    return trends


@app.get("/analytics/class-summary")
async def get_class_summary(
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Get class-wise attendance summary"""
    teacher_id = getattr(current_teacher, 'teacher_id')
    summary = generate_class_wise_summary(db, teacher_id)
    return summary


@app.get("/analytics/top-performers")
async def get_top_performing_students(
    limit: int = 10,
    class_id: Optional[int] = None,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Get top performing students by attendance"""
    performers = get_top_performers(db, limit, class_id)
    return {"top_performers": performers}


@app.get("/analytics/attention-needed")
async def get_students_attention_needed(
    threshold: float = 75.0,
    class_id: Optional[int] = None,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Get students with low attendance needing attention"""
    students = get_students_needing_attention(db, threshold, class_id)
    return {"students_needing_attention": students}


@app.get("/analytics/export/excel")
async def export_attendance_excel(
    class_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Export attendance data to Excel file"""
    excel_buffer = export_attendance_to_excel(db, class_id, start_date, end_date)
    
    filename = f"attendance_report_{date.today().isoformat()}.xlsx"
    
    return FileResponse(
        path=excel_buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=filename
    )


@app.get("/analytics/monthly/{year}/{month}")
async def get_monthly_summary(
    year: int,
    month: int,
    class_id: Optional[int] = None,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Get monthly attendance summary"""
    summary = get_monthly_attendance_summary(db, year, month, class_id)
    return summary


@app.get("/face-demo", response_class=HTMLResponse)
async def face_recognition_demo():
    """Face recognition demo page"""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Face Recognition Demo - Attendance System</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css" rel="stylesheet">
        <style>
            body { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; }
            .demo-container { max-width: 800px; margin: 50px auto; }
            .demo-card { background: rgba(255, 255, 255, 0.95); border-radius: 15px; box-shadow: 0 15px 35px rgba(0,0,0,0.1); }
            .upload-area { border: 3px dashed #dee2e6; border-radius: 10px; padding: 40px; text-align: center; transition: all 0.3s ease; }
            .upload-area:hover { border-color: #007bff; background: rgba(0,123,255,0.05); }
            .upload-area.dragover { border-color: #28a745; background: rgba(40,167,69,0.1); }
            .result-card { margin-top: 20px; }
            .confidence-bar { height: 10px; border-radius: 5px; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="demo-container">
                <div class="card demo-card">
                    <div class="card-header bg-primary text-white text-center">
                        <h2><i class="fas fa-camera me-2"></i>Face Recognition Demo</h2>
                        <p class="mb-0">Upload your photo to test face recognition against the student database</p>
                    </div>
                    <div class="card-body p-4">
                        <!-- Upload Area -->
                        <div class="upload-area" id="uploadArea">
                            <div class="upload-content">
                                <i class="fas fa-cloud-upload-alt fa-3x text-muted mb-3"></i>
                                <h5>Drop an image here or click to select</h5>
                                <p class="text-muted">Supports JPG, PNG, GIF formats</p>
                                <input type="file" id="fileInput" accept="image/*" style="display: none;">
                                <button class="btn btn-primary mt-2" onclick="document.getElementById('fileInput').click()">
                                    <i class="fas fa-file-image me-2"></i>Choose Photo
                                </button>
                            </div>
                        </div>

                        <!-- Options -->
                        <div class="row mt-4">
                            <div class="col-md-6">
                                <div class="form-check">
                                    <input class="form-check-input" type="checkbox" id="autoAttendance" checked>
                                    <label class="form-check-label" for="autoAttendance">
                                        <i class="fas fa-check-circle me-1"></i>Automatically mark attendance
                                    </label>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <button class="btn btn-success w-100" id="recognizeBtn" disabled>
                                    <i class="fas fa-search me-2"></i>Recognize Face
                                </button>
                            </div>
                        </div>

                        <!-- Results Area -->
                        <div id="resultsArea" style="display: none;">
                            <hr>
                            <div class="result-card">
                                <div id="resultContent"></div>
                            </div>
                        </div>

                        <!-- Student Database Info -->
                        <div class="mt-4">
                            <h5><i class="fas fa-database me-2"></i>Database Status</h5>
                            <div id="dbStatus" class="alert alert-info">
                                <i class="fas fa-spinner fa-spin me-2"></i>Loading database statistics...
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
        <script>
            let selectedFile = null;
            let authToken = localStorage.getItem('token');

            // Check if logged in
            if (!authToken) {
                document.getElementById('dbStatus').innerHTML = '<i class="fas fa-exclamation-triangle me-2"></i>Please <a href="/login">login</a> to use face recognition.';
                document.getElementById('recognizeBtn').disabled = true;
            } else {
                loadDatabaseStatus();
            }

            // File input handler
            document.getElementById('fileInput').addEventListener('change', function(e) {
                handleFileSelect(e.target.files[0]);
            });

            // Drag and drop handlers
            const uploadArea = document.getElementById('uploadArea');
            uploadArea.addEventListener('dragover', function(e) {
                e.preventDefault();
                uploadArea.classList.add('dragover');
            });
            uploadArea.addEventListener('dragleave', function(e) {
                e.preventDefault();
                uploadArea.classList.remove('dragover');
            });
            uploadArea.addEventListener('drop', function(e) {
                e.preventDefault();
                uploadArea.classList.remove('dragover');
                handleFileSelect(e.dataTransfer.files[0]);
            });

            function handleFileSelect(file) {
                if (file && file.type.startsWith('image/')) {
                    selectedFile = file;
                    const reader = new FileReader();
                    reader.onload = function(e) {
                        uploadArea.innerHTML = `
                            <img src="${e.target.result}" style="max-width: 300px; max-height: 200px; border-radius: 10px;">
                            <p class="mt-2"><strong>${file.name}</strong></p>
                            <button class="btn btn-outline-secondary" onclick="resetUpload()">Choose Different Photo</button>
                        `;
                    };
                    reader.readAsDataURL(file);
                    document.getElementById('recognizeBtn').disabled = false;
                }
            }

            function resetUpload() {
                selectedFile = null;
                location.reload();
            }

            async function loadDatabaseStatus() {
                try {
                    const response = await fetch('/face/statistics', {
                        headers: { 'Authorization': 'Bearer ' + authToken }
                    });
                    if (response.ok) {
                        const stats = await response.json();
                        document.getElementById('dbStatus').innerHTML = `
                            <i class="fas fa-check-circle me-2 text-success"></i>
                            <strong>${stats.total_students}</strong> students registered, 
                            <strong>${stats.valid_face_files}</strong> face templates ready
                        `;
                    } else {
                        throw new Error('Failed to load statistics');
                    }
                } catch (error) {
                    document.getElementById('dbStatus').innerHTML = '<i class="fas fa-exclamation-triangle me-2"></i>Error loading database status';
                }
            }

            document.getElementById('recognizeBtn').addEventListener('click', async function() {
                if (!selectedFile || !authToken) return;

                const btn = this;
                const originalText = btn.innerHTML;
                btn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Processing...';
                btn.disabled = true;

                try {
                    const formData = new FormData();
                    formData.append('file', selectedFile);
                    formData.append('auto_mark_attendance', document.getElementById('autoAttendance').checked);

                    const response = await fetch('/face/recognize', {
                        method: 'POST',
                        headers: { 'Authorization': 'Bearer ' + authToken },
                        body: formData
                    });

                    const result = await response.json();
                    displayResult(result);

                } catch (error) {
                    displayError('Error during face recognition: ' + error.message);
                } finally {
                    btn.innerHTML = originalText;
                    btn.disabled = false;
                }
            });

            function displayResult(result) {
                const resultsArea = document.getElementById('resultsArea');
                const resultContent = document.getElementById('resultContent');
                
                if (result.recognized) {
                    resultContent.innerHTML = `
                        <div class="alert alert-success">
                            <h5><i class="fas fa-user-check me-2"></i>Student Recognized!</h5>
                            <div class="row">
                                <div class="col-md-6">
                                    <p><strong>Name:</strong> ${result.student_name}</p>
                                    <p><strong>Roll Number:</strong> ${result.roll_number}</p>
                                    <p><strong>Class:</strong> ${result.class_name}</p>
                                    <p><strong>Branch:</strong> ${result.branch}</p>
                                </div>
                                <div class="col-md-6">
                                    <p><strong>Confidence:</strong></p>
                                    <div class="progress mb-2">
                                        <div class="progress-bar bg-success" style="width: ${result.confidence}%">${result.confidence.toFixed(1)}%</div>
                                    </div>
                                    ${result.attendance_marked ? 
                                        '<span class="badge bg-success"><i class="fas fa-check me-1"></i>Attendance Marked</span>' : 
                                        (result.attendance_message ? '<span class="badge bg-warning">' + result.attendance_message + '</span>' : '')
                                    }
                                </div>
                            </div>
                        </div>
                    `;
                } else {
                    resultContent.innerHTML = `
                        <div class="alert alert-warning">
                            <h5><i class="fas fa-user-times me-2"></i>No Match Found</h5>
                            <p>${result.message}</p>
                            <p><small>Confidence was ${result.confidence.toFixed(1)}% - minimum required is usually 30%</small></p>
                        </div>
                    `;
                }
                
                resultsArea.style.display = 'block';
            }

            function displayError(message) {
                const resultsArea = document.getElementById('resultsArea');
                const resultContent = document.getElementById('resultContent');
                
                resultContent.innerHTML = `
                    <div class="alert alert-danger">
                        <h5><i class="fas fa-exclamation-triangle me-2"></i>Error</h5>
                        <p>${message}</p>
                    </div>
                `;
                
                resultsArea.style.display = 'block';
            }
        </script>
    </body>
    </html>
    """


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
