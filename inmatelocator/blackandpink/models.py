import json
from django.db import models
from django.utils import timezone
from facilities.models import Facility, FacilityAdministrator
from localflavor.us.models import USStateField, USPostalCodeField, PhoneNumberField
import urllib
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.conf import settings
from jsonfield import JSONField

class FinishedManager(models.Manager):
    def get_unfinished(self):
        return self.get(finished__isnull=True)

class UpdateRun(models.Model):
    started = models.DateTimeField(auto_now_add=True)
    finished = models.DateTimeField(blank=True, null=True, unique=True)
    errors = JSONField()

    objects = FinishedManager()

    def not_found(self):
        return self.contactcheck_set.filter(status=ContactCheck.STATUS.not_found).count()

    def unknown_fac(self):
        return self.contactcheck_set.filter(status=ContactCheck.STATUS.found_unknown_facility).count()

    def fac_matches(self):
        return self.contactcheck_set.filter(status=ContactCheck.STATUS.found_facility_matches).count()

    def fac_differs_zoho_has(self):
        return self.contactcheck_set.filter(status=ContactCheck.STATUS.found_facility_differs_zoho_has).count()

    def fac_differs_zoho_lacks(self):
        return self.contactcheck_set.filter(status=ContactCheck.STATUS.found_facility_differs_zoho_lacks).count()
    def released_zoho_agrees(self):
        return self.contactcheck_set.filter(status=ContactCheck.STATUS.found_released_zoho_agrees).count()
    def released_zoho_disagrees(self):
        return self.contactcheck_set.filter(status=ContactCheck.STATUS.found_released_zoho_disagrees).count()

    def num_errors(self):
        return len(self.errors)

    def show_errors(self):
        dumped = json.dumps(self.errors, indent=4)
        dumped = dumped.replace(r'\n', "<br>                    ")
        return mark_safe("<pre style='display: inline-block'>{}</pre>".format(dumped))

    def __str__(self):
        return self.started.strftime("%Y-%m-%d, %H:%M")

    class Meta:
        ordering = ['-started']

class MemberProfile(models.Model):
    bp_member_number = models.IntegerField()

    def zoho_url(self):
        return "https://creator.zoho.com/{}/{}/{}/record-edit/{}/{}".format(
            settings.ZOHO_OWNER_NAME,
            settings.ZOHO_APPLICATION_LINK_NAME,
            settings.ZOHO_PROFILE_FORM_NAME,
            settings.ZOHO_PROFILE_VIEW_NAME,
            self.bp_member_number)

    def current_status(self):
        return self.contactcheck_set.latest('created')

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
    status = models.CharField(max_length=255, choices=(
        (STATUS.not_found, "Not Found"),
        (STATUS.found_unknown_facility, "Found search result, but facility unknown"),
        (STATUS.found_facility_matches, "Found, facility matches zoho's"),
        (STATUS.found_facility_differs_zoho_has, "Found, facility differs, zoho has facility"),
        (STATUS.found_facility_differs_zoho_lacks, "Found, facility differs, zoho lacks facility"),
        (STATUS.found_released_zoho_agrees, "Found, released, zoho agrees"),
        (STATUS.found_released_zoho_disagrees, "Found, released, zoho disagrees"),
    ))

    created = models.DateTimeField(auto_now_add=True)

    def facility_name(self):
        if self.facility_id:
            return self.facility.name
        else:
            return None

    def contact_name(self):
        return " ".join((self.entry_before.get('First_Name'), self.entry_before.get('Last_Name')))

    class Meta:
        verbose_name = 'Member address check'
        verbose_name_plural = 'Member address checks'
        ordering = ['-created']
        get_latest_by = 'created'

    def __str__(self):
        return "{} {} {}".format(self.member, self.status, self.created.strftime("%Y-%m-%d"))

class FacilityRun(models.Model):
    started = models.DateTimeField(auto_now_add=True)
    finished = models.DateTimeField(blank=True, null=True, unique=True)

    objects = FinishedManager()

    def __str__(self):
        return "{} {}".format(self.started, self.finished)

    class Meta:
        ordering = ['-started']

