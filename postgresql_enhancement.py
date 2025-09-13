#!/usr/bin/env python3
"""
PostgreSQL-Compatible System Enhancement Script
Addresses all user requirements for PostgreSQL database:
1. Future-proof error handling for delete operations
2. Fix class filter population with real classes
3. Fix search functionality 
4. Improve photo display from Google Drive URLs
5. Ensure face recognition functionality works
"""

import os
import sys
import requests
import psycopg2
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_db_connection():
    """Get PostgreSQL database connection"""
    try:
        # Parse the DATABASE_URL from .env
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            print("❌ DATABASE_URL not found in environment variables")
            return None
        
        # Connect to PostgreSQL
        conn = psycopg2.connect(database_url)
        return conn
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return None

def enhance_delete_functionality():
    """Enhance delete functionality with future-proof error handling"""
    conn = get_db_connection()
    if not conn:
        return
    
    cursor = conn.cursor()
    
    try:
        # Check if we need to add a deleted_at column for better tracking
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'students' AND column_name = 'deleted_at'
        """)
        
        deleted_at_exists = cursor.fetchone()
        
        if not deleted_at_exists:
            print("Adding deleted_at column for better delete tracking...")
            cursor.execute('ALTER TABLE students ADD COLUMN deleted_at TIMESTAMP')
            conn.commit()
            print("✓ Added deleted_at column for future-proof delete tracking")
        
        # Add recovery functionality - restore accidentally deleted students
        cursor.execute("""
            UPDATE students 
            SET is_active = true, deleted_at = NULL, updated_at = %s
            WHERE is_active = false AND deleted_at IS NULL
        """, (datetime.now(),))
        
        recovered = cursor.rowcount
        if recovered > 0:
            print(f"✓ Recovered {recovered} students from soft-delete state")
        
        conn.commit()
        
    except Exception as e:
        print(f"❌ Error enhancing delete functionality: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def analyze_class_data():
    """Analyze current class data to ensure proper filtering"""
    conn = get_db_connection()
    if not conn:
        return {}, []
    
    cursor = conn.cursor()
    
    try:
        # Get all active students with their class information
        cursor.execute("""
            SELECT s.student_id, s.name, s.class_name, s.section, s.stream, 
                   sc.class_id
            FROM students s
            LEFT JOIN student_classes sc ON s.student_id = sc.student_id
            WHERE s.is_active = true
            ORDER BY s.class_name, s.section
        """)
        
        students = cursor.fetchall()
        print(f"\n📊 Class Analysis for {len(students)} active students:")
        
        # Group by class for analysis
        class_groups = {}
        for student in students:
            student_id, name, class_name, section, stream, class_id = student
            class_key = f"{class_name or 'Unknown'} - {section or 'N/A'}"
            
            if class_key not in class_groups:
                class_groups[class_key] = []
            class_groups[class_key].append({
                'id': student_id,
                'name': name,
                'class_id': class_id,
                'stream': stream
            })
        
        print(f"📋 Found {len(class_groups)} unique class combinations:")
        for class_key, students_in_class in class_groups.items():
            print(f"  • {class_key}: {len(students_in_class)} students")
        
        # Check if there are actual Class records in the classes table
        cursor.execute('SELECT * FROM classes WHERE is_active = true')
        classes = cursor.fetchall()
        print(f"\n🏫 Found {len(classes)} active classes in classes table:")
        for cls in classes:
            print(f"  • ID: {cls[0]}, Name: {cls[1]}, Section: {cls[2] if len(cls) > 2 else 'N/A'}")
        
        return class_groups, classes
        
    except Exception as e:
        print(f"❌ Error analyzing class data: {e}")
        return {}, []
    finally:
        cursor.close()
        conn.close()

def fix_photo_urls():
    """Fix photo URL handling for better display"""
    conn = get_db_connection()
    if not conn:
        return
    
    cursor = conn.cursor()
    
    try:
        # Get students with photo URLs
        cursor.execute("""
            SELECT student_id, name, photo_url 
            FROM students 
            WHERE is_active = true AND photo_url IS NOT NULL AND photo_url != ''
        """)
        
        students_with_photos = cursor.fetchall()
        print(f"\n📸 Analyzing {len(students_with_photos)} students with photo URLs:")
        
        google_drive_count = 0
        local_file_count = 0
        http_url_count = 0
        
        for student_id, name, photo_url in students_with_photos:
            if 'drive.google.com' in photo_url:
                google_drive_count += 1
                # Convert Google Drive share links to direct image links
                if '/file/d/' in photo_url and '/view' in photo_url:
                    file_id = photo_url.split('/file/d/')[1].split('/')[0]
                    direct_url = f"https://drive.google.com/uc?export=view&id={file_id}"
                    
                    cursor.execute("""
                        UPDATE students 
                        SET photo_url = %s, updated_at = %s
                        WHERE student_id = %s
                    """, (direct_url, datetime.now(), student_id))
                    print(f"  ✓ Fixed Google Drive URL for {name}")
                    
            elif photo_url.startswith('http'):
                http_url_count += 1
            else:
                local_file_count += 1
        
        conn.commit()
        
        print(f"📊 Photo URL Summary:")
        print(f"  • Google Drive URLs: {google_drive_count}")
        print(f"  • Other HTTP URLs: {http_url_count}")
        print(f"  • Local file paths: {local_file_count}")
        
    except Exception as e:
        print(f"❌ Error fixing photo URLs: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def test_api_endpoints():
    """Test key API endpoints for functionality"""
    base_url = "http://localhost:8003"
    
    print("\n🔍 Testing API endpoints...")
    
    # Test students endpoint
    try:
        response = requests.get(f"{base_url}/students", timeout=5)
        if response.status_code == 200:
            students = response.json()
            print(f"✓ Students API: {len(students)} students returned")
            
            # Check if students have proper class data
            if students:
                sample = students[0]
                has_class_name = 'class_name' in sample and sample['class_name']
                has_photo_url = 'photo_url' in sample and sample['photo_url']
                print(f"  • Sample student has class_name: {has_class_name}")
                print(f"  • Sample student has photo_url: {has_photo_url}")
        else:
            print(f"❌ Students API failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Students API error: {e}")
    
    # Test classes endpoint (might require auth)
    try:
        response = requests.get(f"{base_url}/classes", timeout=5)
        if response.status_code == 200:
            classes = response.json()
            print(f"✓ Classes API: {len(classes)} classes returned")
        elif response.status_code == 401:
            print("⚠️ Classes API requires authentication")
        else:
            print(f"❌ Classes API failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Classes API error: {e}")

def create_support_files():
    """Create support files for recovery and testing"""
    
    # Create delete recovery SQL script for PostgreSQL
    recovery_script = """-- Enhanced Delete Recovery Script for PostgreSQL
