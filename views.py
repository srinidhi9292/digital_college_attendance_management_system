"""
Updated Django Views for Attendance Management System
Path: attendance/views.py
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q, Avg
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from datetime import datetime, timedelta
from .models import *
from .forms import *
from .decorators import role_required

# Login view
def login_view(request):
    """Login view for all users"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome, {user.get_full_name() or user.username}!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'login.html')

#Logout view
@login_required
def logout_view(request):
    """Logout view"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('login')

# Admin Profile View
@login_required
@role_required('admin')
def admin_profile(request):
    """Admin profile view"""
    context = {
        'total_students': Student.objects.count(),
        'total_faculty': Faculty.objects.count(),
        'total_departments': Department.objects.count(),
    }
    return render(request, 'admin_profile.html', context)

#Dashboard view
@login_required
def dashboard_view(request):
    """Role-based dashboard"""
    user = request.user
    
    if not hasattr(user, 'role') or not user.role:
        messages.error(request, 'Your account is not properly configured.')
        logout(request)
        return redirect('login')
    
    if user.role == 'admin':
        return admin_dashboard(request)
    elif user.role == 'faculty':
        return faculty_dashboard(request)
    elif user.role == 'student':
        return student_dashboard(request)
    else:
        messages.error(request, 'Invalid user role.')
        return redirect('login')

#Admin dashboard
@login_required
def admin_dashboard(request):
    """Admin dashboard with statistics"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    context = {
        'total_students': Student.objects.count(),
        'total_faculty': Faculty.objects.count(),
        'total_departments': Department.objects.count(),
        'total_subjects': Subject.objects.count(),
        'active_sections': Section.objects.filter(academic_year__is_active=True).count(),
        'recent_attendance': Attendance.objects.select_related('student', 'timetable').order_by('-marked_at')[:10],
        'low_attendance_students': AttendanceSummary.objects.filter(
            attendance_percentage__lt=75,
            academic_year__is_active=True
        ).select_related('student', 'subject').order_by('attendance_percentage')[:10],
    }
    return render(request, 'admin/dashboard.html', context)

#faculty dashboard
@login_required
@role_required('faculty')
def faculty_dashboard(request):
    """Faculty dashboard with real-time assignment sync"""
    if request.user.role != 'faculty':
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    faculty = Faculty.objects.select_related('user', 'department').get(user=request.user)
    active_year = AcademicYear.objects.filter(is_active=True).first()
    
    if not active_year:
        messages.warning(request, 'No active academic year found. Please contact admin.')
        assignments = SubjectAssignment.objects.none()
        today_classes = Timetable.objects.none()
    else:
        assignments = list(SubjectAssignment.objects.filter(
            faculty=faculty,
            academic_year=active_year,
            is_active=True
        ).select_related('subject', 'section', 'academic_year').order_by('subject__name'))
        
        today = timezone.now().weekday()
        today_classes = list(Timetable.objects.filter(
            subject_assignment__faculty=faculty,
            day_of_week=today,
            is_active=True,
            subject_assignment__academic_year=active_year
        ).select_related(
            'subject_assignment__subject', 
            'subject_assignment__section'
        ).order_by('period_number'))
    
    context = {
        'faculty': faculty,
        'assignments': assignments,
        'today_classes': today_classes,
        'total_assignments': len(assignments),
        'active_year': active_year,
    }
    return render(request, 'faculty/dashboard.html', context)

#student dashboard
@login_required
def student_dashboard(request):
    """Student dashboard with real-time attendance calculation"""
    if request.user.role != 'student':
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    try:
        student = request.user.student_profile
    except:
        messages.error(request, 'Student profile not found.')
        return redirect('login')
    
    active_year = AcademicYear.objects.filter(is_active=True).first()
    
    if not active_year:
        messages.warning(request, 'No active academic year found.')
        context = {
            'student': student,
            'summaries': [],
            'overall_percentage': 0,
            'total_classes': 0,
            'total_attended': 0,
            'today_attendance': [],
            'is_defaulter': False,
        }
        return render(request, 'student/dashboard.html', context)
    
    attended_subject_ids = Attendance.objects.filter(
        student=student,
        timetable__subject_assignment__academic_year=active_year
    ).values_list('timetable__subject_assignment__subject_id', flat=True).distinct()
    
    curriculum_subjects = Subject.objects.filter(
        branch=student.section.branch,
        semester=student.current_semester
    )
    
    all_subject_ids = set(curriculum_subjects.values_list('id', flat=True)) | set(attended_subject_ids)
    subjects = Subject.objects.filter(id__in=all_subject_ids)
    
    summaries = []
    for subject in subjects:
        summary, created = AttendanceSummary.objects.get_or_create(
            student=student,
            subject=subject,
            academic_year=active_year
        )
        
        attendance_records = Attendance.objects.filter(
            student=student,
            timetable__subject_assignment__subject=subject,
            timetable__subject_assignment__academic_year=active_year
        )
        
        total = attendance_records.count()
        attended = attendance_records.filter(status='present').count()
        percentage = (attended / total * 100) if total > 0 else 0
        
        if (summary.total_classes != total or 
            summary.classes_attended != attended or 
            abs(float(summary.attendance_percentage) - percentage) > 0.01):
            
            summary.total_classes = total
            summary.classes_attended = attended
            summary.attendance_percentage = round(percentage, 2)
            summary.save()
        
        summaries.append(summary)
    
    summaries = sorted(summaries, key=lambda x: x.subject.name)
    
    total_classes = sum(s.total_classes for s in summaries)
    total_attended = sum(s.classes_attended for s in summaries)
    overall_percentage = (total_attended / total_classes * 100) if total_classes > 0 else 0
    
    today = timezone.now().date()
    today_attendance = Attendance.objects.filter(
        student=student,
        date=today
    ).select_related('timetable__subject_assignment__subject')
    
    context = {
        'student': student,
        'summaries': summaries,
        'overall_percentage': round(overall_percentage, 2),
        'total_classes': total_classes,
        'total_attended': total_attended,
        'today_attendance': today_attendance,
        'is_defaulter': overall_percentage < 75,
    }
    return render(request, 'student/dashboard.html', context)

