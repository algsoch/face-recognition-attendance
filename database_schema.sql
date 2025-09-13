-- Attendance Management System Database Schema
-- DigitalOcean PostgreSQL Database

-- Drop tables if they exist (for fresh setup)
DROP TABLE IF EXISTS attendance CASCADE;
DROP TABLE IF EXISTS student_classes CASCADE;
DROP TABLE IF EXISTS classes CASCADE;
DROP TABLE IF EXISTS students CASCADE;
DROP TABLE IF EXISTS teachers CASCADE;

-- Table: teachers
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

-- Table: students
CREATE TABLE students (
    student_id SERIAL PRIMARY KEY,
    roll_number VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    class VARCHAR(50),
    section VARCHAR(20),
    stream VARCHAR(100),
    email VARCHAR(150),
    photo_url TEXT,
    face_encoding TEXT, -- Store face encoding as text
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table: classes
CREATE TABLE classes (
    class_id SERIAL PRIMARY KEY,
    class_name VARCHAR(50) NOT NULL,
    section VARCHAR(20),
    stream VARCHAR(100),
    subject VARCHAR(100),
    teacher_id INT REFERENCES teachers(teacher_id) ON DELETE CASCADE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table: student_classes (many-to-many relationship)
CREATE TABLE student_classes (
    id SERIAL PRIMARY KEY,
    student_id INT REFERENCES students(student_id) ON DELETE CASCADE,
    class_id INT REFERENCES classes(class_id) ON DELETE CASCADE,
    enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(student_id, class_id)
);

-- Table: attendance
CREATE TABLE attendance (
    attendance_id SERIAL PRIMARY KEY,
    student_id INT REFERENCES students(student_id) ON DELETE CASCADE,
    teacher_id INT REFERENCES teachers(teacher_id) ON DELETE CASCADE,
    class_id INT REFERENCES classes(class_id) ON DELETE CASCADE,
    status VARCHAR(10) CHECK (status IN ('Present', 'Absent')) NOT NULL,
    attendance_type VARCHAR(20) DEFAULT 'Manual' CHECK (attendance_type IN ('Manual', 'Facial')),
    confidence_score NUMERIC(5,2) DEFAULT NULL, -- For facial recognition
    attendance_date DATE NOT NULL DEFAULT CURRENT_DATE,
    marked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    UNIQUE(student_id, class_id, attendance_date) -- One attendance record per student per class per day
);

-- Indexes for better performance
CREATE INDEX idx_teachers_email ON teachers(email);
CREATE INDEX idx_students_roll_number ON students(roll_number);
CREATE INDEX idx_attendance_date ON attendance(attendance_date);
CREATE INDEX idx_attendance_student_date ON attendance(student_id, attendance_date);
CREATE INDEX idx_attendance_class_date ON attendance(class_id, attendance_date);

-- Insert sample data for testing
INSERT INTO teachers (name, email, password_hash, department) VALUES 
('John Doe', 'john.doe@school.edu', '$2b$12$placeholder_hash', 'Computer Science'),
('Jane Smith', 'jane.smith@school.edu', '$2b$12$placeholder_hash', 'Mathematics');

INSERT INTO students (roll_number, name, class, section, stream, email) VALUES 
('CS001', 'Alice Johnson', '12', 'A', 'Computer Science', 'alice.johnson@student.edu'),
('CS002', 'Bob Wilson', '12', 'A', 'Computer Science', 'bob.wilson@student.edu'),
('CS003', 'Charlie Brown', '12', 'B', 'Computer Science', 'charlie.brown@student.edu');

INSERT INTO classes (class_name, section, stream, subject, teacher_id) VALUES 
('12', 'A', 'Computer Science', 'Data Structures', 1),
('12', 'B', 'Computer Science', 'Algorithms', 1),
('12', 'A', 'Computer Science', 'Calculus', 2);

INSERT INTO student_classes (student_id, class_id) VALUES 
(1, 1), (1, 3),
(2, 1), (2, 3),
(3, 2);

-- View for attendance statistics
CREATE OR REPLACE VIEW attendance_stats AS
SELECT 
    s.student_id,
    s.name as student_name,
    s.roll_number,
    c.class_id,
    c.class_name,
    c.section,
    COUNT(a.attendance_id) as total_days,
    COUNT(CASE WHEN a.status = 'Present' THEN 1 END) as present_days,
    COUNT(CASE WHEN a.status = 'Absent' THEN 1 END) as absent_days,
    ROUND(
        (COUNT(CASE WHEN a.status = 'Present' THEN 1 END) * 100.0 / 
         NULLIF(COUNT(a.attendance_id), 0)), 2
    ) as attendance_percentage
FROM students s
JOIN student_classes sc ON s.student_id = sc.student_id
JOIN classes c ON sc.class_id = c.class_id
LEFT JOIN attendance a ON s.student_id = a.student_id AND c.class_id = a.class_id
GROUP BY s.student_id, s.name, s.roll_number, c.class_id, c.class_name, c.section;
