# Database Migration Guide

## Current Setup: SQLite ✅
The system is currently using SQLite for development with all features working:
- ✅ Authentication 
- ✅ Add Student (branch field fixed)
- ✅ CSV Import (schema alignment fixed)
- ✅ Teacher isolation
- ✅ All CRUD operations

## Future PostgreSQL Migration 🔄

### 1. Prerequisites
```bash
pip install psycopg2-binary
```

### 2. Environment Update
Update `.env` file:
```env
# Change from SQLite
DATABASE_URL=sqlite:///./attendance.db

# To PostgreSQL (example URLs)
DATABASE_URL=postgresql://user:password@localhost:5432/attendance_db
# OR DigitalOcean
DATABASE_URL=postgresql://attendance:AVNS_bTCf0Xh_b148OX_Z0x1@attendance-app-do-user-19447431-0.d.db.ondigitalocean.com:25060/teacher_data?sslmode=require
```

### 3. Database Setup
Run the setup script to create tables and demo data:
```bash
python setup_database.py
```

### 4. SQL Commands for Manual Setup (if needed)
If user permissions don't allow table creation, use these SQL commands:

```sql
-- Create tables
CREATE TABLE teachers (
    teacher_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    department VARCHAR(100),
    phone VARCHAR(20),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE students (
    student_id SERIAL PRIMARY KEY,
    roll_number VARCHAR(50) NOT NULL,
    name VARCHAR(100) NOT NULL,
    class_name VARCHAR(50) NOT NULL,
    section VARCHAR(10) NOT NULL,
    branch VARCHAR(50),
    photo_url TEXT,
    teacher_id INTEGER REFERENCES teachers(teacher_id),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE classes (
    class_id SERIAL PRIMARY KEY,
    class_name VARCHAR(100) NOT NULL,
    section VARCHAR(10) NOT NULL,
    branch VARCHAR(50),
    teacher_id INTEGER REFERENCES teachers(teacher_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE attendance (
    attendance_id SERIAL PRIMARY KEY,
    student_id INTEGER REFERENCES students(student_id),
    teacher_id INTEGER REFERENCES teachers(teacher_id),
    attendance_date DATE NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'Present',
    attendance_type VARCHAR(50),
    confidence_score DECIMAL(5,4),
    notes TEXT,
    marked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO attendance;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO attendance;

-- Create demo teacher (password: password123)
INSERT INTO teachers (name, email, password_hash, department) VALUES 
('Demo Teacher', 'teacher1@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewCy9UDU/MQoM9Ey', 'Computer Science');
```

### 5. Verification
Run the test script to verify everything works:
```bash
python test_fixes.py
```

## Key Features Preserved 🎯
- **Schema Compatibility**: Same models work for both databases
- **Authentication**: JWT tokens work identically  
- **Teacher Isolation**: Each teacher sees only their students
- **CSV Import**: Branch field mapping works correctly
- **Add Student**: No more "[object Object]" errors
- **All APIs**: Identical endpoints and responses

## Migration Benefits 📈
- **Zero Code Changes**: Application logic remains identical
- **Data Persistence**: PostgreSQL for production reliability
- **Scalability**: Better performance for multiple users
- **Backup/Recovery**: Enterprise-grade database features
- **Security**: Role-based access control