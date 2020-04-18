from django.conf.urls import include, url
import blackandpink.views

urlpatterns = [
    url(r'start_update_run', blackandpink.views.start_update_run, name='start_update_run'),
    url(r'start_facility_run', blackandpink.views.start_facility_run, name='start_facility_run'),
]
