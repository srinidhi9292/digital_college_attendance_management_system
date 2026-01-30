"""
Django Models for Attendance Management System
Path: attendance/models.py
"""

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from datetime import datetime, timedelta


class User(AbstractUser):
    """Custom User model with role-based access"""
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('faculty', 'Faculty'),
        ('student', 'Student'),
    ]
    
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    phone = models.CharField(max_length=15, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


class AcademicYear(models.Model):
    """Academic Year model"""
    year = models.CharField(max_length=20, unique=True)  # e.g., "2024-2025"
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'academic_years'
        ordering = ['-start_date']
    
    def __str__(self):
        return self.year


class Department(models.Model):
    """Department model"""
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'departments'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.code})"


class Branch(models.Model):
    """Branch/Course model"""
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='branches')
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10)
    duration_years = models.IntegerField(default=4)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'branches'
        ordering = ['department', 'name']
        unique_together = ['department', 'code']
    
    def __str__(self):
        return f"{self.name} ({self.code})"


class Section(models.Model):
    """Section model for dividing students"""
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='sections')
    name = models.CharField(max_length=10)  # e.g., A, B, C
    semester = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(8)])
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)
    capacity = models.IntegerField(default=60)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'sections'
        ordering = ['branch', 'semester', 'name']
        unique_together = ['branch', 'semester', 'name', 'academic_year']
    
    def __str__(self):
        return f"{self.branch.code} - Sem {self.semester} - Section {self.name}"


class Subject(models.Model):
    """Subject model"""
    SUBJECT_TYPE_CHOICES = [
        ('theory', 'Theory'),
        ('practical', 'Practical'),
        ('both', 'Theory & Practical'),
    ]
    
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='subjects')
    semester = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(8)])
    subject_type = models.CharField(max_length=10, choices=SUBJECT_TYPE_CHOICES, default='theory')
    credits = models.IntegerField(default=3)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'subjects'
        ordering = ['branch', 'semester', 'name']
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class Faculty(models.Model):
    """Faculty profile model"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='faculty_profile')
    employee_id = models.CharField(max_length=20, unique=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='faculty_members')
    designation = models.CharField(max_length=50)
    qualification = models.CharField(max_length=100)
    date_of_joining = models.DateField()
    
    class Meta:
        db_table = 'faculty'
        verbose_name_plural = 'Faculty'
    
    def __str__(self):
        return f"{self.user.get_full_name()} ({self.employee_id})"


class Student(models.Model):
    """Student profile model"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    roll_number = models.CharField(max_length=20, unique=True)
    registration_number = models.CharField(max_length=20, unique=True)
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='students')
    date_of_admission = models.DateField()
    current_semester = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(8)])
    
    class Meta:
        db_table = 'students'
        ordering = ['roll_number']
    
    def __str__(self):
        return f"{self.roll_number} - {self.user.get_full_name()}"


class SubjectAssignment(models.Model):
    """Assignment of subjects to faculty for specific sections"""
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, related_name='subject_assignments')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='subject_assignments')
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'subject_assignments'
        unique_together = ['faculty', 'subject', 'section', 'academic_year']
    
    def __str__(self):
        return f"{self.faculty.user.get_full_name()} - {self.subject.code} - {self.section}"


class Timetable(models.Model):
    """Timetable model for scheduling classes"""
    DAY_CHOICES = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
    ]
    
    subject_assignment = models.ForeignKey(SubjectAssignment, on_delete=models.CASCADE, related_name='timetable_slots')
    day_of_week = models.IntegerField(choices=DAY_CHOICES)
    period_number = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(8)])
    start_time = models.TimeField()
    end_time = models.TimeField()
    room_number = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'timetable'
        ordering = ['day_of_week', 'period_number']
        unique_together = ['subject_assignment', 'day_of_week', 'period_number']
    
    def __str__(self):
        return f"{self.get_day_of_week_display()} - Period {self.period_number} - {self.subject_assignment.subject.code}"
    
    def is_attendance_allowed(self):
        return True


class Attendance(models.Model):
    """Attendance record model"""
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
    ]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendance_records')
    timetable = models.ForeignKey(Timetable, on_delete=models.CASCADE, related_name='attendance_records')
    date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    marked_by = models.ForeignKey(Faculty, on_delete=models.SET_NULL, null=True)
    marked_at = models.DateTimeField(auto_now_add=True)
    is_locked = models.BooleanField(default=False)
    remarks = models.TextField(blank=True)
    
    class Meta:
        db_table = 'attendance'
        ordering = ['-date', 'student']
        unique_together = ['student', 'timetable', 'date']
        indexes = [
            models.Index(fields=['student', 'date']),
            models.Index(fields=['timetable', 'date']),
        ]
    
    def __str__(self):
        return f"{self.student.roll_number} - {self.date} - {self.status}"


class AttendanceSummary(models.Model):
    """Pre-calculated attendance summary for performance"""
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendance_summaries')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)
    total_classes = models.IntegerField(default=0)
    classes_attended = models.IntegerField(default=0)
    attendance_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'attendance_summary'
        unique_together = ['student', 'subject', 'academic_year']
        indexes = [
            models.Index(fields=['student', 'attendance_percentage']),
        ]
    
    def __str__(self):
        return f"{self.student.roll_number} - {self.subject.code} - {self.attendance_percentage}%"
    
    def update_summary(self):
        """Update attendance summary"""
        attendance_records = Attendance.objects.filter(
            student=self.student,
            timetable__subject_assignment__subject=self.subject,
            timetable__subject_assignment__academic_year=self.academic_year
        )
        
        self.total_classes = attendance_records.count()
        self.classes_attended = attendance_records.filter(status='present').count()
        
        if self.total_classes > 0:
            self.attendance_percentage = (self.classes_attended / self.total_classes) * 100
        else:
            self.attendance_percentage = 0
        
        self.save()


class AuditLog(models.Model):
    """Audit log for tracking admin activities"""
    ACTION_CHOICES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('override', 'Override'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=50)
    object_id = models.IntegerField()
    description = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'audit_logs'
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.user} - {self.action} - {self.model_name} - {self.timestamp}"