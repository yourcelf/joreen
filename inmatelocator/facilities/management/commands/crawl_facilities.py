import json
import subprocess
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from facilities.models import *

class Command(BaseCommand):
    help = "Crawl to obtain names and addresses of state facilities."

    def add_arguments(self, parser):
        parser.add_argument('state', nargs='+', type=str)

    def handle(self, *args, **options):
        for state in options['state']:
            proc = subprocess.Popen([
                settings.SCRAPY_BIN,
                'crawl',
                state,
                "-t",
                "json",
                "-o",
                "-"
            ], cwd=settings.SCRAPY_DIR, stdout=subprocess.PIPE)
            stdout, stderr = proc.communicate()
            if proc.returncode != 0:
                raise CommandError("Error crawling {}".format(state))
            data = json.loads(stdout.decode("utf-8"))

            for entry in data:
                lookup = {'state': entry['state']}
                if entry.get('identifier'):
                    lookup['code'] = entry['identifier']
                else:
                    lookup['name'] = entry['organization']
                try:
                    facility = Facility.objects.get(**lookup)
                except Facility.DoesNotExist:
                    facility = Facility(**lookup)

                facility.name = entry['organization']
                facility.code = entry.get('identifier') or ''
                for key in ("address1", "address2", "address3", "city", "zip", "phone"):
                    setattr(facility, key, entry.get(key, ''))

                facility.provenance = entry.get("source")
                facility.provenance_url = entry.get("url")

                if entry.get("type"):
                    facility.type = FacilityType.objects.get_or_create(name=entry['type'])[0]

                facility.administrator = FacilityAdministrator.objects.get_or_create(
                        name=entry['administrator'])[0]

                if entry.get("operator"):
                    facility.operator = FacilityOperator.objects.get_or_create(
                            name=entry['administrator'])[0]

                facility.save()
                for alt in entry.get("alternate_names", []):
                    AlternateName.objects.get_or_create(name=alt, facility=facility)


