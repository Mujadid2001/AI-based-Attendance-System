# AI-Based Attendance System API Documentation

## Overview
This is a completely decoupled REST API backend for an AI-based attendance system. Any frontend application can consume this API by configuring the base URL and handling JWT authentication.

**Base URL**: `http://localhost:8000/api` (development)  
**Production URL**: Configure via `CORS_ALLOWED_ORIGINS` environment variable

## Key Features
- ✅ **Completely Decoupled**: No frontend dependencies
- ✅ **JWT Authentication**: Secure token-based authentication
- ✅ **RESTful Design**: Standard HTTP methods and status codes
- ✅ **CORS Enabled**: Configurable cross-origin resource sharing
- ✅ **Face Recognition**: AI-powered facial recognition for attendance
- ✅ **Voice Notifications**: Audio feedback for attendance marking
- ✅ **Comprehensive Admin Panel**: Django admin for backend management

---

## Authentication

### 1. Register User
**Endpoint**: `POST /api/auth/register/`  
**Permission**: Public  
**Description**: Register a new user account

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!",
  "password_confirm": "SecurePassword123!",
  "first_name": "John",
  "last_name": "Doe",
  "role": "student"
}
```

**Response** (201 Created):
```json
{
  "message": "Registration successful. Please check your email to verify your account.",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "role": "student",
    "is_active": true
  },
  "email_sent": true
}
```

### 2. Login
**Endpoint**: `POST /api/token/`  
**Permission**: Public  
**Description**: Obtain JWT access and refresh tokens

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}
```

**Response** (200 OK):
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "role": "student"
  }
}
```

### 3. Refresh Token
**Endpoint**: `POST /api/token/refresh/`  
**Permission**: Public  
**Description**: Obtain new access token using refresh token

**Request Body**:
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Response** (200 OK):
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### 4. Verify Token
**Endpoint**: `POST /api/token/verify/`  
**Permission**: Public  
**Description**: Verify if a token is valid

**Request Body**:
```json
{
  "token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Response** (200 OK):
```json
{}
```

---

## Students Management

### 1. List Students
**Endpoint**: `GET /api/students/`  
**Permission**: Authenticated  
**Description**: Get list of all students

**Query Parameters**:
- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 20)
- `search`: Search by name, email, or roll number
- `department`: Filter by department
- `semester`: Filter by semester

**Response** (200 OK):
```json
{
  "count": 100,
  "next": "http://localhost:8000/api/students/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "user": {
        "id": 1,
        "email": "student@example.com",
        "first_name": "John",
        "last_name": "Doe"
      },
      "roll_number": "CS2021001",
      "department": "Computer Science",
      "semester": 5,
      "is_active": true,
      "profile_picture": "/media/profiles/student1.jpg",
      "enrolled_courses": [1, 2, 3]
    }
  ]
}
```

### 2. Create Student
**Endpoint**: `POST /api/students/`  
**Permission**: Admin/Teacher  
**Description**: Create new student profile

**Request Body**:
```json
{
  "email": "newstudent@example.com",
  "password": "SecurePassword123!",
  "first_name": "Jane",
  "last_name": "Smith",
  "roll_number": "CS2021002",
  "department": "Computer Science",
  "semester": 5
}
```

### 3. Get Student Details
**Endpoint**: `GET /api/students/{id}/`  
**Permission**: Authenticated  
**Description**: Get detailed information about a specific student

### 4. Update Student
**Endpoint**: `PUT/PATCH /api/students/{id}/`  
**Permission**: Admin/Teacher/Self  
**Description**: Update student information

### 5. Delete Student
**Endpoint**: `DELETE /api/students/{id}/`  
**Permission**: Admin  
**Description**: Delete student profile

---

## Courses Management

### 1. List Courses
**Endpoint**: `GET /api/students/courses/`  
**Permission**: Authenticated  
**Description**: Get list of all courses

**Response** (200 OK):
```json
{
  "count": 10,
  "results": [
    {
      "id": 1,
      "code": "CS101",
      "name": "Introduction to Programming",
      "description": "Basic programming concepts",
      "instructor": {
        "id": 2,
        "name": "Prof. Smith"
      },
      "semester": 1,
      "academic_year": "2023-2024",
      "is_active": true,
      "enrolled_students_count": 45
    }
  ]
}
```

