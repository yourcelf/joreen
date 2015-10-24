from django.db import models
from django.utils import timezone
from facilities.models import Facility
from localflavor.us.models import USStateField, USPostalCodeField, PhoneNumberField

def choices(*args):
    return [(a,a) for a in args]

class Chapter(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class Language(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

# Create your models here.
class MemberProfile(models.Model):
    # Identity
    bp_member_number = models.IntegerField(verbose_name="B&P Member Number")
    preferred_name = models.CharField(max_length=255, blank=True)
    pronoun = models.CharField(max_length=255, blank=True)
    first_name = models.CharField(max_length=255, blank=True)
    middle_name = models.CharField(max_length=255, blank=True)
    last_name = models.CharField(max_length=255, blank=True)
    suffix = models.CharField(max_length=255, blank=True)
    number = models.CharField(max_length=255, blank=True)
    bio = models.TextField()
    status = models.CharField(max_length=255,
            choices=choices("Incarcerated", "Released", "Address Not Found", "Deceased"))
    birthday = models.DateTimeField(null=True)

    faith_for_sort = models.CharField(max_length=255, choices=choices(
        "Christian", "Other", "Wiccan", "Buddhist", "Pagan", "Muslim",
        "Jewish", "Native American", "Athiest", "Hindu"
    ), blank=True)
    faith_in_own_words = models.CharField(max_length=255, blank=True)
    gender_sex_for_sort = models.CharField(max_length=255, choices=choices(
        "Cisman", "Ciswoman", "Trans woman", "Questioning", "Gender non-conforming",
        "Genderqueer", "Intersex", "Trans man", "Two-Spirit"
    ), blank=True)
    gender_in_own_words = models.CharField(max_length=255, blank=True)
    sexuality_for_sort = models.CharField(max_length=255, choices=choices(
        "Bisexual", "Gay", "Straight", "Queer", "Lesbian",
        "Attracted to Men", "Attracted to Transwomen", "Asexual"
    ), blank=True)
    sexuality_in_own_words = models.CharField(max_length=255, blank=True)
    race_ethnicity_for_sort = models.CharField(max_length=255, choices=choices(
        "White", "Black", "Mixed", "Latina / Latino", "American Indian",
        "Asian", "Arab"
    ))
    race_ethnicity_in_own_words = models.CharField(max_length=255)
    hiv_status = models.CharField(max_length=255,
        choices=choices("Negative", "Positive"), blank=True)
    languages = models.ManyToManyField(Language, null=True)
    portrait_picture = models.TextField()
    permission_to_display_doc_portrait_picture = models.NullBooleanField()
    types_of_pen_pals_looking_for = models.CharField(max_length=255)
    wants_to_have_pen_pal_friendship = models.NullBooleanField()
    wants_to_have_pen_pal_romance = models.NullBooleanField()
    wants_to_write_about_social_justice_activism = models.NullBooleanField()
    wants_to_write_sexy_erotic_letters = models.NullBooleanField()
    webpage = models.URLField()
    email = models.EmailField()

    # Address
    name_for_letters = models.CharField(max_length=255)
    cell_block_info = models.CharField(max_length=255, blank=True, verbose_name="Cell/Block Info")
    facility = models.ForeignKey(Facility, null=True, blank=True)
    in_solitary_confinement = models.NullBooleanField()
    release_date = models.DateTimeField(null=True)

    # Non-facility address
    address1 = models.CharField(blank=True, help_text="Leave blank if in a facility")
    address2 = models.CharField(blank=True, help_text="Leave blank if in a facility")
    address3 = models.CharField(blank=True, help_text="Leave blank if in a facility")
    city = models.CharField(blank=True, help_text="Leave blank if in a facility")
    state = USStateField(blank=True, help_text="Leave blank if in a facility")
    zip = USPostalCodeField(blank=True, help_text="Leave blank if in a facility")

    # Management
    chapter_affiliation = models.ForeignKey(Chapter, null=True)
    current_address_method = models.CharField(max_length=255, choices=choices(
        "Envelope or Letter", "Online Search", "Freeworld Friend/Family", "Autoupdater"
    ))
    date_address_current = models.DateTimeField()

    can_write_to_people_under_18_years_old = models.NullBooleanField()

    on_pen_pal_list = models.NullBooleanField()
    on_card_party_list = models.NullBooleanField()
    on_p2p_list = models.CharField(max_length=255, choices=choices(
        "No", "Yes", "Yes- Only Out of State Prisoners"
    ), blank=True)
    on_erotica_list = models.NullBooleanField()
    hot_pink_erotica = models.CharField(max_length=255, choices=choices(
        'Requested erotica and/or HOT PINK (not just "Wants to Write Sexy/Erotic Letters")',
        'Has submitted art or stories for HOT PINK (Email typed entries to hotpink@blackandpink.org OR set aside art/stories/feedback for pick up), Requested erotica and/or HOT PINK (not just "Wants to Write Sexy/Erotic Letters")',
        'Has submitted art or stories for HOT PINK (Email typed entries to hotpink@blackandpink.org OR set aside art/stories/feedback for pick up)',
        'HOT PINK rejected, send other erotica]'
    ), blank=True)
    has_free_world_pen_pal = models.CharField(max_length=255, choices=choices(
        "Not that B&P knows of", "Yes", "No"
    ), blank=True)
    has_reading_disability_needs_typed_printed_letters = models.NullBooleanField()
    how_many_people_write_you_now = models.IntegerField(null=True)
    how_they_heard_of_b_p = models.CharField(max_length=255, blank=True)

    discrete_in_letters = models.NullBooleanField()
    federal_prisoner_with_access_to_corrlinks = models.NullBooleanField()
    is_there_a_first_letter = models.NullBooleanField()

    profile_note = models.TextField()

    send_newsletter = models.CharField(max_length=255, choices=choices(
        "Yes, English",
        "Yes, Spanish and English",
        "Yes, Spanish",
        "No, no longer incarcerated!",
        "No, per request",
        "No, unsure why returned",
        "No, see profile note!",
        "No, other",
        "No, refused by prison (unspecific)",
        "No, refused by prison for pen-pal",
        "No, refused by prison for promotion of homosexuality",
        "No, refused by prison for inmate-to-inmate communication"
    ), default="Yes, English")


    # Meta
    created = models.DateTimeField(default=timezone.now)
    modified = models.DateTimeField(auto_now=True)
    last_modified_by = models.ForeignKey('auth.User', null=True)
