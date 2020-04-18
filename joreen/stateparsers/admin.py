from django.contrib import admin

from stateparsers.models import FacilityNameResult, NetlocThrottle
from joreen.admin_base import BaseAdmin


class FacilityNameResultAdmin(BaseAdmin):
    list_display = ["name", "facility_url", "administrator"]
    list_filter = ["administrator"]
    search_fields = ["name"]
    readonly_fields = ["administrator", "name", "facility_url"]


admin.site.register(FacilityNameResult, FacilityNameResultAdmin)


class NetlocThrottleAdmin(BaseAdmin):
    list_display = ["netloc", "wait_until", "as_date"]
    readonly_fields = ["netloc", "wait_until", "as_date"]


# admin.site.register(NetlocThrottle, NetlocThrottleAdmin)
