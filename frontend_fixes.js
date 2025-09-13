
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
