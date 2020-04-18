import time
import datetime
from urllib.parse import urlparse
from django.db import models

from facilities.models import FacilityAdministrator, Facility


class NetlocThrottleManager(models.Manager):
    def touch(self, url, seconds):
        netloc = urlparse(url).netloc
        self.update_or_create(
            netloc=netloc, defaults={"wait_until": time.time() + seconds}
        )

    def block(self, url):
        netloc = urlparse(url).netloc
        try:
            model = self.get(netloc=netloc)
        except NetlocThrottle.DoesNotExist:
            return False

        delta = model.wait_until - time.time()
        if delta <= 0:
            # print("RELEASE", url, time.time())
            return False

        # print("Waiting...", url, time.time(), delta)
        time.sleep(delta)
        return self.block(url)


class NetlocThrottle(models.Model):
    netloc = models.CharField(unique=True, max_length=255)
    wait_until = models.IntegerField()

    objects = NetlocThrottleManager()

    def as_date(self):
        return datetime.datetime.fromtimestamp(self.wait_until)

    def __str__(self):
        return self.netloc

    class Meta:
        app_label = "stateparsers"


class FacilityNameResultManager(models.Manager):
    def log_name(self, admin_name, facility_name, facility_url=""):
        obj, created = self.get_or_create(
            administrator=FacilityAdministrator.objects.get(name=admin_name),
            name=facility_name,
            facility_url=facility_url,
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
    facility_url = models.TextField(
        blank=True,
        help_text="URL to the facility in question if provided by search site",
    )

    created = models.DateTimeField(auto_now_add=True)

    objects = FacilityNameResultManager()

    def find_facilities(self):
        return Facility.objects.find_by_name(self.administrator.name, self.name)

    def __str__(self):
        return self.name

    class Meta:
        app_label = "stateparsers"
        verbose_name = "Facility name reported by search backend"
        verbose_name_plural = "Facility names reported by search backends"