# ==================== ADMIN VIEWS ====================

@login_required
@role_required('admin')
def manage_departments(request):
    """Manage departments"""
    if request.method == 'POST':
        form = DepartmentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Department created successfully.')
            return redirect('manage_departments')
    else:
        form = DepartmentForm()
    
    departments = Department.objects.all()
    context = {
        'form': form, 
        'departments': departments,
    }
    return render(request, 'admin/manage_departments.html', context)

@login_required
@role_required('admin')
def add_department(request):
    """Add new department"""
    if request.method == 'POST':
        code = request.POST.get('code')
        name = request.POST.get('name')
        
        try:
            Department.objects.create(
                code=code,
                name=name
            )
            messages.success(request, 'Department added successfully.')
        except Exception as e:
            messages.error(request, f'Error adding department: {str(e)}')
    
    return redirect('manage_departments')

@login_required
@role_required('admin')
def edit_department(request, pk):
    """Edit department"""
    department = get_object_or_404(Department, pk=pk)
    
    if request.method == 'POST':
        department.code = request.POST.get('code')
        department.name = request.POST.get('name')
        
        try:
            department.save()
            messages.success(request, 'Department updated successfully.')
        except Exception as e:
            messages.error(request, f'Error updating department: {str(e)}')
    
    return redirect('manage_departments')

@login_required
@role_required('admin')
def delete_department(request, pk):
    """Delete department"""
    department = get_object_or_404(Department, pk=pk)
    
    if request.method == 'POST':
        try:
            department.delete()
            messages.success(request, 'Department deleted successfully.')
        except Exception as e:
            messages.error(request, f'Error deleting department: {str(e)}')
    
    return redirect('manage_departments')

@login_required
@role_required('admin')
def manage_branches(request):
    """Manage branches"""
    if request.method == 'POST':
        form = BranchForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Branch created successfully.')
            return redirect('manage_branches')
    else:
        form = BranchForm()
    
    branches = Branch.objects.select_related('department').all()
    departments = Department.objects.all() 
    
    context = {
        'form': form, 
        'branches': branches,
        'departments': departments
    }
    return render(request, 'admin/manage_branches.html', context)

@login_required
@role_required('admin')
def edit_branch(request, pk):
    """Edit branch"""
    branch = get_object_or_404(Branch, pk=pk)
    
    if request.method == 'POST':
        form = BranchForm(request.POST, instance=branch)
        if form.is_valid():
            form.save()
            messages.success(request, 'Branch updated successfully.')
        else:
            messages.error(request, 'Error updating branch.')
    
    return redirect('manage_branches')

@login_required
@role_required('admin')
def delete_branch(request, pk):
    """Delete branch"""
    branch = get_object_or_404(Branch, pk=pk)
    
    if request.method == 'POST':
        try:
            branch.delete()
            messages.success(request, 'Branch deleted successfully.')
        except Exception as e:
            messages.error(request, f'Error deleting branch: {str(e)}')
    
    return redirect('manage_branches')

@login_required
@role_required('admin')
def manage_sections(request):
    """Manage sections"""
    if request.method == 'POST':
        branch_id = request.POST.get('branch')
        name = request.POST.get('name')
        semester = request.POST.get('semester')
        academic_year_input = request.POST.get('academic_year')
        capacity = request.POST.get('capacity')
        
        try:
            if '-' not in academic_year_input or len(academic_year_input.split('-')) != 2:
                messages.error(request, 'Invalid academic year format. Use YYYY-YYYY (e.g., 2024-2025)')
                return redirect('manage_sections')
            
            academic_year, created = AcademicYear.objects.get_or_create(
                year=academic_year_input,
                defaults={
                    'start_date': f'{academic_year_input.split("-")[0]}-06-01',  
                    'end_date': f'{academic_year_input.split("-")[1]}-05-31',    
                    'is_active': True
                }
            )
            
            Section.objects.create(
                branch_id=branch_id,
                name=name,
                semester=semester,
                academic_year=academic_year,
                capacity=capacity
            )
            
            messages.success(request, f'Section created successfully for academic year {academic_year_input}.')
        except Exception as e:
            messages.error(request, f'Error creating section: {str(e)}')
        
        return redirect('manage_sections')
    
    sections = Section.objects.select_related('branch', 'academic_year').all()
    branches = Branch.objects.select_related('department').all()
    departments = Department.objects.all()
    academic_years = AcademicYear.objects.all()
    
    context = {
        'sections': sections,
        'branches': branches,
        'departments': departments,
        'academic_years': academic_years
    }
    return render(request, 'admin/manage_sections.html', context)

