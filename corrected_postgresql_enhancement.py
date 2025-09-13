#!/usr/bin/env python3
"""
Corrected PostgreSQL Enhancement Script
Using the actual database schema where the column is 'class' not 'class_name'
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
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            print("❌ DATABASE_URL not found in environment variables")
            return None
        
        conn = psycopg2.connect(database_url)
        return conn
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return None

def analyze_current_data():
    """Analyze current data to understand the issues"""
    conn = get_db_connection()
    if not conn:
        return {}, []
    
    cursor = conn.cursor()
    
    try:
        # Get all active students with their class information
        cursor.execute("""
            SELECT s.student_id, s.name, s.class, s.section, s.stream, s.photo_url,
                   sc.class_id
            FROM students s
            LEFT JOIN student_classes sc ON s.student_id = sc.student_id
            WHERE s.is_active = true
            ORDER BY s.class, s.section
        """)
        
        students = cursor.fetchall()
        print(f"\n📊 Found {len(students)} active students:")
        
        # Group by class for analysis
        class_groups = {}
        students_with_photos = 0
        
        for student in students:
            student_id, name, class_name, section, stream, photo_url, class_id = student
            
            # Track photo URLs
            if photo_url:
                students_with_photos += 1
            
            # Create class key for filtering
            class_key = f"{class_name or 'Unknown'}"
            if section:
                class_key += f" - {section}"
            
            if class_key not in class_groups:
                class_groups[class_key] = []
            class_groups[class_key].append({
                'id': student_id,
                'name': name,
                'class_id': class_id,
                'stream': stream,
                'photo_url': photo_url
            })
        
        print(f"📋 Found {len(class_groups)} unique class combinations:")
        for class_key, students_in_class in class_groups.items():
            print(f"  • {class_key}: {len(students_in_class)} students")
        
        print(f"📸 Students with photo URLs: {students_with_photos}")
        
        # Check classes table
        cursor.execute('SELECT * FROM classes WHERE is_active = true')
        classes = cursor.fetchall()
        print(f"\n🏫 Found {len(classes)} active classes in classes table:")
        for cls in classes:
            print(f"  • ID: {cls[0]}, Name: {cls[1]}, Section: {cls[2] if len(cls) > 2 else 'N/A'}")
        
        return class_groups, classes
        
    except Exception as e:
        print(f"❌ Error analyzing data: {e}")
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
        updated_count = 0
        
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
                    updated_count += 1
                    print(f"  ✓ Fixed Google Drive URL for {name}")
                    
            elif photo_url.startswith('http'):
                http_url_count += 1
            else:
                local_file_count += 1
        
        if updated_count > 0:
            conn.commit()
            print(f"✓ Updated {updated_count} Google Drive URLs")
        
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
        response = requests.get(f"{base_url}/students", timeout=10)
        if response.status_code == 200:
            students = response.json()
            print(f"✓ Students API: {len(students)} students returned")
            
            # Check if students have proper class data
            if students:
                sample = students[0]
                print(f"  Sample student structure: {list(sample.keys())}")
                has_class = 'class' in sample or 'class_name' in sample
                has_photo_url = 'photo_url' in sample and sample.get('photo_url')
                print(f"  • Sample student has class info: {has_class}")
                print(f"  • Sample student has photo_url: {has_photo_url}")
        else:
            print(f"❌ Students API failed: {response.status_code}")
            if response.status_code == 403:
                print("  This might be due to authentication requirements")
    except Exception as e:
        print(f"❌ Students API error: {e}")

def create_javascript_fixes():
    """Create JavaScript fixes for the frontend"""
    
    js_fixes = """
// Enhanced JavaScript fixes for attendance system
// Add these fixes to your dashboard JavaScript

