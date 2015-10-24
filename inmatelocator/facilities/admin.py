from django.contrib import admin

from facilities.models import *

class AlternateNameInline(admin.StackedInline):
    model = AlternateName

class FacilityAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'state', 'administrator', 'operator', 'type']
    list_filter = ['state', 'type', 'administrator', 'operator']
    search_fields = ['code', 'name', 'address1', 'address2', 'address3', 'city', 'state', 'zip']
    inlines = [AlternateNameInline]
admin.site.register(Facility, FacilityAdmin)

class FacilityAdministratorAdmin(admin.ModelAdmin):
    search_fields = ['name']
admin.site.register(FacilityAdministrator, FacilityAdministratorAdmin)

class FacilityOperatorAdmin(admin.ModelAdmin):
    search_fields = ['name']
admin.site.register(FacilityOperator, FacilityOperatorAdmin)

class FacilityTypeAdmin(admin.ModelAdmin):
    search_fields = ['name']
admin.site.register(FacilityType, FacilityTypeAdmin)