@login_required
@role_required('admin')
def edit_section(request, pk):
    """Edit section"""
    section = get_object_or_404(Section, pk=pk)
    
    if request.method == 'POST':
        try:
            section.branch_id = request.POST.get('branch')
            section.name = request.POST.get('name')
            section.semester = request.POST.get('semester')
            section.capacity = request.POST.get('capacity')
            
            academic_year_input = request.POST.get('academic_year')
            
            if '-' not in academic_year_input or len(academic_year_input.split('-')) != 2:
                messages.error(request, 'Invalid academic year format. Use YYYY-YYYY (e.g., 2024-2025)')
                return redirect('manage_sections')
            
            academic_year, created = AcademicYear.objects.get_or_create(
                year=academic_year_input,
                defaults={
                    'start_date': f'{academic_year_input.split("-")[0]}-06-01',  
                    'end_date': f'{academic_year_input.split("-")[1]}-05-31',    
                    'is_active': True
                }
            )
            
            section.academic_year = academic_year
            section.save()
            
            messages.success(request, 'Section updated successfully.')
        except Exception as e:
            messages.error(request, f'Error updating section: {str(e)}')
    
    return redirect('manage_sections')

@login_required
@role_required('admin')
def delete_section(request, pk):
    """Delete section"""
    section = get_object_or_404(Section, pk=pk)
    
    if request.method == 'POST':
        try:
            section.delete()
            messages.success(request, 'Section deleted successfully.')
        except Exception as e:
            messages.error(request, f'Error deleting section: {str(e)}')
    
    return redirect('manage_sections')

@login_required
@role_required('admin')
def manage_subjects(request):
    """Manage subjects with department-branch cascading feature"""
    if request.method == 'POST':
        branch_id = request.POST.get('branch')
        name = request.POST.get('name')
        code = request.POST.get('code')
        semester = request.POST.get('semester')
        credits = request.POST.get('credits')
        subject_type = request.POST.get('subject_type')
        
        try:
            Subject.objects.create(
                branch_id=branch_id,
                name=name,
                code=code,
                semester=semester,
                credits=credits,
                subject_type=subject_type
            )
            messages.success(request, 'Subject created successfully.')
        except Exception as e:
            messages.error(request, f'Error creating subject: {str(e)}')
        
        return redirect('manage_subjects')
    
    subjects = Subject.objects.select_related('branch__department').all()
    departments = Department.objects.all()
    branches = Branch.objects.select_related('department').all()
    
    context = {
        'subjects': subjects,
        'departments': departments,
        'branches': branches
    }
    return render(request, 'admin/manage_subjects.html', context)

@login_required
@role_required('admin')
def edit_subject(request, pk):
    """Edit subject"""
    subject = get_object_or_404(Subject, pk=pk)
    
    if request.method == 'POST':
        try:
            subject.branch_id = request.POST.get('branch')
            subject.name = request.POST.get('name')
            subject.code = request.POST.get('code')
            subject.semester = request.POST.get('semester')
            subject.credits = request.POST.get('credits')
            subject.subject_type = request.POST.get('subject_type', 'theory')
            subject.save()
            
            messages.success(request, 'Subject updated successfully.')
        except Exception as e:
            messages.error(request, f'Error updating subject: {str(e)}')
    
    return redirect('manage_subjects')

@login_required
@role_required('admin')
def delete_subject(request, pk):
    """Delete subject"""
    subject = get_object_or_404(Subject, pk=pk)
    
    if request.method == 'POST':
        try:
            subject.delete()
            messages.success(request, 'Subject deleted successfully.')
        except Exception as e:
            messages.error(request, f'Error deleting subject: {str(e)}')
    
    return redirect('manage_subjects')

@login_required
@role_required('admin')
def manage_faculty(request):
    """Manage faculty"""
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        full_name = request.POST.get('full_name')
        
        if password1 != password2:
            messages.error(request, 'Passwords do not match.')
            return redirect('manage_faculty')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return redirect('manage_faculty')
        
        try:
            name_parts = full_name.strip().split(' ', 1)
            first_name = name_parts[0]
            last_name = name_parts[1] if len(name_parts) > 1 else ''
            
            user = User.objects.create(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                role='faculty'
            )
            user.set_password(password1)
            user.save()
            
            Faculty.objects.create(
                user=user,
                employee_id=request.POST.get('employee_id'),
                department_id=request.POST.get('department'),
                designation=request.POST.get('designation'),
                qualification=request.POST.get('qualification'),
                date_of_joining=request.POST.get('date_of_joining')
            )
            
            messages.success(request, f'Faculty {user.get_full_name()} created successfully.')
        except Exception as e:
            messages.error(request, f'Error creating faculty: {str(e)}')
        
        return redirect('manage_faculty')
    
    faculty_form = FacultyForm()
    faculty_list = Faculty.objects.select_related('user', 'department').all()
    departments = Department.objects.all()
    
    context = {
        'faculty_form': faculty_form,
        'faculty_list': faculty_list,
        'departments': departments
    }
    return render(request, 'admin/manage_faculty.html', context)

