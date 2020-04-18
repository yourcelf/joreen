from django.http import HttpResponse
from django.contrib.auth.decorators import permission_required

from blackandpink.models import UpdateRun, FacilityRun
import blackandpink.tasks

# Create your views here.
@permission_required('blackandpink.add_updaterun')
def start_update_run(request):
    try:
        current = UpdateRun.objects.get_unfinished()
    except UpdateRun.DoesNotExist:
        current = None
    if current is not None:
        return HttpResponse("Update Run Started: {}".format(current.started.isoformat()))

    blackandpink.tasks.do_update_run.delay()
    return HttpResponse("Started")

# Create your views here.
@permission_required('blackandpink.add_facilityrun')
def start_facility_run(request):
    try:
        current = FacilityRun.objects.get_unfinished()
    except FacilityRun.DoesNotExist:
        current = None
    if current is not None:
        return HttpResponse("Facility Run Started: {}".format(current.started.isoformat()))

    blackandpink.tasks.do_facility_run.delay()
    return HttpResponse("Started")