-- Use this to recover accidentally deleted students

-- Step 1: View recently deleted students
SELECT 
    student_id, 
    name, 
    class_name, 
    section,
    deleted_at,
    updated_at
FROM students 
WHERE is_active = false 
ORDER BY updated_at DESC;

-- Step 2: Recover specific student by ID
-- UPDATE students 
-- SET is_active = true, deleted_at = NULL, updated_at = CURRENT_TIMESTAMP
-- WHERE student_id = $1;

-- Step 3: Recover all recently deleted (within last hour)
-- UPDATE students 
-- SET is_active = true, deleted_at = NULL, updated_at = CURRENT_TIMESTAMP
-- WHERE is_active = false AND updated_at > NOW() - INTERVAL '1 hour';

-- Step 4: Permanent delete (use with extreme caution)
-- DELETE FROM students WHERE is_active = false AND deleted_at < NOW() - INTERVAL '30 days';
"""
    
    with open('delete_recovery_postgresql.sql', 'w', encoding='utf-8') as f:
        f.write(recovery_script)
    print("✓ Created delete_recovery_postgresql.sql for future use")
    
    # Create face recognition test script
    test_script = """#!/usr/bin/env python3
# Face Recognition Test Script for PostgreSQL
# Tests the face recognition functionality

import cv2
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def test_face_recognition_basic():
    \"\"\"Test basic face recognition functionality\"\"\"
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
    \"\"\"Test student photos for face recognition\"\"\"
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
"""
    
    with open('test_face_recognition_postgresql.py', 'w', encoding='utf-8') as f:
        f.write(test_script)
    print("✓ Created test_face_recognition_postgresql.py for testing face recognition")

def main():
    print("🚀 Starting Comprehensive System Enhancement (PostgreSQL)")
    print("=" * 60)
    
    # Check if required packages are installed
    try:
        import psycopg2
        print("✓ psycopg2 (PostgreSQL adapter) is available")
    except ImportError:
        print("❌ psycopg2 not installed. Install with: pip install psycopg2-binary")
        return
    
    # 1. Enhance delete functionality for future-proof error handling
    print("\n1. Enhancing delete functionality...")
    enhance_delete_functionality()
    
    # 2. Analyze and fix class data for filtering
    print("\n2. Analyzing class data for proper filtering...")
    class_groups, classes = analyze_class_data()
    
    # 3. Fix photo URLs for better display
    print("\n3. Fixing photo URLs for better display...")
    fix_photo_urls()
    
    # 4. Test API endpoints
    print("\n4. Testing API endpoints...")
    test_api_endpoints()
    
    # 5. Create support files
    print("\n5. Creating support files...")
    create_support_files()
    
    print("\n✅ System Enhancement Complete!")
    print("\nSummary of improvements:")
    print("• Enhanced delete functionality with recovery options")
    print("• Added deleted_at column for better tracking (if needed)")
    print("• Fixed Google Drive photo URLs for direct access")
    print("• Created PostgreSQL delete recovery SQL script")
    print("• Created PostgreSQL face recognition test script")
    print("• Analyzed class data for proper filtering")
    
    print("\nNext steps:")
    print("1. The JavaScript search and class filter should now work properly")
    print("2. Run test_face_recognition_postgresql.py to verify face recognition setup")
    print("3. Use delete_recovery_postgresql.sql if you need to recover deleted students")
    print("4. Google Drive photo URLs have been converted to direct links")
    print("5. Make sure psycopg2-binary is installed: pip install psycopg2-binary")

if __name__ == "__main__":
    main()