@login_required
@role_required('admin')
def edit_faculty(request, pk):
    """Edit faculty"""
    faculty = get_object_or_404(Faculty, pk=pk)
    user = faculty.user
    
    if request.method == 'POST':
        try:
            full_name = request.POST.get('full_name')
            name_parts = full_name.strip().split(' ', 1)
            user.first_name = name_parts[0]
            user.last_name = name_parts[1] if len(name_parts) > 1 else ''
            user.email = request.POST.get('email')
            user.phone = request.POST.get('phone')
            user.save()
            
            faculty.employee_id = request.POST.get('employee_id')
            faculty.department_id = request.POST.get('department')
            faculty.designation = request.POST.get('designation')
            faculty.qualification = request.POST.get('qualification')
            faculty.date_of_joining = request.POST.get('date_of_joining')
            faculty.save()
            
            messages.success(request, 'Faculty updated successfully.')
        except Exception as e:
            messages.error(request, f'Error updating faculty: {str(e)}')
            
    return redirect('manage_faculty')

@login_required
@role_required('admin')
def delete_faculty(request, pk):
    """Delete faculty"""
    faculty = get_object_or_404(Faculty, pk=pk)
    
    if request.method == 'POST':
        try:
            user = faculty.user
            faculty.delete()
            user.delete()
            messages.success(request, 'Faculty deleted successfully.')
        except Exception as e:
            messages.error(request, f'Error deleting faculty: {str(e)}')
    
    return redirect('manage_faculty')

@login_required
@role_required('admin')
def manage_students(request):
    """List and Add Students"""
    if request.method == 'POST':
        username = request.POST.get('username')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        password = request.POST.get('password')
        
        try:
            user = User.objects.create(
                username=username,
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone=phone,
                role='student'
            )
            user.set_password(password)
            user.save()
            
            Student.objects.create(
                user=user,
                roll_number=request.POST.get('roll_number'),
                registration_number=request.POST.get('registration_number'),
                section_id=request.POST.get('section'),
                date_of_admission=request.POST.get('date_of_admission'),
                current_semester=request.POST.get('current_semester')
            )
            messages.success(request, 'Student created successfully.')
        except Exception as e:
            messages.error(request, f'Error creating student: {str(e)}')
        return redirect('manage_students')
    
    student_form = StudentForm()
    students = Student.objects.select_related('user', 'section').all()
    sections = Section.objects.all()
    
    context = {
        'student_form': student_form,
        'students': students,
        'sections': sections
    }
    return render(request, 'admin/manage_students.html', context)

@login_required
@role_required('admin')
def edit_student(request, pk):
    """Edit student and user information"""
    student = get_object_or_404(Student, pk=pk)
    user = student.user
    
    if request.method == 'POST':
        try:
            user.first_name = request.POST.get('first_name', '').strip()
            user.last_name = request.POST.get('last_name', '').strip()
            user.email = request.POST.get('email', '').strip()
            user.phone = request.POST.get('phone', '').strip()
            user.save()
            
            student.roll_number = request.POST.get('roll_number', '').strip()
            student.registration_number = request.POST.get('registration_number', '').strip()
            student.section_id = request.POST.get('section')
            student.current_semester = request.POST.get('current_semester')
            student.date_of_admission = request.POST.get('date_of_admission')
            student.save()
            
            messages.success(request, 'Student updated successfully.')
        except Exception as e:
            messages.error(request, f'Error updating student: {str(e)}')
    
    return redirect('manage_students')

@login_required
@role_required('admin')
def delete_student(request, pk):
    """Delete student and associated user"""
    student = get_object_or_404(Student, pk=pk)
    if request.method == 'POST':
        user = student.user
        user.delete()
        messages.success(request, 'Student record removed.')
    return redirect('manage_students')

