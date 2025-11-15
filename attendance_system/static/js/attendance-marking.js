/**
 * Attendance Marking Module
 * Real-time face recognition and attendance management
 */

let attendanceVideoStream = null;
let attendanceFaceDetectionLoaded = false;
let currentSession = null;
let recognizedFaces = new Map();

// Initialize face detection for attendance
async function initializeAttendanceFaceDetection() {
    try {
        const MODEL_URL = 'https://cdn.jsdelivr.net/npm/@vladmandic/face-api/model/';
        await faceapi.nets.tinyFaceDetector.load(MODEL_URL);
        await faceapi.nets.faceLandmark68Net.load(MODEL_URL);
        await faceapi.nets.faceRecognitionNet.load(MODEL_URL);
        attendanceFaceDetectionLoaded = true;
        console.log('Attendance face detection models loaded');
    } catch (error) {
        console.error('Error loading face detection models:', error);
        showAttendanceMessage('Error loading face detection models', 'error');
    }
}

// Load available sessions
async function loadSessions() {
    try {
        const response = await fetch('/api/attendance/sessions/', {
            method: 'GET',
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        });

        if (!response.ok) throw new Error('Failed to load sessions');

        const sessions = await response.json();
        const select = document.getElementById('sessionSelect');
        
        sessions.forEach(session => {
            const option = document.createElement('option');
            option.value = session.id;
            option.textContent = `${session.course_name} - ${session.date}`;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading sessions:', error);
        showAttendanceMessage('Error loading sessions', 'error');
    }
}

// Load session details
async function loadSessionDetails() {
    const sessionId = document.getElementById('sessionSelect').value;
    if (!sessionId) return;

    try {
        const response = await fetch(`/api/attendance/sessions/${sessionId}/`, {
            method: 'GET',
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        });

        if (!response.ok) throw new Error('Failed to load session details');

        const session = await response.json();
        currentSession = session;

        // Display session details
        const detailsContainer = document.getElementById('sessionDetailsContainer');
        detailsContainer.innerHTML = `
            <div class="mb-3">
                <h6 class="text-muted mb-1">Course</h6>
                <p class="mb-2"><strong>${session.course_name}</strong></p>
            </div>
            <div class="mb-3">
                <h6 class="text-muted mb-1">Date</h6>
                <p class="mb-2"><strong>${new Date(session.date).toLocaleDateString()}</strong></p>
            </div>
            <div class="mb-3">
                <h6 class="text-muted mb-1">Time</h6>
                <p class="mb-2"><strong>${session.start_time} - ${session.end_time}</strong></p>
            </div>
            <div class="mb-3">
                <h6 class="text-muted mb-1">Total Students</h6>
                <p class="mb-2"><strong>${session.enrolled_students || 0}</strong></p>
            </div>
            <div class="progress" style="height: 20px;">
                <div class="progress-bar" role="progressbar" style="width: ${(session.marked || 0) / (session.enrolled_students || 1) * 100}%">
                    ${session.marked || 0} Marked
                </div>
            </div>
        `;

        // Load recent attendance for this session
        await loadRecentAttendance(sessionId);
    } catch (error) {
        console.error('Error loading session details:', error);
        showAttendanceMessage('Error loading session details', 'error');
    }
}

// Load recent attendance
async function loadRecentAttendance(sessionId) {
    try {
        const response = await fetch(`/api/attendance/sessions/${sessionId}/records/`, {
            method: 'GET',
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        });

        if (!response.ok) throw new Error('Failed to load attendance records');

        const records = await response.json();
        const container = document.getElementById('recentAttendanceContainer');

        if (records.length === 0) {
            container.innerHTML = '<p class="text-muted">No attendance records</p>';
            return;
        }

        let html = '';
        records.slice(0, 10).forEach(record => {
            const statusClass = {
                'present': 'success',
                'absent': 'danger',
                'late': 'warning'
            }[record.status] || 'info';

            html += `
                <div class="d-flex justify-content-between align-items-center py-2 border-bottom">
                    <div>
                        <strong>${record.student_name}</strong>
                        <small class="d-block text-muted">${record.time}</small>
                    </div>
                    <span class="badge bg-${statusClass}">${record.status.toUpperCase()}</span>
                </div>
            `;
        });

        container.innerHTML = html;
    } catch (error) {
        console.error('Error loading recent attendance:', error);
    }
}

// Start attendance webcam
async function startAttendanceWebcam() {
    try {
        if (!attendanceFaceDetectionLoaded) {
            await initializeAttendanceFaceDetection();
        }

        if (!currentSession) {
            showAttendanceMessage('Please select a session first', 'warning');
            return;
        }

        const video = document.getElementById('attendanceWebcam');
        attendanceVideoStream = await navigator.mediaDevices.getUserMedia({
            video: {
                width: { ideal: 1280 },
                height: { ideal: 720 },
                facingMode: 'user'
            },
            audio: false
        });

        video.srcObject = attendanceVideoStream;
        document.getElementById('startAttendanceWebcamBtn').style.display = 'none';
        document.getElementById('stopAttendanceWebcamBtn').style.display = 'inline-block';
        document.getElementById('captureAttendanceBtn').style.display = 'inline-block';
        document.getElementById('webcamStatus').className = 'badge bg-success';
        document.getElementById('webcamStatus').innerHTML = '<i class="fas fa-video"></i> Active';

        // Start face detection
        detectFacesForAttendance(video);
        showAttendanceMessage('Webcam started. Faces will be recognized automatically.', 'success');
    } catch (error) {
        console.error('Error accessing webcam:', error);
        showAttendanceMessage('Unable to access webcam', 'error');
    }
}

// Stop attendance webcam
function stopAttendanceWebcam() {
    if (attendanceVideoStream) {
        attendanceVideoStream.getTracks().forEach(track => track.stop());
        attendanceVideoStream = null;
    }

    document.getElementById('attendanceWebcam').srcObject = null;
    document.getElementById('startAttendanceWebcamBtn').style.display = 'inline-block';
    document.getElementById('stopAttendanceWebcamBtn').style.display = 'none';
    document.getElementById('captureAttendanceBtn').style.display = 'none';
    document.getElementById('webcamStatus').className = 'badge bg-danger';
    document.getElementById('webcamStatus').innerHTML = '<i class="fas fa-video"></i> Offline';
    document.getElementById('faceOverlay').innerHTML = '';

    showAttendanceMessage('Webcam stopped', 'info');
}

// Detect faces for attendance
async function detectFacesForAttendance(video) {
    if (!attendanceVideoStream) return;

    try {
        const detections = await faceapi
            .detectAllFaces(video, new faceapi.TinyFaceDetectorOptions())
            .withFaceLandmarks()
            .withFaceDescriptors();

        // Draw faces on overlay
        const overlay = document.getElementById('faceOverlay');
        overlay.innerHTML = '';

        if (detections.length > 0) {
            document.getElementById('faceInfo').style.display = 'block';
            let infoHtml = `<div><strong>${detections.length} face(s) detected</strong></div>`;

            detections.forEach((detection, index) => {
                const { x, y, width, height } = detection.detection.box;
                
                // Draw face box
                const box = document.createElement('div');
                box.className = 'face-box';
                box.style.left = x + 'px';
                box.style.top = y + 'px';
                box.style.width = width + 'px';
                box.style.height = height + 'px';
                overlay.appendChild(box);

                // Draw label
                const label = document.createElement('div');
                label.className = 'face-label';
                label.style.left = x + 'px';
                label.style.top = (y - 25) + 'px';
                label.textContent = `Face ${index + 1}`;
                overlay.appendChild(label);

                infoHtml += `<div class="mt-2"><small>Face ${index + 1} confidence: ${Math.round(detection.detection.score * 100)}%</small></div>`;
            });

            document.getElementById('faceInfoContent').innerHTML = infoHtml;
        } else {
            document.getElementById('faceInfo').style.display = 'none';
        }
    } catch (error) {
        console.error('Error detecting faces:', error);
    }

    requestAnimationFrame(() => detectFacesForAttendance(video));
}

// Capture attendance
async function captureAttendance() {
    const video = document.getElementById('attendanceWebcam');
    const canvas = document.getElementById('attendanceCanvas');

    if (!currentSession) {
        showAttendanceMessage('Please select a session', 'warning');
        return;
    }

    try {
        document.getElementById('recognitionStatus').style.display = 'block';
        
        // Prepare image
        const ctx = canvas.getContext('2d');
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        ctx.translate(canvas.width, 0);
        ctx.scale(-1, 1);
        ctx.drawImage(video, 0, 0);

        canvas.toBlob(async (blob) => {
            const formData = new FormData();
            formData.append('image', blob);
            formData.append('session_id', currentSession.id);

            try {
                const response = await fetch('/api/attendance/mark_by_face/', {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-CSRFToken': getCookie('csrftoken')
                    }
                });

                const result = await response.json();

                if (response.ok) {
                    showAttendanceMessage(`Attendance marked for ${result.student_name}`, 'success');
                    // Update recent attendance
                    await loadRecentAttendance(currentSession.id);
                } else {
                    showAttendanceMessage(result.detail || 'Failed to mark attendance', 'error');
                }
            } catch (error) {
                showAttendanceMessage('Error marking attendance: ' + error.message, 'error');
            } finally {
                document.getElementById('recognitionStatus').style.display = 'none';
            }
        }, 'image/jpeg', 0.95);
    } catch (error) {
        console.error('Error capturing attendance:', error);
        showAttendanceMessage('Error capturing image', 'error');
        document.getElementById('recognitionStatus').style.display = 'none';
    }
}

// Manual attendance submission
document.addEventListener('DOMContentLoaded', function() {
    // Set today's date as default
    const today = new Date().toISOString().split('T')[0];
    const dateInput = document.getElementById('manualDate');
    if (dateInput) {
        dateInput.value = today;
    }

    // Load students for manual entry
    loadStudentsForManualEntry();

    // Handle form submission
    const form = document.getElementById('manualAttendanceForm');
    if (form) {
        form.addEventListener('submit', submitManualAttendance);
    }

    // Load sessions
    loadSessions();
    initializeAttendanceFaceDetection();
});

// Load students for manual entry
async function loadStudentsForManualEntry() {
    try {
        const response = await fetch('/api/students/', {
            method: 'GET',
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        });

        if (!response.ok) throw new Error('Failed to load students');

        const students = await response.json();
        const select = document.getElementById('manualStudent');

        students.forEach(student => {
            const option = document.createElement('option');
            option.value = student.id;
            option.textContent = student.user.email;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading students:', error);
    }
}

// Submit manual attendance
async function submitManualAttendance(e) {
    e.preventDefault();

    const studentId = document.getElementById('manualStudent').value;
    const status = document.getElementById('manualStatus').value;
    const date = document.getElementById('manualDate').value;
    const sessionId = document.getElementById('sessionSelect').value;

    if (!sessionId) {
        showAttendanceMessage('Please select a session', 'warning');
        return;
    }

    try {
        const response = await fetch(`/api/attendance/sessions/${sessionId}/mark_attendance/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                student_id: studentId,
                status: status,
                date: date
            })
        });

        const result = await response.json();

        if (response.ok) {
            showAttendanceMessage('Attendance marked successfully', 'success');
            document.getElementById('manualAttendanceForm').reset();
            await loadRecentAttendance(sessionId);
        } else {
            showAttendanceMessage(result.detail || 'Failed to mark attendance', 'error');
        }
    } catch (error) {
        console.error('Error submitting attendance:', error);
        showAttendanceMessage('Error submitting attendance', 'error');
    }
}

// Show message
function showAttendanceMessage(message, type = 'info') {
    const container = document.getElementById('attendanceMessages');
    const alertClass = {
        'success': 'alert-success',
        'error': 'alert-danger',
        'warning': 'alert-warning',
        'info': 'alert-info'
    }[type] || 'alert-info';

    const alertHtml = `
        <div class="alert ${alertClass} alert-dismissible fade show" role="alert">
            <strong>${type.charAt(0).toUpperCase() + type.slice(1)}:</strong> ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;

    container.insertAdjacentHTML('beforeend', alertHtml);

    setTimeout(() => {
        const alert = container.querySelector('.alert');
        if (alert) alert.remove();
    }, 5000);
}

// Get CSRF token
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
