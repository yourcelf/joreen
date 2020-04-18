from collections import defaultdict
from django.core.management.base import BaseCommand

from stateparsers.models import FacilityNameResult

class Command(BaseCommand):
    help = "Write a fixture that contains all facilities"

    def handle(self, *args, **options):
        unknown = []
        multiple = []
        for fnr in FacilityNameResult.objects.all().order_by('administrator'):
            facilities = list(fnr.find_facilities())
            if len(facilities) == 0:
                unknown.append(fnr)
            elif len(facilities) > 1:
                f1 = facilities[0]
                for facility in facilities[1:]:
                    if facility.name != f1.name or facility.code != f1.code:
                        multiple.append((fnr, facilities))
                        break

        unknown.sort(key=lambda fnr: (fnr.administrator.name, fnr.name))
        multiple.sort(key=lambda fnrf: (fnrf[0].administrator.name, fnrf[0].name))

        cur_admin = None
        print("##########################################")
        print("MULTIPLE: ", len(multiple))
        for fnr, facilities in multiple:
            if fnr.administrator != cur_admin:
                print()
                print("-------------- ", fnr.administrator.name, " ---------------")
                cur_admin = fnr.administrator
            print()
            print(fnr.name)
            for facility in facilities:
                for line in facility.flat_address().split("\n"):
                    print("   ", line)
                print()

        print("##########################################")
        print("UNKNOWN: ", len(unknown))
        cur_admin = None
        for fnr in unknown:
            if fnr.administrator != cur_admin:
                print()
                print("-------------- ", fnr.administrator.name, " ---------------")
                cur_admin = fnr.administrator
            print(fnr.name)