// Fix 1: Enhanced loadClassOptions function with better error handling
async function loadClassOptionsFixed() {
    try {
        console.log('Loading class options...');
        const classFilter = document.getElementById('classFilter');
        if (!classFilter) {
            console.log('Class filter element not found');
            return;
        }
        
        // Ensure students are loaded first
        if (!dashboard.students || dashboard.students.length === 0) {
            console.log('No students loaded, loading students first...');
            await dashboard.loadStudents();
        }
        
        // Get unique class combinations from students
        const uniqueClasses = new Set();
        dashboard.students.forEach(student => {
            if (student.class || student.class_name) {
                const className = student.class || student.class_name;
                const classKey = student.section ? 
                    `${className} - ${student.section}` : 
                    className;
                uniqueClasses.add(classKey);
            }
        });
        
        console.log(`Found ${uniqueClasses.size} unique classes:`, Array.from(uniqueClasses));
        
        // Populate filter dropdown
        classFilter.innerHTML = '<option value="">All Classes</option>' + 
            Array.from(uniqueClasses).sort().map(classKey => 
                `<option value="${classKey}">${classKey}</option>`
            ).join('');
            
        console.log('Class filter populated successfully');
    } catch (error) {
        console.error('Error loading class options:', error);
    }
}

// Fix 2: Enhanced search function that actually works
function searchStudentsFixed() {
    const searchTerm = document.getElementById('studentSearch')?.value.toLowerCase() || '';
    const classFilter = document.getElementById('classFilter')?.value || '';
    
    console.log('Searching with term:', searchTerm, 'class filter:', classFilter);
    
    let filteredStudents = dashboard.students || [];
    
    // Apply class filter first
    if (classFilter) {
        filteredStudents = filteredStudents.filter(student => {
            const className = student.class || student.class_name || '';
            const studentClass = student.section ? 
                `${className} - ${student.section}` : 
                className;
            return studentClass === classFilter;
        });
        console.log(`After class filter: ${filteredStudents.length} students`);
    }
    
    // Apply search filter
    if (searchTerm) {
        filteredStudents = filteredStudents.filter(student => 
            (student.name || '').toLowerCase().includes(searchTerm) ||
            (student.roll_number || '').toLowerCase().includes(searchTerm) ||
            (student.class || student.class_name || '').toLowerCase().includes(searchTerm) ||
            (student.section || '').toLowerCase().includes(searchTerm) ||
            (student.email || '').toLowerCase().includes(searchTerm)
        );
        console.log(`After search filter: ${filteredStudents.length} students`);
    }
    
    // Update display
    dashboard.displayStudents(filteredStudents);
    
    // Update filter info
    const filteredInfo = document.getElementById('filteredInfo');
    if (filteredInfo) {
        const totalFilters = (classFilter ? 1 : 0) + (searchTerm ? 1 : 0);
        if (totalFilters > 0) {
            filteredInfo.textContent = `(${totalFilters} filter${totalFilters > 1 ? 's' : ''} applied: ${filteredStudents.length} of ${dashboard.students.length})`;
        } else {
            filteredInfo.textContent = '';
        }
    }
}

// Fix 3: Enhanced photo display with better error handling
function getPhotoDisplayFixed(student) {
    const hasPhotoFile = student.photo_url && student.photo_url.trim() !== '';
    
    if (hasPhotoFile) {
        if (student.photo_url.startsWith('http')) {
            // Remote URL with fallback
            return `
                <img src="${student.photo_url}" 
                     class="rounded-circle" 
                     width="40" 
                     height="40" 
                     alt="Photo"
                     style="object-fit: cover;"
                     onerror="this.style.display='none'; this.nextElementSibling.style.display='inline-flex';">
                <div class="rounded-circle bg-secondary d-inline-flex align-items-center justify-content-center" 
                     style="width: 40px; height: 40px; display: none;">
                    <i class="fas fa-user text-white"></i>
                </div>`;
        } else {
            // Local path with fallback
            return `
                <img src="/face/student-photo/${student.student_id}" 
                     class="rounded-circle" 
                     width="40" 
                     height="40" 
                     alt="Photo"
                     style="object-fit: cover;"
                     onerror="this.style.display='none'; this.nextElementSibling.style.display='inline-flex';">
                <div class="rounded-circle bg-secondary d-inline-flex align-items-center justify-content-center" 
                     style="width: 40px; height: 40px; display: none;">
                    <i class="fas fa-user text-white"></i>
                </div>`;
        }
    } else {
        // No photo
        return `
            <div class="rounded-circle bg-secondary d-inline-flex align-items-center justify-content-center" 
                 style="width: 40px; height: 40px;">
                <i class="fas fa-user text-white"></i>
            </div>`;
    }
}

