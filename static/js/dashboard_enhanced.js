// Force refresh students function
async function forceRefreshStudents() {
    console.log('Force refreshing students...');
    
    // Clear existing data
    dashboard.students = [];
    
    // Update UI to show loading
    const countElement = document.getElementById('studentCount');
    if (countElement) {
        countElement.textContent = 'Loading...';
    }
    
    const tbody = document.getElementById('studentsTable');
    if (tbody) {
        tbody.innerHTML = '<tr><td colspan="9" class="text-center">Loading students...</td></tr>';
    }
    
    try {
        // Force fresh API call
        const timestamp = new Date().getTime();
        const result = await api.request(`students?refresh=${timestamp}`);
        console.log('Force refresh result:', result);
        
        if (result && result.success && result.data) {
            const studentsData = Array.isArray(result.data) ? result.data : [];
            dashboard.students = studentsData;
            
            // Update count
            if (countElement) {
                countElement.textContent = studentsData.length.toString();
            }
            
            // Update table
            if (studentsData.length > 0) {
                // Call the original display function with working data
                dashboard.displayStudents(studentsData);
            } else {
                if (tbody) {
                    tbody.innerHTML = '<tr><td colspan="9" class="text-center text-muted">No students found in database</td></tr>';
                }
            }
            
            showAlert(`Refreshed: ${studentsData.length} students loaded`, 'success');
        } else {
            if (countElement) {
                countElement.textContent = '0';
            }
            if (tbody) {
                tbody.innerHTML = '<tr><td colspan="9" class="text-center text-danger">Failed to load students</td></tr>';
            }
            showAlert('Failed to refresh students', 'error');
        }
    } catch (error) {
        console.error('Force refresh error:', error);
        if (countElement) {
            countElement.textContent = 'Error';
        }
        if (tbody) {
            tbody.innerHTML = '<tr><td colspan="9" class="text-center text-danger">Error refreshing students</td></tr>';
        }
        showAlert('Error refreshing students: ' + error.message, 'error');
    }
}

// Enhanced Dashboard JavaScript with Facial Recognition functionality
class AttendanceAPI {
    constructor() {
        // Use the current page's origin for API calls
        this.baseURL = window.location.origin + '/';
        console.log('API base URL:', this.baseURL);
    }

    get token() {
        const token = localStorage.getItem('access_token');
        console.log('Token retrieved:', token ? 'Present' : 'Missing');
        return token;
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers
        };

        if (this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
            console.log('Request to', endpoint, 'with authorization header');
        } else {
            console.warn('Request to', endpoint, 'without authorization header');
        }

        try {
            const response = await fetch(url, {
                ...options,
                headers
            });

            if (response.status === 401) {
                this.logout();
                return;
            }

            const data = await response.json();
            return { success: response.ok, data, status: response.status };
        } catch (error) {
            console.error('API request failed:', error);
            return { success: false, error: error.message };
        }
    }

    async uploadFile(endpoint, formData) {
        const url = `${this.baseURL}${endpoint}`;
        const headers = {};

        if (this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }

        try {
            const response = await fetch(url, {
                method: 'POST',
                headers,
                body: formData
            });

            if (response.status === 401) {
                this.logout();
                return;
            }

            const data = await response.json();
            return { success: response.ok, data, status: response.status };
        } catch (error) {
            console.error('Upload failed:', error);
            return { success: false, error: error.message };
        }
    }

    logout() {
        localStorage.removeItem('access_token');
        window.location.href = '/login';
    }
}

const api = new AttendanceAPI();

// Face Recognition Manager
class FaceRecognition {
    constructor() {
        this.video = null;
        this.canvas = null;
        this.context = null;
        this.stream = null;
    }

    async startCamera() {
        try {
            this.video = document.getElementById('video');
            this.canvas = document.getElementById('canvas');
            this.context = this.canvas.getContext('2d');

            this.stream = await navigator.mediaDevices.getUserMedia({ 
                video: { width: 400, height: 300 } 
            });
            
            this.video.srcObject = this.stream;
            this.video.style.display = 'block';
            document.getElementById('cameraPlaceholder').style.display = 'none';
            
            document.getElementById('captureBtn').disabled = false;
            document.getElementById('stopBtn').disabled = false;
            
            return true;
        } catch (error) {
            console.error('Camera access failed:', error);
            showAlert('Camera access denied or not available', 'error');
            return false;
        }
    }

    stopCamera() {
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
            this.stream = null;
        }
        
        if (this.video) {
            this.video.style.display = 'none';
        }
        
        document.getElementById('cameraPlaceholder').style.display = 'flex';
        document.getElementById('captureBtn').disabled = true;
        document.getElementById('stopBtn').disabled = true;
    }

    captureImage() {
        if (!this.video || !this.canvas) return null;
        
        this.context.drawImage(this.video, 0, 0, 400, 300);
        return this.canvas.toDataURL('image/jpeg');
    }

    async recognizeFromCamera() {
        const imageData = this.captureImage();
        if (!imageData) {
            showAlert('Failed to capture image', 'error');
            return;
        }

        const formData = new FormData();
        formData.append('image_data', imageData);

        const result = await api.uploadFile('face/recognize-from-camera', formData);
        
        if (result.success && result.data.recognized) {
            const student = result.data;
            document.getElementById('recognitionResult').innerHTML = `
                <div class="alert alert-success">
                    <h6><i class="fas fa-check-circle"></i> Student Recognized!</h6>
                    <p><strong>Name:</strong> ${student.student_name}</p>
                    <p><strong>Roll Number:</strong> ${student.roll_number}</p>
                    <p><strong>Class:</strong> ${student.class_info}</p>
                    <p><strong>Confidence:</strong> ${(student.confidence * 100).toFixed(1)}%</p>
                    <div class="mt-2">
                        <button class="btn btn-success btn-sm me-2" onclick="markAttendanceQuick(${student.student_id}, 'present')">
                            <i class="fas fa-check"></i> Mark Present
                        </button>
                        <button class="btn btn-warning btn-sm" onclick="markAttendanceQuick(${student.student_id}, 'absent')">
                            <i class="fas fa-times"></i> Mark Absent
                        </button>
                    </div>
                </div>
            `;
        } else {
            document.getElementById('recognitionResult').innerHTML = `
                <div class="alert alert-warning">
                    <h6><i class="fas fa-exclamation-triangle"></i> No Match Found</h6>
                    <p>Could not recognize the person. Please try again or mark attendance manually.</p>
                </div>
            `;
        }
    }
}

const faceRecognition = new FaceRecognition();

// Dashboard Data Management
class Dashboard {
    constructor() {
        this.charts = {};
        this.currentSection = 'dashboard';
        this.students = [];
        this.attendanceData = {};
    }

    async init() {
        await this.loadDashboardData();
        this.setupEventListeners();
        this.setTodayDate();
    }

    setTodayDate() {
        const today = new Date().toISOString().split('T')[0];
        const dateInput = document.getElementById('attendanceDate');
        if (dateInput) {
            dateInput.value = today;
        }
    }

    setupEventListeners() {
        // Auto-refresh data every 5 minutes
        setInterval(() => {
            if (this.currentSection === 'dashboard') {
                this.loadDashboardData();
            }
        }, 300000);
    }

    async loadDashboardData() {
        try {
            await Promise.all([
                this.loadStats(),
                this.loadCharts(),
                this.loadRecentActivity()
            ]);
        } catch (error) {
            console.error('Error loading dashboard data:', error);
        }
    }

