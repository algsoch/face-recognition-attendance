"""
SQLAlchemy ORM Models for Attendance Management System
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Date, Numeric, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.database import Base


class Teacher(Base):
    __tablename__ = "teachers"
    
    teacher_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False, index=True)
    password_hash = Column(Text, nullable=False)
    department = Column(String(100))
    phone = Column(String(20))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    students = relationship("Student", back_populates="teacher")
    classes = relationship("Class", back_populates="teacher")
    attendance_records = relationship("Attendance", back_populates="teacher")


class Student(Base):
    __tablename__ = "students"
    __table_args__ = (
        UniqueConstraint('roll_number', 'teacher_id', name='uq_student_roll_teacher'),
    )
    
    student_id = Column(Integer, primary_key=True, index=True)
    roll_number = Column(String(50), nullable=False, index=True)  # Removed unique=True
    name = Column(String(100), nullable=False)
    class_name = Column(String(100), nullable=False)  # Direct class name from CSV
    section = Column(String(10), nullable=False)      # Direct section from CSV
    branch = Column(String(100), nullable=False)      # Direct branch from CSV
    photo_url = Column(Text)
    teacher_id = Column(Integer, ForeignKey("teachers.teacher_id"))  # Direct teacher assignment
    face_encoding = Column(Text)  # Store face encoding as JSON string
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime)
    
    # Relationships
    teacher = relationship("Teacher", back_populates="students")
    student_classes = relationship("StudentClass", back_populates="student")
    attendance_records = relationship("Attendance", back_populates="student")


class Class(Base):
    __tablename__ = "classes"
    
    class_id = Column(Integer, primary_key=True, index=True)
    class_name = Column(String(50), nullable=False)
    section = Column(String(20))
    stream = Column(String(100))
    subject = Column(String(100))
    teacher_id = Column(Integer, ForeignKey("teachers.teacher_id", ondelete="CASCADE"))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    teacher = relationship("Teacher", back_populates="classes")
    student_classes = relationship("StudentClass", back_populates="class_obj", cascade="all, delete-orphan")


class StudentClass(Base):
    __tablename__ = "student_classes"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.student_id", ondelete="CASCADE"))
    class_id = Column(Integer, ForeignKey("classes.class_id", ondelete="CASCADE"))
    enrolled_at = Column(DateTime, default=func.now())
    
    # Unique constraint
    __table_args__ = (UniqueConstraint('student_id', 'class_id', name='uq_student_class'),)
    
    # Relationships
    student = relationship("Student", back_populates="student_classes")
    class_obj = relationship("Class", back_populates="student_classes")


class Attendance(Base):
    __tablename__ = "attendance"
    
    attendance_id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.student_id", ondelete="CASCADE"))
    teacher_id = Column(Integer, ForeignKey("teachers.teacher_id", ondelete="CASCADE"))
    status = Column(String(10), nullable=False)  # 'Present' or 'Absent'
    attendance_type = Column(String(20), default='Manual')  # 'Manual' or 'Facial'
    confidence_score = Column(Numeric(5, 2))  # For facial recognition
    attendance_date = Column(Date, nullable=False, default=func.current_date(), index=True)
    marked_at = Column(DateTime, default=func.now())
    notes = Column(Text)
    
    # Unique constraint - one attendance record per student per day
    __table_args__ = (UniqueConstraint('student_id', 'attendance_date', name='uq_student_date'),)
    
    # Relationships
    student = relationship("Student", back_populates="attendance_records")
    teacher = relationship("Teacher", back_populates="attendance_records")
