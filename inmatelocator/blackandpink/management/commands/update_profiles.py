from django.core.management.base import BaseCommand
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.conf import settings
from queue import Queue
import traceback

from facilities.models import FacilityAdministrator
from stateparsers import AVAILABLE_STATES
from blackandpink import zoho
from blackandpink.blackandpink import Address, Profile, FacilityDirectory
from blackandpink.models import UpdateRun, MemberProfile, ContactCheck

def log_exception(update_run, exception, member_number):
    print(exception)
    print(traceback.format_exc())
    update_run.errors.append({
        "exception": str(exception),
        "traceback": traceback.format_exc(),
        "member_number": member_number
    })
    update_run.save()

def search(update_run, member, profile, facility_directory):
    match_result_set = profile.search() 
    profile_match = match_result_set.best()
    profile_match.classify(facility_directory)
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

    address_changed = profile_match.status in (
        ContactCheck.STATUS.found_facility_differs_zoho_has,
        ContactCheck.STATUS.found_facility_differs_zoho_lacks,
    )
    entry_changed = address_changed or profile_match.status in (
        ContactCheck.STATUS.found_released_zoho_disagrees,
    )

    entry_before = profile.zoho_profile
    entry_after = ""

    cc = ContactCheck.objects.create(
        update_run=update_run,
        member=member,
        raw_facility_name=raw_facility_name,
        entry_before=profile.zoho_profile,
        entry_after="",
        search_result=profile_match.result.to_dict() if profile_match.result else None,
        entry_changed=entry_changed,
        facility=profile_match.facility_match.facility if profile_match.facility_match else None,
        administrator=administrator,
        status=profile_match.status,
    )

def update_zoho(cc, facility_directory):
    address_key = None
    address_status = None
    release_status = None
    S = ContactCheck.STATUS

    if cc.status == S.found_facility_matches:
        # All good; just update the address status to "ok".
        address_key = None
        address_status = "ok"
    elif cc.status == S.found_facility_differs_zoho_has:
        zoho_facility = facility_directory.get_by_facility(cc.facility).zoho_facility
        address_key = zoho_facility['Facility_Add2_City_State_Zip']
        address_status = "ok"
    elif cc.status == S.found_facility_differs_zoho_lacks:
        # Even if at time of creating the contact check the facility didn't
        # exist, it might have been added already.  Try finding it in the
        # facility directory.
        zoho_facility = facility_directory.get_by_facility(cc.facility)
        if not zoho_facility:
            # Add the joreen facility to zoho.
            zoho_facility = zoho.add_facility(cc.facility)
            # Add the zoho result to our in-memory directory for further processing.
            facility_directory.add_facility(zoho_facility)
        address_key = zoho_facility['Facility_Add2_City_State_Zip']
        address_status = "ok"
    elif cc.status in (S.found_released_zoho_disagrees,
                       S.found_released_zoho_agrees):
        address_key = None
        address_status = "seemingly released"
        release_status = "Released"
    elif cc.status == S.not_found:
        address_key = None
        address_status = "not found"
    elif cc.status == S.found_unknown_facility:
        address_key = None
        address_status = "unknown facility"
    else:
        raise Exception("Unknown cc status: {}".format(cc.status))

    cc.entry_after = zoho.update_profile(
        update_url="{}{}".format(settings.SITE_URL, cc.get_absolute_url()),
        zoho_profile_id=cc.member.zoho_id,
        address_status=address_status,
        release_status=release_status,
        zoho_facility_key=address_key)
    cc.save()

class Command(BaseCommand):
    help = "Search for all profiles from zoho in respective DOC search sites, " \
           "attempt to find current addresses, and update them if needed."

    def handle(self, *args, **options):
        num_worker_threads = 1
        # Fetch the profiles.
        zoho_profiles = zoho.fetch_all_profiles()
        print("Profiles fetched")

        # Fetch a mapping of zoho facilit
        facility_directory = FacilityDirectory()
        print("Facility directory fetched")

        # Instantiate profile objects for each zoho dict
        profiles = []
        for zoho_profile in zoho_profiles:
            profile = Profile.from_zoho(zoho_profile)
            # Exclude people without addresses
            if not profile.address:
                continue

            # Exclude released and deceased people
            if not profile.status_is_searchable():
                continue

            # Exclude personal addresses and non-prison addresses
            facility_type = facility_directory.get_facility_type(zoho_profile=zoho_profile)
            if facility_type not in ("State", "Federal", "Detention Center",
                    "State Prison- Hospital", "County Jail", "", None):
                continue

            # Exclude non-federal addresses outside available states
            if facility_type != "Federal" and profile.address.state not in AVAILABLE_STATES:
                continue

            # Proceed!
            profiles.append(profile)

        # Create our update run model to store results.
        update_run = UpdateRun.objects.create(errors=[], total_count=len(profiles))

        search_queue = []
        for profile in profiles:
            member, created = MemberProfile.objects.update_or_create(
                    bp_member_number=profile.bp_member_number,
                    defaults={
                        'bp_member_number': profile.bp_member_number,
                        'zoho_id': profile.zoho_profile['ID'],
                    })
            search_queue.append({
                'update_run': update_run,
                'member': member,
                'profile': profile,
                'facility_directory': facility_directory
            })
        print("MemberProfile instances updated")

        for kwargs in search_queue:
            try:
                search(**kwargs)
            except Exception as e:
                log_exception(update_run, e, kwargs['member'].bp_member_number)
                continue
        print("Searches complete")

        for cc in ContactCheck.objects.filter(update_run=update_run, entry_after=""):
            try:
                update_zoho(cc, facility_directory)
            except Exception as e:
                log_exception(update_run, e, cc.member.bp_member_number)
                continue
        print("Zoho updates complete")

        update_run.finished = timezone.now()
        update_run.save()
