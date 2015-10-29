from django.contrib import admin

from stateparsers.models import FacilityNameResult

# Register your models here.
class FacilityNameResultAdmin(admin.ModelAdmin):
    list_display = ['name', 'facility_url', 'administrator']
    list_filter = ['administrator']
    search_fields = ['name']
admin.site.register(FacilityNameResult, FacilityNameResultAdmin)
