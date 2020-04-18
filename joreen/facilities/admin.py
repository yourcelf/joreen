from django.contrib import admin

from facilities.models import *
from joreen.admin_base import BaseAdmin

class AlternateNameInline(admin.StackedInline):
    model = AlternateName
    readonly_fields = ['name']
    extra = 0
    max_num = 0

class FacilityAdmin(BaseAdmin):
    list_display = ['name', 'code', 'state', 'address1', 'administrator', 'general']
    list_filter = ['general', 'administrator', 'operator', 'state', 'type']
    search_fields = ['code', 'name', 'address1', 'address2', 'city', 'state', 'zip']
    readonly_fields = ['code', 'name', 'city', 'address1', 'address2', 'state', 'zip', 'phone', 'general', 'type', 'administrator', 'operator', 'provenance', 'provenance_url']
    inlines = [AlternateNameInline]
admin.site.register(Facility, FacilityAdmin)

class FacilityAdministratorAdmin(BaseAdmin):
    search_fields = ['name']
    readonly_fields = ['name']
#admin.site.register(FacilityAdministrator, FacilityAdministratorAdmin)

class FacilityOperatorAdmin(BaseAdmin):
    search_fields = ['name']
    readonly_fields = ['name']
#admin.site.register(FacilityOperator, FacilityOperatorAdmin)

class FacilityTypeAdmin(BaseAdmin):
    search_fields = ['name']
    readonly_fields = ['name']
#admin.site.register(FacilityType, FacilityTypeAdmin)
