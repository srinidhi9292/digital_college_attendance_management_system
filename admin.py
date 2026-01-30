from django.contrib import admin

# Register your models here.
"""
Django Admin Configuration
Path: attendance/admin.py
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import *


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom User Admin"""
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_staff')
    list_filter = ('role', 'is_staff', 'is_active')
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('role', 'phone')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Additional Info', {'fields': ('role', 'phone')}),
    )


@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    list_display = ('year', 'start_date', 'end_date', 'is_active')
    list_filter = ('is_active',)


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'created_at')
    search_fields = ('name', 'code')


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'department', 'duration_years')
    list_filter = ('department',)
    search_fields = ('name', 'code')


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ('name', 'branch', 'semester', 'academic_year', 'capacity')
    list_filter = ('branch', 'semester', 'academic_year')


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'branch', 'semester', 'subject_type', 'credits')
    list_filter = ('branch', 'semester', 'subject_type')
    search_fields = ('name', 'code')


@admin.register(Faculty)
class FacultyAdmin(admin.ModelAdmin):
    list_display = ('employee_id', 'user', 'department', 'designation', 'date_of_joining')
    list_filter = ('department', 'designation')
    search_fields = ('employee_id', 'user__username', 'user__first_name', 'user__last_name')


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('roll_number', 'user', 'section', 'current_semester', 'date_of_admission')
    list_filter = ('section', 'current_semester')
    search_fields = ('roll_number', 'registration_number', 'user__username', 'user__first_name', 'user__last_name')


@admin.register(SubjectAssignment)
class SubjectAssignmentAdmin(admin.ModelAdmin):
    list_display = ('faculty', 'subject', 'section', 'academic_year', 'is_active')
    list_filter = ('academic_year', 'is_active')


@admin.register(Timetable)
class TimetableAdmin(admin.ModelAdmin):
    list_display = ('subject_assignment', 'day_of_week', 'period_number', 'start_time', 'end_time', 'room_number')
    list_filter = ('day_of_week', 'is_active')


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('student', 'timetable', 'date', 'status', 'marked_by', 'is_locked')
    list_filter = ('date', 'status', 'is_locked')
    search_fields = ('student__roll_number', 'student__user__first_name', 'student__user__last_name')
    date_hierarchy = 'date'


@admin.register(AttendanceSummary)
class AttendanceSummaryAdmin(admin.ModelAdmin):
    list_display = ('student', 'subject', 'total_classes', 'classes_attended', 'attendance_percentage', 'last_updated')
    list_filter = ('academic_year',)
    search_fields = ('student__roll_number', 'subject__code')


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'model_name', 'timestamp', 'ip_address')
    list_filter = ('action', 'model_name', 'timestamp')
    search_fields = ('user__username', 'description')
    date_hierarchy = 'timestamp'
    readonly_fields = ('user', 'action', 'model_name', 'object_id', 'description', 'ip_address', 'timestamp')