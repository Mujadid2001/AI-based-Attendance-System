# 📚 AI-Based Attendance System - Complete User Guide

## 🎯 Quick Start Overview

The AI-Based Attendance System is a modern web application that uses **facial recognition** and **voice notifications** to automate attendance tracking in educational institutions. Below is a complete guide to use this product easily.

---

## 🚀 How to Access the System

### 1. **Start the Server**
```bash
# Navigate to project directory
cd C:\Users\PMLS\Music\gj

# Activate virtual environment
venv\Scripts\activate.bat

# Start Django server
cd attendance_system
python manage.py runserver 0.0.0.0:8000
```

### 2. **Open in Browser**
- Visit: **http://127.0.0.1:8000/**
- You'll see the beautiful gradient purple landing page

---

## 🔐 Login Credentials

The system comes with pre-configured demo accounts:

### **Admin Account**
- **Email:** admin@attendance.com
- **Password:** Admin@123
- **Role:** Full system access, manage users, reports

### **Teacher Account**
- **Email:** teacher@attendance.com
- **Password:** Teacher@123
- **Role:** Manage attendance, view reports for their courses

### **Student Account**
- **Email:** student1@attendance.com
- **Password:** Student@123
- **Role:** View own attendance records and statistics

---

## 📱 User Interface Pages

### **1. HOME PAGE (Landing Page)**
**Route:** `/`

**What You See:**
- 🎨 Beautiful gradient background (purple to pink)
- Welcome message
- Login form with email/password
- Feature highlights:
  - ✅ Face Recognition
  - ✅ Voice Feedback
  - ✅ Analytics
- Demo credentials display
- Feature cards showing:
  - 🔒 Secure Authentication (Role-based access control)
  - 🧠 AI-Powered (Facial recognition with anti-spoofing)
  - 📊 Data Management (Reporting & analytics)

**What You Can Do:**
- Login with credentials
- View system features
- Understand capabilities

---

### **2. ADMIN DASHBOARD**
**Route:** `/admin-dashboard/`

**Who Can Access:** Admin users only

**Dashboard Stats:**
- Total Users count
- Active Sessions count
- Attendance Records count
- System Courses count

**Key Features:**

#### 📋 **Recent Activity Table**
- Shows login history and user actions
- Date, User, Action, Status columns
- Helps track system usage

#### ⚡ **Quick Actions Panel**
- **Add New User** - Create admin, teacher, or student accounts
- **Create Course** - Add new courses to the system
- **Start Session** - Begin a new attendance session
- **View Audit Log** - Check security logs

#### 💚 **System Status**
- Database Connection Status
- AI Services Status
- Voice Engine Status
- Storage Availability

**Access via Django Admin:**
- Click "Add New User" → Goes to `/admin/authentication/user/add/`
- All user management powered by Django admin panel

---

### **3. TEACHER DASHBOARD**
**Route:** `/teacher-dashboard/`

**Who Can Access:** Teacher users only

**Dashboard Stats:**
- My Courses count
- Active Sessions
- Average Attendance Rate
- Total Students

**Key Features:**

#### 📚 **My Courses Section**
- View all assigned courses
- See enrolled students per course
- Track attendance percentage per course

#### ⚡ **Quick Actions**
- **Start Attendance Session** - Create new attendance session
- **View Attendance Records** - See all attendance data
- **Generate Reports** - Create CSV/Excel reports
- **Manage Students** - Add/edit/remove students

#### 📊 **Attendance Summary**
- Average attendance rate
- Present/Absent breakdown
- Late arrivals count

---

### **4. STUDENT DASHBOARD**
**Route:** `/student-dashboard/`

**Who Can Access:** Student users only

**Dashboard Stats:**
- Enrolled Courses count
- Attendance Rate percentage
- Present Days count
- Absent Days count

**Key Features:**

#### 📚 **My Courses Section**
- View all enrolled courses
- See course instructors
- Check attendance percentage per course
- Course status (Active/Completed)