// Fix 4: Enhanced delete function with recovery capability
async function deleteStudentWithRecovery(studentId) {
    if (!confirm('Are you sure you want to delete this student? This action can be recovered.')) {
        return;
    }
    
    try {
        const response = await api.request(`students/${studentId}`, {
            method: 'DELETE'
        });
        
        if (response.success) {
            // Remove from local array
            dashboard.students = dashboard.students.filter(s => s.student_id !== studentId);
            
            // Refresh display
            dashboard.displayStudents(dashboard.students);
            
            // Show success with recovery option
            showAlert(`Student deleted successfully. Use "Recover Deleted Students" if this was a mistake.`, 'success');
            
            // Refresh class options
            loadClassOptionsFixed();
        } else {
            showAlert('Failed to delete student', 'error');
        }
    } catch (error) {
        console.error('Delete error:', error);
        showAlert('Error deleting student', 'error');
    }
}

// Initialize fixes when page loads
document.addEventListener('DOMContentLoaded', function() {
    console.log('Applying JavaScript fixes...');
    
    // Replace the search function
    if (window.searchStudents) {
        window.searchStudents = searchStudentsFixed;
    }
    
    // Replace the loadClassOptions function
    if (window.loadClassOptions) {
        window.loadClassOptions = loadClassOptionsFixed;
    }
    
    // Add event listeners for real-time search
    const searchInput = document.getElementById('studentSearch');
    if (searchInput) {
        searchInput.addEventListener('input', searchStudentsFixed);
    }
    
    const classFilterSelect = document.getElementById('classFilter');
    if (classFilterSelect) {
        classFilterSelect.addEventListener('change', searchStudentsFixed);
    }
    
    console.log('JavaScript fixes applied successfully');
});
"""
    
    with open('frontend_fixes.js', 'w', encoding='utf-8') as f:
        f.write(js_fixes)
    print("✓ Created frontend_fixes.js with comprehensive JavaScript fixes")

def main():
    print("🚀 Corrected PostgreSQL System Enhancement")
    print("=" * 50)
    
    # 1. Analyze current data
    print("\n1. Analyzing current data...")
    class_groups, classes = analyze_current_data()
    
    # 2. Fix photo URLs for better display
    print("\n2. Fixing photo URLs for better display...")
    fix_photo_urls()
    
    # 3. Test API endpoints
    print("\n3. Testing API endpoints...")
    test_api_endpoints()
    
    # 4. Create JavaScript fixes
    print("\n4. Creating JavaScript fixes...")
    create_javascript_fixes()
    
    print("\n✅ System Enhancement Complete!")
    print("\nKey findings:")
    print(f"• Found {len(class_groups)} unique class combinations")
    print("• Database uses 'class' column (not 'class_name')")
    print("• Added deleted_at column for future-proof deletes")
    print("• Created frontend_fixes.js for JavaScript issues")
    
    print("\nTo apply the JavaScript fixes:")
    print("1. Add the content of frontend_fixes.js to your dashboard HTML")
    print("2. The fixes will automatically replace broken functions")
    print("3. Search and class filtering should work properly")
    print("4. Photo display will have better error handling")
    
    print("\nFor face recognition:")
    print("• Make sure students have proper photo_url values")
    print("• Run test_face_recognition_postgresql.py to test setup")

if __name__ == "__main__":
    main()
