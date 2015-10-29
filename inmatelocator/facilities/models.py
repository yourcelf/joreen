from django.db import models
from django.db.models import Q
from django.utils import timezone
from localflavor.us.models import USStateField, USPostalCodeField, PhoneNumberField

class FacilityType(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class FacilityAdministrator(models.Model):
    name = models.CharField(max_length=255,
            help_text="The incarcerating state or entity, e.g. Federal Bureau of Prisons; California")

    def __str__(self):
        return self.name

class FacilityOperator(models.Model):
    name = models.CharField(max_length=255,
            help_text="The company or department that operates, e.g. Corrections Corporation of America; California Department of Corrections")

    def __str__(self):
        return self.name

class FacilityManager(models.Manager):
    def find_by_name(self, admin, name, **kwargs):
        return self.filter(
            Q(name__iexact=name) | Q(alternatename__name__iexact=name),
            administrator__name=admin, **kwargs
        ).distinct()

    def find_by_partial_name(self, admin, name, **kwargs):
        return self.filter(
            Q(name__icontains=name) | Q(alternatename__name__icontains=name),
            administrator__name=admin, **kwargs
        ).distinct()

class Facility(models.Model):
    code = models.CharField(max_length=255,
        help_text="Facility code provided by facility administrator.  The more unique the better, though some DOC's have many addresses under the same code.", blank=True)
    name = models.CharField(max_length=255,
        help_text="Canonical name for the facility")
    address1 = models.CharField(max_length=255, blank=True)
    address2 = models.CharField(max_length=255, blank=True)
    address3 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=255)
    state = USStateField()
    zip = USPostalCodeField()
    phone = PhoneNumberField(blank=True)
    general = models.BooleanField(default=False, help_text="Is this address a 'general mail' address for facilities with this code?")

    type = models.ForeignKey(FacilityType, null=True)
    administrator = models.ForeignKey(FacilityAdministrator, null=True)
    operator = models.ForeignKey(FacilityOperator, null=True)

    provenance = models.CharField(max_length=255, verbose_name="data source")
    provenance_url = models.CharField(max_length=255, verbose_name="data source URL")

    modified = models.DateTimeField(auto_now=True)

    objects = FacilityManager()

    def __str__(self):
        return self.code

    class Meta:
        verbose_name_plural = "facilities"
        ordering = ['state', 'name', 'general']

class AlternateName(models.Model):
    facility = models.ForeignKey(Facility)
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name
