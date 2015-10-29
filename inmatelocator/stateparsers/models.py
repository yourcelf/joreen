from django.db import models

from facilities.models import FacilityAdministrator, Facility

class FacilityNameResultManager(models.Manager):
    def log_name(self, admin_name, facility_name, facility_url=""):
        obj, created = self.get_or_create(
            administrator=FacilityAdministrator.objects.get(name=admin_name),
            name=facility_name,
            facility_url=facility_url
        )
        return obj

class FacilityNameResult(models.Model):
    """
    Log a record of the strings used to refer to prison facilities, as seen on
    DOC search pages.  Used to test accuracy of name
    parsing/cleaning/associating logic.
    """
    administrator = models.ForeignKey(FacilityAdministrator)
    name = models.CharField(max_length=255)
    facility_url = models.CharField(max_length=255, blank=True,
            help_text="URL to the facility in question if provided by search site")
    facility = models.ForeignKey(Facility, blank=True, null=True,
            help_text="Set to manually associate a string with a facility, preempting other ways to guess at the identity of this facility.")

    created = models.DateTimeField(auto_now_add=True)

    objects = FacilityNameResultManager()

    def __str__(self):
        return self.name

    class Meta:
        app_label = 'stateparsers'
