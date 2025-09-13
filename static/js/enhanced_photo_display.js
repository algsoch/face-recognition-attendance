// Force immediate photo display fix - no more 404 errors
function createPhotoDisplay(student) {
    const hasPhotoFile = student.photo_url && student.photo_url.trim() !== '';
    
    if (!hasPhotoFile) {
        return `<div class="rounded-circle bg-secondary d-inline-flex align-items-center justify-content-center" style="width: 40px; height: 40px;"><i class="fas fa-user text-white"></i></div>`;
    }
    
    // ALWAYS use direct URL for remote photos - NO LOCAL ENDPOINT CALLS
    if (student.photo_url.startsWith('http')) {
        return `<img src="${student.photo_url}" class="rounded-circle" width="40" height="40" alt="Photo" style="object-fit: cover;" onerror="this.style.display='none'; this.nextElementSibling.style.display='inline-flex';"><div class="rounded-circle bg-secondary d-inline-flex align-items-center justify-content-center" style="width: 40px; height: 40px; display: none;"><i class="fas fa-user text-white"></i></div>`;
    } else {
        return `<img src="/face/student-photo/${student.student_id}" class="rounded-circle" width="40" height="40" alt="Photo" style="object-fit: cover;" onerror="this.style.display='none'; this.nextElementSibling.style.display='inline-flex';"><div class="rounded-circle bg-secondary d-inline-flex align-items-center justify-content-center" style="width: 40px; height: 40px; display: none;"><i class="fas fa-user text-white"></i></div>`;
    }
}

// Override ALL existing photo display functions immediately
if (typeof window !== 'undefined') {
    // Wait for dashboard to load then override
    setTimeout(() => {
        if (typeof dashboard !== 'undefined' && dashboard.displayStudents) {
            const originalDisplayStudents = dashboard.displayStudents;
            dashboard.displayStudents = function(students) {
                console.log('FIXED displayStudents called with:', students);
                const tbody = document.getElementById('studentsTable');
                if (!tbody || !students || !Array.isArray(students)) return;
                
                const countElement = document.getElementById('studentCount');
                if (countElement) countElement.textContent = `${students.length}`;
                
                tbody.innerHTML = students.map(student => {
                    const photoDisplay = createPhotoDisplay(student);
                    const attendanceStatus = this.attendanceData[student.student_id] || 'not_marked';
                    const statusBadge = attendanceStatus === 'present' ? 'bg-success' : attendanceStatus === 'absent' ? 'bg-danger' : 'bg-secondary';
                    const statusText = attendanceStatus === 'present' ? 'Present' : attendanceStatus === 'absent' ? 'Absent' : 'Not marked';
                    
                    return `<tr><td><input type="checkbox" class="student-checkbox" value="${student.student_id}"></td><td>${photoDisplay}</td><td>${student.roll_number}</td><td>${student.name}</td><td>${student.class || 'N/A'}</td><td>${student.section || 'N/A'}</td><td>${student.branch || 'N/A'}</td><td><span class="badge ${statusBadge}">${statusText}</span></td><td><div class="btn-group btn-group-sm"><button class="btn btn-outline-primary" onclick="editStudent(${student.student_id})" title="Edit"><i class="fas fa-edit"></i></button><button class="btn btn-outline-success" onclick="markStudentAttendance(${student.student_id}, 'present')" title="Mark Present"><i class="fas fa-check"></i></button><button class="btn btn-outline-danger" onclick="markStudentAttendance(${student.student_id}, 'absent')" title="Mark Absent"><i class="fas fa-times"></i></button><button class="btn btn-outline-danger" onclick="dashboard.deleteStudent(${student.student_id})" title="Delete"><i class="fas fa-trash"></i></button></div></td></tr>`;
                }).join('');
                console.log(`FIXED: Displayed ${students.length} students with direct photo URLs`);
            };
        }
    }, 1000);
}

