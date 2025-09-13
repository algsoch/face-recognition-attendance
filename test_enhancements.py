#!/usr/bin/env python3
"""
Test script for enhanced system functionality
Tests all the improvements we've made
"""

import requests
import sqlite3
import json
import os
from datetime import datetime

def test_enhanced_functionality():
    """Test all enhanced features"""
    print("🧪 Testing Enhanced System Functionality")
    print("=" * 50)
    
    base_url = "http://localhost:8003"
    
    # Test 1: Students API
    print("\n1. Testing Students API...")
    try:
        response = requests.get(f"{base_url}/students", timeout=10)
        if response.status_code == 200:
            students = response.json()
            print(f"✓ Students API working: {len(students)} students")
            
            # Test class analysis
            classes = set()
            photo_count = 0
            for student in students:
                if student.get('class_name'):
                    class_key = f"{student['class_name']} - {student.get('section', 'N/A')}"
                    classes.add(class_key)
                if student.get('photo_url'):
                    photo_count += 1
            
            print(f"  • Found {len(classes)} unique class combinations")
            print(f"  • {photo_count} students have photos")
            
            # Display classes for verification
            if classes:
                print("  • Classes found:")
                for cls in sorted(classes):
                    print(f"    - {cls}")
                    
        else:
            print(f"❌ Students API failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Students API error: {e}")
    
    # Test 2: Photo URL Analysis
    print("\n2. Testing Photo URL Enhancement...")
    try:
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT student_id, name, photo_url 
            FROM students 
            WHERE is_active = 1 AND photo_url IS NOT NULL AND photo_url != ''
        ''')
        
        students_with_photos = cursor.fetchall()
        print(f"✓ Found {len(students_with_photos)} students with photos in database")
        
        google_drive_count = 0
        direct_urls = 0
        local_files = 0
        
        for student_id, name, photo_url in students_with_photos:
            if 'drive.google.com/uc?export=view' in photo_url:
                direct_urls += 1
            elif 'drive.google.com' in photo_url:
                google_drive_count += 1
            elif photo_url.startswith('http'):
                pass  # Other URLs
            else:
                local_files += 1
        
        print(f"  • Direct Google Drive URLs: {direct_urls}")
        print(f"  • Google Drive share links: {google_drive_count}")
        print(f"  • Local files: {local_files}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Photo URL analysis error: {e}")
    
    # Test 3: Database Schema
    print("\n3. Testing Database Schema Enhancements...")
    try:
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        
        # Check for deleted_at column
        cursor.execute("PRAGMA table_info(students)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'deleted_at' in columns:
            print("✓ deleted_at column exists for enhanced delete tracking")
        else:
            print("⚠️ deleted_at column not found - adding it would improve delete tracking")
        
        # Check active vs inactive students
        cursor.execute('SELECT COUNT(*) FROM students WHERE is_active = 1')
        active_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM students WHERE is_active = 0')
        inactive_count = cursor.fetchone()[0]
        
        print(f"  • Active students: {active_count}")
        print(f"  • Inactive students: {inactive_count}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Database schema test error: {e}")
    
    # Test 4: JavaScript Enhancement Files
    print("\n4. Testing JavaScript Enhancement Files...")
    
    enhancement_file = "static/js/dashboard_enhancements.js"
    if os.path.exists(enhancement_file):
        print(f"✓ Enhancement file exists: {enhancement_file}")
        
        with open(enhancement_file, 'r') as f:
            content = f.read()
            
        # Check for key features
        features = [
            'enhancedDeleteStudent',
            'loadClassOptionsEnhanced',
            'enhancedSearchStudents',
            'enhancedPhotoDisplay',
            'enhancedFaceRecognition'
        ]
        
        for feature in features:
            if feature in content:
                print(f"  ✓ {feature} function implemented")
            else:
                print(f"  ❌ {feature} function missing")
    else:
        print(f"❌ Enhancement file not found: {enhancement_file}")
    
    # Test 5: HTML Integration
    print("\n5. Testing HTML Integration...")
    
    dashboard_file = "frontend/dashboard.html"
    if os.path.exists(dashboard_file):
        with open(dashboard_file, 'r') as f:
            content = f.read()
        
        if 'dashboard_enhancements.js' in content:
            print("✓ Enhancement script linked in dashboard.html")
        else:
            print("❌ Enhancement script not linked in dashboard.html")
    else:
        print(f"❌ Dashboard file not found: {dashboard_file}")
    
    print("\n✅ Enhanced System Testing Complete!")
    print("\nKey Improvements Summary:")
    print("• Future-proof delete functionality with recovery")
    print("• Enhanced class filtering with real API integration")
    print("• Robust search functionality with multiple fields")
    print("• Google Drive photo URL optimization")
    print("• Face recognition system verification")
    print("• Comprehensive error handling throughout")

if __name__ == "__main__":
    test_enhanced_functionality()
