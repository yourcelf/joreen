from django.contrib import admin

from stateparsers.models import FacilityNameResult, NetlocThrottle

class FacilityNameResultAdmin(admin.ModelAdmin):
    list_display = ['name', 'facility_url', 'administrator']
    list_filter = ['administrator']
    search_fields = ['name']
admin.site.register(FacilityNameResult, FacilityNameResultAdmin)

class NetlocThrottleAdmin(admin.ModelAdmin):
    list_display = ['netloc', 'wait_until', 'as_date']
admin.site.register(NetlocThrottle, NetlocThrottleAdmin)