// Also override displayStudentsWithPhotos if it exists
if (typeof dashboard !== 'undefined' && dashboard.displayStudentsWithPhotos) {
    const originalDisplayStudentsWithPhotos = dashboard.displayStudentsWithPhotos;
    
    dashboard.displayStudentsWithPhotos = function(students) {
        console.log('Enhanced displayStudentsWithPhotos called with:', students);
        const tbody = document.getElementById('photoStudentsTable');
        
        if (!tbody || !students || !Array.isArray(students)) {
            console.error('Missing tbody or invalid students data for photo view');
            return;
        }
        
        const studentsToShow = students.slice(0, 50); // Limit for performance
        
        tbody.innerHTML = studentsToShow.map(student => {
            const photoDisplay = createPhotoDisplay(student);
            
            return `
                <tr>
                    <td>${photoDisplay}</td>
                    <td>${student.roll_number}</td>
                    <td>${student.name}</td>
                    <td>${student.class || 'N/A'}</td>
                    <td>${student.section || 'N/A'}</td>
                    <td>
                        <div class="btn-group btn-group-sm">
                            <button class="btn btn-outline-primary" onclick="editStudent(${student.student_id})" title="Edit">
                                <i class="fas fa-edit"></i>
                            </button>
                            <button class="btn btn-outline-success" onclick="markStudentAttendance(${student.student_id}, 'present')" title="Mark Present">
                                <i class="fas fa-check"></i>
                            </button>
                        </div>
                    </td>
                </tr>
            `;
        }).join('');
        
        console.log(`Displayed ${studentsToShow.length} students in photo view with enhanced photo handling`);
    };
}

// Enhanced search functionality with proper class filtering
function enhancedSearchStudents() {
    const searchTerm = document.getElementById('studentSearch').value.toLowerCase();
    const classFilter = document.getElementById('classFilter').value;
    
    let filteredStudents = dashboard.students;
    
    // Apply class filter first
    if (classFilter) {
        filteredStudents = filteredStudents.filter(student => {
            const studentClass = student.section ? 
                `${student.class} - ${student.section}` : 
                student.class;
            return studentClass === classFilter;
        });
    }
    
    // Apply search filter
    if (searchTerm) {
        filteredStudents = filteredStudents.filter(student => 
            student.name.toLowerCase().includes(searchTerm) ||
            student.roll_number.toLowerCase().includes(searchTerm) ||
            (student.class && student.class.toLowerCase().includes(searchTerm)) ||
            (student.section && student.section.toLowerCase().includes(searchTerm)) ||
            (student.branch && student.branch.toLowerCase().includes(searchTerm))
        );
    }
    
    dashboard.displayStudents(filteredStudents);
    
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

// Enhanced class filter population
async function enhancedLoadClassOptions() {
    try {
        const classFilter = document.getElementById('classFilter');
        if (!classFilter) return;
        
        // Get unique class combinations from students
        const uniqueClasses = new Set();
        dashboard.students.forEach(student => {
            if (student.class) {
                const classKey = student.section ? 
                    `${student.class} - ${student.section}` : 
                    student.class;
                uniqueClasses.add(classKey);
            }
        });
        
        // Populate filter dropdown
        classFilter.innerHTML = '<option value="">All Classes</option>' + 
            Array.from(uniqueClasses).sort().map(classKey => 
                `<option value="${classKey}">${classKey}</option>`
            ).join('');
            
        console.log(`Loaded ${uniqueClasses.size} class options for filtering`);
    } catch (error) {
        console.error('Error loading enhanced class options:', error);
    }
}

// Override existing functions if they exist
if (typeof searchStudents !== 'undefined') {
    window.searchStudents = enhancedSearchStudents;
}

if (typeof loadClassOptions !== 'undefined') {
    window.loadClassOptions = enhancedLoadClassOptions;
}

console.log('✅ Enhanced photo display and filtering loaded successfully');