@login_required
@role_required('admin')
def manage_timetable(request):
    """Manage permanent timetable entries with predefined timings"""
    # Predefined period timings
    PERIOD_TIMINGS = {
        1: ('09:30', '10:20'),
        2: ('10:20', '11:10'),
        3: ('11:30', '12:20'),
        4: ('12:20', '13:10'),
        5: ('14:10', '15:00'),
        6: ('15:00', '15:50'),
        7: ('15:50', '16:30'),
    }
    
    if request.method == 'POST':
        subject_assignment_id = request.POST.get('subject_assignment')
        day_of_week = request.POST.get('day_of_week')
        period_numbers = request.POST.get('period_number')
        room_number = request.POST.get('room_number', '')
        
        try:
            assignment = SubjectAssignment.objects.get(id=subject_assignment_id)
            
            # Parse period numbers
            periods = [p.strip() for p in period_numbers.split(',') if p.strip()]
            
            try:
                periods = [int(p) for p in periods]
            except ValueError:
                messages.error(request, 'Invalid period number format. Use numbers separated by commas (e.g., 1,2,3)')
                return redirect('manage_timetable')
            
            # Validate periods are in range 1-7
            if any(p < 1 or p > 7 for p in periods):
                messages.error(request, 'Period numbers must be between 1 and 7.')
                return redirect('manage_timetable')
            
            # Check for conflicts
            conflicts = []
            for period in periods:
                conflict = Timetable.objects.filter(
                    day_of_week=day_of_week,
                    period_number=period,
                    subject_assignment__faculty=assignment.faculty,
                    subject_assignment__academic_year=assignment.academic_year,
                    is_active=True
                ).exists()
                
                if conflict:
                    conflicts.append(f"Period {period}")
            
            if conflicts:
                messages.error(request, f'Conflict: Faculty is already assigned during {", ".join(conflicts)} on this day.')
                return redirect('manage_timetable')
            
            # Get start and end times from first and last periods
            start_time = PERIOD_TIMINGS[min(periods)][0]
            end_time = PERIOD_TIMINGS[max(periods)][1]
            
            # Create timetable entries
            created_count = 0
            for period in periods:
                Timetable.objects.create(
                    subject_assignment=assignment,
                    day_of_week=day_of_week,
                    period_number=period,
                    start_time=start_time,
                    end_time=end_time,
                    room_number=room_number,
                    is_active=True
                )
                created_count += 1
            
            if len(periods) > 1:
                messages.success(request, f'Lab session created successfully for periods {", ".join(map(str, periods))}.')
            else:
                messages.success(request, f'Timetable entry created successfully for period {periods[0]}.')
                
        except SubjectAssignment.DoesNotExist:
            messages.error(request, 'Invalid subject assignment selected.')
        except Exception as e:
            messages.error(request, f'Error creating timetable: {str(e)}')
        
        return redirect('manage_timetable')
    
    timetable = Timetable.objects.select_related(
        'subject_assignment__subject',
        'subject_assignment__section',
        'subject_assignment__faculty__user',
        'subject_assignment__academic_year'
    ).filter(is_active=True).order_by('day_of_week', 'period_number')
    
    subject_assignments = SubjectAssignment.objects.select_related(
        'faculty__user',
        'subject',
        'section',
        'academic_year'
    ).filter(is_active=True)
    
    context = {
        'timetable': timetable,
        'subject_assignments': subject_assignments,
        'days': Timetable.DAY_CHOICES,
        'period_timings': PERIOD_TIMINGS,
    }
    
    return render(request, 'admin/manage_timetable.html', context)

@login_required
@role_required('admin')
def delete_timetable(request, pk):
    """Delete timetable entry"""
    timetable = get_object_or_404(Timetable, pk=pk)
    
    if request.method == 'POST':
        try:
            timetable.delete()
            messages.success(request, 'Timetable entry deleted successfully.')
        except Exception as e:
            messages.error(request, f'Error deleting timetable: {str(e)}')
    
    return redirect('manage_timetable')

@login_required
@role_required('admin')
def manage_subject_assignments(request):
    """Manage subject assignments"""
    if request.method == 'POST':
        faculty_id = request.POST.get('faculty')
        subject_id = request.POST.get('subject')
        section_id = request.POST.get('section')
        academic_year_input = request.POST.get('academic_year')
        
        try:
            if '-' not in academic_year_input or len(academic_year_input.split('-')) != 2:
                messages.error(request, 'Invalid academic year format. Use YYYY-YYYY (e.g., 2024-2025)')
                return redirect('manage_subject_assignments')
            
            academic_year, created = AcademicYear.objects.get_or_create(
                year=academic_year_input,
                defaults={
                    'start_date': f'{academic_year_input.split("-")[0]}-06-01',  
                    'end_date': f'{academic_year_input.split("-")[1]}-05-31',    
                    'is_active': True
                }
            )
            
            existing = SubjectAssignment.objects.filter(
                faculty_id=faculty_id,
                subject_id=subject_id,
                section_id=section_id,
                academic_year=academic_year
            ).first()
            
            if existing:
                messages.warning(request, 'This assignment already exists.')
            else:
                SubjectAssignment.objects.create(
                    faculty_id=faculty_id,
                    subject_id=subject_id,
                    section_id=section_id,
                    academic_year=academic_year,
                    is_active=True
                )
                messages.success(request, 'Subject assignment created successfully.')
        except Exception as e:
            messages.error(request, f'Error creating assignment: {str(e)}')
        
        return redirect('manage_subject_assignments')
    
    assignments = SubjectAssignment.objects.select_related(
        'faculty__user',
        'subject',
        'section',
        'academic_year'
    ).all()
    
    faculties = Faculty.objects.select_related('user').all()
    subjects = Subject.objects.all()
    sections = Section.objects.select_related('branch').all()
    
    context = {
        'assignments': assignments,
        'faculties': faculties,
        'subjects': subjects,
        'sections': sections,
    }
    return render(request, 'admin/manage_subject_assignments.html', context)

