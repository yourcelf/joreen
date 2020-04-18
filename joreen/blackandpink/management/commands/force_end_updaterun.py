from django.core.management.base import BaseCommand
from django.utils import timezone

from blackandpink.models import UpdateRun

class Command(BaseCommand):
    help = "Mark an UpdateRun as finished."
    def handle(self, *args, **options):
        while True:
            try:
                ur = UpdateRun.objects.get_unfinished()
                ur.finished = timezone.now()
                ur.save()
            except UpdateRun.DoesNotExist:
                break
