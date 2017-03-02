from django.contrib import admin

from blackandpink.models import UpdateRun, MemberProfile, ContactCheck, UnknownFacility, UnknownFacilityMatch, FacilityRun
from inmatelocator.admin_base import BaseAdmin

class UpdateRunAdmin(BaseAdmin):
    list_display = [
        'started',
        'finished',
        'complete', 

        'fac_matches',
        'moved',
        'released_zoho_disagrees',
        'unknown_fac',
        'not_found',
        'num_errors',
    ]
    date_hierarchy = 'started'
    readonly_fields = [
        'started',
        'finished',
        'total_count',
        'complete',
        'fac_matches',
        'moved',
        'released_zoho_disagrees',
        'unknown_fac',
        'not_found',
        'num_errors',
        'show_errors',
    ]
    exclude = ['errors']

    def changelist_view(self, request, extra_context=None):
        if extra_context is None:
            extra_context = {}
        try:
            started = UpdateRun.objects.get_unfinished()
        except UpdateRun.DoesNotExist:
            started = None
        if started:
            extra_context['updaterun_started'] = started.started
        else:
            extra_context['updaterun_started'] = None
        return super(UpdateRunAdmin, self).changelist_view(request, extra_context)
    
admin.site.register(UpdateRun, UpdateRunAdmin)

#class FacilityRunAdmin(BaseAdmin):
#    list_display = ['started', 'finished']
#    readonly_fields = ['started', 'finished']
#admin.site.register(FacilityRun, FacilityRunAdmin)
    

#class MemberProfileAdmin(BaseAdmin):
#    list_display = ['bp_member_number', 'zoho_url', 'current_status']
#    search_fields = ['bp_member_number', 'zoho_id']
#    readonly_fields = ['bp_member_number', 'zoho_id', 'zoho_url', 'current_status']
#admin.site.register(MemberProfile, MemberProfileAdmin)

class ContactCheckAdmin(BaseAdmin):
    list_display = ['member', 'contact_name', 'created', 'status', 'raw_facility_name', 'facility_name', 'administrator']
    list_filter = ['status', 'entry_changed', 'administrator', 'update_run']
    search_fields = ['member__bp_member_number', 'raw_facility_name']
    date_hierarchy = 'created'
    readonly_fields = ['update_run', 'member', 'contact_name', 'raw_facility_name', 'facility', 'administrator', 'changes', 'entry_before', 'entry_after', 'search_result', 'entry_changed', 'status']
    list_per_page = 5
    def has_add_permission(self, request):
        return False
admin.site.register(ContactCheck, ContactCheckAdmin)

class UnknownFacilityMatchInline(admin.TabularInline):
    model = UnknownFacilityMatch
    readonly_fields = ['match', 'facility_address', 'score', 'breakdown_description', 'facility_source_url']
    exclude = ['breakdown']
    extra = 0
    max_num = 0
    def has_add_permission(self, request):
        return False

class UnknownFacilityAdmin(BaseAdmin):
    list_display = ['flat_address', 'current_address_count', 'address_valid', 'best_match_score', 'state']
    list_filter = ['address_valid', 'state', 'current_address_count']
    search_fields = ['flat_address', 'zoho_id']
    readonly_fields = ['created', 'zoho_id', 'current_address_count', 'zoho_address', 'address_valid', 'comment', 'state', 'zoho_url_link','google_it']
    inlines = [UnknownFacilityMatchInline]
    exclude = ['zoho_url', 'flat_address']

    def changelist_view(self, request, extra_context=None):
        if extra_context is None:
            extra_context = {}
        extra_context['facilityrun_latest'] = FacilityRun.objects.latest()
        try:
            started = FacilityRun.objects.get_unfinished()
        except FacilityRun.DoesNotExist:
            started = None
        if started:
            extra_context['facilityrun_started'] = started.started
        else:
            extra_context['facilityrun_started'] = None
        return super(UnknownFacilityAdmin, self).changelist_view(request, extra_context)
admin.site.register(UnknownFacility, UnknownFacilityAdmin)
