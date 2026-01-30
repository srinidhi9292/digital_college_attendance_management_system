"""
Django Forms for Attendance Management System
Path: attendance/forms.py
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm as DjangoUserCreationForm
from .models import *


class UserCreationForm(DjangoUserCreationForm):
    """Custom user creation form"""
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    email = forms.EmailField(required=True)
    phone = forms.CharField(max_length=15, required=False)
    
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'phone', 'password1', 'password2')


class DepartmentForm(forms.ModelForm):
    """Department form"""
    class Meta:
        model = Department
        fields = ['name', 'code', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class BranchForm(forms.ModelForm):
    """Branch form"""
    class Meta:
        model = Branch
        fields = ['department', 'name', 'code', 'duration_years']
        widgets = {
            'department': forms.Select(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'duration_years': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class SectionForm(forms.ModelForm):
    """Section form"""
    class Meta:
        model = Section
        fields = ['branch', 'name', 'semester', 'academic_year', 'capacity']
        widgets = {
            'branch': forms.Select(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'semester': forms.NumberInput(attrs={'class': 'form-control'}),
            'academic_year': forms.Select(attrs={'class': 'form-control'}),
            'capacity': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class SubjectForm(forms.ModelForm):
    """Subject form"""
    class Meta:
        model = Subject
        fields = ['name', 'code', 'branch', 'semester', 'subject_type', 'credits']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'branch': forms.Select(attrs={'class': 'form-control'}),
            'semester': forms.NumberInput(attrs={'class': 'form-control'}),
            'subject_type': forms.Select(attrs={'class': 'form-control'}),
            'credits': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class FacultyForm(forms.ModelForm):
    """Faculty form"""
    class Meta:
        model = Faculty
        fields = ['employee_id', 'department', 'designation', 'qualification', 'date_of_joining']
        widgets = {
            'employee_id': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.Select(attrs={'class': 'form-control'}),
            'designation': forms.TextInput(attrs={'class': 'form-control'}),
            'qualification': forms.TextInput(attrs={'class': 'form-control'}),
            'date_of_joining': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


class StudentForm(forms.ModelForm):
    """Student form"""
    class Meta:
        model = Student
        fields = ['roll_number', 'registration_number', 'section', 'date_of_admission', 'current_semester']
        widgets = {
            'roll_number': forms.TextInput(attrs={'class': 'form-control'}),
            'registration_number': forms.TextInput(attrs={'class': 'form-control'}),
            'section': forms.Select(attrs={'class': 'form-control'}),
            'date_of_admission': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'current_semester': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class TimetableForm(forms.ModelForm):
    """Timetable form with improved display"""
    class Meta:
        model = Timetable
        fields = ['subject_assignment', 'day_of_week', 'period_number', 'start_time', 'end_time', 'room_number']
        widgets = {
            'subject_assignment': forms.Select(attrs={'class': 'form-control'}),
            'day_of_week': forms.Select(attrs={'class': 'form-control'}),
            'period_number': forms.NumberInput(attrs={'class': 'form-control'}),
            'start_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'room_number': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show active assignments
        self.fields['subject_assignment'].queryset = SubjectAssignment.objects.filter(
            is_active=True
        ).select_related('faculty__user', 'subject', 'section', 'academic_year')
        
        # Improve dropdown display
        self.fields['subject_assignment'].label_from_instance = lambda obj: (
            f"{obj.faculty.user.get_full_name()} - {obj.subject.code} ({obj.subject.name}) - "
            f"{obj.section} - {obj.academic_year.year}"
        )


class AttendanceForm(forms.ModelForm):
    """Attendance form"""
    class Meta:
        model = Attendance
        fields = ['status', 'remarks']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-control'}),
            'remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }