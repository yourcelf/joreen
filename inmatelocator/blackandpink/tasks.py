from django.core.management import call_command
from blackandpink.models import UpdateRun

from celery import shared_task

@shared_task(name='inmatelocator.blackandpink.tasks.do_update_run')
def do_update_run():
    try:
        UpdateRun.objects.get_unfinished()
        return
    except UpdateRun.DoesNotExist:
        call_command("update_profiles")

@shared_task(name='inmatelocator.blackandpink.tasks.do_facility_run')
def do_facility_run():
    try:
        FacilityRun.objects.get_unfinished()
        return
    except FacilityRun.DoesNotExist:
        call_command("match_zoho_facilities")