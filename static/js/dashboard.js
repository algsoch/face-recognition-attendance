// Dashboard JavaScript functionality
class AttendanceAPI {
    constructor() {
        this.baseURL = '/';
        this.token = localStorage.getItem('access_token');
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers
        };

        if (this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
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

    logout() {
        localStorage.removeItem('access_token');
        window.location.href = '/login.html';
    }
}

const api = new AttendanceAPI();

// Dashboard Data Management
class Dashboard {
    constructor() {
        this.charts = {};
        this.currentSection = 'dashboard';
        this.init();
    }

    async init() {
        if (!api.token) {
            api.logout();
            return;
        }

        await this.loadDashboardData();
        this.setupEventListeners();
    }

    async loadDashboardData() {
        try {
            // Load attendance statistics
            const statsResponse = await api.request('analytics/attendance-stats');
            if (statsResponse.success) {
                this.updateStatsCards(statsResponse.data);
            }

            // Load attendance trends
            const trendsResponse = await api.request('analytics/trends?days=30');
            if (trendsResponse.success) {
                this.updateTrendsChart(trendsResponse.data);
            }

            // Load top performers
            const performersResponse = await api.request('analytics/top-performers?limit=5');
            if (performersResponse.success) {
                this.updateTopPerformers(performersResponse.data.top_performers);
            }

            // Load students needing attention
            const attentionResponse = await api.request('analytics/attention-needed?threshold=75');
            if (attentionResponse.success) {
                this.updateAttentionNeeded(attentionResponse.data.students_needing_attention);
            }

        } catch (error) {
            console.error('Error loading dashboard data:', error);
            this.showAlert('Error loading dashboard data', 'error');
        }
    }

    updateStatsCards(stats) {
        document.getElementById('totalStudents').textContent = stats.total_students || 0;
        document.getElementById('presentToday').textContent = stats.present_today || 0;
        document.getElementById('absentToday').textContent = stats.absent_today || 0;
        document.getElementById('attendancePercentage').textContent = 
            `${stats.attendance_percentage || 0}%`;

        // Update pie chart
        this.updatePieChart(stats);
    }

    updateTrendsChart(trendsData) {
        const ctx = document.getElementById('trendsChart').getContext('2d');
        
        if (this.charts.trends) {
            this.charts.trends.destroy();
        }

        this.charts.trends = new Chart(ctx, {
            type: 'line',
            data: {
                labels: trendsData.dates || [],
                datasets: [{
                    label: 'Present',
                    data: trendsData.present_count || [],
                    borderColor: 'rgb(75, 192, 192)',
                    backgroundColor: 'rgba(75, 192, 192, 0.1)',
                    tension: 0.4
                }, {
                    label: 'Absent',
                    data: trendsData.absent_count || [],
                    borderColor: 'rgb(255, 99, 132)',
                    backgroundColor: 'rgba(255, 99, 132, 0.1)',
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Daily Attendance Trends'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }

    updatePieChart(stats) {
        const ctx = document.getElementById('pieChart').getContext('2d');
        
        if (this.charts.pie) {
            this.charts.pie.destroy();
        }

        this.charts.pie = new Chart(ctx, {
            type: 'pie',
            data: {
                labels: ['Present', 'Absent'],
                datasets: [{
                    data: [stats.present_today || 0, stats.absent_today || 0],
                    backgroundColor: [
                        'rgba(75, 192, 192, 0.8)',
                        'rgba(255, 99, 132, 0.8)'
                    ],
                    borderColor: [
                        'rgb(75, 192, 192)',
                        'rgb(255, 99, 132)'
                    ],
                    borderWidth: 2
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

    updateTopPerformers(performers) {
        const container = document.getElementById('topPerformers');
        
        if (!performers || performers.length === 0) {
            container.innerHTML = '<p class="text-muted">No data available</p>';
            return;
        }

        let html = '<div class="list-group list-group-flush">';
        performers.forEach((student, index) => {
            html += `
                <div class="list-group-item d-flex justify-content-between align-items-center">
                    <div>
                        <strong>#${index + 1} ${student.name}</strong><br>
                        <small class="text-muted">${student.roll_number} - ${student.class_name}${student.section ? ' ' + student.section : ''}</small>
                    </div>
                    <span class="badge bg-success rounded-pill">${student.attendance_percentage}%</span>
                </div>
            `;
        });
        html += '</div>';
        
        container.innerHTML = html;
    }

    updateAttentionNeeded(students) {
        const container = document.getElementById('attentionNeeded');
        
        if (!students || students.length === 0) {
            container.innerHTML = '<p class="text-success">All students have good attendance!</p>';
            return;
        }

        let html = '<div class="list-group list-group-flush">';
        students.slice(0, 5).forEach(student => {
            html += `
                <div class="list-group-item d-flex justify-content-between align-items-center">
                    <div>
                        <strong>${student.name}</strong><br>
                        <small class="text-muted">${student.roll_number} - ${student.class_name}${student.section ? ' ' + student.section : ''}</small>
                    </div>
                    <span class="badge bg-warning rounded-pill">${student.attendance_percentage}%</span>
                </div>
            `;
        });
        html += '</div>';
        
        container.innerHTML = html;
    }

    async loadStudents() {
        try {
            const response = await api.request('students');
            if (response.success) {
                this.updateStudentsTable(response.data);
            }
        } catch (error) {
            console.error('Error loading students:', error);
        }
    }

    updateStudentsTable(students) {
        const tbody = document.getElementById('studentsTable');
        
        if (!students || students.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center">No students found</td></tr>';
            return;
        }

        let html = '';
        students.forEach(student => {
            html += `
                <tr>
                    <td>${student.roll_number}</td>
                    <td>${student.name}</td>
                    <td>${student.class_name || '-'}</td>
                    <td>${student.section || '-'}</td>
                    <td>${student.stream || '-'}</td>
                    <td>
                        <button class="btn btn-sm btn-outline-primary" onclick="editStudent(${student.student_id})">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn btn-sm btn-outline-danger" onclick="deleteStudent(${student.student_id})">
                            <i class="fas fa-trash"></i>
                        </button>
                    </td>
                </tr>
            `;
        });
        
        tbody.innerHTML = html;
    }

    showAlert(message, type = 'info') {
        // Create alert element
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        // Insert at top of main content
        const main = document.querySelector('main');
        main.insertBefore(alertDiv, main.firstChild);

        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 5000);
    }

    setupEventListeners() {
        // Add student form submission
        document.getElementById('addStudentForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            await this.addStudent();
        });
    }

    async addStudent() {
        const formData = {
            roll_number: document.getElementById('rollNumber').value,
            name: document.getElementById('studentName').value,
            class_name: document.getElementById('studentClass').value,
            section: document.getElementById('studentSection').value,
            stream: document.getElementById('studentStream').value,
            email: document.getElementById('studentEmail').value
        };

        try {
            const response = await api.request('students', {
                method: 'POST',
                body: JSON.stringify(formData)
            });

            if (response.success) {
                this.showAlert('Student added successfully!', 'success');
                bootstrap.Modal.getInstance(document.getElementById('addStudentModal')).hide();
                document.getElementById('addStudentForm').reset();
                
                if (this.currentSection === 'students') {
                    await this.loadStudents();
                }
            } else {
                this.showAlert(response.data.detail || 'Error adding student', 'error');
            }
        } catch (error) {
            this.showAlert('Error adding student', 'error');
        }
    }
}

// Navigation Functions
function showSection(sectionName) {
    // Hide all content sections
    const sections = ['dashboard', 'students', 'classes', 'attendance', 'reports', 'profile'];
    sections.forEach(section => {
        document.getElementById(`${section}Content`).style.display = 'none';
    });

    // Show selected section
    document.getElementById(`${sectionName}Content`).style.display = 'block';

    // Update navigation
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
    });
    event.target.classList.add('active');

    // Update page title
    const titles = {
        dashboard: 'Dashboard',
        students: 'Students Management',
        classes: 'Classes Management',
        attendance: 'Attendance Management',
        reports: 'Reports & Analytics',
        profile: 'Profile Settings'
    };
    document.getElementById('pageTitle').textContent = titles[sectionName] || sectionName;

    // Load section-specific data
    dashboard.currentSection = sectionName;
    if (sectionName === 'students') {
        dashboard.loadStudents();
    }
}

function showDashboard() { showSection('dashboard'); }
function showStudents() { showSection('students'); }
function showClasses() { showSection('classes'); }
function showAttendance() { showSection('attendance'); }
function showReports() { showSection('reports'); }
function showProfile() { showSection('profile'); }

function refreshData() {
    if (dashboard.currentSection === 'dashboard') {
        dashboard.loadDashboardData();
    } else if (dashboard.currentSection === 'students') {
        dashboard.loadStudents();
    }
}

function logout() {
    if (confirm('Are you sure you want to logout?')) {
        api.logout();
    }
}

function showAddStudentModal() {
    new bootstrap.Modal(document.getElementById('addStudentModal')).show();
}

function showUploadModal() {
    // TODO: Implement file upload modal
    alert('CSV upload feature coming soon!');
}

function addStudent() {
    dashboard.addStudent();
}

function editStudent(studentId) {
    // TODO: Implement edit student functionality
    alert(`Edit student ${studentId} - Coming soon!`);
}

function deleteStudent(studentId) {
    if (confirm('Are you sure you want to delete this student?')) {
        // TODO: Implement delete student functionality
        alert(`Delete student ${studentId} - Coming soon!`);
    }
}

function searchStudents() {
    // TODO: Implement search functionality
    const searchTerm = document.getElementById('studentSearch').value;
    alert(`Search for: ${searchTerm} - Coming soon!`);
}

// Initialize dashboard when page loads
let dashboard;
document.addEventListener('DOMContentLoaded', () => {
    dashboard = new Dashboard();
});
