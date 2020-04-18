from django.conf.urls import url
import api.views

urlpatterns = [
    url(r"^states.json", api.views.states),
    url(r"^search.json", api.views.search),
]
