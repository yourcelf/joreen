from django.contrib import admin

from blackandpink.models import UpdateRun, MemberProfile, ContactCheck

class UpdateRunAdmin(admin.ModelAdmin):
    list_display = ['started', 'finished', 'num_ok',
            'num_not_found', 'num_unknown_facility', 'num_seemingly_released']
    date_hierarchy = 'started'
admin.site.register(UpdateRun, UpdateRunAdmin)

class MemberProfileAdmin(admin.ModelAdmin):
    list_display = ['bp_member_number', 'zoho_url', 'current_status']
    search_fields = ['bp_member_number']
admin.site.register(MemberProfile, MemberProfileAdmin)

class ContactCheckAdmin(admin.ModelAdmin):
    list_display = ['member', 'created', 'status', 'raw_facility_name']
    list_filter = ['status', 'entry_changed']
    search_fields = ['member__bp_member_number', 'raw_facility_name']
    date_hierarchy = 'created'
admin.site.register(ContactCheck, ContactCheckAdmin)
