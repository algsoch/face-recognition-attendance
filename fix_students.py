#!/usr/bin/env python3
"""
Fix Students Data Script
Reactivate all inactive students
"""

from backend.database import SessionLocal
from backend.models import Student

def fix_students_data():
    """Reactivate all students"""
    print("🔧 FIXING STUDENTS DATA")
    print("=" * 50)
    
    db = SessionLocal()
    
    try:
        # Count inactive students
        inactive_students = db.query(Student).filter(Student.is_active == False).all()
        print(f"📊 Found {len(inactive_students)} inactive students")
        
        if inactive_students:
            print("🔄 Reactivating students...")
            
            for student in inactive_students:
                print(f"   ✅ Reactivating: {student.name} (Roll: {student.roll_number})")
                student.is_active = True
            
            db.commit()
            print(f"✅ Successfully reactivated {len(inactive_students)} students!")
            
            # Verify the fix
            active_count = db.query(Student).filter(Student.is_active == True).count()
            print(f"📊 Active students now: {active_count}")
            
        else:
            print("ℹ️  No inactive students found")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    
    finally:
        db.close()
    
    print("=" * 50)
    print("🎯 FIX COMPLETE")

if __name__ == "__main__":
    fix_students_data()
