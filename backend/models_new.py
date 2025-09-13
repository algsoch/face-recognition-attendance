"""
New database models with string IDs and proper teacher isolation
Designed for real attendance registry system
"""
from sqlalchemy import Column, String, Text, Boolean, DateTime, Date, Time, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime, date

Base = declarative_base()


class Teacher(Base):
    """Teacher model with string-based ID"""
    __tablename__ = "teachers"
    
    teacher_id = Column(String(50), primary_key=True)  # String ID like "TCH001", "vicky_mech"
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    department = Column(String(100))
    phone = Column(String(20))
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    classes = relationship("Class", back_populates="teacher")


class Class(Base):
    """Class model with string-based ID and teacher isolation"""
    __tablename__ = "classes"
    
    class_id = Column(String(50), primary_key=True)  # String ID like "MECH_3_A", "CS_3_B"
    class_name = Column(String(100), nullable=False)  # "Mechanical", "Computer Science"
    section = Column(String(10), nullable=False)     # "3", "A", "B"
    branch = Column(String(100))                     # "Mechanical", "Computer Science"
    teacher_id = Column(String(50), ForeignKey("teachers.teacher_id"), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    teacher = relationship("Teacher", back_populates="classes")
    students = relationship("Student", back_populates="class_ref")


class Student(Base):
    """Student model with string-based ID and teacher isolation"""
    __tablename__ = "students"
    
    student_id = Column(String(50), primary_key=True)  # String ID like "STU_4001", "MECH_4001"
    roll_number = Column(String(20), nullable=False)
    name = Column(String(100), nullable=False)
    class_id = Column(String(50), ForeignKey("classes.class_id"), nullable=False)
    
    # Individual fields from CSV
    class_name = Column(String(100), nullable=False)  # Direct from CSV 'Class' column
    section = Column(String(20), nullable=False)      # Direct from CSV 'Section' column  
    branch = Column(String(100))                      # Direct from CSV 'Branch' column
    
    # Contact info
    email = Column(String(150))
    phone = Column(String(20))
    
    # Photo and recognition
    photo_url = Column(Text)  # Direct Google Drive URLs
    face_encoding = Column(Text)  # JSON encoded face recognition data
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)
    
    # Relationships
    class_ref = relationship("Class", back_populates="students")
    attendance_records = relationship("AttendanceRecord", back_populates="student")


class AttendanceRecord(Base):
    """Date-wise attendance records like real registry"""
    __tablename__ = "attendance_records"
    
    record_id = Column(String(100), primary_key=True)  # "MECH_2025-09-13_STU_4001"
    student_id = Column(String(50), ForeignKey("students.student_id"), nullable=False)
    class_id = Column(String(50), ForeignKey("classes.class_id"), nullable=False)
    teacher_id = Column(String(50), ForeignKey("teachers.teacher_id"), nullable=False)
    
    # Date and time tracking
    attendance_date = Column(Date, nullable=False, default=date.today)
    check_in_time = Column(Time, nullable=True)
    check_out_time = Column(Time, nullable=True)
    
    # Attendance status
    status = Column(String(20), default="present")  # present, absent, late, excused
    
    # Additional info
    notes = Column(Text)  # Teacher notes
    marked_by_method = Column(String(50), default="manual")  # manual, face_recognition, qr_code
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    student = relationship("Student", back_populates="attendance_records")
    teacher = relationship("Teacher")
    class_ref = relationship("Class")


class AttendanceSession(Base):
    """Daily attendance sessions for each class"""
    __tablename__ = "attendance_sessions"
    
    session_id = Column(String(100), primary_key=True)  # "MECH_3_2025-09-13_MORNING"
    class_id = Column(String(50), ForeignKey("classes.class_id"), nullable=False)
    teacher_id = Column(String(50), ForeignKey("teachers.teacher_id"), nullable=False)
    
    # Session details
    session_date = Column(Date, nullable=False, default=date.today)
    session_time = Column(String(20), default="MORNING")  # MORNING, AFTERNOON, EVENING
    subject = Column(String(100))  # Subject being taught
    
    # Session status
    is_active = Column(Boolean, default=True)
    is_completed = Column(Boolean, default=False)
    
    # Timestamps
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    teacher = relationship("Teacher")
    class_ref = relationship("Class")
