import os
import subprocess
from django.core.management.base import BaseCommand
from facilities.models import *

DEST = os.path.join(
    os.path.dirname(__file__), "..", "..", "fixtures", "facilities.json"
)


class Command(BaseCommand):
    help = "Write a fixture that contains all facilities"

    def handle(self, *args, **options):
        result = subprocess.check_output(
            ["python", "manage.py", "dumpdata", "facilities", "--indent", "2"]
        )
        with open(DEST, "w") as fh:
            fh.write(result.decode("utf-8"))
