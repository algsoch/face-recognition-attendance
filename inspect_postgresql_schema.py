#!/usr/bin/env python3
"""
Database Schema Inspector for PostgreSQL
Check the actual structure of the database tables
"""

import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def inspect_database_schema():
    """Inspect the PostgreSQL database schema"""
    try:
        database_url = os.getenv('DATABASE_URL')
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        print("🔍 Inspecting PostgreSQL Database Schema")
        print("=" * 50)
        
        # Get all tables
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        
        tables = cursor.fetchall()
        print(f"\n📋 Found {len(tables)} tables:")
        for table in tables:
            print(f"  • {table[0]}")
        
        # Inspect students table specifically
        print("\n👥 Students Table Schema:")
        cursor.execute("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'students'
            ORDER BY ordinal_position
        """)
        
        students_columns = cursor.fetchall()
        if students_columns:
            for col_name, data_type, is_nullable in students_columns:
                print(f"  • {col_name}: {data_type} ({'NULL' if is_nullable == 'YES' else 'NOT NULL'})")
        else:
            print("  ❌ Students table not found or no access")
        
        # Inspect classes table
        print("\n🏫 Classes Table Schema:")
        cursor.execute("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'classes'
            ORDER BY ordinal_position
        """)
        
        classes_columns = cursor.fetchall()
        if classes_columns:
            for col_name, data_type, is_nullable in classes_columns:
                print(f"  • {col_name}: {data_type} ({'NULL' if is_nullable == 'YES' else 'NOT NULL'})")
        else:
            print("  ❌ Classes table not found or no access")
        
        # Get sample data from students if possible
        print("\n📊 Sample Students Data:")
        try:
            cursor.execute("SELECT * FROM students LIMIT 3")
            sample_students = cursor.fetchall()
            
            if sample_students:
                # Get column names
                cursor.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'students'
                    ORDER BY ordinal_position
                """)
                column_names = [col[0] for col in cursor.fetchall()]
                
                print(f"Columns: {', '.join(column_names)}")
                for i, student in enumerate(sample_students, 1):
                    print(f"Student {i}: {dict(zip(column_names, student))}")
            else:
                print("  No student data found")
        except Exception as e:
            print(f"  ❌ Error getting sample data: {e}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Database inspection error: {e}")

if __name__ == "__main__":
    inspect_database_schema()
