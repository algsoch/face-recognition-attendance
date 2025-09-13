// Student Portal JavaScript functionality
class StudentPortal {
    constructor() {
        this.webcam = null;
        this.stream = null;
        this.classes = [];
        this.init();
    }

    async init() {
        this.updateDateTime();
        setInterval(() => this.updateDateTime(), 1000);
        
        await this.loadClasses();
        this.setupEventListeners();
    }

    updateDateTime() {
        const now = new Date();
        const options = {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        };
        document.getElementById('currentDateTime').textContent = now.toLocaleDateString('en-US', options);
    }

    async loadClasses() {
        try {
            // For demo purposes, we'll use mock data
            // In production, this would fetch from the API
            const mockClasses = [
                { class_id: 1, class_name: '12', section: 'A', subject: 'Computer Science' },
                { class_id: 2, class_name: '12', section: 'B', subject: 'Mathematics' },
                { class_id: 3, class_name: '11', section: 'A', subject: 'Physics' }
            ];

            this.classes = mockClasses;
            this.updateClassSelects();
        } catch (error) {
            console.error('Error loading classes:', error);
            this.showAlert('Error loading classes', 'error');
        }
    }

    updateClassSelects() {
        const selects = ['classSelect', 'uploadClassSelect'];
        
        selects.forEach(selectId => {
            const select = document.getElementById(selectId);
            select.innerHTML = '<option value="">Select a class...</option>';
            
            this.classes.forEach(cls => {
                const option = document.createElement('option');
                option.value = cls.class_id;
                option.textContent = `${cls.class_name}${cls.section ? '-' + cls.section : ''} (${cls.subject})`;
                select.appendChild(option);
            });
        });
    }

    async startCamera() {
        try {
            this.stream = await navigator.mediaDevices.getUserMedia({ 
                video: { width: 640, height: 480 } 
            });
            
            this.webcam = document.getElementById('webcam');
            this.webcam.srcObject = this.stream;
            
            this.updateStatus('Camera Active', 'success');
            
            // Hide capture overlay initially
            document.getElementById('captureOverlay').style.display = 'none';
            
            // Show capture overlay on hover
            this.webcam.addEventListener('mouseenter', () => {
                document.getElementById('captureOverlay').style.display = 'flex';
            });
            
            this.webcam.addEventListener('mouseleave', () => {
                document.getElementById('captureOverlay').style.display = 'none';
            });
            
        } catch (error) {
            console.error('Error accessing camera:', error);
            this.showAlert('Error accessing camera. Please allow camera permissions.', 'error');
            this.updateStatus('Camera Error', 'danger');
        }
    }

    stopCamera() {
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
            this.stream = null;
        }
        
        if (this.webcam) {
            this.webcam.srcObject = null;
        }
        
