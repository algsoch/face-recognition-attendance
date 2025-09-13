# Attendance Management System Setup Guide

## Installation and Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Database Setup

1. **Initialize Database Schema:**
   - Connect to your DigitalOcean PostgreSQL database
   - Run the SQL script from `database_schema.sql`

```bash
psql "postgresql://doadmin:AVNS_lTjSpSEPTsF1gby4DUx@attendance-app-do-user-19447431-0.d.db.ondigitalocean.com:25060/defaultdb?sslmode=require" -f database_schema.sql
```

### 3. Environment Configuration

The `.env` file is already configured with:
- Database connection string
- JWT secret key
- Application settings

**Important:** Change the `SECRET_KEY` in production!

### 4. Run the Application

```bash
python main.py
```

Or using uvicorn directly:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## Application Features

### 🎯 Core Features Implemented

1. **Teacher Authentication**
   - JWT-based login/register system
   - Secure password hashing
   - Session management

2. **Student Management**
   - Add/edit/delete students
   - CSV/Excel bulk import
   - Student photo upload for facial recognition

3. **Attendance Management**
   - Manual attendance marking
   - Bulk attendance operations
   - Date-based filtering
   - Real-time statistics

4. **Facial Recognition**
   - Student photo enrollment
   - Webcam-based attendance
   - Confidence scoring
   - Face encoding storage

5. **Analytics & Reports**
   - Attendance statistics
   - Trend analysis
   - Top performers tracking
   - Excel export functionality

6. **Web Interface**
   - Teacher dashboard with charts
   - Student self-attendance portal
   - Responsive design
   - Real-time updates

### 🚀 API Endpoints

#### Authentication
- `POST /auth/register` - Teacher registration
- `POST /auth/login` - Teacher login
- `GET /auth/me` - Get current teacher info

#### Students
- `GET /students` - List students
- `POST /students` - Create student
- `PUT /students/{id}` - Update student
- `DELETE /students/{id}` - Delete student
- `POST /students/upload` - CSV/Excel import

#### Classes
- `GET /classes` - List classes
- `POST /classes` - Create class
- `PUT /classes/{id}` - Update class

#### Attendance
- `POST /attendance` - Mark attendance
- `POST /attendance/bulk` - Bulk attendance
- `GET /attendance` - Get attendance records

#### Facial Recognition
- `POST /face/upload-student-photo/{id}` - Upload student photo
- `POST /face/recognize-attendance` - Face recognition attendance
- `GET /face/webcam-stream` - Webcam stream

#### Analytics
- `GET /analytics/attendance-stats` - Overall statistics
- `GET /analytics/trends` - Attendance trends
- `GET /analytics/top-performers` - Top students
- `GET /analytics/export/excel` - Export to Excel

### 🌐 Frontend Pages

1. **Login Page** (`/login`)
   - Teacher authentication
   - Registration form
   - Password toggle

2. **Teacher Dashboard** (`/dashboard`)
   - Statistics overview
   - Attendance trends chart
   - Student management
   - Class management

3. **Student Portal** (`/student-portal`)
   - Facial recognition interface
   - Webcam capture
   - Photo upload option
   - Attendance history

## Database Schema

### Tables Created:
- `teachers` - Teacher information and authentication
- `students` - Student records with face encoding
- `classes` - Class information
- `student_classes` - Many-to-many relationship
- `attendance` - Attendance records with confidence scores

### Key Features:
- Unique constraints for data integrity
- Indexes for performance
- Foreign key relationships
- Face encoding storage as JSON

## Security Features

1. **JWT Authentication**
   - Secure token-based authentication
   - Configurable expiration time
   - Bearer token authorization

2. **Password Security**
   - bcrypt password hashing
   - Strong password requirements

3. **Database Security**
   - SSL/TLS connection (sslmode=require)
   - Parameterized queries (SQLAlchemy ORM)
   - Input validation

## Face Recognition System

### Technology Stack:
- OpenCV for image processing
- face-recognition library for encoding
- Real-time webcam capture
- Base64 image transmission

### Features:
- Face detection and encoding
- Similarity matching with confidence scores
- Support for webcam and file upload
- Tolerance adjustment for accuracy

## Frontend Technology

### Libraries Used:
- Bootstrap 5 for UI components
- Chart.js for data visualization
- Font Awesome for icons
- Vanilla JavaScript for functionality

### Features:
- Responsive design
- Real-time charts
- Interactive components
- Camera integration

## Production Deployment

### Requirements:
1. Python 3.8+
2. DigitalOcean PostgreSQL database
3. SSL certificate for HTTPS
4. Proper environment variables

### Security Checklist:
- [ ] Change SECRET_KEY in production
- [ ] Enable HTTPS
- [ ] Configure CORS properly
- [ ] Set up proper logging
- [ ] Monitor database connections
- [ ] Regular backups

### Performance Optimization:
- Database connection pooling
- Image compression for face recognition
- Caching for frequently accessed data
- CDN for static assets

## Troubleshooting

### Common Issues:

1. **Database Connection Failed**
   - Check DATABASE_URL in .env
   - Verify DigitalOcean database credentials
   - Ensure SSL mode is enabled

2. **Camera Not Working**
   - Check browser permissions
   - Ensure HTTPS for production
   - Verify webcam availability

3. **Face Recognition Issues**
   - Ensure good lighting
   - Check face encoding quality
   - Verify confidence threshold

4. **Import Errors**
   - Install all requirements.txt dependencies
   - Check Python version compatibility
   - Verify virtual environment activation

## Sample Data

The database schema includes sample data:
- 2 teachers (John Doe, Jane Smith)
- 3 students with different classes
- 3 classes with different subjects
- Student-class relationships

### Demo Credentials:
- Email: john.doe@school.edu
- Password: password123 (hash needs to be generated)

## API Documentation

The complete API documentation is available at:
- `http://localhost:8000/docs` (Swagger UI)
- `http://localhost:8000/redoc` (ReDoc)

## Support

For issues or questions:
1. Check the logs for error messages
2. Verify database connectivity
3. Ensure all dependencies are installed
4. Check browser console for frontend errors

## License

This project is for educational purposes and demonstration of attendance management system capabilities.
