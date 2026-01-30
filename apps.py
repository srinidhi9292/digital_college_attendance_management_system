"""
Apps Configuration
Path: attendance/apps.py
"""

from django.apps import  AppConfig

class AttendanceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'attendance'
    verbose_name = 'Attendance Management System'

    def ready(self):
        # Import signals or perform any startup operations
        # Import signals here if needed
        # import attendance.signals
        pass