#!/usr/bin/env python3
# Face Recognition Test Script for PostgreSQL
# Tests the face recognition functionality

import cv2
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def test_face_recognition_basic():
    """Test basic face recognition functionality"""
    try:
        import face_recognition
        print("✓ Face recognition library imported successfully")
        
        # Test camera access
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            print("✓ Camera access working")
            cap.release()
        else:
            print("❌ Camera access failed")
        
        return True
    except ImportError:
        print("❌ Face recognition libraries not installed")
        print("Install with: pip install face-recognition opencv-python")
        return False

def test_student_photos():
    """Test student photos for face recognition"""
    try:
        database_url = os.getenv('DATABASE_URL')
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT student_id, name, photo_url 
            FROM students 
            WHERE is_active = true AND photo_url IS NOT NULL AND photo_url != ''
            LIMIT 5
        ''')
        
        students = cursor.fetchall()
        print(f"Testing {len(students)} student photos...")
        
        for student_id, name, photo_url in students:
            if photo_url.startswith('http'):
                print(f"✓ {name}: Remote URL - {photo_url[:50]}...")
            else:
                if os.path.exists(photo_url):
                    print(f"✓ {name}: Local file exists")
                else:
                    print(f"❌ {name}: Local file not found - {photo_url}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Database connection error: {e}")

if __name__ == "__main__":
    print("🧠 Face Recognition System Test (PostgreSQL)")
    print("=" * 50)
    
    if test_face_recognition_basic():
        test_student_photos()
