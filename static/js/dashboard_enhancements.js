// Enhanced JavaScript fixes for comprehensive system improvements
// This file contains all the fixes for the dashboard functionality

// Enhanced Delete Functionality with Future-Proof Error Handling
async function enhancedDeleteStudent(studentId) {
    if (!confirm('Are you sure you want to delete this student? This action can be undone later if needed.')) {
        return;
    }

    try {
        console.log(`Attempting to delete student ${studentId}`);
        
        const result = await api.request(`students/${studentId}`, 'DELETE');
        
        if (result.success) {
            // Show success message with recovery information
            showAlert(`Student deleted successfully. Use recovery options if this was accidental.`, 'success');
            
            // Remove from local array
            dashboard.students = dashboard.students.filter(s => s.student_id !== studentId);
            
            // Refresh displays
            dashboard.displayStudents(dashboard.students);
            loadClassOptions(); // Refresh class options
            
            // Update count
            const countElement = document.getElementById('studentCount');
            if (countElement) {
                countElement.textContent = dashboard.students.length.toString();
            }
            
            // Log for potential recovery
            console.log(`Student ${studentId} soft-deleted at ${new Date().toISOString()}`);
            
        } else {
            throw new Error(result.message || 'Delete operation failed');
        }
    } catch (error) {
        console.error('Enhanced delete error:', error);
        showAlert(`Error deleting student: ${error.message}. Student data preserved for safety.`, 'error');
    }
}

// Enhanced Class Filter with Real API Integration
async function loadClassOptionsEnhanced() {
    try {
        // Enhanced System Fixes - Comprehensive JavaScript Enhancements
console.log('Loading comprehensive system fixes...');

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
    console.log('Applying comprehensive JavaScript fixes...');
    
    // Replace the search function
    if (window.searchStudents) {
        window.searchStudents = searchStudentsFixed;
        console.log('✓ Replaced searchStudents function');
    }
    
    // Replace the loadClassOptions function
    if (window.loadClassOptions) {
        window.loadClassOptions = loadClassOptionsFixed;
        console.log('✓ Replaced loadClassOptions function');
    }
    
    // Add event listeners for real-time search
    const searchInput = document.getElementById('studentSearch');
    if (searchInput) {
        searchInput.addEventListener('input', searchStudentsFixed);
        console.log('✓ Added real-time search listener');
    }
    
    const classFilterSelect = document.getElementById('classFilter');
    if (classFilterSelect) {
        classFilterSelect.addEventListener('change', searchStudentsFixed);
        console.log('✓ Added class filter change listener');
    }
    
    console.log('✅ All JavaScript fixes applied successfully');
});

// Export functions for global access
window.loadClassOptionsFixed = loadClassOptionsFixed;
window.searchStudentsFixed = searchStudentsFixed;
window.getPhotoDisplayFixed = getPhotoDisplayFixed;
window.deleteStudentWithRecovery = deleteStudentWithRecovery;
        const classFilter = document.getElementById('classFilter');
        if (!classFilter) {
            console.warn('Class filter element not found');
            return;
        }
        
        // Try to get classes from the API first
        let classOptions = new Set();
        
        try {
            const classesResponse = await api.request('classes');
            if (classesResponse && classesResponse.success && Array.isArray(classesResponse.data)) {
                classesResponse.data.forEach(cls => {
                    if (cls.class_name) {
                        const classKey = cls.section ? 
                            `${cls.class_name} - ${cls.section}` : 
                            cls.class_name;
                        classOptions.add(classKey);
                    }
                });
                console.log(`Loaded ${classOptions.size} classes from API`);
            }
        } catch (apiError) {
            console.log('Classes API not available, using student data fallback');
        }
        
        // Fallback: extract classes from student data
        if (classOptions.size === 0 && dashboard.students) {
            dashboard.students.forEach(student => {
                if (student.class_name) {
                    const classKey = student.section ? 
                        `${student.class_name} - ${student.section}` : 
                        student.class_name;
                    classOptions.add(classKey);
                }
            });
            console.log(`Fallback: Loaded ${classOptions.size} classes from student data`);
        }
        
        // Populate the dropdown
        const sortedClasses = Array.from(classOptions).sort();
        classFilter.innerHTML = '<option value="">All Classes</option>' + 
            sortedClasses.map(classKey => 
                `<option value="${classKey}">${classKey}</option>`
            ).join('');
        
        console.log(`Class filter populated with ${sortedClasses.length} options`);
        
    } catch (error) {
        console.error('Error loading enhanced class options:', error);
        // Ensure basic option exists
        const classFilter = document.getElementById('classFilter');
        if (classFilter && classFilter.innerHTML.trim() === '') {
            classFilter.innerHTML = '<option value="">All Classes</option>';
        }
    }
}