### 2. Create Course
**Endpoint**: `POST /api/students/courses/`  
**Permission**: Admin/Teacher  
**Description**: Create new course

### 3. Enroll Student in Course
**Endpoint**: `POST /api/students/courses/{course_id}/enroll/`  
**Permission**: Admin/Teacher  
**Description**: Enroll a student in a course

**Request Body**:
```json
{
  "student_id": 1
}
```

---

## Attendance Management

### 1. Create Attendance Session
**Endpoint**: `POST /api/attendance/sessions/`  
**Permission**: Teacher/Admin  
**Description**: Create new attendance session for a course

**Request Body**:
```json
{
  "course": 1,
  "date": "2024-12-12",
  "start_time": "09:00:00",
  "end_time": "10:30:00",
  "location": "Room 301",
  "session_type": "lecture"
}
```

**Response** (201 Created):
```json
{
  "id": 1,
  "course": {
    "id": 1,
    "code": "CS101",
    "name": "Introduction to Programming"
  },
  "date": "2024-12-12",
  "start_time": "09:00:00",
  "end_time": "10:30:00",
  "location": "Room 301",
  "session_type": "lecture",
  "is_active": true,
  "total_students": 45,
  "present_count": 0,
  "absent_count": 0
}
```

### 2. List Attendance Sessions
**Endpoint**: `GET /api/attendance/sessions/`  
**Permission**: Authenticated  
**Description**: Get list of attendance sessions

**Query Parameters**:
- `course`: Filter by course ID
- `date`: Filter by date (YYYY-MM-DD)
- `is_active`: Filter by active status

### 3. Mark Attendance
**Endpoint**: `POST /api/attendance/mark/`  
**Permission**: Teacher/Admin  
**Description**: Manually mark attendance for a student

**Request Body**:
```json
{
  "session": 1,
  "student": 1,
  "status": "present",
  "remarks": "On time"
}
```

### 4. Get Attendance Records
**Endpoint**: `GET /api/attendance/records/`  
**Permission**: Authenticated  
**Description**: Get attendance records

**Query Parameters**:
- `session`: Filter by session ID
- `student`: Filter by student ID
- `course`: Filter by course ID
- `status`: Filter by status (present/absent/late)

### 5. Export Attendance Report
**Endpoint**: `GET /api/attendance/export/`  
**Permission**: Teacher/Admin  
**Description**: Export attendance data as CSV

**Query Parameters**:
- `course`: Course ID
- `start_date`: Start date (YYYY-MM-DD)
- `end_date`: End date (YYYY-MM-DD)
- `format`: Export format (csv/excel)

---

## AI Core (Face Recognition)

### 1. Register Face
**Endpoint**: `POST /api/ai/register-face/`  
**Permission**: Authenticated  
**Description**: Register student's face for recognition
**Content-Type**: `multipart/form-data`

**Request Body** (Form Data):
- `student_id`: Student ID (integer)
- `images`: Multiple face images (files)

**Response** (200 OK):
```json
{
  "message": "Face registered successfully",
  "student_id": 1,
  "images_processed": 5,
  "face_encodings_saved": 5
}
```

### 2. Recognize Face
**Endpoint**: `POST /api/ai/recognize-face/`  
**Permission**: Authenticated  
**Description**: Recognize student from face image
**Content-Type**: `multipart/form-data`

**Request Body** (Form Data):
- `image`: Face image file
- `session_id`: Attendance session ID (optional)

**Response** (200 OK):
```json
{
  "recognized": true,
  "student": {
    "id": 1,
    "name": "John Doe",
    "roll_number": "CS2021001"
  },
  "confidence": 0.95,
  "attendance_marked": true,
  "session_id": 1
}
```

### 3. Bulk Face Recognition
**Endpoint**: `POST /api/ai/recognize-bulk/`  
**Permission**: Teacher/Admin  
**Description**: Recognize multiple faces from group photo
**Content-Type**: `multipart/form-data`

**Request Body** (Form Data):
- `image`: Group photo
- `session_id`: Attendance session ID

**Response** (200 OK):
```json
{
  "total_faces_detected": 10,
  "recognized_students": 8,
  "unrecognized_faces": 2,
  "students": [
    {
      "student_id": 1,
      "name": "John Doe",
      "confidence": 0.95
    }
  ],
  "attendance_marked": true
}
```

