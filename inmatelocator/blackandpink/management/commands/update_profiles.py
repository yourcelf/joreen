from django.core.management.base import BaseCommand
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.conf import settings
from queue import Queue
import traceback
import threading

from facilities.models import FacilityAdministrator
from stateparsers import AVAILABLE_STATES
from blackandpink import zoho
from blackandpink.blackandpink import Address, Profile, FacilityDirectory
from blackandpink.models import UpdateRun, MemberProfile, ContactCheck


lock = threading.Lock()

def search_job(update_run, member, profile, facility_directory):
    try:
        match_result_set = profile.search() 
    except Exception as e:
        update_run.errors.append({
            "exception": str(e),
            "traceback": traceback.format_exc(),
            "member_number": profile.bp_member_number,
        })
        with lock:
            update_run.save() # persist this in case we bork elsewhere.
        return 

    profile_match = match_result_set.best()
    profile_match.classify(facility_directory)
    with lock:
        print(profile.bp_member_number, profile.first_name, profile.last_name, profile_match.status)

    if profile_match.result and profile_match.result.administrator_name:
        administrator = FacilityAdministrator.objects.get(
                name=profile_match.result.administrator_name)
    else:
        administrator = None

    if profile_match.result and profile_match.status != ContactCheck.STATUS.not_found:
        raw_facility_name = profile_match.result.raw_facility_name or ""
    else:
        raw_facility_name = ""

    cc = ContactCheck.objects.create(
        update_run=update_run,
        member=member,
        raw_facility_name=raw_facility_name,
        entry_before=profile.zoho_profile,
        entry_after="...",
        search_result=profile_match.result.to_dict() if profile_match.result else None,
        entry_changed=profile_match.status in (
            ContactCheck.STATUS.found_facility_differs_zoho_has,
            ContactCheck.STATUS.found_facility_differs_zoho_lacks,
            ContactCheck.STATUS.found_released_zoho_disagrees,
        ),
        facility=profile_match.facility_match.facility if profile_match.facility_match else None,
        administrator=administrator,
        status=profile_match.status,
    )


work_queue = Queue()
def worker():
    while True:
        item = work_queue.get()
        if item is None:
            break
        search_job(**item)
        work_queue.task_done()

class Command(BaseCommand):
    help = "Search for all profiles from zoho in respective DOC search sites, " \
           "attempt to find current addresses, and update them if needed."

    def handle(self, *args, **options):
        num_worker_threads = 1
        # Fetch the profiles.
        zoho_profiles = zoho.fetch_all_profiles()
        print("Profiles fetched")

        # Create our update run model to store results.
        update_run = UpdateRun.objects.create(errors=[])

        # Fetch a mapping of zoho facilit
        facility_directory = FacilityDirectory()
        print("Facility directory fetched")

        # Queue up the search jobs to perform.
        for zoho_profile in zoho_profiles:
            profile = Profile.from_zoho(zoho_profile)
            # FIXME: allow federal from all states.
            if not profile.address or (profile.address.state not in AVAILABLE_STATES):
                continue

            member, created = MemberProfile.objects.get_or_create(
                    bp_member_number=profile.bp_member_number)

            work_queue.put({
                'update_run': update_run,
                'member': member,
                'profile': profile,
                'facility_directory': facility_directory
            })

        # Start search threads.
        threads = []
        for i in range(num_worker_threads):
            t = threading.Thread(target=worker)
            t.start()
            threads.append(t)

        work_queue.join()

        for i in range(num_worker_threads):
            work_queue.put(None)
        for t in threads:
            t.join()

        update_run.finished = timezone.now()
        update_run.save()
