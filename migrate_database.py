"""
Database migration script to change roll_number constraint from global unique to per-teacher unique
"""
import sqlite3
import os
from backend.database import engine, Base
from backend.models import Teacher, Student, Class, Attendance

def migrate_database():
    """Migrate database to new schema with per-teacher roll number uniqueness"""
    
    # Database file path
    db_path = "attendance.db"
    
    print("Starting database migration...")
    
    # Check if database exists
    if not os.path.exists(db_path):
        print("Database doesn't exist, creating new one with correct schema...")
        Base.metadata.create_all(bind=engine)
        print("Migration completed - new database created.")
        return
    
    # Backup existing data
    print("Backing up existing data...")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Backup teachers
    cursor.execute("SELECT * FROM teachers")
    teachers_data = cursor.fetchall()
    
    # Backup students
    cursor.execute("SELECT * FROM students")
    students_data = cursor.fetchall()
    
    # Backup classes
    cursor.execute("SELECT * FROM classes")
    classes_data = cursor.fetchall()
    
    # Backup attendance
    cursor.execute("SELECT * FROM attendance")
    attendance_data = cursor.fetchall()
    
    print(f"Backed up {len(teachers_data)} teachers, {len(students_data)} students, {len(classes_data)} classes, {len(attendance_data)} attendance records")
    
    conn.close()
    
    # Remove old database
    print("Removing old database...")
    os.remove(db_path)
    
    # Create new database with updated schema
    print("Creating new database with updated schema...")
    Base.metadata.create_all(bind=engine)
    
    # Restore data
    print("Restoring data...")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Restore teachers (teacher_id, name, email, password_hash, department, phone, is_active, created_at, updated_at)
    if teachers_data:
        cursor.executemany(
            "INSERT INTO teachers (teacher_id, name, email, password_hash, department, phone, is_active, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            teachers_data
        )
    
    # Restore students
    if students_data:
        cursor.executemany(
            "INSERT INTO students (student_id, roll_number, name, class_name, section, branch, photo_url, teacher_id, face_encoding, is_active, created_at, updated_at, deleted_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            students_data
        )
    
    # Restore classes
    if classes_data:
        cursor.executemany(
            "INSERT INTO classes (class_id, class_name, section, subject, teacher_id, is_active, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            classes_data
        )
    
    # Restore attendance
    if attendance_data:
        cursor.executemany(
            "INSERT INTO attendance (attendance_id, student_id, class_id, teacher_id, date, status, attendance_type, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            attendance_data
        )
    
    conn.commit()
    conn.close()
    
    print(f"Migration completed successfully!")
    print(f"Restored {len(teachers_data)} teachers, {len(students_data)} students, {len(classes_data)} classes, {len(attendance_data)} attendance records")
    print("Roll numbers are now unique per teacher instead of globally unique.")

if __name__ == "__main__":
    migrate_database()