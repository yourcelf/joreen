from django.conf.urls import include, url
from django.contrib import admin

admin.site.index_template = "admin/view_not_change_index.html"
admin.site.site_header = "Joreen"
admin.site.site_title = "Joreen Facility Updater"

urlpatterns = [
    url(r"^admin/", admin.site.urls),
    url(r"^account/", include("django.contrib.auth.urls")),
    url(r"^api/", include("api.urls")),
    url(r"^blackandpink/", include("blackandpink.urls")),
    url(r"", include("frontend.urls")),
]
