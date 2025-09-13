#!/usr/bin/env python3
"""
Clean Database and Re-import CSV with Proper Google Drive URLs
This script will:
1. Clean the existing students data
2. Re-import CSV with proper Google Drive URL conversion
3. Fix photo URL formatting for direct access
"""

import psycopg2
import pandas as pd
import os
import sys
from datetime import datetime
import re

# Database connection details from .env
DATABASE_URL = "postgresql://doadmin:AVNS_lTjSpSEPTsF1gby4DUx@attendance-app-do-user-19447431-0.d.db.ondigitalocean.com:25060/defaultdb?sslmode=require"

def connect_to_db():
    """Connect to PostgreSQL database"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return None

def clean_existing_data(conn):
    """Clean existing student data"""
    cursor = conn.cursor()
    try:
        # Delete existing students (we'll do a hard delete for clean import)
        cursor.execute("DELETE FROM student_classes")
        cursor.execute("DELETE FROM students")
        
        # Reset auto-increment if exists
        cursor.execute("ALTER SEQUENCE IF EXISTS students_student_id_seq RESTART WITH 1")
        
        conn.commit()
        print("✓ Cleaned existing student data")
        return True
    except Exception as e:
        print(f"❌ Error cleaning data: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()

def convert_google_drive_url(url):
    """Convert Google Drive share URL to direct image URL"""
    if not url or not isinstance(url, str):
        return None
    
    if 'drive.google.com' in url and '/file/d/' in url:
        # Extract file ID from Google Drive URL
        match = re.search(r'/file/d/([a-zA-Z0-9_-]+)', url)
        if match:
            file_id = match.group(1)
            # Convert to direct access URL
            direct_url = f"https://drive.google.com/uc?export=view&id={file_id}"
            return direct_url
    
    return url

def import_csv_data(conn, csv_file_path):
    """Import CSV data with proper photo URL handling"""
    if not os.path.exists(csv_file_path):
        print(f"❌ CSV file not found: {csv_file_path}")
        return False
    
    try:
        # Read CSV file
        df = pd.read_csv(csv_file_path)
        print(f"📄 Read CSV with {len(df)} rows")
        print(f"📋 Columns: {list(df.columns)}")
        
        # Show first few rows for verification
        print("\n🔍 First 3 rows of CSV:")
        print(df.head(3).to_string())
        
        cursor = conn.cursor()
        imported_count = 0
        
        for index, row in df.iterrows():
            try:
                # Extract data with proper column mapping
                class_name = str(row.get('Class', '')).strip()
                section = str(row.get('Section', '')).strip()
                roll_number = str(row.get('Roll Number', '')).strip()
                branch = str(row.get('Branch', '')).strip()
                name = str(row.get('Name', '')).strip()
                photo_url = row.get('Photo', '')
                
                # Skip empty rows
                if not name or name == 'nan':
                    continue
                
                # Convert Google Drive URL if present
                if photo_url and photo_url != 'nan':
                    photo_url = convert_google_drive_url(str(photo_url))
                else:
                    photo_url = None
                
                # Insert student
                cursor.execute("""
                    INSERT INTO students (
                        name, roll_number, class, section, stream, 
                        photo_url, is_active, created_at, updated_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING student_id
                """, (
                    name,
                    roll_number,
                    class_name,
                    section,
                    branch,  # Using branch as stream
                    photo_url,
                    True,
                    datetime.now(),
                    datetime.now()
                ))
                
                student_id = cursor.fetchone()[0]
                imported_count += 1
                
                print(f"✓ Imported: {name} (ID: {student_id}) - Class: {class_name} {section}")
                if photo_url:
                    print(f"  📸 Photo URL: {photo_url[:60]}...")
                
            except Exception as e:
                print(f"❌ Error importing row {index}: {e}")
                print(f"   Row data: {dict(row)}")
                continue
        
        conn.commit()
        print(f"\n✅ Successfully imported {imported_count} students")
        return True
        
    except Exception as e:
        print(f"❌ Error importing CSV: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()

def verify_import(conn):
    """Verify the imported data"""
    cursor = conn.cursor()
    try:
        # Count total students
        cursor.execute("SELECT COUNT(*) FROM students WHERE is_active = true")
        total_count = cursor.fetchone()[0]
        
        # Count students with photos
        cursor.execute("SELECT COUNT(*) FROM students WHERE is_active = true AND photo_url IS NOT NULL")
        photo_count = cursor.fetchone()[0]
        
        # Get sample data
        cursor.execute("""
            SELECT student_id, name, class, section, stream, 
                   CASE 
                       WHEN photo_url IS NOT NULL THEN SUBSTRING(photo_url, 1, 50) || '...'
                       ELSE 'No photo'
                   END as photo_preview
            FROM students 
            WHERE is_active = true 
            ORDER BY student_id 
            LIMIT 5
        """)
        
        samples = cursor.fetchall()
        
        print(f"\n📊 Import Verification:")
        print(f"  • Total active students: {total_count}")
        print(f"  • Students with photos: {photo_count}")
        print(f"  • Photo coverage: {(photo_count/total_count*100):.1f}%")
        
        print(f"\n👥 Sample students:")
        for student in samples:
            student_id, name, class_name, section, stream, photo_preview = student
            print(f"  • {student_id}: {name} - {class_name} {section} ({stream}) - {photo_preview}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error verifying import: {e}")
        return False
    finally:
        cursor.close()

def find_csv_file():
    """Find CSV file in the current directory"""
    csv_files = [f for f in os.listdir('.') if f.endswith('.csv')]
    
    if not csv_files:
        print("❌ No CSV files found in current directory")
        return None
    
    if len(csv_files) == 1:
        print(f"📄 Found CSV file: {csv_files[0]}")
        return csv_files[0]
    
    print("📄 Multiple CSV files found:")
    for i, file in enumerate(csv_files, 1):
        print(f"  {i}. {file}")
    
    try:
        choice = int(input("Enter the number of the CSV file to import: ")) - 1
        if 0 <= choice < len(csv_files):
            return csv_files[choice]
        else:
            print("❌ Invalid choice")
            return None
    except ValueError:
        print("❌ Invalid input")
        return None

def main():
    print("🚀 Clean Database and Re-import CSV with Google Drive URLs")
    print("=" * 60)
    
    # Check if pandas is installed
    try:
        import pandas as pd
    except ImportError:
        print("❌ pandas is not installed. Install with: pip install pandas")
        return
    
    # Connect to database
    conn = connect_to_db()
    if not conn:
        return
    
    try:
        # Find CSV file
        csv_file = find_csv_file()
        if not csv_file:
            csv_file = input("Enter the path to your CSV file: ").strip()
        
        if not csv_file or not os.path.exists(csv_file):
            print("❌ CSV file not found")
            return
        
        print(f"\n📁 Using CSV file: {csv_file}")
        
        # Confirm clean operation
        response = input("\n⚠️  This will DELETE all existing student data. Continue? (yes/no): ")
        if response.lower() != 'yes':
            print("❌ Operation cancelled")
            return
        
        # Clean existing data
        print("\n🧹 Cleaning existing data...")
        if not clean_existing_data(conn):
            return
        
        # Import new data
        print("\n📥 Importing CSV data...")
        if not import_csv_data(conn, csv_file):
            return
        
        # Verify import
        print("\n✅ Verifying import...")
        verify_import(conn)
        
        print("\n🎉 Database clean and re-import completed successfully!")
        print("\nNext steps:")
        print("1. Start the server: python -c \"import uvicorn; from main import app; uvicorn.run(app, host='0.0.0.0', port=8003)\"")
        print("2. Open dashboard: http://localhost:8003/dashboard")
        print("3. Check that students load properly and photos display correctly")
        
    finally:
        conn.close()

if __name__ == "__main__":
    main()
