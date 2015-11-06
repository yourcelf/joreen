from django.core.management.base import BaseCommand
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.conf import settings

from stateparsers import AVAILABLE_STATES
from blackandpink import zoho
from blackandpink.blackandpink import Address
from blackandpink.models import UnknownFacility, UnknownFacilityMatch

class Command(BaseCommand):
    help = "Attempt to match all zoho facilities with known facilities, and " \
           "create UnknownFacility objects for any that are not recognized."

    def handle(self, *args, **options):
        zoho_facilities = zoho.fetch_all_facilities()

        found = 0
        existing_unknown = 0
        new_unknown = 0
        for zoho_facility in zoho_facilities:
            if "Personal" in zoho_facility.get('Facility_Type', ''):
                continue
            address = Address.from_zoho(zoho_facility)

            if not (address.state in AVAILABLE_STATES or
                    zoho_facility.get('Facility_Type') == 'Federal'):
                continue

            zoho_url = "https://creator.zoho.com/{}/{}/{}/record-edit/{}/{}".format(
                    settings.ZOHO_OWNER_NAME,
                    settings.ZOHO_APPLICATION_LINK_NAME,
                    settings.ZOHO_FACILITIES_FORM_NAME,
                    settings.ZOHO_FACILITIES_VIEW_NAME,
                    zoho_facility['ID'])

            current_count = 0
            if zoho_facility['Mailing_Address_Date_Current'] != '[]':
                current_count = len(zoho_facility['Mailing_Address_Date_Current'].split('],'))
            uf_defaults = {
                'state': address.state or '',
                'flat_address': address.flatten(),
                'zoho_url': zoho_url,
                'current_address_count': current_count,
                'address_valid': True,
                'comment': ''
            }

            try:
                address.validate()
            except ValidationError as e:
                uf_defaults['comment'] = str(e)
                uf_defaults['address_valid'] = False
                UnknownFacility.objects.update_or_create(
                    zoho_id=zoho_facility['ID'],
                    defaults=uf_defaults
                )
                continue

            matches = address.find_matching_facilities()
            if matches and matches[0].is_valid():
                found += 1
                UnknownFacility.objects.filter(zoho_id=zoho_facility['ID']).delete()
            else:
                uf, created = UnknownFacility.objects.update_or_create(
                    zoho_id=zoho_facility['ID'],
                    defaults=uf_defaults
                )
                if created:
                    new_unknown += 1
                else:
                    existing_unknown += 1

                ufms = []
                for match in matches:
                    ufm, created = UnknownFacilityMatch.objects.update_or_create(
                            unknown_facility=uf,
                            match=match.facility,
                            defaults={'score': match.score,
                                      'breakdown': match.breakdown})
                    ufms.append(ufm)
                # Clear any prior UnknownFacilityMatch'es that are no longer
                # relevant by asserting that this list of ufm's is the whole
                # set.
                uf.unknownfacilitymatch_set = ufms