class UnknownFacility(models.Model):
    zoho_id = models.CharField(max_length=255, unique=True)
    current_address_count = models.IntegerField(help_text="How many profiles are listed with this as the current address?")
    flat_address = models.TextField(verbose_name="Unmatched address")
    state = models.CharField(blank=True, max_length=255)
    address_valid = models.BooleanField(default=True)
    comment = models.TextField(blank=True)
    created = models.DateTimeField(auto_now_add=True)

    def best_match_score(self):
        try:
            return self.unknownfacilitymatch_set.all().order_by('-score')[0].score
        except IndexError:
            return None

    def zoho_url(self):
        return "https://creator.zoho.com/{}/{}/{}/record-edit/{}/{}".format(
            settings.ZOHO_OWNER_NAME,
            settings.ZOHO_APPLICATION_LINK_NAME,
            settings.ZOHO_FACILITIES_FORM_NAME,
            settings.ZOHO_FACILITIES_VIEW_NAME,
            self.zoho_id)

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
            "<a href='https://www.google.com/?q={}' target='_blank'>Google: {}</a>".format(qname, name)
        )

    def zoho_address(self):
        return mark_safe("<pre style='display: inline-block'>{}</pre>".format(escape(self.flat_address)))

    def __str__(self):
        return self.zoho_url()

    class Meta:
        verbose_name = "Unmatched zoho facilities"
        verbose_name_plural = "Unmatched zoho facilities"
        ordering = ['-current_address_count']

class UnknownFacilityMatch(models.Model):
    unknown_facility = models.ForeignKey(UnknownFacility)
    match = models.ForeignKey(Facility)
    score = models.IntegerField()
    breakdown = JSONField()

    def breakdown_description(self):
        if 'fatal' in self.breakdown:
            text = "Rejected because of {}".format(self.breakdown['fatal'])
        elif self.breakdown.get('street_total', 100) < 90:
            text = "Rejected because the address match score is too low."
        elif self.breakdown.get('street_total', 100) == 100 and \
                self.breakdown.get('name', 100) < 50:
            text = "Rejected because the name match score is too low."
        else:
            text = ""

        breakdown = {}
        breakdown.update(self.breakdown)
        parts = []
        if 'fatal' in breakdown:
            breakdown.pop('fatal')
        for v,k in sorted([(v, k) for k,v in breakdown.items()]):
            parts.append("<li>{}: {}</li>".format(escape(k.replace('_', ' ')), escape(v)))
        return mark_safe("<p><b>{}</b></p><p>Match scores:</p><ul>{}</ul>".format(text, "\n".join(parts)))

    def facility_address(self):
        return self.match.flat_address()

    def facility_source_url(self):
        if self.match.provenance_url:
            url = escape(self.match.provenance_url)
            return mark_safe('<a href="{}" target="_blank">{}</a>'.format(url, url))
        return self.match.provenance

    class Meta:
        verbose_name = 'Rejected facility match'
        verbose_name_plural = 'Rejected facility matches'
        ordering = ['-score']

