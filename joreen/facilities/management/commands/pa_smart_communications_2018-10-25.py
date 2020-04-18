from django.core.management.base import BaseCommand

from facilities.models import Facility


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        pa_scis = Facility.objects.filter(
            name__startswith="SCI", administrator__name="Pennsylvania"
        )
        for fac in pa_scis:
            fac.address1 = "Smart Communications/PADOC"
            fac.address2 = "PO Box 33028"
            fac.city = "St Petersburg"
            fac.state = "FL"
            fac.zip = "33733"
            fac.provenance = "PA website"
            fac.provenance_url = (
                "https://www.cor.pa.gov/family-and-friends/Pages/Mailing-Addresses.aspx"
            )
            fac.save()