@login_required
@role_required('admin')
def delete_subject_assignment(request, pk):
    """Delete subject assignment"""
    assignment = get_object_or_404(SubjectAssignment, pk=pk)
    
    if request.method == 'POST':
        try:
            assignment.delete()
            messages.success(request, 'Subject assignment deleted successfully.')
        except Exception as e:
            messages.error(request, f'Error deleting assignment: {str(e)}')
    
    return redirect('manage_subject_assignments')



# Admin Change Password View
@login_required
@role_required('admin')
def admin_change_password(request):
    """Admin change password view"""
    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        # Verify old password
        if not request.user.check_password(old_password):
            messages.error(request, 'Current password is incorrect.')
            return redirect('admin_change_password')
        
        # Check if new passwords match
        if new_password != confirm_password:
            messages.error(request, 'New passwords do not match.')
            return redirect('admin_change_password')
        
        # Check password length
        if len(new_password) < 8:
            messages.error(request, 'Password must be at least 8 characters long.')
            return redirect('admin_change_password')
        
        # Update password
        request.user.set_password(new_password)
        request.user.save()
        
        # Update session to prevent logout
        update_session_auth_hash(request, request.user)
        
        messages.success(request, 'Password changed successfully!')
        return redirect('dashboard')
    
    return render(request, 'admin_change_password.html')

# ==================== FACULTY VIEWS ====================


from datetime import datetime, timedelta

@login_required
@role_required('faculty')
def mark_attendance(request, timetable_id):
    """Mark attendance for a class with correct date calculation"""
    from .utils import update_summaries_after_attendance_marking
    
    timetable = get_object_or_404(Timetable, id=timetable_id)
    faculty = request.user.faculty_profile
    
    if timetable.subject_assignment.faculty != faculty:
        messages.error(request, 'Unauthorized access.')
        return redirect('dashboard')
    
    section = timetable.subject_assignment.section
    students = Student.objects.filter(section=section).order_by('roll_number')
    
    # Calculate the correct date based on timetable day
    today = timezone.now()
    current_weekday = today.weekday()  # 0 = Monday, 6 = Sunday
    timetable_day = timetable.day_of_week  # 0 = Monday, 5 = Saturday
    
    # Calculate days difference
    days_diff = timetable_day - current_weekday
    
    # If the timetable day is in the past this week, use that date
    # If it's today, use today
    # If it's in the future this week, use that date
    attendance_date = (today + timedelta(days=days_diff)).date()
    
    # If trying to mark attendance for a future date, show error
    if attendance_date > today.date():
        messages.error(request, f'Cannot mark attendance for future date ({attendance_date}). This class is on {timetable.get_day_of_week_display()}.')
        return redirect('faculty_weekly_schedule')
    
    if request.method == 'POST':
        attendance_marked = False
        
        for student in students:
            status = request.POST.get(f'status_{student.id}')
            if status:
                attendance, created = Attendance.objects.update_or_create(
                    student=student,
                    timetable=timetable,
                    date=attendance_date,
                    defaults={
                        'status': status,
                        'marked_by': faculty,
                        'is_locked': False
                    }
                )
                attendance_marked = True
        
        if attendance_marked:
            update_summaries_after_attendance_marking(
                section=section,
                subject=timetable.subject_assignment.subject,
                academic_year=timetable.subject_assignment.academic_year
            )
            
            messages.success(request, f'Attendance marked successfully for {attendance_date.strftime("%d %B %Y")}.')
        else:
            messages.warning(request, 'No attendance was marked.')
        
        return redirect('faculty_weekly_schedule')
    
    # Get existing attendance for the calculated date
    existing_attendance = Attendance.objects.filter(
        timetable=timetable,
        date=attendance_date
    )
    
    attendance_map = {att.student.id: att.status for att in existing_attendance}
    
    students_list = []
    for student in students:
        student.current_status = attendance_map.get(student.id, None)
        students_list.append(student)
    
    context = {
        'timetable': timetable,
        'students': students_list,
        'today': attendance_date,  
        'actual_class_date': attendance_date,
        'day_name': timetable.get_day_of_week_display()
    }
    return render(request, 'faculty/mark_attendance.html', context)

