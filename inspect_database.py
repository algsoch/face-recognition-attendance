#!/usr/bin/env python3
"""
Database Students Inspection Script
Check the actual state of students in the database
"""

from backend.database import SessionLocal
from backend.models import Student
from sqlalchemy import text

def inspect_students_database():
    """Inspect the students table directly"""
    print("🔍 DATABASE STUDENTS INSPECTION")
    print("=" * 50)
    
    db = SessionLocal()
    
    try:
        # Check total students count
        total_count = db.query(Student).count()
        print(f"📊 Total students in database: {total_count}")
        
        # Check active students count
        active_count = db.query(Student).filter(Student.is_active == True).count()
        print(f"✅ Active students (is_active = True): {active_count}")
        
        # Check inactive students count
        inactive_count = db.query(Student).filter(Student.is_active == False).count()
        print(f"❌ Inactive students (is_active = False): {inactive_count}")
        
        # Check NULL is_active count
        null_count = db.query(Student).filter(Student.is_active.is_(None)).count()
        print(f"❓ NULL is_active students: {null_count}")
        
        # Show first few students with their is_active status
        print(f"\n📋 First 10 students with their is_active status:")
        students = db.query(Student).limit(10).all()
        
        if students:
            for student in students:
                print(f"   ID: {student.student_id}, Name: {student.name}, Roll: {student.roll_number}, is_active: {student.is_active}")
        else:
            print("   No students found!")
        
        # Check what the API filter would return
        api_students = db.query(Student).filter(Student.is_active == True).all()
        print(f"\n🔍 Students that API would return (is_active == True): {len(api_students)}")
        
        # Check what happens without the filter
        all_students = db.query(Student).all()
        print(f"🔍 Students without filter: {len(all_students)}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    finally:
        db.close()
    
    print("=" * 50)
    print("🎯 INSPECTION COMPLETE")

if __name__ == "__main__":
    inspect_students_database()
