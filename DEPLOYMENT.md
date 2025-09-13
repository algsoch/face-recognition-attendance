# 🚀 Deployment Checklist

## Pre-Deployment Setup

### 1. Environment Verification
- [ ] Python 3.8+ installed
- [ ] pip package manager available
- [ ] DigitalOcean PostgreSQL database accessible
- [ ] Database URL connection string verified

### 2. Dependencies Installation
```bash
pip install -r requirements.txt
```

### 3. Environment Configuration
- [ ] `.env` file created with proper values
- [ ] `DATABASE_URL` set to DigitalOcean PostgreSQL connection
- [ ] `SECRET_KEY` generated (use strong random string)
- [ ] `ALGORITHM` set to "HS256"
- [ ] `ACCESS_TOKEN_EXPIRE_MINUTES` configured (default: 30)

### 4. Database Setup
```bash
python -c "from backend.database import engine, Base; from backend import models; Base.metadata.create_all(bind=engine)"
```

### 5. Directory Structure Verification
- [ ] `faces/` directory exists (created automatically)
- [ ] `frontend/` directory with HTML files
- [ ] `static/` directory with CSS/JS files
- [ ] `backend/` directory with Python modules

## Testing Checklist

### 1. Server Start Test
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```
- [ ] Server starts without errors
- [ ] Health check accessible: http://localhost:8000/health
- [ ] API documentation: http://localhost:8000/docs

### 2. Frontend Access Test
- [ ] Dashboard: http://localhost:8000/
- [ ] Login page: http://localhost:8000/login
- [ ] Student portal: http://localhost:8000/student-portal

### 3. Database Connectivity Test
```bash
python test_system.py
```
- [ ] Database connection successful
- [ ] API endpoints responding
- [ ] Authentication working

### 4. Functional Testing
- [ ] Teacher registration and login
- [ ] Student creation and management
- [ ] Class creation and assignment
- [ ] Attendance marking (manual)
- [ ] CSV/Excel import functionality
- [ ] Analytics and reporting
- [ ] Facial recognition (if camera available)

## Production Deployment

### 1. Security Hardening
- [ ] Change `SECRET_KEY` to production value
- [ ] Enable HTTPS (SSL/TLS certificates)
- [ ] Configure CORS properly for production domain
- [ ] Set secure cookie flags
- [ ] Enable database SSL connection verification

### 2. Performance Optimization
- [ ] Configure database connection pooling
- [ ] Set up Redis for session management (optional)
- [ ] Enable gzip compression
- [ ] Configure static file serving (nginx/apache)
- [ ] Set up CDN for static assets (optional)

### 3. Monitoring and Logging
- [ ] Configure application logging
- [ ] Set up error tracking (Sentry, etc.)
- [ ] Database performance monitoring
- [ ] Server resource monitoring
- [ ] Backup strategy implemented

### 4. Domain and Hosting
- [ ] Domain name configured
- [ ] DNS records set up
- [ ] Server/hosting platform configured
- [ ] Load balancer configured (if needed)
- [ ] SSL certificate installed

## Environment-Specific Configurations

### Development
```env
DATABASE_URL=postgresql://doadmin:password@localhost:5432/attendance_dev
SECRET_KEY=dev-secret-key-change-in-production
DEBUG=True
```

### Production
```env
DATABASE_URL=postgresql://doadmin:AVNS_lTjSpSEPTsF1gby4DUx@attendance-app-do-user-19447431-0.d.db.ondigitalocean.com:25060/defaultdb?sslmode=require
SECRET_KEY=super-secure-production-key-min-32-chars
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
```

## Troubleshooting Common Issues

### Database Connection Issues
1. Verify database URL format
2. Check network connectivity to DigitalOcean
3. Verify SSL requirements
4. Check firewall settings

### Facial Recognition Issues
1. Ensure OpenCV is properly installed
2. Check camera permissions
3. Verify face_recognition library installation
4. Test with good lighting conditions

### File Upload Issues
1. Check file size limits
2. Verify file format support (CSV, Excel)
3. Ensure proper file encoding
4. Check server disk space

### Performance Issues
1. Monitor database query performance
2. Check server resource usage
3. Optimize large data operations
4. Consider pagination for large datasets

## Backup and Recovery

### Database Backup
- [ ] Regular automated backups scheduled
- [ ] Backup restoration procedure tested
- [ ] Point-in-time recovery capability verified

### Application Backup
- [ ] Source code version control (Git)
- [ ] Configuration files backed up
- [ ] Static files and uploads backed up
- [ ] Disaster recovery plan documented

## Maintenance Schedule

### Daily
- [ ] Monitor application logs
- [ ] Check system resource usage
- [ ] Verify backup completion

### Weekly
- [ ] Review security logs
- [ ] Update dependencies (if needed)
- [ ] Performance metrics review

### Monthly
- [ ] Full system backup test
- [ ] Security audit
- [ ] Capacity planning review
- [ ] User feedback collection

## Support and Documentation

### User Training
- [ ] Teacher training materials prepared
- [ ] Student portal usage guide
- [ ] Admin documentation complete

### Technical Documentation
- [ ] API documentation up to date
- [ ] Database schema documented
- [ ] Deployment procedures documented
- [ ] Troubleshooting guide available

---

## Quick Commands Reference

### Start Development Server
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Run Tests
```bash
python test_system.py
```

### Database Reset (Development Only)
```bash
python -c "from backend.database import engine, Base; Base.metadata.drop_all(bind=engine); Base.metadata.create_all(bind=engine)"
```

### Generate New Secret Key
```python
import secrets
print(secrets.token_urlsafe(32))
```