    async loadStats() {
        const result = await api.request('attendance/statistics');
        if (result.success) {
            const stats = result.data;
            document.getElementById('totalStudents').textContent = stats.total_students || 0;
            document.getElementById('presentToday').textContent = stats.present_today || 0;
            document.getElementById('absentToday').textContent = stats.absent_today || 0;
            document.getElementById('attendancePercentage').textContent = 
                `${(stats.attendance_percentage || 0).toFixed(1)}%`;
        }
    }

    async loadCharts() {
        await Promise.all([
            this.loadTrendsChart(),
            this.loadPieChart()
        ]);
    }

    async loadTrendsChart() {
        const result = await api.request('analytics/daily-trends');
        if (result.success) {
            const ctx = document.getElementById('trendsChart').getContext('2d');
            
            if (this.charts.trends) {
                this.charts.trends.destroy();
            }

            this.charts.trends = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: result.data.dates,
                    datasets: [{
                        label: 'Attendance %',
                        data: result.data.percentages,
                        borderColor: 'rgb(75, 192, 192)',
                        backgroundColor: 'rgba(75, 192, 192, 0.2)',
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            display: false
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 100
                        }
                    }
                }
            });
        }
    }

    async loadPieChart() {
        const result = await api.request('attendance/statistics');
        if (result.success) {
            const stats = result.data;
            const ctx = document.getElementById('pieChart').getContext('2d');
            
            if (this.charts.pie) {
                this.charts.pie.destroy();
            }

            this.charts.pie = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: ['Present', 'Absent'],
                    datasets: [{
                        data: [stats.present_today, stats.absent_today],
                        backgroundColor: ['#28a745', '#dc3545']
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            position: 'bottom'
                        }
                    }
                }
            });
        }
    }

    async loadRecentActivity() {
        const [performers, attention] = await Promise.all([
            api.request('analytics/top-performers'),
            api.request('analytics/students-needing-attention')
        ]);

        if (performers.success) {
            this.displayTopPerformers(performers.data);
        }

        if (attention.success) {
            this.displayAttentionNeeded(attention.data);
        }
    }

    displayTopPerformers(data) {
        const container = document.getElementById('topPerformers');
        if (data.length === 0) {
            container.innerHTML = '<p class="text-muted">No data available</p>';
            return;
        }

        container.innerHTML = data.map(student => `
            <div class="d-flex justify-content-between align-items-center py-2 border-bottom">
                <div>
                    <strong>${student.name}</strong><br>
                    <small class="text-muted">${student.roll_number}</small>
                </div>
                <span class="badge bg-success">${student.attendance_percentage.toFixed(1)}%</span>
            </div>
        `).join('');
    }

    displayAttentionNeeded(data) {
        const container = document.getElementById('attentionNeeded');
        if (data.length === 0) {
            container.innerHTML = '<p class="text-muted">All students are doing well!</p>';
            return;
        }

        container.innerHTML = data.map(student => `
            <div class="d-flex justify-content-between align-items-center py-2 border-bottom">
                <div>
                    <strong>${student.name}</strong><br>
                    <small class="text-muted">${student.roll_number}</small>
                </div>
                <span class="badge bg-danger">${student.attendance_percentage.toFixed(1)}%</span>
            </div>
        `).join('');
    }

    async loadStudents() {
        console.log('loadStudents called');
        
        // Update count to show loading
        const countElement = document.getElementById('studentCount');
        if (countElement) {
            countElement.textContent = 'Loading...';
        }
        
        try {
            // Force fresh request by adding timestamp
            const timestamp = new Date().getTime();
            const result = await api.request(`students?_t=${timestamp}`);
            console.log('Students API result:', result);
            console.log('Students API success:', result?.success);
            console.log('Students API data:', result?.data);
            console.log('Students API data type:', typeof result?.data);
            console.log('Students API data length:', result?.data?.length);
            
            if (result && result.success && result.data) {
                // Ensure we have an array
                let studentsData = Array.isArray(result.data) ? result.data : [];
                this.students = studentsData;
                console.log('Assigned students to this.students:', this.students);
                console.log('this.students length:', this.students.length);
                
                // Force table update
                this.displayStudents(this.students);
                this.populateStudentSelect();
                
                // Ensure count is updated
                if (countElement) {
                    countElement.textContent = this.students.length.toString();
                }
            } else {
                console.error('Failed to load students:', result);
                
                // Update UI to show error state
                if (countElement) {
                    countElement.textContent = '0';
                }
                
                const tbody = document.getElementById('studentsTable');
                if (tbody) {
                    tbody.innerHTML = '<tr><td colspan="9" class="text-center text-danger">Failed to load students. Please try refreshing the page.</td></tr>';
                }
                
                showAlert('Failed to load students: ' + (result?.data?.detail || 'Unknown error'), 'error');
            }
        } catch (error) {
            console.error('Error loading students:', error);
            
            // Update UI to show error state
            if (countElement) {
                countElement.textContent = 'Error';
            }
            
            const tbody = document.getElementById('studentsTable');
            if (tbody) {
                tbody.innerHTML = '<tr><td colspan="9" class="text-center text-danger">Error loading students. Please check your connection and try again.</td></tr>';
            }
            
            showAlert('Error loading students: ' + error.message, 'error');
        }
    }

    displayStudents(students) {
        console.log('displayStudents called with:', students);
        console.log('Students length:', students ? students.length : 'students is null/undefined');
        console.log('Students data:', JSON.stringify(students, null, 2));
        
        const tbody = document.getElementById('studentsTable');
        
        if (!tbody) {
            console.error('studentsTable element not found!');
            return;
        }
        
        if (!students || students.length === 0) {
            console.log('No students to display, showing empty message');
            tbody.innerHTML = '<tr><td colspan="9" class="text-center text-muted">No students found</td></tr>';
            
            // Update student count
            const countElement = document.getElementById('studentCount');
            if (countElement) {
                countElement.textContent = '0';
            }
            return;
        }
        
        // Update student count
        const countElement = document.getElementById('studentCount');
        if (countElement) {
            countElement.textContent = `${students.length}`;
        }
        
        tbody.innerHTML = students.map(student => {
            // Better photo detection logic
            const hasPhotoFile = student.photo_url && student.photo_url.trim() !== '';
            let photoDisplay;
            
            if (hasPhotoFile) {
                // Try local photo first, then fall back to remote URL
                if (student.photo_url.startsWith('http')) {
                    // Remote URL - try local photo first, then remote
                    photoDisplay = `
                        <img src="/face/student-photo/${student.student_id}" 
                             class="rounded-circle" 
                             width="40" 
                             height="40" 
                             alt="Photo"
                             onerror="this.style.display='none'; this.nextElementSibling.style.display='block';">
                        <img src="${student.photo_url}" 
                             class="rounded-circle" 
                             width="40" 
                             height="40" 
                             alt="Photo"
                             style="display: none;"
                             onerror="this.style.display='none'; this.nextElementSibling.style.display='inline-flex';">
                        <div class="rounded-circle bg-secondary d-inline-flex align-items-center justify-content-center" 
                             style="width: 40px; height: 40px; display: none;">
                            <i class="fas fa-user text-white"></i>
                        </div>`;
                } else {
                    // Local path
                    photoDisplay = `
                        <img src="/face/student-photo/${student.student_id}" 
                             class="rounded-circle" 
                             width="40" 
                             height="40" 
                             alt="Photo"
                             onerror="this.style.display='none'; this.nextElementSibling.style.display='inline-flex';">
                        <div class="rounded-circle bg-secondary d-inline-flex align-items-center justify-content-center" 
                             style="width: 40px; height: 40px; display: none;">
                            <i class="fas fa-user text-white"></i>
                        </div>`;
                }
            } else {
                photoDisplay = `
                    <div class="rounded-circle bg-secondary d-inline-flex align-items-center justify-content-center" style="width: 40px; height: 40px;">
                        <i class="fas fa-user text-white"></i>
                    </div>`;
            }
            
            const attendanceStatus = this.attendanceData[student.student_id] || 'not_marked';
            const statusBadge = attendanceStatus === 'present' ? 'bg-success' : 
                              attendanceStatus === 'absent' ? 'bg-danger' : 'bg-secondary';
            const statusText = attendanceStatus === 'present' ? 'Present' : 
                             attendanceStatus === 'absent' ? 'Absent' : 'Not marked';

            return `
                <tr>
                    <td>
                        <input type="checkbox" class="student-checkbox" value="${student.student_id}">
                    </td>
                    <td>${photoDisplay}</td>
                    <td>${student.roll_number}</td>
                    <td>${student.name}</td>
                    <td>${student.class_name || 'N/A'}</td>
                    <td>${student.section || 'N/A'}</td>
                    <td>${student.stream || 'N/A'}</td>
                    <td><span class="badge ${statusBadge}">${statusText}</span></td>
                    <td>
                        <div class="btn-group btn-group-sm">
                            <button class="btn btn-success ${attendanceStatus === 'present' ? 'active' : ''}" 
                                    onclick="markAttendanceQuick(${student.student_id}, 'present')" title="Mark Present">
                                <i class="fas fa-check"></i>
                            </button>
                            <button class="btn btn-danger ${attendanceStatus === 'absent' ? 'active' : ''}" 
                                    onclick="markAttendanceQuick(${student.student_id}, 'absent')" title="Mark Absent">
                                <i class="fas fa-times"></i>
                            </button>
                            <button class="btn btn-outline-primary" onclick="editStudentModal(${student.student_id})" title="Edit Student">
                                <i class="fas fa-edit"></i>
                            </button>
                            <button class="btn btn-outline-danger" onclick="confirmDeleteStudent(${student.student_id}, '${student.name}')" title="Delete Student">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </td>
                </tr>
            `;
        }).join('');
        
        console.log('Students table updated with', students.length, 'students');
    }

    populateStudentSelect() {
        const select = document.getElementById('photoStudentSelect');
        if (select) {
            select.innerHTML = '<option value="">Choose a student...</option>' + 
                this.students.map(student => 
                    `<option value="${student.student_id}">${student.name} (${student.roll_number})</option>`
                ).join('');
        }
    }

    async loadStudentsWithPhotos() {
        const result = await api.request('face/students-with-photos');
        if (result.success) {
            this.displayStudentsWithPhotos(result.data);
        }
    }

    displayStudentsWithPhotos(students) {
        const container = document.getElementById('studentsWithPhotos');
        if (students.length === 0) {
            container.innerHTML = '<p class="text-muted">No students with photos enrolled yet.</p>';
            return;
        }

        container.innerHTML = students.map(student => `
            <div class="d-flex justify-content-between align-items-center py-2 border-bottom">
                <div>
                    <strong>${student.name}</strong><br>
                    <small class="text-muted">${student.roll_number} - ${student.class_info}</small>
                </div>
                <button class="btn btn-sm btn-outline-danger" onclick="removeStudentPhoto(${student.student_id})">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        `).join('');
    }

    async loadAttendanceForDate() {
        const date = document.getElementById('attendanceDate').value;
        const result = await api.request(`attendance/date/${date}`);
        
        if (result.success) {
            this.attendanceData = {};
            result.data.forEach(record => {
                this.attendanceData[record.student_id] = record.status;
            });
            this.displayAttendanceTable();
        }
    }

    displayAttendanceTable(students = null) {
        const tbody = document.getElementById('attendanceTable');
        if (!tbody) return;

        const studentsToShow = students || this.students;
        
        tbody.innerHTML = studentsToShow.map(student => {
            // Better photo detection logic
            const hasPhotoFile = student.photo_url && student.photo_url.trim() !== '';
            let photoDisplay;
            
            if (hasPhotoFile) {
                // Try local photo first, then fall back to remote URL
                if (student.photo_url.startsWith('http')) {
                    // Remote URL - try local photo first, then remote
                    photoDisplay = `
                        <img src="/face/student-photo/${student.student_id}" 
                             class="rounded-circle" 
                             width="40" 
                             height="40" 
                             alt="Photo"
                             onerror="this.style.display='none'; this.nextElementSibling.style.display='block';">
                        <img src="${student.photo_url}" 
                             class="rounded-circle" 
                             width="40" 
                             height="40" 
                             alt="Photo"
                             style="display: none;"
                             onerror="this.style.display='none'; this.nextElementSibling.style.display='inline-flex';">
                        <div class="rounded-circle bg-secondary d-inline-flex align-items-center justify-content-center" 
                             style="width: 40px; height: 40px; display: none;">
                            <i class="fas fa-user text-white"></i>
                        </div>`;
                } else {
                    // Local path
                    photoDisplay = `
                        <img src="/face/student-photo/${student.student_id}" 
                             class="rounded-circle" 
                             width="40" 
                             height="40" 
                             alt="Photo"
                             onerror="this.style.display='none'; this.nextElementSibling.style.display='inline-flex';">
                        <div class="rounded-circle bg-secondary d-inline-flex align-items-center justify-content-center" 
                             style="width: 40px; height: 40px; display: none;">
                            <i class="fas fa-user text-white"></i>
                        </div>`;
                }
            } else {
                photoDisplay = `
                    <div class="rounded-circle bg-secondary d-inline-flex align-items-center justify-content-center" style="width: 40px; height: 40px;">
                        <i class="fas fa-user text-white"></i>
                    </div>`;
            }
            
            const status = this.attendanceData[student.student_id] || 'not_marked';
            const statusDisplay = status === 'present' ? 
                '<span class="badge bg-success">Present</span>' :
                status === 'absent' ? 
                '<span class="badge bg-danger">Absent</span>' :
                '<span class="badge bg-secondary">Not Marked</span>';

            return `
                <tr>
                    <td>${photoDisplay}</td>
                    <td>${student.roll_number}</td>
                    <td>${student.name}</td>
                    <td>${student.class_name || 'N/A'} - ${student.section || 'N/A'}</td>
                    <td>${statusDisplay}</td>
                    <td>
                        <div class="btn-group btn-group-sm">
                            <button class="btn btn-success ${status === 'present' ? 'active' : ''}" 
                                onclick="markAttendanceQuick(${student.student_id}, 'present')">
                                <i class="fas fa-check"></i> Present
                            </button>
                            <button class="btn btn-danger ${status === 'absent' ? 'active' : ''}" 
                                onclick="markAttendanceQuick(${student.student_id}, 'absent')">
                                <i class="fas fa-times"></i> Absent
                            </button>
                        </div>
                    </td>
                </tr>
            `;
        }).join('');
    }
}

