from django.core.management.base import BaseCommand
from attendance.models import AttendanceSummary, AcademicYear


class Command(BaseCommand):
    help = 'Recalculate all attendance summaries till date'

    def handle(self, *args, **options):
        active_year = AcademicYear.objects.filter(is_active=True).first()
        
        if not active_year:
            self.stdout.write(self.style.ERROR('No active academic year found!'))
            return
        
        summaries = AttendanceSummary.objects.filter(academic_year=active_year)
        count = summaries.count()
        
        self.stdout.write(f'Updating {count} attendance summaries...')
        
        for i, summary in enumerate(summaries, 1):
            summary.update_summary()
            if i % 50 == 0:
                self.stdout.write(f'Processed {i}/{count}...')
        
        self.stdout.write(self.style.SUCCESS(f'Successfully updated {count} summaries!'))