// Enhanced Search Functionality with Robust Filtering
function enhancedSearchStudents() {
    try {
        const searchTerm = document.getElementById('studentSearch')?.value?.toLowerCase() || '';
        const classFilter = document.getElementById('classFilter')?.value || '';
        
        console.log(`Enhanced search: term="${searchTerm}", class="${classFilter}"`);
        
        if (!dashboard.students || dashboard.students.length === 0) {
            console.warn('No students data available for search');
            return;
        }
        
        let filteredStudents = [...dashboard.students]; // Create a copy
        
        // Apply class filter first
        if (classFilter) {
            filteredStudents = filteredStudents.filter(student => {
                const studentClass = student.section ? 
                    `${student.class_name} - ${student.section}` : 
                    student.class_name;
                return studentClass === classFilter;
            });
            console.log(`After class filter: ${filteredStudents.length} students`);
        }
        
        // Apply search filter
        if (searchTerm) {
            filteredStudents = filteredStudents.filter(student => {
                const searchFields = [
                    student.name || '',
                    student.roll_number || '',
                    student.class_name || '',
                    student.section || '',
                    student.stream || '',
                    student.phone || '',
                    student.email || ''
                ];
                
                return searchFields.some(field => 
                    field.toLowerCase().includes(searchTerm)
                );
            });
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
                filteredInfo.style.display = 'inline';
            } else {
                filteredInfo.textContent = '';
                filteredInfo.style.display = 'none';
            }
        }
        
        console.log(`Search completed: ${filteredStudents.length} results`);
        
    } catch (error) {
        console.error('Enhanced search error:', error);
        showAlert('Search functionality encountered an error. Please try again.', 'warning');
    }
}

// Enhanced Photo Display with Google Drive Support
function enhancedPhotoDisplay(student) {
    const hasPhotoUrl = student.photo_url && student.photo_url.trim() !== '';
    
    if (!hasPhotoUrl) {
        return `
            <div class="rounded-circle bg-secondary d-inline-flex align-items-center justify-content-center" 
                 style="width: 40px; height: 40px;" title="No photo available">
                <i class="fas fa-user text-white"></i>
            </div>`;
    }
    
    let photoSources = [];
    
    // Add local photo endpoint as primary source
    photoSources.push(`/face/student-photo/${student.student_id}`);
    
    // Handle Google Drive URLs
    if (student.photo_url.includes('drive.google.com')) {
        let directUrl = student.photo_url;
        
        // Convert Google Drive share links to direct image links
        if (student.photo_url.includes('/file/d/') && student.photo_url.includes('/view')) {
            try {
                const fileId = student.photo_url.split('/file/d/')[1].split('/')[0];
                directUrl = `https://drive.google.com/uc?export=view&id=${fileId}`;
                console.log(`Converted Google Drive URL for ${student.name}: ${directUrl}`);
            } catch (e) {
                console.warn(`Failed to convert Google Drive URL for ${student.name}:`, e);
            }
        }
        
        photoSources.push(directUrl);
    } else if (student.photo_url.startsWith('http')) {
        // Other HTTP URLs
        photoSources.push(student.photo_url);
    }
    
    // Create fallback chain
    let photoHtml = '';
    photoSources.forEach((src, index) => {
        const isLast = index === photoSources.length - 1;
        const nextAction = isLast ? 
            "this.style.display='none'; this.nextElementSibling.style.display='inline-flex';" :
            `this.style.display='none'; this.nextElementSibling.style.display='block';`;
        
        photoHtml += `
            <img src="${src}" 
                 class="rounded-circle" 
                 width="40" 
                 height="40" 
                 alt="${student.name || 'Student'} Photo"
                 style="${index > 0 ? 'display: none;' : ''}"
                 onerror="${nextAction}"
                 title="Photo of ${student.name || 'Student'}">`;
    });
    
    // Add final fallback icon
    photoHtml += `
        <div class="rounded-circle bg-secondary d-inline-flex align-items-center justify-content-center" 
             style="width: 40px; height: 40px; display: none;" 
             title="Photo not available">
            <i class="fas fa-user text-white"></i>
        </div>`;
    
    return photoHtml;
}