const dashboard = new Dashboard();

// Navigation Functions with proper URL routing
function navigateTo(section) {
    // Update URL
    const newUrl = section === 'dashboard' ? '/dashboard' : `/dashboard/${section}`;
    history.pushState({section}, '', newUrl);
    
    // Show appropriate section
    switch(section) {
        case 'dashboard':
            showDashboard();
            break;
        case 'students':
            showStudents();
            break;
        case 'classes':
            showClasses();
            break;
        case 'attendance':
            showAttendance();
            break;
        case 'face-recognition':
            showFaceRecognition();
            break;
        case 'reports':
            showReports();
            break;
        case 'profile':
            showProfile();
            break;
    }
}

// Handle browser back/forward buttons
window.addEventListener('popstate', function(event) {
    if (event.state && event.state.section) {
        navigateTo(event.state.section);
    } else {
        showDashboard();
    }
});

// Navigation Functions
function showDashboard() {
    hideAllSections();
    document.getElementById('dashboardContent').style.display = 'block';
    document.getElementById('pageTitle').textContent = 'Dashboard';
    setActiveNavLink(0);
    dashboard.currentSection = 'dashboard';
    dashboard.loadDashboardData();
}

function showStudents() {
    hideAllSections();
    document.getElementById('studentsContent').style.display = 'block';
    document.getElementById('pageTitle').textContent = 'Students';
    setActiveNavLink(1);
    dashboard.currentSection = 'students';
    
    // Load students immediately and handle errors gracefully
    console.log('showStudents: Starting to load students...');
    
    // First try to load students
    dashboard.loadStudents().then(() => {
        console.log('showStudents: Students loaded, now loading attendance...');
        // Then load attendance data
        return dashboard.loadAttendanceForDate();
    }).catch(error => {
        console.error('showStudents: Error loading data:', error);
        // Still try to update the student count even if there's an error
        const countElement = document.getElementById('studentCount');
        if (countElement) {
            countElement.textContent = '0';
        }
    });
    
    // Also load class options for filtering
    loadClassOptions();
}

