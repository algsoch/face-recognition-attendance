"""
Setup script to initialize SQLite database with demo data
"""
from backend.database import engine, SessionLocal
from backend.models import Base, Teacher
from backend.auth import get_password_hash
from sqlalchemy.orm import Session

def setup_database():
    """Initialize database with tables and demo data"""
    print("🔧 Setting up SQLite database...")
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("✅ Tables created successfully")
    
    # Create demo teacher
    db = SessionLocal()
    try:
        # Check if demo teacher already exists
        existing_teacher = db.query(Teacher).filter(Teacher.email == "teacher1@example.com").first()
        if existing_teacher:
            print("✅ Demo teacher already exists")
            return
        
        # Create demo teacher
        hashed_password = get_password_hash("password123")
        demo_teacher = Teacher(
            name="Demo Teacher",
            email="teacher1@example.com",
            password_hash=hashed_password,
            department="Computer Science",
            phone="123-456-7890"
        )
        db.add(demo_teacher)
        db.commit()
        db.refresh(demo_teacher)
        
        print(f"✅ Demo teacher created with ID: {demo_teacher.teacher_id}")
        print("📋 Login credentials:")
        print("   Email: teacher1@example.com")
        print("   Password: password123")
        
    except Exception as e:
        print(f"❌ Error creating demo teacher: {e}")
        db.rollback()
    finally:
        db.close()

def migration_note():
    """Display migration instructions for PostgreSQL"""
    print("\n" + "="*60)
    print("🔄 FUTURE POSTGRESQL MIGRATION INSTRUCTIONS")
    print("="*60)
    print("To switch to PostgreSQL later:")
    print("1. Update DATABASE_URL in .env file:")
    print("   DATABASE_URL=postgresql://user:pass@host:port/db")
    print("2. Install psycopg2: pip install psycopg2-binary")
    print("3. Run this setup script again")
    print("4. The application will work identically!")
    print("="*60)

if __name__ == "__main__":
    setup_database()
    migration_note()