#def choices(*args):
#    return [(a,a) for a in args]
#class Chapter(models.Model):
#    name = models.CharField(max_length=255)
#
#    def __str__(self):
#        return self.name
#
#class Language(models.Model):
#    name = models.CharField(max_length=255)
#
#    def __str__(self):
#        return self.name
#
## Create your models here.
#class MemberProfile(models.Model):
#    # Identity
#    bp_member_number = models.IntegerField(verbose_name="B&P Member Number")
#    preferred_name = models.CharField(max_length=255, blank=True)
#    pronoun = models.CharField(max_length=255, blank=True)
#    first_name = models.CharField(max_length=255, blank=True)
#    middle_name = models.CharField(max_length=255, blank=True)
#    last_name = models.CharField(max_length=255, blank=True)
#    suffix = models.CharField(max_length=255, blank=True)
#    number = models.CharField(max_length=255, blank=True)
#    bio = models.TextField()
#    status = models.CharField(max_length=255,
#            choices=choices("Incarcerated", "Released", "Address Not Found", "Deceased"))
#    birthday = models.DateTimeField(null=True)
#
#    faith_for_sort = models.CharField(max_length=255, choices=choices(
#        "Christian", "Other", "Wiccan", "Buddhist", "Pagan", "Muslim",
#        "Jewish", "Native American", "Athiest", "Hindu"
#    ), blank=True)
#    faith_in_own_words = models.CharField(max_length=255, blank=True)
#    gender_sex_for_sort = models.CharField(max_length=255, choices=choices(
#        "Cisman", "Ciswoman", "Trans woman", "Questioning", "Gender non-conforming",
#        "Genderqueer", "Intersex", "Trans man", "Two-Spirit"
#    ), blank=True)
#    gender_in_own_words = models.CharField(max_length=255, blank=True)
#    sexuality_for_sort = models.CharField(max_length=255, choices=choices(
#        "Bisexual", "Gay", "Straight", "Queer", "Lesbian",
#        "Attracted to Men", "Attracted to Transwomen", "Asexual"
#    ), blank=True)
#    sexuality_in_own_words = models.CharField(max_length=255, blank=True)
#    race_ethnicity_for_sort = models.CharField(max_length=255, choices=choices(
#        "White", "Black", "Mixed", "Latina / Latino", "American Indian",
#        "Asian", "Arab"
#    ))
#    race_ethnicity_in_own_words = models.CharField(max_length=255)
#    hiv_status = models.CharField(max_length=255,
#        choices=choices("Negative", "Positive"), blank=True)
#    languages = models.ManyToManyField(Language, null=True)
#    portrait_picture = models.TextField()
#    permission_to_display_doc_portrait_picture = models.NullBooleanField()
#    types_of_pen_pals_looking_for = models.CharField(max_length=255)
#    wants_to_have_pen_pal_friendship = models.NullBooleanField()
#    wants_to_have_pen_pal_romance = models.NullBooleanField()
#    wants_to_write_about_social_justice_activism = models.NullBooleanField()
#    wants_to_write_sexy_erotic_letters = models.NullBooleanField()
#    webpage = models.URLField()
#    email = models.EmailField()
#
#    # Address
#    name_for_letters = models.CharField(max_length=255)
#    cell_block_info = models.CharField(max_length=255, blank=True, verbose_name="Cell/Block Info")
#    facility = models.ForeignKey(Facility, null=True, blank=True)
#    in_solitary_confinement = models.NullBooleanField()
#    release_date = models.DateTimeField(null=True)
#
#    # Non-facility address
#    address1 = models.CharField(blank=True, help_text="Leave blank if in a facility")
#    address2 = models.CharField(blank=True, help_text="Leave blank if in a facility")
#    address3 = models.CharField(blank=True, help_text="Leave blank if in a facility")
#    city = models.CharField(blank=True, help_text="Leave blank if in a facility")
#    state = USStateField(blank=True, help_text="Leave blank if in a facility")
#    zip = USPostalCodeField(blank=True, help_text="Leave blank if in a facility")
#
#    # Management
#    chapter_affiliation = models.ForeignKey(Chapter, null=True)
#    current_address_method = models.CharField(max_length=255, choices=choices(
#        "Envelope or Letter", "Online Search", "Freeworld Friend/Family", "Autoupdater"
#    ))
#    date_address_current = models.DateTimeField()
#
#    can_write_to_people_under_18_years_old = models.NullBooleanField()
#
#    on_pen_pal_list = models.NullBooleanField()
#    on_card_party_list = models.NullBooleanField()
#    on_p2p_list = models.CharField(max_length=255, choices=choices(
#        "No", "Yes", "Yes- Only Out of State Prisoners"
#    ), blank=True)
#    on_erotica_list = models.NullBooleanField()
#    hot_pink_erotica = models.CharField(max_length=255, choices=choices(
#        'Requested erotica and/or HOT PINK (not just "Wants to Write Sexy/Erotic Letters")',
#        'Has submitted art or stories for HOT PINK (Email typed entries to hotpink@blackandpink.org OR set aside art/stories/feedback for pick up), Requested erotica and/or HOT PINK (not just "Wants to Write Sexy/Erotic Letters")',
#        'Has submitted art or stories for HOT PINK (Email typed entries to hotpink@blackandpink.org OR set aside art/stories/feedback for pick up)',
#        'HOT PINK rejected, send other erotica]'
#    ), blank=True)
#    has_free_world_pen_pal = models.CharField(max_length=255, choices=choices(
#        "Not that B&P knows of", "Yes", "No"
#    ), blank=True)
#    has_reading_disability_needs_typed_printed_letters = models.NullBooleanField()
#    how_many_people_write_you_now = models.IntegerField(null=True)
#    how_they_heard_of_b_p = models.CharField(max_length=255, blank=True)
#
#    discrete_in_letters = models.NullBooleanField()
#    federal_prisoner_with_access_to_corrlinks = models.NullBooleanField()
#    is_there_a_first_letter = models.NullBooleanField()
#
#    profile_note = models.TextField()
#
#    send_newsletter = models.CharField(max_length=255, choices=choices(
#        "Yes, English",
#        "Yes, Spanish and English",
#        "Yes, Spanish",
#        "No, no longer incarcerated!",
#        "No, per request",
#        "No, unsure why returned",
#        "No, see profile note!",
#        "No, other",
#        "No, refused by prison (unspecific)",
#        "No, refused by prison for pen-pal",
#        "No, refused by prison for promotion of homosexuality",
#        "No, refused by prison for inmate-to-inmate communication"
#    ), default="Yes, English")
#
#
#    # Meta
#    created = models.DateTimeField(default=timezone.now)
#    modified = models.DateTimeField(auto_now=True)
#    last_modified_by = models.ForeignKey('auth.User', null=True)