function showClasses() {
    hideAllSections();
    document.getElementById('classesContent').style.display = 'block';
    document.getElementById('pageTitle').textContent = 'Classes';
    setActiveNavLink(2);
    dashboard.currentSection = 'classes';
    loadClasses();
}

function showAttendance() {
    hideAllSections();
    document.getElementById('attendanceContent').style.display = 'block';
    document.getElementById('pageTitle').textContent = 'Attendance';
    setActiveNavLink(3);
    dashboard.currentSection = 'attendance';
    dashboard.loadStudents().then(() => {
        dashboard.loadAttendanceForDate();
    });
}

function showFaceRecognition() {
    hideAllSections();
    document.getElementById('faceRecognitionContent').style.display = 'block';
    document.getElementById('pageTitle').textContent = 'Face Recognition';
    setActiveNavLink(4);
    dashboard.currentSection = 'face';
    dashboard.loadStudentsWithPhotos();
    dashboard.loadStudents(); // For photo upload dropdown
}

function showReports() {
    hideAllSections();
    document.getElementById('reportsContent').style.display = 'block';
    document.getElementById('pageTitle').textContent = 'Reports';
    setActiveNavLink(5);
    dashboard.currentSection = 'reports';
    loadReportsData();
}

function showProfile() {
    hideAllSections();
    document.getElementById('profileContent').style.display = 'block';
    document.getElementById('pageTitle').textContent = 'Profile';
    setActiveNavLink(6);
    dashboard.currentSection = 'profile';
    loadProfile();
}

function hideAllSections() {
    const sections = ['dashboardContent', 'studentsContent', 'classesContent', 
                     'attendanceContent', 'faceRecognitionContent', 'reportsContent', 'profileContent'];
    sections.forEach(id => {
        const element = document.getElementById(id);
        if (element) element.style.display = 'none';
    });
}

function setActiveNavLink(index) {
    document.querySelectorAll('.nav-link').forEach((link, i) => {
        link.classList.toggle('active', i === index);
    });
}

// Face Recognition Functions
function startCamera() {
    faceRecognition.startCamera();
}

function stopCamera() {
    faceRecognition.stopCamera();
}

function captureAndRecognize() {
    faceRecognition.recognizeFromCamera();
}

// Attendance Functions
async function markAttendanceQuick(studentId, status) {
    const date = document.getElementById('attendanceDate')?.value || new Date().toISOString().split('T')[0];
    
    // Capitalize status for API compatibility
    const capitalizedStatus = status.charAt(0).toUpperCase() + status.slice(1);
    
    const attendanceData = {
        student_id: studentId,
        class_id: 1, // Default class ID - you may want to make this dynamic
        attendance_date: date,
        status: capitalizedStatus
    };

    const result = await api.request('attendance/mark', {
        method: 'POST',
        body: JSON.stringify(attendanceData)
    });

    if (result.success) {
        showAlert(`Attendance marked as ${status}`, 'success');
        
        // Update local attendance data
        dashboard.attendanceData[studentId] = status;
        
        // Force refresh of attendance data for the current date
        await dashboard.loadAttendanceForDate();
        
        // Refresh both views regardless of current section
        if (dashboard.currentSection === 'attendance') {
            dashboard.displayAttendanceTable();
        }
        if (dashboard.currentSection === 'students') {
            dashboard.displayStudents(dashboard.students);
        }
        
        // Also refresh the dashboard statistics
        dashboard.loadDashboardData();
        
    } else {
        console.error('Attendance marking failed:', result);
        showAlert('Failed to mark attendance: ' + (result.data?.detail || 'Unknown error'), 'error');
    }
}

async function loadAttendanceForDate() {
    await dashboard.loadAttendanceForDate();
}

// Photo Management Functions
async function uploadStudentPhoto() {
    const studentId = document.getElementById('photoStudentSelect').value;
    const fileInput = document.getElementById('studentPhotoFile');
    
    if (!studentId || !fileInput.files[0]) {
        showAlert('Please select a student and photo', 'error');
        return;
    }

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);

    const result = await api.uploadFile(`face/upload-student-photo/${studentId}`, formData);
    
    if (result.success) {
        showAlert('Photo uploaded successfully', 'success');
        dashboard.loadStudentsWithPhotos();
        fileInput.value = '';
        document.getElementById('photoStudentSelect').value = '';
    } else {
        showAlert(result.data?.detail || 'Failed to upload photo', 'error');
    }
}

async function removeStudentPhoto(studentId) {
    if (!confirm('Are you sure you want to remove this student\'s photo?')) {
        return;
    }

    const result = await api.request(`face/remove-student-photo/${studentId}`, {
        method: 'DELETE'
    });

    if (result.success) {
        showAlert('Photo removed successfully', 'success');
        dashboard.loadStudentsWithPhotos();
    } else {
        showAlert('Failed to remove photo', 'error');
    }
}

function uploadPhotoModal(studentId) {
    // Set the student ID in the photo upload dropdown
    const select = document.getElementById('photoStudentSelect');
    if (select) {
        select.value = studentId;
    }
    // Switch to face recognition tab
    showFaceRecognition();
    // Scroll to upload section
    setTimeout(() => {
        document.querySelector('#faceRecognitionContent .card:last-child').scrollIntoView({ behavior: 'smooth' });
    }, 100);
}

