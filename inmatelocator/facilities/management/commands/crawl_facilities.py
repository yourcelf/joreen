import json
import subprocess
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from facilities.models import *
from stateparsers.states import BaseStateSearch

class Command(BaseCommand):
    help = "Crawl to obtain names and addresses of state facilities."

    def add_arguments(self, parser):
        parser.add_argument('state', nargs='+', type=str)

    def handle(self, *args, **options):
        states = options['state']
        if 'all' in states:
            states = ['california', 'federal', 'florida', 'newyork', 'pennsylvania', 'texas']
        for state in states:
            proc = subprocess.Popen([
                settings.SCRAPY_BIN,
                'crawl',
                state,
                "--loglevel",
                "WARNING",
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
                lookup = {
                    'name': entry['organization'],
                    'code': entry.get('identifier') or '',
                    'address1': entry.get('address1') or '',
                    'address2': entry.get('address2') or '',
                    'city': entry.get('city') or '',
                    'state': entry.get('state') or '',
                    'zip': entry.get('zip') or ''
                }
                if lookup['state']:
                    lookup['state'] = BaseStateSearch.get_state(lookup['state'])
                try:
                    facility = Facility.objects.get(**lookup)
                except Facility.DoesNotExist:
                    facility = Facility(**lookup)

                facility.phone = entry.get('phone') or ''
                facility.provenance = entry.get("source")
                facility.provenance_url = entry.get("url")
                facility.general = entry.get('general') or False

                if entry.get("type"):
                    facility.type = FacilityType.objects.get_or_create(name=entry['type'])[0]

                facility.administrator = FacilityAdministrator.objects.get_or_create(
                        name=entry['administrator'])[0]

                if entry.get("operator"):
                    facility.operator = FacilityOperator.objects.get_or_create(
                            name=entry['operator'])[0]

                facility.save()
                for alt in entry.get("alternate_names", []):
                    AlternateName.objects.get_or_create(name=alt, facility=facility)


