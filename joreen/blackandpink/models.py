import json
from django.db import models
from django.utils import timezone
from facilities.models import Facility, FacilityAdministrator
from localflavor.us.models import USStateField, USPostalCodeField, PhoneNumberField
import urllib
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.conf import settings
from django.core import urlresolvers
from jsonfield import JSONField


class FinishedManager(models.Manager):
    def get_unfinished(self):
        try:
            return self.filter(finished__isnull=True)[0]
        except IndexError:
            raise self.model.DoesNotExist


class UpdateRun(models.Model):
    started = models.DateTimeField(auto_now_add=True)
    finished = models.DateTimeField(blank=True, null=True, unique=True)
    total_count = models.IntegerField()
    errors = JSONField()

    objects = FinishedManager()

    def complete(self):
        if self.total_count == 0:
            return "0%"
        cc_count = self.contactcheck_set.count()
        if cc_count == 0:
            return "0%"
        updated_count = self.contactcheck_set.exclude(entry_after="").count()
        return "search: {:2.1f}%, update: {:2.1f}%".format(
            (100 * cc_count / self.total_count), (100 * updated_count / cc_count)
        )

    def not_found(self):
        return self.contactcheck_set.filter(
            status=ContactCheck.STATUS.not_found
        ).count()

    def unknown_fac(self):
        return self.contactcheck_set.filter(
            status=ContactCheck.STATUS.found_unknown_facility
        ).count()

    def fac_matches(self):
        return self.contactcheck_set.filter(
            status=ContactCheck.STATUS.found_facility_matches
        ).count()

    fac_matches.short_description = "Same"

    def moved(self):
        return (
            self.contactcheck_set.filter(
                status=ContactCheck.STATUS.found_facility_differs_zoho_has
            ).count()
            + self.contactcheck_set.filter(
                status=ContactCheck.STATUS.found_facility_differs_zoho_lacks
            ).count()
        )

    def released_zoho_agrees(self):
        return self.contactcheck_set.filter(
            status=ContactCheck.STATUS.found_released_zoho_agrees
        ).count()

    released_zoho_agrees.short_description = "prev released"

    def released_zoho_disagrees(self):
        return self.contactcheck_set.filter(
            status=ContactCheck.STATUS.found_released_zoho_disagrees
        ).count()

    released_zoho_disagrees.short_description = "newly released"

    def num_errors(self):
        return len(self.errors)

    num_errors.short_description = "crawl errors"

    def show_errors(self):
        dumped = json.dumps(self.errors, indent=4)
        dumped = dumped.replace(r"\n", "<br>                    ")
        return mark_safe("<pre style='display: inline-block'>{}</pre>".format(dumped))

    def __str__(self):
        return self.started.strftime("%Y-%m-%d, %H:%M")

    class Meta:
        ordering = ["-started"]


class MemberProfile(models.Model):
    bp_member_number = models.IntegerField()
    zoho_id = models.CharField(max_length=255, default="")

    def zoho_url(self):
        return "https://creator.zoho.com/{}/{}/{}/record-edit/{}/{}".format(
            settings.ZOHO_OWNER_NAME,
            settings.ZOHO_APPLICATION_LINK_NAME,
            settings.ZOHO_PROFILE_FORM_NAME,
            settings.ZOHO_PROFILE_VIEW_NAME,
            self.zoho_id,
        )

    def current_status(self):
        return self.contactcheck_set.latest("created")

    def __str__(self):
        return str(self.bp_member_number)


class ContactCheck(models.Model):
    class STATUS:
        not_found = "not_found"
        found_released_zoho_agrees = "found_released_zoho_agrees"
        found_released_zoho_disagrees = "found_released_zoho_disagrees"
        found_unknown_facility = "found_unknown_facility"
        found_facility_matches = "found_facility_matches"
        found_facility_differs_zoho_has = "found_facility_differs_zoho_has"
        found_facility_differs_zoho_lacks = "found_facility_differs_zoho_lacks"

    update_run = models.ForeignKey(UpdateRun)
    member = models.ForeignKey(MemberProfile)
    raw_facility_name = models.CharField(blank=True, max_length=255)
    facility = models.ForeignKey(Facility, blank=True, null=True)
    administrator = models.ForeignKey(FacilityAdministrator, blank=True, null=True)
    entry_before = JSONField()
    entry_after = JSONField()
    search_result = JSONField()
    entry_changed = models.BooleanField(default=False)
    status = models.CharField(
        max_length=255,
        choices=(
            (STATUS.not_found, "Not Found"),
            (
                STATUS.found_unknown_facility,
                "Found search result, but facility unknown",
            ),
            (STATUS.found_facility_matches, "Found, facility matches zoho's"),
            (
                STATUS.found_facility_differs_zoho_has,
                "Found, facility differs, zoho has facility",
            ),
            (
                STATUS.found_facility_differs_zoho_lacks,
                "Found, facility differs, zoho lacks facility",
            ),
            (STATUS.found_released_zoho_agrees, "Found, released, zoho agrees"),
            (STATUS.found_released_zoho_disagrees, "Found, released, zoho disagrees"),
        ),
    )

    created = models.DateTimeField(auto_now_add=True)

    def facility_name(self):
        if self.facility_id:
            return self.facility.name
        else:
            return None

    def contact_name(self):
        return " ".join(
            (self.entry_before.get("First_Name"), self.entry_before.get("Last_Name"))
        )

    def changes(self):
        before = self.entry_before
        after = (
            self.entry_after[0]
            if isinstance(self.entry_after, list)
            else self.entry_after
        )
        before_keys = set(before.keys())
        after_keys = set(after.keys())
        added = after_keys - before_keys
        removed = before_keys - after_keys
        changed = [k for k in after_keys if k in before_keys and after[k] != before[k]]
        html = []
        removed_tmpl = (
            "<div style='color: #900; text-decoration: line-through'>-{}: {}</div>"
        )
        added_tmpl = "<div style='color: #090'>+{}: {}</div>"
        changed_tmpl = "<div>{}: <span style='color: #900; text-decoration: line-through'>{}</span> <span style='color: #090'>{}</span></div>"
        for key in sorted(removed):
            html.append(removed_tmpl.format(escape(key), escape(before[key])))
        for key in sorted(added):
            html.append(added_tmpl.format(escape(key), escape(after[key])))
        for key in sorted(changed):
            html.append(
                changed_tmpl.format(
                    escape(key), escape(before[key]), escape(after[key])
                )
            )
        return mark_safe(
            "<div style='display: inline-block'>{}</div>".format("\n".join(html))
        )

    class Meta:
        verbose_name = "Member address check"
        verbose_name_plural = "Member address checks"
        ordering = ["-created"]
        get_latest_by = "created"

    def __str__(self):
        return "{} {} {}".format(
            self.member, self.status, self.created.strftime("%Y-%m-%d")
        )

    def get_absolute_url(self):
        return urlresolvers.reverse(
            "admin:blackandpink_contactcheck_change", args=(self.pk,)
        )