// Utility Functions
function showAlert(message, type = 'info') {
    const alertClass = type === 'error' ? 'alert-danger' : 
                      type === 'success' ? 'alert-success' : 'alert-info';
    
    const alertHtml = `
        <div class="alert ${alertClass} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    // Create a temporary container for alerts if it doesn't exist
    let alertContainer = document.getElementById('alertContainer');
    if (!alertContainer) {
        alertContainer = document.createElement('div');
        alertContainer.id = 'alertContainer';
        alertContainer.style.position = 'fixed';
        alertContainer.style.top = '20px';
        alertContainer.style.right = '20px';
        alertContainer.style.zIndex = '9999';
        alertContainer.style.width = '300px';
        document.body.appendChild(alertContainer);
    }
    
    alertContainer.innerHTML = alertHtml;
    
    // Auto-remove alert after 5 seconds
    setTimeout(() => {
        const alert = alertContainer.querySelector('.alert');
        if (alert) {
            alert.remove();
        }
    }, 5000);
}

function refreshData() {
    if (dashboard.currentSection === 'dashboard') {
        dashboard.loadDashboardData();
    } else if (dashboard.currentSection === 'students') {
        dashboard.loadStudents();
    } else if (dashboard.currentSection === 'face') {
        dashboard.loadStudentsWithPhotos();
    } else if (dashboard.currentSection === 'attendance') {
        dashboard.loadAttendanceForDate();
    }
    showAlert('Data refreshed', 'success');
}

function logout() {
    api.logout();
}

// Initialize dashboard when page loads
document.addEventListener('DOMContentLoaded', function() {
    // Check if user is logged in
    if (!localStorage.getItem('access_token')) {
        window.location.href = '/login';
        return;
    }
    
    // Clean URL hash
    if (window.location.hash) {
        history.replaceState(null, null, window.location.pathname);
    }
    
    dashboard.init();
});

// Additional student management functions (keeping existing functionality)
async function addStudent() {
    const formData = {
        roll_number: document.getElementById('rollNumber').value,
        name: document.getElementById('studentName').value,
        class_name: document.getElementById('studentClass').value,
        section: document.getElementById('studentSection').value,
        branch: document.getElementById('studentStream').value,  // Changed from 'stream' to 'branch'
        email: document.getElementById('studentEmail').value
    };

    const result = await api.request('students', {
        method: 'POST',
        body: JSON.stringify(formData)
    });

    if (result.success) {
        const newStudent = result.data;
        showAlert('Student added successfully', 'success');
        
        // Check if photo was uploaded
        const photoFile = document.getElementById('newStudentPhoto').files[0];
        if (photoFile) {
            // Upload photo for the new student
            const photoFormData = new FormData();
            photoFormData.append('file', photoFile);
            
            const photoResult = await api.uploadFile(`face/upload-student-photo/${newStudent.student_id}`, photoFormData);
            if (photoResult.success) {
                showAlert('Student and photo added successfully', 'success');
            } else {
                showAlert('Student added but photo upload failed', 'warning');
            }
        }
        
        const modal = bootstrap.Modal.getInstance(document.getElementById('addStudentModal'));
        modal.hide();
        document.getElementById('addStudentForm').reset();
        dashboard.loadStudents();
    } else {
        // Better error handling to avoid "[object Object]" display
        let errorMessage = 'Failed to add student';
        if (result.data) {
            if (typeof result.data === 'string') {
                errorMessage = result.data;
            } else if (result.data.detail) {
                errorMessage = result.data.detail;
            } else if (result.data.message) {
                errorMessage = result.data.message;
            } else {
                errorMessage = JSON.stringify(result.data);
            }
        }
        showAlert(errorMessage, 'error');
    }
}

function showAddStudentModal() {
    const modal = new bootstrap.Modal(document.getElementById('addStudentModal'));
    modal.show();
}

function showUploadModal() {
    // Create a simple upload modal for CSV files
    const modalHtml = `
        <div class="modal fade" id="uploadModal" tabindex="-1">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Upload Students CSV</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="mb-3">
                            <label class="form-label">Select CSV File</label>
                            <input type="file" class="form-control" id="csvFile" accept=".csv,.xlsx">
                        </div>
                        <div class="alert alert-info">
                            <strong>Required CSV Format:</strong><br>
                            <code>Class, Section, Roll Number, Branch, Name, Photo</code><br><br>
                            <strong>Example:</strong><br>
                            <table class="table table-sm table-bordered">
                                <thead>
                                    <tr>
                                        <th>Class</th>
                                        <th>Section</th>
                                        <th>Roll Number</th>
                                        <th>Branch</th>
                                        <th>Name</th>
                                        <th>Photo</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr>
                                        <td>10</td>
                                        <td>A</td>
                                        <td>101</td>
                                        <td>Science</td>
                                        <td>John Doe</td>
                                        <td>https://example.com/photo.jpg</td>
                                    </tr>
                                    <tr>
                                        <td>12</td>
                                        <td>B</td>
                                        <td>201</td>
                                        <td>Commerce</td>
                                        <td>Jane Smith</td>
                                        <td>https://drive.google.com/file/photo.png</td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                        <div class="alert alert-warning">
                            <strong>Important Notes:</strong><br>
                            • Photo URLs will be automatically downloaded<br>
                            • Supports Google Drive, Dropbox, and direct image URLs<br>
                            • Roll Number and Name are required fields<br>
                            • Duplicate roll numbers will be skipped
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                        <button type="button" class="btn btn-primary" onclick="uploadCSVFile()">
                            <i class="fas fa-upload"></i> Upload & Import Students
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Remove existing modal if present
    const existingModal = document.getElementById('uploadModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // Add modal to body
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('uploadModal'));
    modal.show();
}

// Reports Functions
async function loadReportsData() {
    try {
        const stats = await api.request('attendance/statistics');
        if (stats.success) {
            document.getElementById('statsTotal').textContent = stats.data.total_students || 0;
            document.getElementById('statsAverage').textContent = `${(stats.data.attendance_percentage || 0).toFixed(1)}%`;
            document.getElementById('statsClasses').textContent = stats.data.classes_conducted || 0;
            document.getElementById('statsUpdated').textContent = new Date().toLocaleDateString();
        }
    } catch (error) {
        console.error('Error loading reports data:', error);
    }
}

async function generateReport() {
    const reportType = document.getElementById('reportType').value;
    const startDate = document.getElementById('reportStartDate').value;
    const endDate = document.getElementById('reportEndDate').value;
    
    let endpoint = '';
    switch (reportType) {
        case 'attendance':
            endpoint = `analytics/report?start_date=${startDate}&end_date=${endDate}`;
            break;
        case 'monthly':
            endpoint = 'analytics/class-summary';
            break;
        case 'student':
            endpoint = 'analytics/attention-needed';
            break;
    }
    
    const result = await api.request(endpoint);
    if (result.success) {
        displayReportData(result.data, reportType);
    } else {
        showAlert('Failed to generate report', 'error');
    }
}

function displayReportData(data, type) {
    const container = document.getElementById('reportOutput');
    
    if (type === 'attendance' && data.student_data) {
        container.innerHTML = `
            <div class="table-responsive">
                <h5>Attendance Report</h5>
                <p><strong>Period:</strong> ${data.report_period?.start_date || 'N/A'} to ${data.report_period?.end_date || 'N/A'}</p>
                <p><strong>Total Students:</strong> ${data.summary_statistics?.total_students || 0}</p>
                <p><strong>Average Attendance:</strong> ${(data.summary_statistics?.average_attendance_percentage || 0).toFixed(1)}%</p>
                
                <table class="table table-striped">
                    <thead>
                        <tr>
                            <th>Roll No.</th>
                            <th>Student Name</th>
                            <th>Class</th>
                            <th>Total Days</th>
                            <th>Present Days</th>
                            <th>Attendance %</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${data.student_data.map(record => `
                            <tr>
                                <td>${record.roll_number}</td>
                                <td>${record.student_name}</td>
                                <td>${record.class_name} - ${record.section}</td>
                                <td>${record.total_days}</td>
                                <td>${record.present_days}</td>
                                <td><span class="badge ${record.attendance_percentage >= 75 ? 'bg-success' : 'bg-danger'}">${record.attendance_percentage.toFixed(1)}%</span></td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;
    } else if (type === 'monthly' && Array.isArray(data)) {
        container.innerHTML = `
            <div class="table-responsive">
                <table class="table table-striped">
                    <thead>
                        <tr>
                            <th>Class</th>
                            <th>Total Students</th>
                            <th>Average Attendance</th>
                            <th>Last Updated</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${data.map(item => `
                            <tr>
                                <td>${item.class_name || 'N/A'}</td>
                                <td>${item.total_students || 0}</td>
                                <td>${(item.average_attendance || 0).toFixed(1)}%</td>
                                <td>${item.last_updated || 'N/A'}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;
    } else if (type === 'student' && Array.isArray(data)) {
        container.innerHTML = `
            <div class="table-responsive">
                <h5>Students Needing Attention</h5>
                <table class="table table-striped">
                    <thead>
                        <tr>
                            <th>Student Name</th>
                            <th>Roll No.</th>
                            <th>Class</th>
                            <th>Attendance %</th>
                            <th>Absent Days</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${data.map(student => `
                            <tr>
                                <td>${student.name || student.student_name}</td>
                                <td>${student.roll_number}</td>
                                <td>${student.class_name || 'N/A'}</td>
                                <td><span class="badge bg-danger">${(student.attendance_percentage || 0).toFixed(1)}%</span></td>
                                <td>${student.absent_days || 0}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;
    } else {
        container.innerHTML = '<p class="text-muted">No data available for the selected report.</p>';
    }
}

