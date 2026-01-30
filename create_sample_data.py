from django.core.management.base import BaseCommand
from attendance.models import *
from django.contrib.auth.hashers import make_password
from datetime import date

class Command(BaseCommand):
    help = 'Creates sample data'

    def handle(self, *args, **kwargs):
        # Create Academic Year
        academic_year = AcademicYear.objects.create(
            year="2024-2025",
            start_date=date(2024, 7, 1),
            end_date=date(2025, 6, 30),
            is_active=True
        )
        
        # Create Department
        dept = Department.objects.create(
            name="Computer Science",
            code="CSE"
        )
        
        # Create Branch
        branch = Branch.objects.create(
            department=dept,
            name="B.Tech CSE",
            code="BTCSE",
            duration_years=4
        )
        
        # Create Section
        section = Section.objects.create(
            branch=branch,
            name="A",
            semester=5,
            academic_year=academic_year,
            capacity=60
        )
        
        # Create Admin User
        User.objects.create(
            username="admin",
            email="admin@college.edu",
            first_name="Admin",
            last_name="User",
            role="admin",
            is_staff=True,
            is_superuser=True,
            password=make_password("admin123")
        )
        
        self.stdout.write(self.style.SUCCESS('Sample data created!'))