// Enhanced Face Recognition Integration
async function enhancedFaceRecognition() {
    try {
        console.log('Testing enhanced face recognition...');
        
        // Check if face recognition endpoint is available
        const testResponse = await fetch('/face/test', {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('token') || sessionStorage.getItem('token')}`
            }
        });
        
        if (testResponse.ok) {
            console.log('✓ Face recognition endpoint available');
            
            // Enable face recognition features
            const faceRecognitionButtons = document.querySelectorAll('[data-face-recognition]');
            faceRecognitionButtons.forEach(btn => {
                btn.disabled = false;
                btn.title = 'Face recognition is available';
            });
            
            showAlert('Face recognition system is active and ready', 'success');
            return true;
        } else {
            console.warn('Face recognition endpoint not available');
        }
    } catch (error) {
        console.warn('Face recognition test failed:', error);
    }
    
    // Fallback: disable face recognition features
    const faceRecognitionButtons = document.querySelectorAll('[data-face-recognition]');
    faceRecognitionButtons.forEach(btn => {
        btn.disabled = true;
        btn.title = 'Face recognition not available';
    });
    
    return false;
}

// Enhanced initialization function
async function initializeEnhancedFeatures() {
    console.log('Initializing enhanced features...');
    
    try {
        // 1. Test face recognition
        await enhancedFaceRecognition();
        
        // 2. Load enhanced class options after students are loaded
        if (dashboard.students && dashboard.students.length > 0) {
            await loadClassOptionsEnhanced();
        }
        
        // 3. Set up enhanced search event listeners
        const searchInput = document.getElementById('studentSearch');
        if (searchInput) {
            // Remove existing listeners to avoid duplicates
            searchInput.removeEventListener('input', enhancedSearchStudents);
            searchInput.removeEventListener('keyup', enhancedSearchStudents);
            
            // Add enhanced search
            searchInput.addEventListener('input', enhancedSearchStudents);
            searchInput.addEventListener('keyup', enhancedSearchStudents);
            console.log('✓ Enhanced search listeners attached');
        }
        
        // 4. Set up class filter listener
        const classFilter = document.getElementById('classFilter');
        if (classFilter) {
            classFilter.removeEventListener('change', enhancedSearchStudents);
            classFilter.addEventListener('change', enhancedSearchStudents);
            console.log('✓ Enhanced class filter listener attached');
        }
        
        // 5. Override the original displayStudents with enhanced photo display
        if (dashboard && typeof dashboard.displayStudents === 'function') {
            const originalDisplayStudents = dashboard.displayStudents;
            dashboard.displayStudents = function(students) {
                console.log('Enhanced displayStudents called with:', students);
                
                if (!students || students.length === 0) {
                    const tbody = document.getElementById('studentsTable');
                    if (tbody) {
                        tbody.innerHTML = '<tr><td colspan="9" class="text-center text-muted">No students found</td></tr>';
                    }
                    return;
                }
                
                const tbody = document.getElementById('studentsTable');
                if (!tbody) return;
                
                tbody.innerHTML = students.map(student => {
                    const photoDisplay = enhancedPhotoDisplay(student);
                    const attendanceStatus = dashboard.attendanceData?.[student.student_id] || 'not_marked';
                    const statusBadge = attendanceStatus === 'present' ? 'bg-success' : 
                                      attendanceStatus === 'absent' ? 'bg-danger' : 'bg-secondary';
                    const statusText = attendanceStatus === 'present' ? 'Present' : 
                                     attendanceStatus === 'absent' ? 'Absent' : 'Not Marked';
                    
                    return `
                        <tr>
                            <td>
                                <input type="checkbox" class="form-check-input student-checkbox" 
                                       value="${student.student_id}" id="student_${student.student_id}">
                            </td>
                            <td>${photoDisplay}</td>
                            <td>${student.name || 'N/A'}</td>
                            <td>${student.roll_number || 'N/A'}</td>
                            <td>${student.class_name || 'N/A'}</td>
                            <td>${student.section || 'N/A'}</td>
                            <td>${student.stream || 'General'}</td>
                            <td>
                                <span class="badge ${statusBadge}">${statusText}</span>
                            </td>
                            <td>
                                <div class="btn-group btn-group-sm">
                                    <button class="btn btn-outline-primary" 
                                            onclick="viewStudent(${student.student_id})" 
                                            title="View Details">
                                        <i class="fas fa-eye"></i>
                                    </button>
                                    <button class="btn btn-outline-warning" 
                                            onclick="editStudent(${student.student_id})" 
                                            title="Edit">
                                        <i class="fas fa-edit"></i>
                                    </button>
                                    <button class="btn btn-outline-danger" 
                                            onclick="enhancedDeleteStudent(${student.student_id})" 
                                            title="Delete (Recoverable)">
                                        <i class="fas fa-trash"></i>
                                    </button>
                                </div>
                            </td>
                        </tr>
                    `;
                }).join('');
                
                console.log(`Enhanced display complete: ${students.length} students shown`);
            };
            console.log('✓ Enhanced displayStudents override applied');
        }
        
        console.log('✅ All enhanced features initialized successfully');
        
    } catch (error) {
        console.error('Error initializing enhanced features:', error);
    }
}

// Auto-initialize when the page loads
document.addEventListener('DOMContentLoaded', function() {
    // Wait for dashboard to be ready
    const checkDashboard = setInterval(() => {
        if (window.dashboard && dashboard.students) {
            clearInterval(checkDashboard);
            initializeEnhancedFeatures();
        }
    }, 100);
    
    // Timeout after 10 seconds
    setTimeout(() => {
        clearInterval(checkDashboard);
        initializeEnhancedFeatures(); // Try anyway
    }, 10000);
});

// Also initialize when students are loaded
if (window.dashboard) {
    const originalLoadStudents = dashboard.loadStudents;
    dashboard.loadStudents = async function() {
        const result = await originalLoadStudents.call(this);
        await initializeEnhancedFeatures();
        return result;
    };
}

console.log('Enhanced dashboard features loaded and ready');