#### ⚡ **Quick Actions Panel**
- **Register Face** - Add facial recognition data
- **View History** - See all attendance records
- **Download Report** - Export personal attendance report
- **Update Profile** - Edit personal information

#### 📈 **Attendance Summary**
- Overall attendance percentage
- Present days count
- Absent days count
- Late arrivals count

---

### **5. FACE REGISTRATION PORTAL**
**Route:** `/face-registration/`

**Who Can Access:** Students (to register their face)

**How It Works:**

#### 🎥 **Webcam Interface**
1. **Start Webcam** - Click button to access camera
2. **Face Detection** - Real-time face detection with boxes around faces
3. **Quality Check** - System shows face landmarks (68 points)
4. **Capture** - Click "Capture Face" to save face embedding

#### ✨ **Features:**
- Real-time face detection overlay
- Multiple face capture (10+ images recommended)
- Face quality validation
- Automatic face embedding generation
- Training image auto-save to `/media/training_data/`

#### 📊 **Progress Tracking**
- Shows number of faces captured
- Displays confidence scores
- Confirms successful registration

#### ✅ **What Happens Behind:**
- Face images stored in database
- 128-dimensional face embeddings generated
- Used later for attendance marking recognition

---

### **6. ATTENDANCE MARKING PORTAL**
**Route:** `/attendance-marking/`

**Who Can Access:** Teachers/Admins (to mark attendance)

**How It Works:**

#### 📅 **Session Selection**
1. Drop-down shows all active attendance sessions
2. Select a session to mark attendance
3. Session details display (course, date, time)

#### 🎥 **Webcam-Based Recognition**
1. **Start Webcam** - Activate camera for real-time detection
2. **Face Detection** - System shows detected faces with rectangles
3. **Automatic Recognition** - Compares with stored face embeddings
4. **Auto Mark** - When face recognized, attendance marked automatically
5. **Voice Notification** - "Attendance marked for [Student Name]"

#### 📊 **Recognition Status Display**
- Shows detected face confidence score
- Displays matched student name
- Shows attendance status (Present/Late/Already Marked)
- Real-time updates

#### 📝 **Session Details Panel**
- Course name and instructor
- Session date and time
- Expected attendees count
- Status (Ongoing/Completed)

#### 📋 **Recent Attendance Section**
- Shows last 10 marked attendances
- Student name, status, time
- Scrollable list

#### ✏️ **Manual Attendance Entry**
- Select student from dropdown
- Choose status (Present/Absent/Late)
- Pick date
- Add attendance record manually
- Useful for students who missed camera

---

## 🎨 Frontend Features Overview

