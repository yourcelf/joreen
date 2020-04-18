from django.contrib import admin


class BaseAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, *args, **kwargs):
        return False

    def changelist_view(self, request, extra_context=None):
        if extra_context is None:
            extra_context = {}
        extra_context["title"] = "Select {} to view".format(
            self.model._meta.verbose_name
        )
        return super(BaseAdmin, self).changelist_view(request, extra_context)

    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        if extra_context is None:
            extra_context = {}
        extra_context["title"] = "View {}".format(self.model._meta.verbose_name)
        return super(BaseAdmin, self).changeform_view(
            request, object_id, form_url, extra_context
        )