class FacilityRun(models.Model):
    started = models.DateTimeField(auto_now_add=True)
    finished = models.DateTimeField(blank=True, null=True, unique=True)

    objects = FinishedManager()

    def __str__(self):
        return "{} {}".format(self.started, self.finished)

    class Meta:
        ordering = ["-started"]
        get_latest_by = "finished"


class UnknownFacility(models.Model):
    zoho_id = models.CharField(max_length=255, unique=True)
    current_address_count = models.IntegerField(
        help_text="How many profiles are listed with this as the current address?"
    )
    flat_address = models.TextField(verbose_name="Unmatched address")
    state = models.CharField(blank=True, max_length=255)
    address_valid = models.BooleanField(default=True)
    comment = models.TextField(blank=True)
    created = models.DateTimeField(auto_now_add=True)

    def best_match_score(self):
        try:
            return self.unknownfacilitymatch_set.all().order_by("-score")[0].score
        except IndexError:
            return None

    def zoho_url(self):
        return "https://creator.zoho.com/{}/{}/{}/record-edit/{}/{}".format(
            settings.ZOHO_OWNER_NAME,
            settings.ZOHO_APPLICATION_LINK_NAME,
            settings.ZOHO_FACILITIES_FORM_NAME,
            settings.ZOHO_FACILITIES_VIEW_NAME,
            self.zoho_id,
        )

    def zoho_url_link(self):
        zoho_url = self.zoho_url()
        return mark_safe(
            "<a href='{}' target='_blank'>{}</a>".format(zoho_url, zoho_url)
        )

    def google_it(self):
        name = self.flat_address.split("\n")[0]
        name = escape(name)
        qname = urllib.parse.quote(name)
        return mark_safe(
            "<a href='https://www.google.com/?q={}' target='_blank'>Google: {}</a>".format(
                qname, name
            )
        )

    def zoho_address(self):
        return mark_safe(
            "<pre style='display: inline-block'>{}</pre>".format(
                escape(self.flat_address)
            )
        )

    def __str__(self):
        return self.zoho_url()

    class Meta:
        verbose_name = "Unmatched zoho facility"
        verbose_name_plural = "Unmatched zoho facilities"
        ordering = ["-current_address_count"]


class UnknownFacilityMatch(models.Model):
    unknown_facility = models.ForeignKey(UnknownFacility)
    match = models.ForeignKey(Facility)
    score = models.IntegerField()
    breakdown = JSONField()

    def breakdown_description(self):
        if "fatal" in self.breakdown:
            text = "Rejected because of {}".format(self.breakdown["fatal"])
        elif self.breakdown.get("street_total", 100) < 90:
            text = "Rejected because the address match score is too low."
        elif (
            self.breakdown.get("street_total", 100) == 100
            and self.breakdown.get("name", 100) < 50
        ):
            text = "Rejected because the name match score is too low."
        else:
            text = ""

        breakdown = {}
        breakdown.update(self.breakdown)
        parts = []
        if "fatal" in breakdown:
            breakdown.pop("fatal")
        for v, k in sorted([(v, k) for k, v in breakdown.items()]):
            parts.append(
                "<li>{}: {}</li>".format(escape(k.replace("_", " ")), escape(v))
            )
        return mark_safe(
            "<p><b>{}</b></p><p>Match scores:</p><ul>{}</ul>".format(
                text, "\n".join(parts)
            )
        )

    def facility_address(self):
        return self.match.flat_address()

    def facility_source_url(self):
        if self.match.provenance_url:
            url = escape(self.match.provenance_url)
            return mark_safe('<a href="{}" target="_blank">{}</a>'.format(url, url))
        return self.match.provenance

    class Meta:
        verbose_name = "Rejected facility match"
        verbose_name_plural = "Rejected facility matches"
        ordering = ["-score"]
