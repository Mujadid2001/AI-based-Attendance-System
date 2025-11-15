"""
Management command to populate sample data.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.student.models import Course, StudentProfile, Enrollment
from datetime import datetime

User = get_user_model()


class Command(BaseCommand):
    help = 'Populate database with sample data'
    
    def handle(self, *args, **options):
        self.stdout.write('Starting data population...')
        
        # Create admin
        admin, created = User.objects.get_or_create(
            email='admin@attendance.com',
            defaults={
                'first_name': 'Admin',
                'last_name': 'User',
                'role': User.Role.ADMIN,
                'is_staff': True,
                'is_superuser': True,
                'is_active': True
            }
        )
        if created:
            admin.set_password('Admin@123')
            admin.save()
            self.stdout.write(self.style.SUCCESS('Created admin user'))
        
        # Create teacher
        teacher, created = User.objects.get_or_create(
            email='teacher@attendance.com',
            defaults={
                'first_name': 'John',
                'last_name': 'Teacher',
                'role': User.Role.TEACHER,
                'phone': '1234567890',
                'is_active': True
            }
        )
        if created:
            teacher.set_password('Teacher@123')
            teacher.save()
            self.stdout.write(self.style.SUCCESS('Created teacher user'))
        
        # Create courses
        courses_data = [
            ('CS101', 'Introduction to Programming'),
            ('CS201', 'Data Structures'),
            ('CS301', 'Web Development'),
        ]
        
        for code, name in courses_data:
            course, created = Course.objects.get_or_create(
                code=code,
                defaults={
                    'name': name,
                    'instructor': teacher,
                    'max_students': 30,
                    'is_active': True
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created course: {code}'))
        
        # Create sample students
        students_data = [
            ('STU001', 'student1@attendance.com', 'Alice', 'Smith'),
            ('STU002', 'student2@attendance.com', 'Bob', 'Johnson'),
            ('STU003', 'student3@attendance.com', 'Charlie', 'Brown'),
            ('STU004', 'student4@attendance.com', 'Diana', 'Davis'),
            ('STU005', 'student5@attendance.com', 'Eve', 'Wilson'),
        ]
        
        for roll, email, first, last in students_data:
            user, user_created = User.objects.get_or_create(
                email=email,
                defaults={
                    'first_name': first,
                    'last_name': last,
                    'role': User.Role.STUDENT,
                    'is_active': True
                }
            )
            
            if user_created:
                user.set_password('Student@123')
                user.save()
            
            student, created = StudentProfile.objects.get_or_create(
                user=user,
                defaults={
                    'roll_number': roll,
                    'department': 'Computer Science',
                    'semester': 3
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created student: {roll}'))
            
            # Enroll in courses
            for course in Course.objects.all():
                Enrollment.objects.get_or_create(
                    student=student,
                    course=course
                )
        
        self.stdout.write(self.style.SUCCESS('✅ Data population completed!'))
        self.stdout.write('')
        self.stdout.write('Sample Credentials:')
        self.stdout.write('Admin: admin@attendance.com / Admin@123')
        self.stdout.write('Teacher: teacher@attendance.com / Teacher@123')
        self.stdout.write('Student: student1@attendance.com / Student@123')
