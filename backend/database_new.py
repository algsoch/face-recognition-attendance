"""
New database setup with string-based IDs and teacher isolation
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os
from dotenv import load_dotenv
import psycopg2

# Load environment variables
load_dotenv()

# Database URL
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is required")

# Create engine
engine = create_engine(DATABASE_URL)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class
Base = declarative_base()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_db_connection():
    """Test database connection"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.close()
        return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False

def create_tables():
    """Create all tables"""
    from backend.models_new import Base
    Base.metadata.create_all(bind=engine)
    print("✅ All tables created successfully!")

def reset_database():
    """Reset database and create fresh tables"""
    from backend.models_new import Base
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("✅ Database reset complete!")
