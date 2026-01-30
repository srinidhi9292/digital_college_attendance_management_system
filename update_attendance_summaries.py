"""
Django Management Command to Update Attendance Summaries
Path: attendance/management/commands/update_attendance_summaries.py

Create this file structure:
attendance/
    management/
        __init__.py
        commands/
            __init__.py
            update_attendance_summaries.py

Run with: python manage.py update_attendance_summaries
"""

from django.core.management.base import BaseCommand
from attendance.models import Student, Subject, AcademicYear, AttendanceSummary, Attendance

class Command(BaseCommand):
    help = 'Update all attendance summaries for all students'

    def handle(self, *args, **options):
        self.stdout.write('Starting attendance summary update...')
        
        active_year = AcademicYear.objects.filter(is_active=True).first()
        if not active_year:
            self.stdout.write(self.style.ERROR('No active academic year found!'))
            return
        
        students = Student.objects.all()
        total_updated = 0
        
        for student in students:
            # Get all subjects for this student's section
            subjects = Subject.objects.filter(
                branch=student.section.branch,
                semester=student.current_semester
            )
            
            for subject in subjects:
                # Get or create summary
                summary, created = AttendanceSummary.objects.get_or_create(
                    student=student,
                    subject=subject,
                    academic_year=active_year
                )
                
                # Calculate attendance from scratch
                attendance_records = Attendance.objects.filter(
                    student=student,
                    timetable__subject_assignment__subject=subject,
                    timetable__subject_assignment__academic_year=active_year
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
                
                total_updated += 1
                
                if created:
                    self.stdout.write(f'Created summary for {student.roll_number} - {subject.code}')
                else:
                    self.stdout.write(f'Updated summary for {student.roll_number} - {subject.code}')
        
        self.stdout.write(self.style.SUCCESS(f'Successfully updated {total_updated} attendance summaries'))