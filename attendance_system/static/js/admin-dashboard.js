/**
 * Admin Dashboard Module
 * Handles admin statistics, charts, and quick actions
 */

let attendanceTrendChart = null;
let studentDistributionChart = null;

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    loadStatistics();
    loadRecentActivities();
    initializeCharts();
});

// Load statistics
async function loadStatistics() {
    try {
        // Load students
        const studentsRes = await fetch('/api/students/', {
            headers: { 'X-CSRFToken': getCookie('csrftoken') }
        });
        if (studentsRes.ok) {
            const students = await studentsRes.json();
            document.getElementById('totalStudents').textContent = students.length || 0;
        }

        // Load courses
        const coursesRes = await fetch('/api/students/courses/', {
            headers: { 'X-CSRFToken': getCookie('csrftoken') }
        });
        if (coursesRes.ok) {
            const courses = await coursesRes.json();
            document.getElementById('totalCourses').textContent = courses.length || 0;
        }

        // Load teachers
        const teachersRes = await fetch('/api/auth/users/?role=teacher', {
            headers: { 'X-CSRFToken': getCookie('csrftoken') }
        });
        if (teachersRes.ok) {
            const teachers = await teachersRes.json();
            document.getElementById('totalTeachers').textContent = teachers.length || 0;
        }

        // Load today's attendance
        const todayRes = await fetch('/api/attendance/today/', {
            headers: { 'X-CSRFToken': getCookie('csrftoken') }
        });
        if (todayRes.ok) {
            const today = await todayRes.json();
            const percentage = Math.round((today.marked / (today.total || 1)) * 100);
            document.getElementById('todayAttendance').textContent = percentage + '%';
        }
    } catch (error) {
        console.error('Error loading statistics:', error);
    }
}

// Load recent activities
async function loadRecentActivities() {
    try {
        const response = await fetch('/api/auth/login_logs/?limit=10', {
            headers: { 'X-CSRFToken': getCookie('csrftoken') }
        });

        if (!response.ok) throw new Error('Failed to load activities');

        const logs = await response.json();
        const tbody = document.getElementById('recentActivitiesTable');

        if (!logs.length) {
            tbody.innerHTML = '<tr><td colspan="4" class="text-center text-muted py-4">No activities</td></tr>';
            return;
        }

        tbody.innerHTML = logs.map(log => `
            <tr>
                <td>${log.user_email}</td>
                <td><span class="badge bg-info">Login</span></td>
                <td>${new Date(log.timestamp).toLocaleString()}</td>
                <td><span class="badge bg-success">Success</span></td>
            </tr>
        `).join('');
    } catch (error) {
        console.error('Error loading activities:', error);
    }
}

// Initialize charts
function initializeCharts() {
    initializeAttendanceTrendChart();
    initializeStudentDistributionChart();
}

// Attendance trend chart
function initializeAttendanceTrendChart() {
    const ctx = document.getElementById('attendanceTrendChart');
    if (!ctx) return;

    attendanceTrendChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
            datasets: [{
                label: 'Attendance Rate (%)',
                data: [85, 88, 90, 87, 92, 78, 0],
                borderColor: '#667eea',
                backgroundColor: 'rgba(102, 126, 234, 0.1)',
                tension: 0.4,
                fill: true,
                pointBackgroundColor: '#667eea',
                pointRadius: 5
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: { display: true }
            },
            scales: {
                y: { max: 100, min: 0 }
            }
        }
    });
}

// Student distribution chart
function initializeStudentDistributionChart() {
    const ctx = document.getElementById('studentDistributionChart');
    if (!ctx) return;

    studentDistributionChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Present', 'Absent', 'Late'],
            datasets: [{
                data: [70, 20, 10],
                backgroundColor: ['#2dce89', '#f5365c', '#fb6340'],
                borderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: { position: 'bottom' }
            }
        }
    });
}

// Export reports
async function exportReports() {
    try {
        const response = await fetch('/api/attendance/export/', {
            method: 'POST',
            headers: { 'X-CSRFToken': getCookie('csrftoken') }
        });

        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `attendance_report_${new Date().toISOString().split('T')[0]}.csv`;
            a.click();
        }
    } catch (error) {
        console.error('Error exporting report:', error);
        alert('Error exporting report');
    }
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