@login_required
@role_required('faculty')
def edit_attendance(request, timetable_id):
    """Edit attendance for a specific class/date"""
    from .utils import update_summaries_after_attendance_marking
    
    timetable = get_object_or_404(Timetable, id=timetable_id)
    faculty = request.user.faculty_profile
    
    if timetable.subject_assignment.faculty != faculty:
        messages.error(request, 'Unauthorized access.')
        return redirect('dashboard')
    
    section = timetable.subject_assignment.section
    students = Student.objects.filter(section=section).order_by('roll_number')
    
    # Get selected date or default to today
    selected_date = request.GET.get('date', timezone.now().date())
    if isinstance(selected_date, str):
        selected_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
    
    if request.method == 'POST':
        attendance_updated = False
        
        for student in students:
            status = request.POST.get(f'status_{student.id}')
            if status:
                attendance, created = Attendance.objects.update_or_create(
                    student=student,
                    timetable=timetable,
                    date=selected_date,
                    defaults={
                        'status': status,
                        'marked_by': faculty,
                        'is_locked': False
                    }
                )
                attendance_updated = True
        
        if attendance_updated:
            update_summaries_after_attendance_marking(
                section=section,
                subject=timetable.subject_assignment.subject,
                academic_year=timetable.subject_assignment.academic_year
            )
            
            messages.success(request, f'Attendance updated successfully for {selected_date}.')
        else:
            messages.warning(request, 'No changes were made.')
        
        return redirect('faculty_weekly_schedule')
    
    # Get existing attendance for the selected date
    existing_attendance = Attendance.objects.filter(
        timetable=timetable,
        date=selected_date
    )
    
    attendance_map = {att.student.id: att.status for att in existing_attendance}
    
    students_list = []
    for student in students:
        student.current_status = attendance_map.get(student.id, None)
        students_list.append(student)
    
    # Get all dates when attendance was marked for this timetable
    marked_dates = Attendance.objects.filter(
        timetable=timetable
    ).values_list('date', flat=True).distinct().order_by('-date')
    
    context = {
        'timetable': timetable,
        'students': students_list,
        'selected_date': selected_date,
        'marked_dates': marked_dates,
    }
    return render(request, 'faculty/edit_attendance.html', context)

@login_required
@role_required('faculty')
def view_attendance_records(request):
    """View attendance records and download report"""
    faculty = request.user.faculty_profile
    assignments = SubjectAssignment.objects.filter(
        faculty=faculty,
        is_active=True
    ).select_related('subject', 'section')
    
    selected_assignment = None
    attendance_data = []
    
    if request.GET.get('assignment'):
        assignment_id = request.GET.get('assignment')
        selected_assignment = get_object_or_404(SubjectAssignment, id=assignment_id, faculty=faculty)
        
        if request.GET.get('download') == 'pdf':
            return download_faculty_attendance_report(request, selected_assignment)
        
        students = Student.objects.filter(section=selected_assignment.section)
        
        for student in students:
            summary = AttendanceSummary.objects.filter(
                student=student,
                subject=selected_assignment.subject,
                academic_year=selected_assignment.academic_year
            ).first()
            
            if summary:
                attendance_data.append({
                    'student': student,
                    'total_classes': summary.total_classes,
                    'attended': summary.classes_attended,
                    'percentage': summary.attendance_percentage
                })
    
    context = {
        'assignments': assignments,
        'selected_assignment': selected_assignment,
        'attendance_data': attendance_data
    }
    return render(request, 'faculty/view_attendance.html', context)

def download_faculty_attendance_report(request, assignment):
    """Download attendance report for faculty's class"""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    from io import BytesIO
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    
    title = Paragraph(f"Attendance Report - {assignment.subject.name}", styles['Title'])
    elements.append(title)
    elements.append(Spacer(1, 12))
    
    details = f"Faculty: {assignment.faculty.user.get_full_name()}<br/>Section: {assignment.section}<br/>Academic Year: {assignment.academic_year}"
    elements.append(Paragraph(details, styles['Normal']))
    elements.append(Spacer(1, 12))
    
    students = Student.objects.filter(section=assignment.section).order_by('roll_number')
    
    data = [['Roll Number', 'Student Name', 'Total Classes', 'Attended', 'Percentage']]
    for student in students:
        summary = AttendanceSummary.objects.filter(
            student=student,
            subject=assignment.subject,
            academic_year=assignment.academic_year
        ).first()
        
        if summary:
            data.append([
                student.roll_number,
                student.user.get_full_name(),
                str(summary.total_classes),
                str(summary.classes_attended),
                f"{summary.attendance_percentage}%"
            ])
    
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(table)
    doc.build(elements)
    
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="attendance_{assignment.subject.code}_{assignment.section.name}.pdf"'
    
    return response

@login_required
@role_required('faculty')
def faculty_profile(request):
    """Faculty profile and settings"""
    faculty = request.user.faculty_profile
    
    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        name_parts = full_name.strip().split(' ', 1)
        request.user.first_name = name_parts[0]
        request.user.last_name = name_parts[1] if len(name_parts) > 1 else ''
        request.user.email = request.POST.get('email')
        request.user.phone = request.POST.get('phone')
        request.user.save()
        
        faculty.designation = request.POST.get('designation')
        faculty.qualification = request.POST.get('qualification')
        faculty.save()
        
        messages.success(request, 'Profile updated successfully.')
        return redirect('faculty_profile')
    
    context = {'faculty': faculty}
    return render(request, 'faculty/faculty_profile.html', context)