async function exportToExcel() {
    const startDate = document.getElementById('reportStartDate').value;
    const endDate = document.getElementById('reportEndDate').value;
    
    try {
        const response = await fetch(`/analytics/export/excel?start_date=${startDate}&end_date=${endDate}`, {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
        });
        
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `attendance_report_${new Date().toISOString().split('T')[0]}.xlsx`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
            showAlert('Report exported successfully', 'success');
        } else {
            showAlert('Failed to export report', 'error');
        }
    } catch (error) {
        console.error('Export error:', error);
        showAlert('Failed to export report', 'error');
    }
}

// Profile Functions
async function loadProfile() {
    const result = await api.request('auth/me');
    if (result.success) {
        const profile = result.data;
        document.getElementById('profileName').textContent = profile.name || 'N/A';
        document.getElementById('profileEmail').textContent = profile.email || 'N/A';
        document.getElementById('profileDepartment').textContent = profile.department || 'N/A';
        document.getElementById('profilePhone').textContent = profile.phone || 'N/A';
        document.getElementById('profileSince').textContent = new Date(profile.created_at).toLocaleDateString();
        
        // Fill edit form
        document.getElementById('editName').value = profile.name || '';
        document.getElementById('editEmail').value = profile.email || '';
        document.getElementById('editDepartment').value = profile.department || '';
        document.getElementById('editPhone').value = profile.phone || '';
        
        // Load activity stats
        loadActivityStats();
    }
}

async function loadActivityStats() {
    try {
        const [studentsResult, statsResult] = await Promise.all([
            api.request('students'),
            api.request('attendance/statistics')
        ]);
        
        if (studentsResult.success) {
            document.getElementById('activityStudents').textContent = studentsResult.data.length;
        }
        
        if (statsResult.success) {
            const stats = statsResult.data;
            document.getElementById('activityClasses').textContent = stats.classes_conducted || 0;
            document.getElementById('activityAttendance').textContent = (stats.present_today + stats.absent_today) || 0;
            document.getElementById('activityAverage').textContent = `${(stats.attendance_percentage || 0).toFixed(1)}%`;
        }
    } catch (error) {
        console.error('Error loading activity stats:', error);
    }
}

function editProfile() {
    const inputs = ['editName', 'editDepartment', 'editPhone'];
    inputs.forEach(id => {
        document.getElementById(id).readOnly = false;
    });
    document.getElementById('editButtons').style.display = 'block';
}

function cancelEdit() {
    const inputs = ['editName', 'editDepartment', 'editPhone'];
    inputs.forEach(id => {
        document.getElementById(id).readOnly = true;
    });
    document.getElementById('editButtons').style.display = 'none';
    loadProfile(); // Reload original values
}

async function saveProfile() {
    const profileData = {
        name: document.getElementById('editName').value,
        department: document.getElementById('editDepartment').value,
        phone: document.getElementById('editPhone').value
    };
    
    const result = await api.request('teachers/profile', {
        method: 'PUT',
        body: JSON.stringify(profileData)
    });
    
    if (result.success) {
        showAlert('Profile updated successfully', 'success');
        cancelEdit();
        loadProfile();
    } else {
        showAlert('Failed to update profile', 'error');
    }
}

// Class Management Functions
async function loadClasses() {
    // For now, we'll create mock class data based on students
    const studentsResult = await api.request('students');
    if (studentsResult.success) {
        const students = studentsResult.data;
        const classMap = new Map();
        
        students.forEach(student => {
            const classKey = `${student.class_name || 'Unknown'}-${student.section || 'N/A'}-${student.stream || 'General'}`;
            if (!classMap.has(classKey)) {
                classMap.set(classKey, {
                    class_name: student.class_name || 'Unknown',
                    section: student.section || 'N/A',
                    stream: student.stream || 'General',
                    students: []
                });
            }
            classMap.get(classKey).students.push(student);
        });
        
        displayClasses(Array.from(classMap.values()));
    }
}

function displayClasses(classes) {
    const tbody = document.getElementById('classesTable');
    if (!tbody) return;
    
    tbody.innerHTML = classes.map(classInfo => {
        const totalStudents = classInfo.students.length;
        const avgAttendance = 85; // Mock data - you can calculate this from actual attendance
        
        return `
            <tr>
                <td>${classInfo.class_name}</td>
                <td>${classInfo.section}</td>
                <td>${classInfo.stream}</td>
                <td>${totalStudents}</td>
                <td>${avgAttendance}%</td>
                <td>
                    <div class="btn-group btn-group-sm">
                        <button class="btn btn-outline-primary" onclick="viewClassDetails('${classInfo.class_name}', '${classInfo.section}')" title="View Details">
                            <i class="fas fa-eye"></i>
                        </button>
                        <button class="btn btn-outline-success" onclick="markClassAttendance('${classInfo.class_name}', '${classInfo.section}')" title="Mark Attendance">
                            <i class="fas fa-clipboard-check"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `;
    }).join('');
}

function showAddClassModal() {
    const modal = new bootstrap.Modal(document.getElementById('addClassModal'));
    modal.show();
}

async function addClass() {
    // Since we don't have a class entity, we'll just show a message
    showAlert('Class information will be automatically created when you add students to it', 'info');
    const modal = bootstrap.Modal.getInstance(document.getElementById('addClassModal'));
    modal.hide();
    document.getElementById('addClassForm').reset();
}

function viewClassDetails(className, section) {
    showAlert(`Viewing details for ${className} - ${section}`, 'info');
    // You can implement detailed class view here
}

function markClassAttendance(className, section) {
    showAttendance();
    // Filter students by class
    setTimeout(() => {
        const students = dashboard.students.filter(s => 
            s.class_name === className && s.section === section
        );
        dashboard.displayAttendanceTable(students);
    }, 100);
}

function searchClasses() {
    const searchTerm = document.getElementById('classSearch').value.toLowerCase();
    // Implement search functionality
    showAlert('Search functionality implemented', 'info');
}

// CSV Upload Function
async function uploadCSVFile() {
    const fileInput = document.getElementById('csvFile');
    const file = fileInput.files[0];
    
    if (!file) {
        showAlert('Please select a CSV file', 'error');
        return;
    }
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const result = await api.uploadFile('students/upload', formData);
        
        if (result.success) {
            showAlert('Students imported successfully', 'success');
            
            // Hide modal first
            const modal = bootstrap.Modal.getInstance(document.getElementById('uploadModal'));
            if (modal) {
                modal.hide();
            }
            
            // Clear file input
            fileInput.value = '';
            
            // Force reload students and display them
            console.log('Reloading students after CSV upload...');
            await dashboard.loadStudents();
            
            // Ensure we're on the students page
            if (dashboard.currentSection !== 'students') {
                showStudents();
            } else {
                // Force refresh the display
                dashboard.displayStudents(dashboard.students);
            }
            
            console.log('Students display updated after CSV import');
        } else {
            showAlert('Failed to import students: ' + (result.data?.detail || 'Unknown error'), 'error');
        }
    } catch (error) {
        console.error('Upload error:', error);
        showAlert('Failed to upload file', 'error');
    }
}

// ========== NEW ENHANCED FEATURES ==========

// Bulk Attendance Functions
async function bulkMarkAttendance(status) {
    const checkboxes = document.querySelectorAll('.student-checkbox:checked');
    const studentIds = Array.from(checkboxes).map(cb => parseInt(cb.value));
    
    if (studentIds.length === 0) {
        showAlert('Please select students first', 'warning');
        return;
    }
    
    const confirmation = confirm(`Mark ${studentIds.length} students as ${status}?`);
    if (!confirmation) return;
    
    const date = document.getElementById('attendanceDate')?.value || new Date().toISOString().split('T')[0];
    
    const attendanceData = {
        student_ids: studentIds,
        status: status.charAt(0).toUpperCase() + status.slice(1),
        date: date,
        class_id: 1
    };

    try {
        const result = await api.request('attendance/bulk-mark', {
            method: 'POST',
            body: JSON.stringify(attendanceData)
        });

        if (result.success) {
            showAlert(`Bulk attendance marked for ${result.data.successful} students`, 'success');
            
            // Update local attendance data
            studentIds.forEach(studentId => {
                dashboard.attendanceData[studentId] = status;
            });
            
            // Refresh displays
            await dashboard.loadAttendanceForDate();
            dashboard.displayStudents(dashboard.students);
            if (dashboard.currentSection === 'attendance') {
                dashboard.displayAttendanceTable();
            }
            
            // Clear selections
            document.getElementById('selectAllStudents').checked = false;
            checkboxes.forEach(cb => cb.checked = false);
            
        } else {
            showAlert('Failed to mark bulk attendance: ' + (result.data?.detail || 'Unknown error'), 'error');
        }
    } catch (error) {
        console.error('Bulk attendance error:', error);
        showAlert('Failed to mark bulk attendance', 'error');
    }
}

// Selection Functions
function toggleSelectAll() {
    const selectAllCheckbox = document.getElementById('selectAllStudents') || document.getElementById('headerCheckbox');
    const studentCheckboxes = document.querySelectorAll('.student-checkbox');
    
    studentCheckboxes.forEach(checkbox => {
        checkbox.checked = selectAllCheckbox.checked;
    });
}

// Class-based Attendance Functions
async function markAttendanceByClass() {
    const classFilter = document.getElementById('classFilter');
    const selectedClass = classFilter.value;
    
    if (!selectedClass) {
        showAlert('Please select a class first', 'warning');
        return;
    }
    
    // Filter students by selected class
    const filteredStudents = dashboard.students.filter(student => {
        const studentClass = student.section ? 
            `${student.class_name} - ${student.section}` : 
            student.class_name;
        return studentClass === selectedClass;
    });
    
    if (filteredStudents.length === 0) {
        showAlert('No students found in the selected class', 'warning');
        return;
    }
    
    // Show class attendance modal
    showClassAttendanceModal(selectedClass, filteredStudents);
}