        this.updateStatus('Camera Stopped', 'secondary');
        document.getElementById('captureOverlay').style.display = 'flex';
    }

    async captureAttendance() {
        const classId = document.getElementById('classSelect').value;
        
        if (!classId) {
            this.showAlert('Please select a class first', 'warning');
            return;
        }

        if (!this.webcam || !this.stream) {
            this.showAlert('Please start the camera first', 'warning');
            return;
        }

        try {
            this.showLoading(true);
            this.updateStatus('Processing...', 'warning');

            // Capture image from webcam
            const canvas = document.getElementById('canvas');
            const context = canvas.getContext('2d');
            
            canvas.width = this.webcam.videoWidth;
            canvas.height = this.webcam.videoHeight;
            context.drawImage(this.webcam, 0, 0);
            
            // Convert to base64
            const imageData = canvas.toDataURL('image/jpeg', 0.8);
            
            // Send to facial recognition API
            const response = await fetch('/face/recognize-attendance', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    image: imageData,
                    class_id: parseInt(classId)
                })
            });

            const result = await response.json();
            
            if (result.success) {
                this.showSuccessResult(result);
                this.updateStatus('Attendance Marked', 'success');
                this.loadStudentStats(result.student.student_id);
            } else {
                this.showErrorResult(result.message);
                this.updateStatus('Recognition Failed', 'danger');
            }

        } catch (error) {
            console.error('Error capturing attendance:', error);
            this.showAlert('Error processing attendance', 'error');
            this.updateStatus('Error', 'danger');
        } finally {
            this.showLoading(false);
        }
    }

    showSuccessResult(result) {
        const container = document.getElementById('resultContainer');
        container.innerHTML = `
            <div class="alert alert-success success-animation">
                <div class="row align-items-center">
                    <div class="col-auto">
                        <i class="fas fa-check-circle fa-2x"></i>
                    </div>
                    <div class="col">
                        <h6 class="mb-1">Attendance Marked Successfully!</h6>
                        <p class="mb-1">
                            <strong>${result.student.name}</strong> (${result.student.roll_number})
                        </p>
                        <small>Confidence: ${result.student.confidence}%</small>
                    </div>
                </div>
            </div>
        `;

        // Update recognition status
        const statusContainer = document.getElementById('recognitionStatus');
        statusContainer.innerHTML = `
            <div class="text-center">
                <i class="fas fa-user-check fa-3x text-success mb-2"></i>
                <h6>${result.student.name}</h6>
                <p class="text-muted mb-0">${result.student.roll_number}</p>
                <small class="text-success">Recognized with ${result.student.confidence}% confidence</small>
            </div>
        `;

        // Auto-hide result after 5 seconds
        setTimeout(() => {
            container.innerHTML = '';
        }, 5000);
    }

    showErrorResult(message) {
        const container = document.getElementById('resultContainer');
        container.innerHTML = `
            <div class="alert alert-danger">
                <div class="row align-items-center">
                    <div class="col-auto">
                        <i class="fas fa-times-circle fa-2x"></i>
                    </div>
                    <div class="col">
                        <h6 class="mb-1">Recognition Failed</h6>
                        <p class="mb-0">${message}</p>
                    </div>
                </div>
            </div>
        `;

        // Reset recognition status
        const statusContainer = document.getElementById('recognitionStatus');
        statusContainer.innerHTML = `
            <div class="text-center text-muted">
                <i class="fas fa-user-circle fa-3x mb-2"></i>
                <p>Position your face in front of the camera</p>
            </div>
        `;

        // Auto-hide result after 5 seconds
        setTimeout(() => {
            container.innerHTML = '';
        }, 5000);
    }

    async loadStudentStats(studentId) {
        try {
            // Mock student attendance data
            const mockStats = {
                total_days: 25,
                present_days: 22,
                attendance_percentage: 88,
                recent_attendance: [
                    { date: '2024-01-15', status: 'Present', class: 'Computer Science' },
                    { date: '2024-01-14', status: 'Present', class: 'Mathematics' },
                    { date: '2024-01-13', status: 'Absent', class: 'Physics' },
                    { date: '2024-01-12', status: 'Present', class: 'Computer Science' },
                    { date: '2024-01-11', status: 'Present', class: 'Mathematics' }
                ]
            };

            this.updateStudentStats(mockStats);
        } catch (error) {
            console.error('Error loading student stats:', error);
        }
    }

    updateStudentStats(stats) {
        document.getElementById('attendancePercentage').textContent = `${stats.attendance_percentage}%`;
        document.getElementById('totalDays').textContent = stats.total_days;
        document.getElementById('attendanceProgress').style.width = `${stats.attendance_percentage}%`;

        // Update attendance history
        const historyContainer = document.getElementById('attendanceHistory');
        if (stats.recent_attendance && stats.recent_attendance.length > 0) {
            let html = '<div class="list-group list-group-flush">';
            
            stats.recent_attendance.forEach(record => {
                const statusIcon = record.status === 'Present' ? 'check-circle text-success' : 'times-circle text-danger';
                const date = new Date(record.date).toLocaleDateString();
                
                html += `
                    <div class="list-group-item d-flex justify-content-between align-items-center py-2">
                        <div>
                            <small class="fw-bold">${record.class}</small><br>
                            <small class="text-muted">${date}</small>
                        </div>
                        <i class="fas fa-${statusIcon}"></i>
                    </div>
                `;
            });
            
            html += '</div>';
            historyContainer.innerHTML = html;
        }
    }

    updateStatus(text, type) {
        const badge = document.getElementById('statusBadge');
        badge.textContent = text;
        badge.className = `badge bg-${type} status-badge`;
    }

    showLoading(show) {
        const loading = document.getElementById('loadingIndicator');
        const captureBtn = document.getElementById('captureBtn');
        
        if (show) {
            loading.style.display = 'block';
            captureBtn.disabled = true;
        } else {
            loading.style.display = 'none';
            captureBtn.disabled = false;
        }
    }

    showAlert(message, type = 'info') {
        // Create alert element
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show position-fixed`;
        alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        document.body.appendChild(alertDiv);

        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 5000);
    }

    setupEventListeners() {
        // File upload preview
        document.getElementById('photoUpload').addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = (e) => {
                    document.getElementById('photoPreview').src = e.target.result;
                    document.getElementById('previewContainer').style.display = 'block';
                };
                reader.readAsDataURL(file);
            }
        });

        // Auto-start camera on page load (optional)
        // this.startCamera();
    }

    async processUploadedImage() {
        const fileInput = document.getElementById('photoUpload');
        const classId = document.getElementById('uploadClassSelect').value;
        
        if (!fileInput.files[0]) {
            this.showAlert('Please select a photo', 'warning');
            return;
        }
        
        if (!classId) {
            this.showAlert('Please select a class', 'warning');
            return;
        }

        try {
            const file = fileInput.files[0];
            const reader = new FileReader();
            
            reader.onload = async (e) => {
                const imageData = e.target.result;
                
                const response = await fetch('/face/recognize-attendance', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        image: imageData,
                        class_id: parseInt(classId)
                    })
                });

                const result = await response.json();
                
                if (result.success) {
                    this.showAlert('Attendance marked successfully!', 'success');
                    bootstrap.Modal.getInstance(document.getElementById('uploadModal')).hide();
                    this.showSuccessResult(result);
                    this.loadStudentStats(result.student.student_id);
                } else {
                    this.showAlert(result.message, 'warning');
                }
            };
            
            reader.readAsDataURL(file);
            
        } catch (error) {
            console.error('Error processing uploaded image:', error);
            this.showAlert('Error processing image', 'error');
        }
    }
}

// Global functions
function startCamera() {
    portal.startCamera();
}

function stopCamera() {
    portal.stopCamera();
}

function captureAttendance() {
    portal.captureAttendance();
}

function uploadImage() {
    new bootstrap.Modal(document.getElementById('uploadModal')).show();
}

function processUploadedImage() {
    portal.processUploadedImage();
}

// Initialize portal when page loads
let portal;
document.addEventListener('DOMContentLoaded', () => {
    portal = new StudentPortal();
});