# Faculty Change Password View
@login_required
@role_required('faculty')
def faculty_change_password(request):
    """Faculty change password view"""
    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        if not request.user.check_password(old_password):
            messages.error(request, 'Current password is incorrect.')
            return redirect('faculty_change_password')
        
        if new_password != confirm_password:
            messages.error(request, 'New passwords do not match.')
            return redirect('faculty_change_password')
        
        if len(new_password) < 8:
            messages.error(request, 'Password must be at least 8 characters long.')
            return redirect('faculty_change_password')
        
        request.user.set_password(new_password)
        request.user.save()
        update_session_auth_hash(request, request.user)
        
        messages.success(request, 'Password changed successfully!')
        return redirect('faculty_profile')
    
    return render(request, 'faculty/faculty_change_password.html')


# ==================== STUDENT VIEWS ====================

@login_required
@role_required('student')
def view_my_attendance(request):
    """View student's own attendance with real-time calculation"""
    student = request.user.student_profile
    active_year = AcademicYear.objects.filter(is_active=True).first()
    
    if not active_year:
        messages.warning(request, 'No active academic year found.')
        context = {
            'summaries': [],
            'selected_subject': None,
            'detailed_attendance': []
        }
        return render(request, 'student/view_attendance.html', context)
    
    subjects = Subject.objects.filter(
        branch=student.section.branch,
        semester=student.current_semester
    )
    
    summaries = []
    for subject in subjects:
        summary, created = AttendanceSummary.objects.get_or_create(
            student=student,
            subject=subject,
            academic_year=active_year
        )
        
        attendance_records = Attendance.objects.filter(
            student=student,
            timetable__subject_assignment__subject=subject,
            timetable__subject_assignment__academic_year=active_year
        )
        
        total = attendance_records.count()
        attended = attendance_records.filter(status='present').count()
        percentage = (attended / total * 100) if total > 0 else 0
        
        summary.total_classes = total
        summary.classes_attended = attended
        summary.attendance_percentage = round(percentage, 2)
        summary.save()
        
        summaries.append(summary)
    
    selected_subject = None
    detailed_attendance = []
    
    if request.GET.get('subject'):
        subject_id = request.GET.get('subject')
        selected_subject = get_object_or_404(Subject, id=subject_id)
        
        detailed_attendance = Attendance.objects.filter(
            student=student,
            timetable__subject_assignment__subject=selected_subject,
            timetable__subject_assignment__academic_year=active_year
        ).select_related('timetable', 'marked_by').order_by('-date')
    
    context = {
        'summaries': summaries,
        'selected_subject': selected_subject,
        'detailed_attendance': detailed_attendance
    }
    return render(request, 'student/view_attendance.html', context)

@login_required
@role_required('student')
def student_profile(request):
    """Student profile and settings"""
    student = request.user.student_profile
    
    if request.method == 'POST':
        request.user.first_name = request.POST.get('first_name')
        request.user.last_name = request.POST.get('last_name')
        request.user.email = request.POST.get('email')
        request.user.phone = request.POST.get('phone')
        request.user.save()
        
        messages.success(request, 'Profile updated successfully.')
        return redirect('student_profile')
    
    context = {'student': student}
    return render(request, 'student/student_profile.html', context)

# Student Change Password View
@login_required
@role_required('student')
def student_change_password(request):
    """Student change password view"""
    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        if not request.user.check_password(old_password):
            messages.error(request, 'Current password is incorrect.')
            return redirect('student_change_password')
        
        if new_password != confirm_password:
            messages.error(request, 'New passwords do not match.')
            return redirect('student_change_password')
        
        if len(new_password) < 8:
            messages.error(request, 'Password must be at least 8 characters long.')
            return redirect('student_change_password')
        
        request.user.set_password(new_password)
        request.user.save()
        update_session_auth_hash(request, request.user)
        
        messages.success(request, 'Password changed successfully!')
        return redirect('student_profile')
    
    return render(request, 'student/student_change_password.html')

@login_required
@role_required('student')
def download_attendance_report(request):
    """This function is no longer used"""
    messages.info(request, 'Attendance download feature has been removed.')
    return redirect('view_my_attendance')

@login_required
@role_required('faculty')
def faculty_weekly_schedule(request):
    """View full weekly timetable with edit attendance option"""
    faculty = Faculty.objects.select_related('user', 'department').get(user=request.user)
    active_year = AcademicYear.objects.filter(is_active=True).first()
    
    if not active_year:
        messages.warning(request, 'No active academic year found.')
        schedule = {i: [] for i in range(6)}
    else:
        slots = list(Timetable.objects.filter(
            subject_assignment__faculty=faculty,
            subject_assignment__academic_year=active_year,
            is_active=True
        ).select_related(
            'subject_assignment__subject',
            'subject_assignment__section',
            'subject_assignment__faculty__user'
        ).order_by('day_of_week', 'period_number'))
        
        schedule = {i: [] for i in range(6)}
        for slot in slots:
            schedule[slot.day_of_week].append(slot)
    
    context = {
        'schedule': schedule,
        'days': Timetable.DAY_CHOICES,
        'faculty': faculty,
        'active_year': active_year,
    }
    
    response = render(request, 'faculty/weekly_schedule.html', context)
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    
    return response