function showClassAttendanceModal(className, students) {
    const modalHtml = `
        <div class="modal fade" id="classAttendanceModal" tabindex="-1">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">
                            <i class="fas fa-clipboard-check"></i> 
                            Mark Attendance for ${className}
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="row mb-3">
                            <div class="col-md-6">
                                <strong>Class:</strong> ${className}
                            </div>
                            <div class="col-md-6">
                                <strong>Total Students:</strong> ${students.length}
                            </div>
                        </div>
                        
                        <div class="row mb-3">
                            <div class="col-12">
                                <div class="btn-group w-100" role="group">
                                    <button type="button" class="btn btn-success" onclick="markAllClassStudents('present')">
                                        <i class="fas fa-check"></i> Mark All Present
                                    </button>
                                    <button type="button" class="btn btn-danger" onclick="markAllClassStudents('absent')">
                                        <i class="fas fa-times"></i> Mark All Absent
                                    </button>
                                </div>
                            </div>
                        </div>
                        
                        <div class="table-responsive">
                            <table class="table table-sm">
                                <thead>
                                    <tr>
                                        <th>Roll No.</th>
                                        <th>Name</th>
                                        <th>Status</th>
                                        <th>Actions</th>
                                    </tr>
                                </thead>
                                <tbody id="classStudentsTable">
                                    ${students.map(student => `
                                        <tr id="classStudent_${student.student_id}">
                                            <td>${student.roll_number}</td>
                                            <td>${student.name}</td>
                                            <td>
                                                <span id="status_${student.student_id}" class="badge bg-secondary">Not Marked</span>
                                            </td>
                                            <td>
                                                <div class="btn-group btn-group-sm">
                                                    <button class="btn btn-outline-success" onclick="markClassStudentAttendance(${student.student_id}, 'present')">
                                                        <i class="fas fa-check"></i>
                                                    </button>
                                                    <button class="btn btn-outline-danger" onclick="markClassStudentAttendance(${student.student_id}, 'absent')">
                                                        <i class="fas fa-times"></i>
                                                    </button>
                                                </div>
                                            </td>
                                        </tr>
                                    `).join('')}
                                </tbody>
                            </table>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                        <button type="button" class="btn btn-primary" onclick="saveClassAttendance()">
                            <i class="fas fa-save"></i> Save All Changes
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Remove existing modal if any
    const existingModal = document.getElementById('classAttendanceModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // Add modal to page
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('classAttendanceModal'));
    modal.show();
    
    // Store class students data globally for access in other functions
    window.currentClassStudents = students;
}

async function markClassStudentAttendance(studentId, status) {
    const statusBadge = document.getElementById(`status_${studentId}`);
    statusBadge.className = `badge ${status === 'present' ? 'bg-success' : 'bg-danger'}`;
    statusBadge.textContent = status === 'present' ? 'Present' : 'Absent';
    
    // Store the status change for bulk saving
    if (!window.classAttendanceChanges) {
        window.classAttendanceChanges = {};
    }
    window.classAttendanceChanges[studentId] = status;
}

async function markAllClassStudents(status) {
    if (!window.currentClassStudents) return;
    
    const confirmation = confirm(`Mark all ${window.currentClassStudents.length} students as ${status}?`);
    if (!confirmation) return;
    
    window.currentClassStudents.forEach(student => {
        markClassStudentAttendance(student.student_id, status);
    });
}

async function saveClassAttendance() {
    if (!window.classAttendanceChanges || Object.keys(window.classAttendanceChanges).length === 0) {
        showAlert('No changes to save', 'info');
        return;
    }
    
    const date = document.getElementById('attendanceDate')?.value || new Date().toISOString().split('T')[0];
    const studentIds = Object.keys(window.classAttendanceChanges).map(id => parseInt(id));
    
    try {
        // Group by status for bulk operations
        const presentStudents = studentIds.filter(id => window.classAttendanceChanges[id] === 'present');
        const absentStudents = studentIds.filter(id => window.classAttendanceChanges[id] === 'absent');
        
        let successCount = 0;
        
        // Mark present students
        if (presentStudents.length > 0) {
            const presentData = {
                student_ids: presentStudents,
                status: 'Present',
                date: date,
                class_id: 1
            };
            
            const presentResult = await api.request('attendance/bulk-mark', {
                method: 'POST',
                body: JSON.stringify(presentData)
            });
            
            if (presentResult.success) {
                successCount += presentResult.data.successful;
            }
        }
        
        // Mark absent students
        if (absentStudents.length > 0) {
            const absentData = {
                student_ids: absentStudents,
                status: 'Absent',
                date: date,
                class_id: 1
            };
            
            const absentResult = await api.request('attendance/bulk-mark', {
                method: 'POST',
                body: JSON.stringify(absentData)
            });
            
            if (absentResult.success) {
                successCount += absentResult.data.successful;
            }
        }
        
        showAlert(`Attendance saved for ${successCount} students`, 'success');
        
        // Update local attendance data
        Object.keys(window.classAttendanceChanges).forEach(studentId => {
            dashboard.attendanceData[parseInt(studentId)] = window.classAttendanceChanges[studentId];
        });
        
        // Refresh displays
        await dashboard.loadAttendanceForDate();
        dashboard.displayStudents(dashboard.students);
        if (dashboard.currentSection === 'attendance') {
            dashboard.displayAttendanceTable();
        }
        
        // Close modal
        const modal = bootstrap.Modal.getInstance(document.getElementById('classAttendanceModal'));
        modal.hide();
        
        // Clear changes
        window.classAttendanceChanges = {};
        
    } catch (error) {
        console.error('Save attendance error:', error);
        showAlert('Failed to save attendance', 'error');
    }
}

// Class Filtering Functions
async function loadClassOptions() {
    try {
        const classFilter = document.getElementById('classFilter');
        if (!classFilter) return;
        
        // Get unique class combinations from students
        const uniqueClasses = new Set();
        dashboard.students.forEach(student => {
            if (student.class_name) {
                const classKey = student.section ? 
                    `${student.class_name} - ${student.section}` : 
                    student.class_name;
                uniqueClasses.add(classKey);
            }
        });
        
        // Populate filter dropdown
        classFilter.innerHTML = '<option value="">All Classes</option>' + 
            Array.from(uniqueClasses).sort().map(classKey => 
                `<option value="${classKey}">${classKey}</option>`
            ).join('');
    } catch (error) {
        console.error('Error loading class options:', error);
    }
}

function filterStudentsByClass() {
    const classFilter = document.getElementById('classFilter');
    const selectedClass = classFilter.value;
    
    let filteredStudents = dashboard.students;
    
    if (selectedClass) {
        filteredStudents = dashboard.students.filter(student => {
            const studentClass = student.section ? 
                `${student.class_name} - ${student.section}` : 
                student.class_name;
            return studentClass === selectedClass;
        });
        
        const filteredInfo = document.getElementById('filteredInfo');
        if (filteredInfo) {
            filteredInfo.textContent = `(filtered: ${filteredStudents.length} of ${dashboard.students.length})`;
        }
    } else {
        const filteredInfo = document.getElementById('filteredInfo');
        if (filteredInfo) {
            filteredInfo.textContent = '';
        }
    }
    
    dashboard.displayStudents(filteredStudents);
}

// Student Management Functions
function editStudentModal(studentId) {
    const student = dashboard.students.find(s => s.student_id === studentId);
    if (!student) {
        showAlert('Student not found', 'error');
        return;
    }
    
    // Populate edit form
    document.getElementById('editStudentId').value = student.student_id;
    document.getElementById('editRollNumber').value = student.roll_number;
    document.getElementById('editStudentName').value = student.name;
    document.getElementById('editClassName').value = student.class_name || '';
    document.getElementById('editSection').value = student.section || '';
    document.getElementById('editStream').value = student.stream || '';
    document.getElementById('editStudentEmail').value = student.email || '';
    
    const modal = new bootstrap.Modal(document.getElementById('editStudentModal'));
    modal.show();
}

async function updateStudent() {
    const studentId = document.getElementById('editStudentId').value;
    const studentData = {
        name: document.getElementById('editStudentName').value,
        class_name: document.getElementById('editClassName').value,
        section: document.getElementById('editSection').value,
        stream: document.getElementById('editStream').value,
        email: document.getElementById('editStudentEmail').value
    };
    
    try {
        const result = await api.request(`students/${studentId}`, {
            method: 'PUT',
            body: JSON.stringify(studentData)
        });

        if (result.success) {
            showAlert('Student updated successfully', 'success');
            
            // Update local data
            const studentIndex = dashboard.students.findIndex(s => s.student_id == studentId);
            if (studentIndex !== -1) {
                dashboard.students[studentIndex] = { ...dashboard.students[studentIndex], ...studentData };
            }
            
            // Refresh display
            dashboard.displayStudents(dashboard.students);
            loadClassOptions(); // Refresh class options
            
            const modal = bootstrap.Modal.getInstance(document.getElementById('editStudentModal'));
            modal.hide();
        } else {
            showAlert('Failed to update student: ' + (result.data?.detail || 'Unknown error'), 'error');
        }
    } catch (error) {
        console.error('Update error:', error);
        showAlert('Failed to update student', 'error');
    }
}

function confirmDeleteStudent(studentId, studentName) {
    const confirmation = confirm(`Are you sure you want to delete ${studentName}? This action cannot be undone.`);
    if (confirmation) {
        deleteStudent(studentId);
    }
}

async function deleteStudent(studentId) {
    try {
        const result = await api.request(`students/${studentId}`, {
            method: 'DELETE'
        });

        if (result.success) {
            showAlert('Student deleted successfully', 'success');
            
            // Remove from local data
            dashboard.students = dashboard.students.filter(s => s.student_id !== studentId);
            
            // Refresh display
            dashboard.displayStudents(dashboard.students);
            loadClassOptions(); // Refresh class options
            
        } else {
            showAlert('Failed to delete student: ' + (result.data?.detail || 'Unknown error'), 'error');
        }
    } catch (error) {
        console.error('Delete error:', error);
        showAlert('Failed to delete student', 'error');
    }
}

// Search Function Enhancement
function searchStudents() {
    const searchTerm = document.getElementById('studentSearch').value.toLowerCase();
    const classFilter = document.getElementById('classFilter').value;
    
    let filteredStudents = dashboard.students;
    
    // Apply class filter first
    if (classFilter) {
        filteredStudents = filteredStudents.filter(student => {
            const studentClass = student.section ? 
                `${student.class_name} - ${student.section}` : 
                student.class_name;
            return studentClass === classFilter;
        });
    }
    
    // Apply search filter
    if (searchTerm) {
        filteredStudents = filteredStudents.filter(student => 
            student.name.toLowerCase().includes(searchTerm) ||
            student.roll_number.toLowerCase().includes(searchTerm) ||
            (student.class_name && student.class_name.toLowerCase().includes(searchTerm)) ||
            (student.section && student.section.toLowerCase().includes(searchTerm))
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

// Enhanced showStudents function to load class options
const originalShowStudents = showStudents;
showStudents = function() {
    originalShowStudents();
    // Load class options after students are loaded
    setTimeout(() => {
        if (dashboard.students && dashboard.students.length > 0) {
            loadClassOptions();
        }
    }, 100);
};
