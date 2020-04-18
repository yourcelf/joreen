from django.db import models
from django.db.models import Q
from django.utils import timezone
from localflavor.us.models import USPostalCodeField, USZipCodeField, PhoneNumberField

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
    city = models.CharField(max_length=255)
    state = USPostalCodeField()
    zip = USZipCodeField()
    phone = PhoneNumberField(blank=True, max_length=255)
    general = models.BooleanField(default=False, help_text="Is this address a 'general mail' address for facilities with this code?")

    type = models.ForeignKey(FacilityType, null=True)
    administrator = models.ForeignKey(FacilityAdministrator, null=True)
    operator = models.ForeignKey(FacilityOperator, null=True)

    provenance = models.CharField(max_length=255, verbose_name="data source")
    provenance_url = models.CharField(max_length=255, verbose_name="data source URL")

    modified = models.DateTimeField(auto_now=True)

    objects = FacilityManager()

    def to_result_dict(self):
        out = {}
        for key in ["id", "code", "name", "address1", "address2", "city", "state", "zip", "phone", "general", "provenance", "provenance_url"]:
            out[key] = getattr(self, key)
        out["formatted_address"] = self.flat_address()
        out["administrator"] = self.administrator.name if self.administrator else ""
        out["type"] = self.type.name if self.type else ""
        out["modified"] = self.modified.isoformat()
        return out

    def flat_address(self):
        parts = []
        haz = lambda key: hasattr(self, key) and getattr(self, key)
        if haz('name'): parts.append(self.name)
        if haz('address1'): parts.append(self.address1)
        if haz('address2'): parts.append(self.address2)

        if haz('city') and haz('state') and haz('zip'):
            parts.append("{}, {}  {}".format(self.city, self.state, self.zip))
        else:
            if haz('city'): parts.append(self.city)
            if haz('state'): parts.append(self.state)
            if haz('zip'): parts.append(self.zip)
        return u"\n".join(parts)

    def __str__(self):
        return self.code

    class Meta:
        verbose_name_plural = "facilities"
        ordering = ['state', 'name', '-general', 'address1']

class AlternateName(models.Model):
    facility = models.ForeignKey(Facility)
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name
