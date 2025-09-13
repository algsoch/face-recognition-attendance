#!/usr/bin/env python3
"""
CSV Import Script with Google Drive URL Support
This script helps import CSV files with Google Drive photo URLs
"""

import pandas as pd
import psycopg2
import os
from dotenv import load_dotenv
import re

def convert_google_drive_url(url):
    """Convert Google Drive share URL to direct image URL"""
    if 'drive.google.com' in url and '/file/d/' in url:
        # Extract file ID from URL like: https://drive.google.com/file/d/FILE_ID/view?usp=sharing
        match = re.search(r'/file/d/([a-zA-Z0-9_-]+)', url)
        if match:
            file_id = match.group(1)
            # Convert to direct download URL
            return f"https://drive.google.com/uc?export=view&id={file_id}"
    return url

def import_csv_with_photos(csv_file_path):
    """Import CSV file with photo URL support"""
    
    if not os.path.exists(csv_file_path):
        print(f"❌ CSV file not found: {csv_file_path}")
        return
    
    try:
        # Read CSV file
        df = pd.read_csv(csv_file_path)
        print(f"📄 Read CSV with {len(df)} rows")
        print(f"📋 Columns: {list(df.columns)}")
        
        # Show sample data
        print("\n📊 Sample data:")
        print(df.head())
        
        # Connect to database
        load_dotenv()
        db_url = os.getenv('DATABASE_URL')
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        
        # Clear existing data if requested
        choice = input("\n❓ Do you want to clear existing students first? (y/n): ").lower()
        if choice == 'y':
            cursor.execute('DELETE FROM students')
            print("🗑️ Cleared existing students")
        
        # Import new data
        imported = 0
        for index, row in df.iterrows():
            try:
                # Map CSV columns to database fields
                class_name = row.get('Class', '')
                section = row.get('Section', '')
                roll_number = str(row.get('Roll Number', ''))
                branch = row.get('Branch', '')
                name = row.get('Name', '')
                photo_url = row.get('Photo', '')
                
                # Convert Google Drive URLs
                if photo_url and 'drive.google.com' in photo_url:
                    original_url = photo_url
                    photo_url = convert_google_drive_url(photo_url)
                    print(f"🔄 Converted Google Drive URL for {name}")
                    print(f"   Original: {original_url[:60]}...")
                    print(f"   Direct:   {photo_url[:60]}...")
                
                # Insert into database
                cursor.execute('''
                    INSERT INTO students (
                        class, section, roll_number, branch, name, photo_url,
                        is_active, created_at, updated_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                ''', (class_name, section, roll_number, branch, name, photo_url, True))
                
                imported += 1
                
            except Exception as e:
                print(f"❌ Error importing row {index}: {e}")
                continue
        
        conn.commit()
        print(f"\n✅ Successfully imported {imported} students")
        
        # Show summary
        cursor.execute('SELECT COUNT(*) FROM students WHERE is_active = TRUE')
        total_active = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM students WHERE photo_url IS NOT NULL AND photo_url != %s', ('',))
        with_photos = cursor.fetchone()[0]
        
        print(f"📊 Database Summary:")
        print(f"   • Total active students: {total_active}")
        print(f"   • Students with photos: {with_photos}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error importing CSV: {e}")

def list_csv_files():
    """List available CSV files in the current directory"""
    csv_files = [f for f in os.listdir('.') if f.endswith('.csv')]
    if csv_files:
        print("📁 Available CSV files:")
        for i, file in enumerate(csv_files, 1):
            print(f"   {i}. {file}")
        return csv_files
    else:
        print("❌ No CSV files found in current directory")
        return []

def main():
    print("📁 CSV Import Tool with Google Drive URL Support")
    print("=" * 50)
    
    # List available CSV files
    csv_files = list_csv_files()
    
    if not csv_files:
        csv_path = input("\n📂 Enter the full path to your CSV file: ").strip()
        if csv_path:
            import_csv_with_photos(csv_path)
    else:
        choice = input(f"\n❓ Select a CSV file (1-{len(csv_files)}) or enter custom path: ").strip()
        
        if choice.isdigit() and 1 <= int(choice) <= len(csv_files):
            selected_file = csv_files[int(choice) - 1]
            print(f"📄 Selected: {selected_file}")
            import_csv_with_photos(selected_file)
        else:
            # Custom path
            if os.path.exists(choice):
                import_csv_with_photos(choice)
            else:
                print(f"❌ File not found: {choice}")

if __name__ == "__main__":
    main()