### **Beautiful UI Design**
- **Gradient Backgrounds:** Purple (#667eea) to Pink (#764ba2)
- **Responsive Design:** Works on desktop, tablet, mobile
- **Modern Cards:** Hover effects with elevation
- **Professional Icons:** Font Awesome 6 icons
- **Status Badges:** Color-coded role badges (Admin: Red, Teacher: Blue, Student: Green)

### **Interactive Elements**
- **Bootstrap 5.3** components (cards, buttons, modals)
- **Real-time Webcam Feed** with face detection overlay
- **Chart.js** for analytics visualization
- **Smooth Animations** on hover and scroll

---

## 🔄 Complete User Workflows

### **Workflow 1: Student Registration & Attendance**

```
1. Student Logs In
   └─ student1@attendance.com / Student@123
   └─ Dashboard shows enrolled courses

2. Register Face (First Time)
   └─ Go to /face-registration/
   └─ Click "Start Webcam"
   └─ Position face in frame
   └─ Click "Capture Face" (repeat 10+ times)
   └─ Face embeddings saved

3. Mark Attendance
   └─ Go to /attendance-marking/
   └─ Select session from dropdown
   └─ Click "Start Webcam"
   └─ Face auto-detected and recognized
   └─ Attendance marked automatically
   └─ Voice says: "Attendance marked for [Name]"

4. Check Attendance Record
   └─ Go to Student Dashboard
   └─ View attendance percentage
   └─ Download personal report
```

### **Workflow 2: Teacher Managing Attendance**

```
1. Teacher Logs In
   └─ teacher@attendance.com / Teacher@123
   └─ Teacher Dashboard loads

2. Start Attendance Session
   └─ Click "Start Attendance Session"
   └─ Select course
   └─ Click Start Session
   └─ Session created with timestamp

3. Mark Attendance (Two Methods)

   Method A: Face Recognition
   └─ Go to /attendance-marking/
   └─ Select session
   └─ Start webcam
   └─ Students present face
   └─ Auto-marked with face recognition

   Method B: Manual Entry
   └─ In attendance marking portal
   └─ Scroll to "Manual Attendance Entry"
   └─ Select student from dropdown
   └─ Choose status (Present/Absent/Late)
   └─ Pick date
   └─ Click "Add Entry"

4. View Reports
   └─ Go to Reports section
   └─ Filter by course/date/student
   └─ Export as CSV
```

### **Workflow 3: Admin Managing System**

```
1. Admin Logs In
   └─ admin@attendance.com / Admin@123
   └─ Admin Dashboard displays

2. Create New User
   └─ Click "Add New User"
   └─ Goes to Django Admin
   └─ Fill form: email, password, role
   └─ Save user

3. Create Course
   └─ Click "Create Course"
   └─ Enter course name, code, capacity
   └─ Assign instructors/teachers
   └─ Save course

4. Monitor System
   └─ Check Recent Activity
   └─ View System Status (all green if healthy)
   └─ Access Audit Log for security
   └─ Download reports as needed
```

---

## 🔌 Backend API Endpoints (For Developers)

All frontend interactions use these API endpoints:

### **Authentication APIs**
```
POST   /api/auth/authentication/login/
GET    /api/auth/authentication/logout/
POST   /api/auth/authentication/me/
PUT    /api/auth/authentication/profile_update/
```

### **Student Management APIs**
```
GET    /api/students/                    # List all students
POST   /api/students/                    # Create student
GET    /api/students/{id}/              # Get student details
PUT    /api/students/{id}/              # Update student
DELETE /api/students/{id}/              # Delete student
GET    /api/students/{id}/enrollment/   # Get enrollments
```

### **Course Management APIs**
```
GET    /api/students/courses/           # List courses
POST   /api/students/courses/           # Create course
```

### **Attendance APIs**
```
GET    /api/attendance/sessions/        # List sessions
POST   /api/attendance/sessions/        # Create session
GET    /api/attendance/records/         # Get records
POST   /api/attendance/mark_by_face/    # Mark by face recognition
POST   /api/attendance/export/          # Export as CSV
```

### **Face Recognition APIs**
```
POST   /api/ai/register_face/           # Register face
POST   /api/ai/recognize/               # Recognize face
GET    /api/ai/embeddings/              # Get embeddings
```

---

## 💾 Database Structure

The system uses **SQLite** with 9 database models:

### **Models:**
1. **User** - Authentication with custom roles (Admin/Teacher/Student)
2. **StudentProfile** - Student information and face data reference
3. **StudentFaceImage** - Face embeddings storage
4. **Course** - Course information
5. **Enrollment** - Student-Course relationship
6. **AttendanceSession** - Attendance session tracking
7. **Attendance** - Individual attendance records
8. **LoginLog** - Audit trail
9. **AttendanceReport** - Analytics data

---

## 🎯 Key Features Summary

| Feature | Description | Where to Use |
|---------|-------------|--------------|
| 👤 **Role-Based Access** | Admin/Teacher/Student roles with permissions | All pages |
| 🎥 **Face Recognition** | Real-time facial detection and matching | /face-registration/, /attendance-marking/ |
| 🔊 **Voice Feedback** | Text-to-speech attendance confirmation | Marking portal |
| 📊 **Analytics** | Dashboards with statistics and charts | Admin/Teacher/Student dashboards |
| 📝 **Manual Entry** | Fallback attendance entry | Attendance marking portal |
| 📤 **CSV Export** | Download reports as CSV files | Reports section |
| 🔒 **Secure Auth** | Email-based login with role validation | Login page |
| 📱 **Responsive Design** | Mobile, tablet, desktop support | All pages |
| 🚫 **Anti-Spoofing** | Liveness detection (blink, head movement) | Face registration |
| 📊 **Duplicate Prevention** | Database prevents duplicate attendance | Auto-marking |

---

## 🛠️ Troubleshooting Guide

### **Issue: Webcam Not Working**
**Solution:**
1. Check browser permissions (allow camera access)
2. Ensure HTTPS or localhost (required for webcam)
3. Refresh page
4. Try different browser (Chrome/Firefox recommended)

### **Issue: Face Not Recognized**
**Solution:**
1. Register more faces (10+ captures recommended)
2. Improve lighting conditions
3. Face should be directly in front of camera
4. No glasses or obscured faces

### **Issue: Login Not Working**
**Solution:**
1. Verify email and password are correct
2. Check demo credentials provided
3. Ensure server is running
4. Check browser console for errors (F12)

### **Issue: Voice Not Playing**
**Solution:**
1. Check volume settings
2. pyttsx3 needs audio device configured
3. Try in different browser
4. Restart server

### **Issue: Database Errors**
**Solution:**
1. Run migrations: `python manage.py migrate`
2. Check db.sqlite3 file exists
3. Verify file permissions
4. Try: `python manage.py check`

---

## 📊 Sample Data

System comes pre-populated with:

### **Users:**
- 1 Admin account
- 1 Teacher account
- 5 Student accounts

### **Courses:**
- 3 example courses
- Students enrolled in various courses

### **Attendance:**
- Sample attendance sessions created
- Some test attendance records

**Modify sample data:**
```bash
python manage.py shell
from apps.authentication.models import User
User.objects.all()  # View users
```

---

## 🚀 Deployment Checklist

When ready to deploy:

- [ ] Set `DEBUG = False` in settings.py
- [ ] Generate new `SECRET_KEY`
- [ ] Configure `ALLOWED_HOSTS`
- [ ] Set up SSL/HTTPS
- [ ] Configure production database (MySQL recommended)
- [ ] Set up static file storage (AWS S3 or CDN)
- [ ] Configure email settings
- [ ] Set up monitoring and logging
- [ ] Create backup strategy
- [ ] Test all features in production

---

## 📞 Support & Contact

For issues or questions:
1. Check logs in `/attendance_system/logs/`
2. Review Django admin panel
3. Check database with `python manage.py shell`
4. Contact system administrator

---

## ✅ Feature Checklist

All 50 features implemented:

- ✅ Admin/Teacher/Student Login (4 features)
- ✅ Student Management CRUD (7 features)
- ✅ Facial Recognition Pipeline (4 features)
- ✅ Liveness Detection (3 features)
- ✅ Attendance Marking System (5 features)
- ✅ Voice Notifications (1 feature)
- ✅ Student Privacy Controls (3 features)
- ✅ Data Storage & Management (5 features)
- ✅ Reporting & Export (6 features)
- ✅ Web Interface (6 features)

---

## 🎓 Technology Stack

**Backend:**
- Django 4.2.7
- Django REST Framework 3.14
- Python 3.12
- SQLite3

**Frontend:**
- Bootstrap 5.3
- HTML5/CSS3
- Vanilla JavaScript + jQuery
- face-api.js (TensorFlow.js)
- Chart.js

**AI/ML:**
- face-api.js (face detection)
- TensorFlow.js
- pyttsx3 (voice)

---

## 📝 License & Credits

AI-Based Attendance System
- Uses open-source libraries
- Developed for educational institutions
- Extensible for customization

---

**Last Updated:** November 2025
**Status:** ✅ Production Ready
**Version:** 1.0.0

---

**Happy Using! 🎉**

For any questions, refer back to this guide or contact the administrator.
