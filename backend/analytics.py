"""
Analytics and reporting utilities for attendance data
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, extract, desc
from typing import List, Dict, Optional
from datetime import date, datetime, timedelta
import pandas as pd
from io import BytesIO
import json

from backend.models import Student, Teacher, Class, Attendance, StudentClass


def generate_attendance_report(
    db: Session, 
    class_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    format_type: str = "json"
) -> Dict:
    """Generate comprehensive attendance report"""
    
    # Default date range (last 30 days)
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=30)
    
    # Base query
    query = db.query(
        Student.student_id,
        Student.name.label('student_name'),
        Student.roll_number,
        Class.class_name,
        Class.section,
        func.count(Attendance.attendance_id).label('total_days'),
        func.count(func.nullif(Attendance.status != 'Present', True)).label('present_days'),
        func.count(func.nullif(Attendance.status != 'Absent', True)).label('absent_days')
    ).join(
        StudentClass, Student.student_id == StudentClass.student_id
    ).join(
        Class, StudentClass.class_id == Class.class_id
    ).join(
        Attendance, and_(
            Student.student_id == Attendance.student_id,
            Class.class_id == Attendance.class_id
        )
    ).filter(
        Attendance.attendance_date.between(start_date, end_date)
    )
    
    if class_id:
        query = query.filter(Class.class_id == class_id)
    
    # Group by student
    query = query.group_by(
        Student.student_id, Student.name, Student.roll_number,
        Class.class_name, Class.section
    )
    
    results = query.all()
    
    # Calculate attendance percentages and format data
    report_data = []
    for row in results:
        attendance_percentage = (row.present_days / row.total_days * 100) if row.total_days > 0 else 0
        
        report_data.append({
            'student_id': row.student_id,
            'student_name': row.student_name,
            'roll_number': row.roll_number,
            'class_name': row.class_name,
            'section': row.section,
            'total_days': row.total_days,
            'present_days': row.present_days,
            'absent_days': row.absent_days,
            'attendance_percentage': round(attendance_percentage, 2)
        })
    
    # Generate summary statistics
    total_students = len(report_data)
    avg_attendance = sum(r['attendance_percentage'] for r in report_data) / total_students if total_students > 0 else 0
    
    # Students with low attendance (below 75%)
    low_attendance_students = [r for r in report_data if r['attendance_percentage'] < 75]
    
    summary = {
        'report_period': {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        },
        'summary_statistics': {
            'total_students': total_students,
            'average_attendance_percentage': round(avg_attendance, 2),
            'students_with_low_attendance': len(low_attendance_students),
            'low_attendance_threshold': 75
        },
        'student_data': report_data,
        'low_attendance_students': low_attendance_students
    }
    
    return summary


def generate_daily_attendance_trends(
    db: Session,
    class_id: Optional[int] = None,
    days: int = 30
) -> Dict:
    """Generate daily attendance trends for visualization"""
    
    end_date = date.today()
    start_date = end_date - timedelta(days=days)
    
    # Query daily attendance data
    query = db.query(
        Attendance.attendance_date,
        func.count(Attendance.attendance_id).label('total_marked'),
        func.count(func.nullif(Attendance.status != 'Present', True)).label('present_count'),
        func.count(func.nullif(Attendance.status != 'Absent', True)).label('absent_count')
    ).filter(
        Attendance.attendance_date.between(start_date, end_date)
    )
    
    if class_id:
        query = query.filter(Attendance.class_id == class_id)
    
    query = query.group_by(Attendance.attendance_date).order_by(Attendance.attendance_date)
    
    results = query.all()
    
    # Format data for chart visualization
    trends_data = {
        'dates': [],
        'total_marked': [],
        'present_count': [],
        'absent_count': [],
        'attendance_percentage': []
    }
    
    for row in results:
        attendance_pct = (row.present_count / row.total_marked * 100) if row.total_marked > 0 else 0
        
        trends_data['dates'].append(row.attendance_date.isoformat())
        trends_data['total_marked'].append(row.total_marked)
        trends_data['present_count'].append(row.present_count)
        trends_data['absent_count'].append(row.absent_count)
        trends_data['attendance_percentage'].append(round(attendance_pct, 2))
    
    return trends_data


def generate_class_wise_summary(db: Session, teacher_id: Optional[int] = None) -> Dict:
    """Generate class-wise attendance summary"""
    
    query = db.query(
        Class.class_id,
        Class.class_name,
        Class.section,
        Class.subject,
        Teacher.name.label('teacher_name'),
        func.count(func.distinct(StudentClass.student_id)).label('total_students'),
        func.count(Attendance.attendance_id).label('total_attendance_records'),
        func.count(func.nullif(Attendance.status != 'Present', True)).label('total_present'),
        func.avg(
            func.cast(func.nullif(Attendance.status != 'Present', True), func.FLOAT) * 100
        ).label('avg_attendance_percentage')
    ).join(
        Teacher, Class.teacher_id == Teacher.teacher_id
    ).join(
        StudentClass, Class.class_id == StudentClass.class_id
    ).outerjoin(
        Attendance, Class.class_id == Attendance.class_id
    )
    
    if teacher_id:
        query = query.filter(Class.teacher_id == teacher_id)
    
    query = query.group_by(
        Class.class_id, Class.class_name, Class.section, 
        Class.subject, Teacher.name
    )
    
    results = query.all()
    
    class_summary = []
    for row in results:
        avg_attendance = row.avg_attendance_percentage or 0
        
        class_summary.append({
            'class_id': row.class_id,
            'class_name': row.class_name,
            'section': row.section,
            'subject': row.subject,
            'teacher_name': row.teacher_name,
            'total_students': row.total_students,
            'total_attendance_records': row.total_attendance_records or 0,
            'total_present': row.total_present or 0,
            'average_attendance_percentage': round(avg_attendance, 2)
        })
    
    return {'classes': class_summary}


def get_top_performers(db: Session, limit: int = 10, class_id: Optional[int] = None) -> List[Dict]:
    """Get top performing students by attendance percentage"""
    
    query = db.query(
        Student.student_id,
        Student.name,
        Student.roll_number,
        Class.class_name,
        Class.section,
        func.count(Attendance.attendance_id).label('total_days'),
        func.count(func.nullif(Attendance.status != 'Present', True)).label('present_days'),
        (func.count(func.nullif(Attendance.status != 'Present', True)) * 100.0 / 
         func.count(Attendance.attendance_id)).label('attendance_percentage')
    ).join(
        StudentClass, Student.student_id == StudentClass.student_id
    ).join(
        Class, StudentClass.class_id == Class.class_id
    ).join(
        Attendance, Student.student_id == Attendance.student_id
    )
    
    if class_id:
        query = query.filter(Class.class_id == class_id)
    
    query = query.group_by(
        Student.student_id, Student.name, Student.roll_number,
        Class.class_name, Class.section
    ).having(
        func.count(Attendance.attendance_id) >= 5  # Minimum 5 days of data
    ).order_by(
        desc('attendance_percentage')
    ).limit(limit)
    
    results = query.all()
    
    top_performers = []
    for row in results:
        top_performers.append({
            'student_id': row.student_id,
            'name': row.name,
            'roll_number': row.roll_number,
            'class_name': row.class_name,
            'section': row.section,
            'total_days': row.total_days,
            'present_days': row.present_days,
            'attendance_percentage': round(row.attendance_percentage, 2)
        })
    
    return top_performers


def get_students_needing_attention(
    db: Session, 
    threshold: float = 75.0, 
    class_id: Optional[int] = None
) -> List[Dict]:
    """Get students with attendance below threshold"""
    
    query = db.query(
        Student.student_id,
        Student.name,
        Student.roll_number,
        Class.class_name,
        Class.section,
        func.count(Attendance.attendance_id).label('total_days'),
        func.count(func.nullif(Attendance.status != 'Present', True)).label('present_days'),
        (func.count(func.nullif(Attendance.status != 'Present', True)) * 100.0 / 
         func.count(Attendance.attendance_id)).label('attendance_percentage')
    ).join(
        StudentClass, Student.student_id == StudentClass.student_id
    ).join(
        Class, StudentClass.class_id == Class.class_id
    ).join(
        Attendance, Student.student_id == Attendance.student_id
    )
    
    if class_id:
        query = query.filter(Class.class_id == class_id)
    
    query = query.group_by(
        Student.student_id, Student.name, Student.roll_number,
        Class.class_name, Class.section
    ).having(
        func.count(Attendance.attendance_id) >= 5  # Minimum 5 days of data
    ).having(
        (func.count(func.nullif(Attendance.status != 'Present', True)) * 100.0 / 
         func.count(Attendance.attendance_id)) < threshold
    ).order_by(
        'attendance_percentage'
    )
    
    results = query.all()
    
    attention_needed = []
    for row in results:
        attention_needed.append({
            'student_id': row.student_id,
            'name': row.name,
            'roll_number': row.roll_number,
            'class_name': row.class_name,
            'section': row.section,
            'total_days': row.total_days,
            'present_days': row.present_days,
            'attendance_percentage': round(row.attendance_percentage, 2),
            'deficit_percentage': round(threshold - row.attendance_percentage, 2)
        })
    
    return attention_needed


def export_attendance_to_excel(
    db: Session,
    class_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> BytesIO:
    """Export attendance data to Excel file"""
    
    # Generate report data
    report_data = generate_attendance_report(db, class_id, start_date, end_date)
    
    # Create Excel file in memory
    excel_buffer = BytesIO()
    
    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
        # Summary sheet
        summary_df = pd.DataFrame([report_data['summary_statistics']])
        summary_df.to_excel(writer, sheet_name='Summary', index=False)
        
        # Student data sheet
        student_df = pd.DataFrame(report_data['student_data'])
        student_df.to_excel(writer, sheet_name='Student Attendance', index=False)
        
        # Low attendance students sheet
        if report_data['low_attendance_students']:
            low_attendance_df = pd.DataFrame(report_data['low_attendance_students'])
            low_attendance_df.to_excel(writer, sheet_name='Low Attendance', index=False)
        
        # Daily trends sheet
        trends_data = generate_daily_attendance_trends(db, class_id)
        trends_df = pd.DataFrame(trends_data)
        trends_df.to_excel(writer, sheet_name='Daily Trends', index=False)
    
    excel_buffer.seek(0)
    return excel_buffer


def get_monthly_attendance_summary(db: Session, year: int, month: int, class_id: Optional[int] = None) -> Dict:
    """Get monthly attendance summary"""
    
    query = db.query(
        func.extract('day', Attendance.attendance_date).label('day'),
        func.count(Attendance.attendance_id).label('total_marked'),
        func.count(func.nullif(Attendance.status != 'Present', True)).label('present_count')
    ).filter(
        and_(
            func.extract('year', Attendance.attendance_date) == year,
            func.extract('month', Attendance.attendance_date) == month
        )
    )
    
    if class_id:
        query = query.filter(Attendance.class_id == class_id)
    
    query = query.group_by(func.extract('day', Attendance.attendance_date))
    query = query.order_by(func.extract('day', Attendance.attendance_date))
    
    results = query.all()
    
    monthly_data = {
        'year': year,
        'month': month,
        'daily_attendance': []
    }
    
    for row in results:
        attendance_pct = (row.present_count / row.total_marked * 100) if row.total_marked > 0 else 0
        
        monthly_data['daily_attendance'].append({
            'day': int(row.day),
            'total_marked': row.total_marked,
            'present_count': row.present_count,
            'attendance_percentage': round(attendance_pct, 2)
        })
    
    return monthly_data
