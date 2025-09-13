"""
Enhanced CSV import system with proper teacher isolation and Google Drive URL handling
"""
import pandas as pd
import re
from typing import List, Dict, Any
from backend.database import SessionLocal
from backend.crud import create_student, get_teacher_by_id, get_student_by_roll_number
from backend.schemas import StudentCreate


def convert_google_drive_url(url: str) -> str:
    """Convert Google Drive share URL to direct access URL"""
    if not url or 'drive.google.com' not in url:
        return url
    
    # Extract file ID from various Google Drive URL formats
    patterns = [
        r'/file/d/([a-zA-Z0-9_-]+)',
        r'id=([a-zA-Z0-9_-]+)',
        r'/d/([a-zA-Z0-9_-]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            file_id = match.group(1)
            return f'https://drive.google.com/uc?export=view&id={file_id}'
    
    return url


def validate_csv_columns(df: pd.DataFrame) -> List[str]:
    """Validate CSV has required columns"""
    required_columns = ['Class', 'Section', 'Roll Number', 'Branch', 'Name', 'Photo']
    missing_columns = []
    
    for col in required_columns:
        if col not in df.columns:
            missing_columns.append(col)
    
    return missing_columns


def import_students_from_csv(file_path: str, teacher_id: str) -> Dict[str, Any]:
    """
    Import students from CSV file for a specific teacher
    
    Args:
        file_path: Path to CSV file
        teacher_id: Teacher ID (string) to associate students with
    
    Returns:
        Dictionary with import results
    """
    db = SessionLocal()
    try:
        # Verify teacher exists
        teacher = get_teacher_by_id(db, teacher_id)
        if not teacher:
            return {
                'success': False,
                'error': f'Teacher with ID {teacher_id} not found'
            }
        
        # Read CSV file
        try:
            df = pd.read_csv(file_path)
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to read CSV file: {str(e)}'
            }
        
        # Validate columns
        missing_columns = validate_csv_columns(df)
        if missing_columns:
            return {
                'success': False,
                'error': f'Missing required columns: {missing_columns}'
            }
        
        print(f"CSV columns found: {list(df.columns)}")
        
        # Process each row
        imported_count = 0
        duplicate_count = 0
        error_count = 0
        errors = []
        
        for index, row in df.iterrows():
            try:
                # Extract data from row
                class_name = str(row['Class']).strip()
                section = str(row['Section']).strip()
                roll_number = str(row['Roll Number']).strip()
                branch = str(row['Branch']).strip()
                name = str(row['Name']).strip()
                photo_url = str(row['Photo']).strip()
                
                # Skip empty rows
                if not name or not roll_number:
                    continue
                
                # Check if student already exists for this teacher
                existing_student = get_student_by_roll_number(db, roll_number)
                if existing_student:
                    print(f"Student already exists: {name} (Roll: {roll_number})")
                    duplicate_count += 1
                    continue
                
                # Convert Google Drive URL
                if photo_url and photo_url != 'nan':
                    photo_url = convert_google_drive_url(photo_url)
                    print(f"Converted photo URL for {name}: {photo_url[:60]}...")
                else:
                    photo_url = None
                
                # Create student data
                student_data = StudentCreate(
                    roll_number=roll_number,
                    name=name,
                    class_name=class_name,
                    section=section,
                    branch=branch,
                    photo_url=photo_url
                )
                
                # Create student
                created_student = create_student(db, student_data, teacher_id)
                if created_student:
                    print(f"✅ Imported: {name} (Roll: {roll_number}) -> {created_student.student_id}")
                    imported_count += 1
                else:
                    error_count += 1
                    errors.append(f"Failed to create student: {name}")
                
            except Exception as e:
                error_count += 1
                errors.append(f"Error processing row {index + 1}: {str(e)}")
                print(f"Error processing {name if 'name' in locals() else 'unknown'}: {str(e)}")
        
        # Return results
        return {
            'success': True,
            'imported_count': imported_count,
            'duplicate_count': duplicate_count,
            'error_count': error_count,
            'errors': errors,
            'total_processed': len(df),
            'message': f"Import completed: {imported_count}/{len(df)} students imported, {duplicate_count} duplicates skipped"
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f'Import failed: {str(e)}'
        }
    finally:
        db.close()


def bulk_import_students_by_teacher(csv_data: List[Dict], teacher_id: str) -> Dict[str, Any]:
    """
    Bulk import students from CSV data for a specific teacher
    
    Args:
        csv_data: List of dictionaries containing student data
        teacher_id: Teacher ID to associate students with
    
    Returns:
        Dictionary with import results
    """
    db = SessionLocal()
    try:
        # Verify teacher exists
        teacher = get_teacher_by_id(db, teacher_id)
        if not teacher:
            return {
                'success': False,
                'error': f'Teacher with ID {teacher_id} not found'
            }
        
        imported_count = 0
        duplicate_count = 0
        error_count = 0
        errors = []
        
        for student_data in csv_data:
            try:
                # Check if student already exists for this teacher
                existing_student = get_student_by_roll_and_teacher(
                    db, student_data['roll_number'], teacher_id
                )
                if existing_student:
                    duplicate_count += 1
                    continue
                
                # Convert Google Drive URL
                if student_data.get('photo_url'):
                    student_data['photo_url'] = convert_google_drive_url(student_data['photo_url'])
                
                # Create student
                student_create = StudentCreate(**student_data)
                created_student = create_student(db, student_create, teacher_id)
                
                if created_student:
                    imported_count += 1
                else:
                    error_count += 1
                    errors.append(f"Failed to create student: {student_data.get('name', 'Unknown')}")
                
            except Exception as e:
                error_count += 1
                errors.append(f"Error processing student {student_data.get('name', 'Unknown')}: {str(e)}")
        
        return {
            'success': True,
            'imported_count': imported_count,
            'duplicate_count': duplicate_count,
            'error_count': error_count,
            'errors': errors,
            'total_processed': len(csv_data)
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f'Bulk import failed: {str(e)}'
        }
    finally:
        db.close()
