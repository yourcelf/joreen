from django.contrib import admin

from blackandpink.models import UpdateRun, MemberProfile, ContactCheck, UnknownFacility, UnknownFacilityMatch

class UpdateRunAdmin(admin.ModelAdmin):
    list_display = [
        'started',
        'finished', 

        'found_fac_matches',
        'found_fac_differs_zoho_has',
        'found_fac_differs_zoho_lacks',
        'found_unknown_fac',
        'not_found',
        'num_errors',
    ]
    date_hierarchy = 'started'
    readonly_fields = [
        'started',
        'finished',
        'found_fac_matches',
        'found_fac_differs_zoho_has',
        'found_fac_differs_zoho_lacks',
        'found_unknown_fac',
        'not_found',
        'num_errors',
        'show_errors',
    ]
    exclude = ['errors']
admin.site.register(UpdateRun, UpdateRunAdmin)

class MemberProfileAdmin(admin.ModelAdmin):
    list_display = ['bp_member_number', 'zoho_url', 'current_status']
    search_fields = ['bp_member_number']
admin.site.register(MemberProfile, MemberProfileAdmin)

class ContactCheckAdmin(admin.ModelAdmin):
    list_display = ['member', 'contact_name', 'created', 'status', 'raw_facility_name', 'facility_name', 'administrator']
    list_filter = ['status', 'entry_changed', 'administrator', 'update_run']
    search_fields = ['member__bp_member_number', 'raw_facility_name']
    date_hierarchy = 'created'
    readonly_fields = ['update_run', 'member', 'contact_name', 'raw_facility_name', 'facility', 'administrator', 'entry_before', 'entry_after', 'search_result', 'entry_changed', 'status']
admin.site.register(ContactCheck, ContactCheckAdmin)

class UnknownFacilityMatchInline(admin.TabularInline):
    model = UnknownFacilityMatch
    readonly_fields = ['match', 'facility_address', 'score', 'breakdown_description', 'facility_source_url']
    exclude = ['breakdown']
    extra = 0
    max_num = 0

class UnknownFacilityAdmin(admin.ModelAdmin):
    list_display = ['flat_address', 'current_address_count', 'address_valid', 'best_match_score', 'state']
    list_filter = ['address_valid', 'state', 'current_address_count']
    search_fields = ['flat_address', 'zoho_id']
    readonly_fields = ['created', 'zoho_id', 'current_address_count', 'zoho_address', 'address_valid', 'comment', 'state', 'zoho_url_link','google_it']
    inlines = [UnknownFacilityMatchInline]
    exclude = ['zoho_url', 'flat_address']
admin.site.register(UnknownFacility, UnknownFacilityAdmin)