### 4. Get Training Status
**Endpoint**: `GET /api/ai/training-status/`  
**Permission**: Admin  
**Description**: Get face recognition model training status

**Response** (200 OK):
```json
{
  "total_students": 100,
  "students_with_faces": 95,
  "total_face_samples": 475,
  "model_trained": true,
  "last_training": "2024-12-12T10:30:00Z"
}
```

---

## Error Responses

All endpoints follow standard HTTP status codes and return errors in this format:

**400 Bad Request**:
```json
{
  "error": "Invalid input data",
  "field_errors": {
    "email": ["This field is required."],
    "password": ["Password must be at least 8 characters."]
  }
}
```

**401 Unauthorized**:
```json
{
  "detail": "Authentication credentials were not provided."
}
```

**403 Forbidden**:
```json
{
  "detail": "You do not have permission to perform this action."
}
```

**404 Not Found**:
```json
{
  "detail": "Not found."
}
```

**500 Internal Server Error**:
```json
{
  "error": "An unexpected error occurred. Please try again later."
}
```

---

## Authentication Flow

### For Frontend Applications:

1. **Initial Login**:
   ```
   POST /api/token/
   → Store access & refresh tokens
   ```

2. **API Requests**:
   ```
   Add header: Authorization: Bearer {access_token}
   ```

3. **Token Refresh** (when access token expires):
   ```
   POST /api/token/refresh/
   → Update access token
   ```

4. **Logout**:
   ```
   Clear tokens from storage
   ```

---

## Configuration for Frontend

### Environment Variables Required:
```env
VITE_API_URL=http://localhost:8000/api
VITE_API_TIMEOUT=30000
```

### Axios/Fetch Configuration:
```javascript
// Base URL
const API_BASE_URL = process.env.VITE_API_URL || 'http://localhost:8000/api'

// Headers
const headers = {
  'Content-Type': 'application/json',
  'Authorization': `Bearer ${accessToken}`
}

// For file uploads
const headers = {
  'Content-Type': 'multipart/form-data',
  'Authorization': `Bearer ${accessToken}`
}
```

---

## Health Check

**Endpoint**: `GET /api/health/`  
**Permission**: Public  
**Description**: Check if API is running

**Response** (200 OK):
```json
{
  "status": "healthy",
  "service": "AI Attendance System API"
}
```

---

## API Root

**Endpoint**: `GET /api/`  
**Permission**: Public  
**Description**: Get information about available endpoints

**Response** (200 OK):
```json
{
  "message": "AI-based Attendance System API",
  "version": "1.0.0",
  "endpoints": {
    "authentication": "/api/auth/",
    "students": "/api/students/",
    "attendance": "/api/attendance/",
    "ai": "/api/ai/",
    "token": "/api/token/",
    "admin": "/admin/"
  },
  "documentation": {
    "api_schema": "/api/schema/",
    "browsable_api": "Available on all endpoints when authenticated"
  },
  "health": "/api/health/"
}
```

---

## Rate Limiting

Currently no rate limiting is implemented. For production deployment, consider:
- Django REST Framework throttling
- API Gateway rate limiting
- CDN-level protection

---

## Security Considerations

### For Production Deployment:

1. **HTTPS Only**: Always use HTTPS in production
2. **CORS Configuration**: Set specific allowed origins
3. **JWT Secret**: Use strong, randomly generated SECRET_KEY
4. **Token Expiry**: Configure appropriate token lifetimes
5. **Input Validation**: All inputs are validated server-side
6. **File Upload**: Validate file types and sizes
7. **Database**: Use PostgreSQL with proper backup strategy

### Environment Variables (Required):
```env
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=yourdomain.com
CORS_ALLOWED_ORIGINS=https://yourdomain.com
DB_ENGINE=django.db.backends.postgresql
DB_NAME=attendance_db
DB_USER=db_user
DB_PASSWORD=db_password
DB_HOST=localhost
DB_PORT=5432
```

---

## Support & Contact

For issues or questions about the API:
- Check Django admin panel logs: `/admin/`
- Review application logs: `attendance_system/logs/`
- GitHub Issues: [Repository URL]

---

## Version History

- **v1.0.0** (2024-12-12): Initial release with complete API decoupling
