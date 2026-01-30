

from .models import Student, Subject, AcademicYear, AttendanceSummary, Attendance

def recalculate_student_summary(student, subject, academic_year):
    # Get or create the summary
    summary, created = AttendanceSummary.objects.get_or_create(
        student=student,
        subject=subject,
        academic_year=academic_year
    )
    
    # Calculate from actual attendance records
    attendance_records = Attendance.objects.filter(
        student=student,
        timetable__subject_assignment__subject=subject,
        timetable__subject_assignment__academic_year=academic_year
    )
    
    total_classes = attendance_records.count()
    classes_attended = attendance_records.filter(status='present').count()
    
    if total_classes > 0:
        percentage = (classes_attended / total_classes) * 100
    else:
        percentage = 0
    
    # Update summary
    summary.total_classes = total_classes
    summary.classes_attended = classes_attended
    summary.attendance_percentage = round(percentage, 2)
    summary.save()
    
    return summary


def recalculate_all_summaries_for_student(student):
    
    active_year = AcademicYear.objects.filter(is_active=True).first()
    
    if not active_year:
        return []
    
    # Get all subjects for this student
    subjects = Subject.objects.filter(
        branch=student.section.branch,
        semester=student.current_semester
    )
    
    summaries = []
    for subject in subjects:
        summary = recalculate_student_summary(student, subject, active_year)
        summaries.append(summary)
    
    return summaries


def get_student_overall_attendance(student):
    active_year = AcademicYear.objects.filter(is_active=True).first()
    
    if not active_year:
        return {
            'total_classes': 0,
            'classes_attended': 0,
            'percentage': 0
        }
    
    # Recalculate all summaries first
    summaries = recalculate_all_summaries_for_student(student)
    
    total_classes = sum(s.total_classes for s in summaries)
    classes_attended = sum(s.classes_attended for s in summaries)
    percentage = (classes_attended / total_classes * 100) if total_classes > 0 else 0
    
    return {
        'total_classes': total_classes,
        'classes_attended': classes_attended,
        'percentage': round(percentage, 2)
    }


def update_summaries_after_attendance_marking(section, subject, academic_year):
    students = Student.objects.filter(section=section)
    
    for student in students:
        recalculate_student_summary(student, subject, academic_year)
    
    return True