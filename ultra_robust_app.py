#!/usr/bin/env python3
"""
Ultra-Robust Face Recognition Web Interface
Professional interface for advanced face recognition with ultra-strict validation
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for
import cv2
import numpy as np
import base64
import io
from PIL import Image
import sqlite3
import logging
import json
from pathlib import Path
import sys
import os

# Add backend directory to path
backend_dir = Path(__file__).parent / "backend"
sys.path.append(str(backend_dir))

from backend.ultra_robust_recognition import ultra_robust_recognizer

app = Flask(__name__)
app.secret_key = "ultra_robust_face_recognition_2024"

# Configure logging
logging.basicConfig(level=logging.INFO)

def get_all_students():
    """Get all students from database"""
    try:
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT student_id, roll_number, name, class_name, section, branch, 
                   photo_url, is_active, created_at, updated_at
            FROM students ORDER BY student_id
        ''')
        students = cursor.fetchall()
        conn.close()
        
        return [{
            'student_id': row[0],
            'roll_number': row[1],
            'name': row[2],
            'class_name': row[3],
            'section': row[4],
            'branch': row[5],
            'photo_url': row[6],
            'is_active': row[7],
            'created_at': row[8],
            'updated_at': row[9]
        } for row in students]
    except Exception as e:
        logging.error(f"Error getting students: {e}")
        return []

@app.route('/')
def index():
    """Main page"""
    students = get_all_students()
    return render_template('ultra_robust_index.html', students=students)

@app.route('/ultra-recognition', methods=['POST'])
def ultra_recognition():
    """Ultra-robust face recognition endpoint"""
    try:
        # Get image data
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Read and process image
        image_bytes = file.read()
        image = Image.open(io.BytesIO(image_bytes))
        
        # Convert to OpenCV format
        if image.mode != 'RGB':
            image = image.convert('RGB')
        cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        # Perform ultra-robust recognition
        result = ultra_robust_recognizer.recognize_face_from_image(cv_image)
        
        # Get current encodings status
        encodings_status = {
            'total_encodings': len(ultra_robust_recognizer.face_encodings),
            'available_students': list(ultra_robust_recognizer.face_encodings.keys())
        }
        
        return jsonify({
            'success': True,
            'result': result,
            'encodings_status': encodings_status
        })
        
    except Exception as e:
        logging.error(f"Error in ultra recognition: {e}")
        return jsonify({'error': f'Recognition error: {str(e)}'}), 500

@app.route('/build-ultra-database')
def build_ultra_database():
    """Build ultra-robust face database"""
    try:
        students = get_all_students()
        processed_count = 0
        errors = []
        
        for student in students:
            if student['photo_url']:
                try:
                    success = ultra_robust_recognizer.extract_and_save_face(
                        student['photo_url'], 
                        str(student['student_id'])
                    )
                    if success:
                        processed_count += 1
                    else:
                        errors.append(f"Failed to process student {student['student_id']}")
                except Exception as e:
                    errors.append(f"Error processing student {student['student_id']}: {str(e)}")
            else:
                errors.append(f"Student {student['student_id']} has no photo URL")
        
        return jsonify({
            'success': True,
            'message': f'Ultra-robust database built successfully!',
            'processed_count': processed_count,
            'total_students': len(students),
            'encodings_created': list(ultra_robust_recognizer.face_encodings.keys()),
            'errors': errors
        })
        
    except Exception as e:
        logging.error(f"Error building ultra database: {e}")
        return jsonify({'error': f'Database build error: {str(e)}'}), 500

@app.route('/database-status')
def database_status():
    """Get database status"""
    try:
        students = get_all_students()
        
        status = {
            'total_students': len(students),
            'students_with_photos': len([s for s in students if s['photo_url']]),
            'ultra_encodings': len(ultra_robust_recognizer.face_encodings),
            'encoded_students': list(ultra_robust_recognizer.face_encodings.keys()),
            'students_without_encodings': []
        }
        
        for student in students:
            if str(student['student_id']) not in ultra_robust_recognizer.face_encodings:
                status['students_without_encodings'].append({
                    'student_id': student['student_id'],
                    'name': student['name'],
                    'has_photo': bool(student['photo_url'])
                })
        
        return jsonify(status)
        
    except Exception as e:
        logging.error(f"Error getting database status: {e}")
        return jsonify({'error': f'Status error: {str(e)}'}), 500

@app.template_global()
def confidence_color(confidence):
    """Get color based on confidence level"""
    if confidence >= 95:
        return 'success'
    elif confidence >= 85:
        return 'info'
    elif confidence >= 75:
        return 'warning'
    else:
        return 'danger'

@app.template_global()
def confidence_level_badge(level):
    """Get badge class for confidence level"""
    if level == 'ULTRA_HIGH':
        return 'badge-success'
    elif level == 'HIGH':
        return 'badge-info'
    elif level == 'MEDIUM':
        return 'badge-warning'
    else:
        return 'badge-danger'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8006, debug=True)