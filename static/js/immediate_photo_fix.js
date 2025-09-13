// IMMEDIATE PHOTO FIX - STOP ALL 404 ERRORS
console.log('🔧 IMMEDIATE PHOTO FIX LOADING...');

// Override photo display immediately when page loads
document.addEventListener('DOMContentLoaded', function() {
    console.log('🔧 DOM loaded, applying photo fix...');
    
    // Function to fix photo display
    function fixPhotoDisplay(student) {
        if (student.photo_url && student.photo_url.startsWith('http')) {
            // Use direct URL - NO local endpoint calls
            return `<img src="${student.photo_url}" class="rounded-circle" width="40" height="40" alt="Photo" style="object-fit: cover;" onerror="this.style.display='none'; this.nextElementSibling.style.display='inline-flex';"><div class="rounded-circle bg-secondary d-inline-flex align-items-center justify-content-center" style="width: 40px; height: 40px; display: none;"><i class="fas fa-user text-white"></i></div>`;
        } else {
            return `<div class="rounded-circle bg-secondary d-inline-flex align-items-center justify-content-center" style="width: 40px; height: 40px;"><i class="fas fa-user text-white"></i></div>`;
        }
    }
    
    // Wait for dashboard object to be available
    function waitForDashboard() {
        if (typeof dashboard !== 'undefined' && dashboard.displayStudents) {
            console.log('🔧 Dashboard found, overriding displayStudents...');
            
            // Save original
            const originalDisplayStudents = dashboard.displayStudents;
            
            // Override with fixed version
            dashboard.displayStudents = function(students) {
                console.log('🔧 FIXED displayStudents called with:', students.length, 'students');
                
                const tbody = document.getElementById('studentsTable');
                if (!tbody || !students) return;
                
                // Update count
                const countElement = document.getElementById('studentCount');
                if (countElement) countElement.textContent = students.length;
                
                // Generate table with direct photo URLs
                tbody.innerHTML = students.map(student => {
                    const photoDisplay = fixPhotoDisplay(student);
                    const attendanceStatus = this.attendanceData[student.student_id] || 'not_marked';
                    const statusBadge = attendanceStatus === 'present' ? 'bg-success' : attendanceStatus === 'absent' ? 'bg-danger' : 'bg-secondary';
                    const statusText = attendanceStatus === 'present' ? 'Present' : attendanceStatus === 'absent' ? 'Absent' : 'Not marked';
                    
                    return `<tr>
                        <td><input type="checkbox" class="student-checkbox" value="${student.student_id}"></td>
                        <td>${photoDisplay}</td>
                        <td>${student.roll_number}</td>
                        <td>${student.name}</td>
                        <td>${student.class || 'N/A'}</td>
                        <td>${student.section || 'N/A'}</td>
                        <td>${student.branch || 'N/A'}</td>
                        <td><span class="badge ${statusBadge}">${statusText}</span></td>
                        <td>
                            <div class="btn-group btn-group-sm">
                                <button class="btn btn-outline-primary" onclick="editStudent(${student.student_id})" title="Edit"><i class="fas fa-edit"></i></button>
                                <button class="btn btn-outline-success" onclick="markStudentAttendance(${student.student_id}, 'present')" title="Mark Present"><i class="fas fa-check"></i></button>
                                <button class="btn btn-outline-danger" onclick="markStudentAttendance(${student.student_id}, 'absent')" title="Mark Absent"><i class="fas fa-times"></i></button>
                                <button class="btn btn-outline-danger" onclick="dashboard.deleteStudent(${student.student_id})" title="Delete"><i class="fas fa-trash"></i></button>
                            </div>
                        </td>
                    </tr>`;
                }).join('');
                
                console.log('🔧 FIXED: No more 404 photo errors! Displayed', students.length, 'students');
            };
            
            console.log('✅ Photo display override applied successfully!');
        } else {
            // Try again in 100ms
            setTimeout(waitForDashboard, 100);
        }
    }
    
    // Start waiting for dashboard
    waitForDashboard();
});

console.log('✅ IMMEDIATE PHOTO FIX LOADED!');
